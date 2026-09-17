"""Slow, resumable source discovery. No live execution unless explicitly enabled."""
import argparse
import json
import os
import time
from pathlib import Path
from psycopg.types.json import Jsonb
from .storage import database_connection
from .discovery_settings import enabled
from .discovery_policy import scan_site, scan_feed, safe_error, site_origin
from .discovery_store import Budget, BudgetExhausted, enqueue, claim, finish_site, finish_feed, fail_task, review, status

ROOT = Path(__file__).resolve().parent.parent


def tick(db, budget=None, site_scan=scan_site, feed_scan=scan_feed):
    """One bounded run; durable claims survive an interrupted process."""
    if not enabled('BORIS_DISCOVERY_ENABLED'):
        return {'status':'disabled','processed':0}
    if not db.execute('SELECT pg_try_advisory_lock(67426006) locked').fetchone()['locked']:
        return {'status':'already_running','processed':0}
    budget = budget or Budget(db)
    count = 0
    try:
        while budget.remaining > 0:
            if time.monotonic()>=budget.deadline:
                return {'status':'budget_paused','processed':count,'reason':'discovery_run_budget_exhausted'}
            task = claim(db)
            if not task:
                return {'status':'idle','processed':count}
            try:
                if task['kind']=='site':
                    finish_site(db,task,site_scan(task,budget))
                else:
                    result=feed_scan(task,budget)
                    finish_feed(db,task,result)
                    if result.get('budget_paused'):
                        return {'status':'budget_paused','processed':count+1,'reason':'sampling_checkpoint_saved'}
                count += 1
            except BudgetExhausted as exc:
                fail_task(db,task,safe_error(exc),budget_pause=True)
                return {'status':'budget_paused','processed':count,'reason':safe_error(exc)}
            except Exception as exc:
                # Persist known failures, never credentials/URLs from exception
                # tracebacks. Database errors still fail if state cannot be saved.
                fail_task(db,task,safe_error(exc))
                count += 1
        return {'status':'budget_paused','processed':count}
    finally:
        db.execute('SELECT pg_advisory_unlock(67426006)')


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    sub.add_parser('tick')
    sub.add_parser('setup',help='Apply only additive discovery and inventory schemas; no crawl')
    seeds = sub.add_parser('seed',help='Queue a site or bootstrap existing publisher homepages')
    seeds.add_argument('--url')
    seeds.add_argument('--known-publishers',action='store_true')
    seeds.add_argument('--if-empty',action='store_true',help='Bootstrap only an empty discovery queue')
    seeds.add_argument('--actor',required=True)
    inspect = sub.add_parser('inspect')
    inspect.add_argument('--candidate',type=int,required=True)
    listing = sub.add_parser('list')
    listing.add_argument('--after',type=int,default=0)
    for mode in ('admit','reject'):
        item = sub.add_parser(mode)
        item.add_argument('--candidate',type=int,required=True)
        item.add_argument('--actor',required=True)
        item.add_argument('--reason',required=True)
        item.add_argument('--evidence',action='append',required=True)
        if mode=='admit':
            for key in ('name','country','region'):
                item.add_argument('--'+key,required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command=='tick' and not enabled('BORIS_DISCOVERY_ENABLED'):
        print(json.dumps({'status':'disabled','processed':0})); return 0
    db = database_connection()
    try:
        if args.command=='setup':
            for filename in ('002_continuous_discovery.sql','003_dynamic_inventory.sql'):
                db.execute((ROOT/'sql'/filename).read_text())
            result = {'status':'schema_ready','discovery_enabled':False}
        elif args.command=='seed':
            if not args.actor.strip() or len(args.actor)>200:
                raise ValueError('invalid_reviewer')
            if bool(args.url)==bool(args.known_publishers):
                raise ValueError('invalid_seed_selection')
            if args.if_empty and db.execute('SELECT id FROM news_discovery_tasks LIMIT 1').fetchone():
                print(json.dumps({'status':'already_seeded','inserted':0}));return 0
            urls = [args.url] if args.url else [r['site_url'] for r in db.execute('SELECT DISTINCT site_url FROM news_feeds').fetchall()]
            with db.transaction():
                prepared=[{'url':url} for url in sorted({site_origin(url) for url in urls})]
                inserted=len(db.execute("""INSERT INTO news_discovery_tasks(kind,url)
                  SELECT 'site',x.url FROM jsonb_to_recordset(%s::jsonb) x(url text)
                  ON CONFLICT(kind,url) DO NOTHING RETURNING id""",(Jsonb(prepared),)).fetchall())
                db.execute('INSERT INTO news_discovery_audit(actor,action,details) VALUES(%s,%s,%s)',
                    (args.actor.strip(),'seed',Jsonb({'inserted':inserted,'known_publishers':args.known_publishers})))
            result = {'status':'queued','inserted':inserted}
        elif args.command=='tick':
            result = tick(db)
        elif args.command=='status':
            result = status(db)
        elif args.command=='list':
            rows = db.execute("""SELECT id,rss_url,site_url,status,last_checked_at,last_error,technical_evaluation
              FROM news_discovery_candidates WHERE id>%s ORDER BY id LIMIT 50""",(args.after,)).fetchall()
            result = {'candidates':rows,'next_after':rows[-1]['id'] if len(rows)==50 else None}
        elif args.command=='inspect':
            candidate = db.execute('SELECT * FROM news_discovery_candidates WHERE id=%s',(args.candidate,)).fetchone()
            observations = db.execute('SELECT observed_at,payload FROM news_discovery_observations WHERE candidate_id=%s ORDER BY observed_at DESC LIMIT 30',
                (args.candidate,)).fetchall()
            result = {'candidate':candidate,'observations':observations,'ai_evaluated':False}
        else:
            result = review(db,args.candidate,args.actor,args.reason,args.evidence,
                accept=args.command=='admit',metadata={k:getattr(args,k,None) for k in ('name','country','region')})
        print(json.dumps(result,ensure_ascii=False,default=str))
        return 0
    finally:
        db.close()


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'status':'failed','error':safe_error(exc)}))
        raise SystemExit(1)
