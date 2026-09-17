"""Persistent discovery queue, conservative budgets and explicit human admission."""
from datetime import datetime, timedelta, timezone
import time
import uuid
from psycopg.types.json import Jsonb
from .discovery_policy import assess, normalized_url, site_origin, next_window, retry_delay, POLICY
from .discovery_settings import enabled


class BudgetExhausted(RuntimeError):
    pass


class Budget:
    def __init__(self, db, seconds=180, requests=15):
        self.db = db
        self.deadline = time.monotonic()+max(1, min(seconds, 300))
        self.remaining = max(1, min(requests, 30))

    def reserve(self, max_bytes):
        if self.remaining <= 0 or time.monotonic() >= self.deadline:
            raise BudgetExhausted('discovery_run_budget_exhausted')
        if not 0 < max_bytes <= 4*1024*1024+65536:
            raise ValueError('invalid_request_byte_ceiling')
        row = self.db.execute("""INSERT INTO news_discovery_budget(day,requests_reserved,bytes_reserved)
          VALUES((now() AT TIME ZONE 'UTC')::date,1,%s)
          ON CONFLICT(day) DO UPDATE SET
            requests_reserved=news_discovery_budget.requests_reserved+1,
            bytes_reserved=news_discovery_budget.bytes_reserved+EXCLUDED.bytes_reserved,updated_at=now()
          WHERE news_discovery_budget.requests_reserved<120
            AND news_discovery_budget.bytes_reserved+EXCLUDED.bytes_reserved<=134217728
          RETURNING day""", (max_bytes,)).fetchone()
        if not row:
            raise BudgetExhausted('discovery_daily_budget_exhausted')
        # Reserve the maximum response, not an optimistic after-the-fact charge.
        # Failures/redirects consume reservations; no refund on uncertain I/O.
        self.remaining -= 1


def enqueue(db, kind, url, parent=None, depth=0):
    url = normalized_url(url)
    if kind not in ('site','feed') or depth < 0 or depth > 4:
        raise ValueError('invalid_discovery_task')
    return db.execute("""INSERT INTO news_discovery_tasks(kind,url,parent_url,depth)
      VALUES(%s,%s,%s,%s) ON CONFLICT(kind,url) DO NOTHING RETURNING id""",
      (kind,url,parent,depth)).fetchone()


def claim(db):
    token = uuid.uuid4()
    return db.execute("""WITH turn AS (
      UPDATE news_discovery_dispatch SET claims=claims+1 WHERE id=true RETURNING claims
    ), due AS (
      SELECT t.id FROM news_discovery_tasks t CROSS JOIN turn
      WHERE (status='queued' AND next_attempt_at<=now())
         OR (status='leased' AND lease_until<now())
      ORDER BY CASE WHEN kind=(CASE WHEN turn.claims%%3=0 THEN 'site' ELSE 'feed' END) THEN 0 ELSE 1 END,
        next_attempt_at,t.id
      FOR UPDATE OF t SKIP LOCKED LIMIT 1)
      UPDATE news_discovery_tasks t SET status='leased',lease_token=%s,
        lease_until=now()+interval '10 minutes',attempts=t.attempts+1
      FROM due WHERE t.id=due.id RETURNING t.*""", (token,)).fetchone()


def owned(db, task):
    row = db.execute("""SELECT id FROM news_discovery_tasks WHERE id=%s AND status='leased'
      AND lease_token=%s AND lease_until>now() FOR UPDATE""", (task['id'],task['lease_token'])).fetchone()
    if not row:
        raise ValueError('discovery_lease_lost')


def release(db, task, error=None, complete=False, delay=None):
    delay = delay or (retry_delay(task['attempts'],error) if error else timedelta(hours=6 if task['kind']=='feed' else 24))
    db.execute("""UPDATE news_discovery_tasks SET status=%s,next_attempt_at=now()+%s::interval,
      lease_token=NULL,lease_until=NULL,last_error=%s,
      last_success_at=CASE WHEN %s::text IS NULL THEN now() ELSE last_success_at END
      WHERE id=%s AND lease_token=%s""",
      ('complete' if complete else 'queued',delay,error,error,task['id'],task['lease_token']))


def finish_site(db, task, result):
    with db.transaction():
        owned(db,task)
        for url in result['feeds']:
            if not db.execute('SELECT id FROM news_feeds WHERE rss_url=%s',(url,)).fetchone():
                enqueue(db,'feed',url,result['final_url'],task['depth'])
        for url in result['sites']:
            enqueue(db,'site',url,result['final_url'],task['depth']+1)
        db.execute('UPDATE news_discovery_tasks SET link_cursor=%s WHERE id=%s',
            (result.get('next_link_cursor',0),task['id']))
        release(db,task,delay=timedelta(hours=1) if result.get('truncated_links') else None)


def finish_feed(db, task, result, now=None):
    now = now or datetime.now(timezone.utc)
    with db.transaction():
        owned(db,task)
        # Canonical final URL deduplicates feeds that redirect to the same feed.
        rss_url = result['final_url']
        if db.execute('SELECT id FROM news_feeds WHERE rss_url=%s',(rss_url,)).fetchone():
            release(db,task,complete=True)
            return 'already_registered'
        candidate = db.execute("""INSERT INTO news_discovery_candidates(rss_url,site_url)
          VALUES(%s,%s) ON CONFLICT(rss_url) DO UPDATE SET rss_url=EXCLUDED.rss_url
          RETURNING *""", (rss_url,site_origin(task.get('parent_url') or rss_url))).fetchone()
        if candidate['status'] in ('admitted','rejected'):
            release(db,task,complete=True)
            return candidate['status']
        db.execute("""INSERT INTO news_discovery_observations(candidate_id,payload,task_id,lease_token)
          VALUES(%s,%s,%s,%s) ON CONFLICT(lease_token) DO NOTHING""",
          (candidate['id'],Jsonb(result),task['id'],task['lease_token']))
        observations = db.execute("""SELECT observed_at,payload FROM news_discovery_observations
          WHERE candidate_id=%s ORDER BY observed_at DESC LIMIT 30""",(candidate['id'],)).fetchall()
        evaluation = assess(observations)
        status = 'awaiting_editorial_review' if evaluation['technical_ready'] else 'observing'
        db.execute("""UPDATE news_discovery_candidates SET status=%s,last_checked_at=%s,
          technical_evaluation=%s,last_error=NULL WHERE id=%s""",
          (status,now,Jsonb(evaluation),candidate['id']))
        db.execute('UPDATE news_discovery_tasks SET sample_cursor=%s WHERE id=%s',
            (result.get('next_sample_cursor',0),task['id']))
        release(db,task,delay=timedelta(hours=1) if result.get('budget_paused') else
            timedelta(days=1) if status=='awaiting_editorial_review' else None)
        return status


def fail_task(db, task, error, budget_pause=False):
    with db.transaction():
        owned(db,task)
        release(db,task,error=error,delay=timedelta(hours=1) if budget_pause else None)
        if task['kind']=='feed':
            db.execute("""INSERT INTO news_discovery_candidates(rss_url,site_url,last_checked_at,last_error)
              VALUES(%s,%s,now(),%s) ON CONFLICT(rss_url) DO UPDATE SET
                last_checked_at=now(),last_error=EXCLUDED.last_error
              WHERE news_discovery_candidates.status NOT IN ('admitted','rejected')""",
              (task['url'],site_origin(task.get('parent_url') or task['url']),error))


def review(db, candidate_id, actor, reason, evidence, accept=False, metadata=None, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(actor,str) or not actor.strip() or len(actor)>200:
        raise ValueError('invalid_reviewer')
    if not isinstance(reason,str) or len(reason.strip())<10 or len(reason)>2000:
        raise ValueError('invalid_review_reason')
    if not isinstance(evidence,list) or not 1 <= len(evidence) <= 20:
        raise ValueError('invalid_review_evidence')
    evidence = [normalized_url(value) for value in evidence]
    if accept:
        metadata = metadata or {}
        if any(not isinstance(metadata.get(k),str) or not metadata[k].strip() or len(metadata[k])>300
               for k in ('name','country','region')):
            raise ValueError('invalid_source_metadata')
    with db.transaction():
        candidate = db.execute('SELECT * FROM news_discovery_candidates WHERE id=%s FOR UPDATE',
            (candidate_id,)).fetchone()
        if not candidate:
            raise ValueError('discovery_candidate_not_found')
        if candidate['status'] in ('admitted','rejected'):
            raise ValueError('discovery_already_reviewed')
        if accept and (candidate['status']!='awaiting_editorial_review'
                       or not candidate['technical_evaluation'].get('technical_ready')
                       or candidate.get('last_error')
                       or not candidate.get('last_checked_at')
                       or now-candidate['last_checked_at']>timedelta(days=2)):
            raise ValueError('discovery_technical_review_required')
        feed_id = None
        effective = None
        if accept:
            feed = db.execute("""INSERT INTO news_feeds(rss_url,name,region,country,site_url,justification)
              VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(rss_url) DO NOTHING RETURNING id""",
              (candidate['rss_url'],metadata['name'].strip(),metadata['region'].strip(),
               metadata['country'].strip(),candidate['site_url'],reason.strip())).fetchone()
            if not feed:
                # Do not relabel an existing source or silently overwrite its
                # admission/revocation history through discovery.
                raise ValueError('discovery_source_already_registered')
            feed_id = feed['id']
            effective = next_window(now)
            db.execute("""INSERT INTO news_feed_admissions(feed_id,effective_at,actor,reason,evidence)
              VALUES(%s,%s,%s,%s,%s)""",(feed_id,effective,actor.strip(),reason.strip(),
                Jsonb({'urls':evidence,'policy':POLICY,'candidate_id':candidate_id})))
        status = 'admitted' if accept else 'rejected'
        db.execute("""UPDATE news_discovery_candidates SET status=%s,feed_id=%s,reviewed_at=%s,
          reviewer=%s,review_reason=%s,review_evidence=%s WHERE id=%s""",
          (status,feed_id,now,actor.strip(),reason.strip(),Jsonb(evidence),candidate_id))
        details = {'policy':POLICY,'reason':reason.strip(),'evidence':evidence,
            'effective_at':effective.isoformat() if effective else None,
            'ai_evaluated':False,'technical_evaluation':candidate['technical_evaluation']}
        db.execute("""INSERT INTO news_discovery_audit(actor,action,candidate_id,details)
          VALUES(%s,%s,%s,%s)""",(actor.strip(),status,candidate_id,Jsonb(details)))
        db.execute("""UPDATE news_discovery_tasks SET status='complete',lease_token=NULL,lease_until=NULL
          WHERE kind='feed' AND url=%s""",(candidate['rss_url'],))
        return {'status':status,'candidate_id':candidate_id,'feed_id':feed_id,**details}


def status(db):
    configuration={'enabled':enabled('BORIS_DISCOVERY_ENABLED'),
        'dynamic_inventory_enabled':enabled('BORIS_DYNAMIC_INVENTORY')}
    schema=db.execute("SELECT to_regclass('public.news_discovery_tasks') IS NOT NULL ready").fetchone()['ready']
    base={'schema_version':1,'policy':POLICY,'ai_evaluated':False,
        'measured_at':datetime.now(timezone.utc).isoformat(),'configuration':configuration,'schema_ready':schema}
    if not schema:return {**base,'status':'not_provisioned','tasks':None,'candidates':None,'budget':None,'last_progress':None}
    return {**base,'status':'enabled' if configuration['enabled'] else 'disabled',
        'tasks':db.execute('SELECT status,kind,count(*) total,min(next_attempt_at) next_attempt_at FROM news_discovery_tasks GROUP BY status,kind').fetchall(),
        'candidates':db.execute('SELECT status,count(*) total FROM news_discovery_candidates GROUP BY status').fetchall(),
        'budget':db.execute("SELECT * FROM news_discovery_budget WHERE day=(now() AT TIME ZONE 'UTC')::date").fetchone(),
        'last_progress':db.execute('SELECT max(last_success_at) last_success_at FROM news_discovery_tasks').fetchone(),
        'daily_ceilings':{'requests':120,'bytes_reserved':134217728},
    }
