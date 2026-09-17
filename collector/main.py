"""python -m collector.main setup|preflight|run. Segredos somente por ambiente."""
import argparse
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from collections import deque
from .inventory import urls as active_urls,for_slot as inventory_for_slot
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from psycopg.types.json import Jsonb
from .storage import connect,seed,save_entries,archive
from .extract import fetch_source,fetch_article,digest

ROOT=Path(__file__).resolve().parent.parent

def slot_for(now):
    local=now.astimezone(ZoneInfo('America/Sao_Paulo'))
    return local.replace(hour=(local.hour//6)*6,minute=0,second=0,microsecond=0).astimezone(timezone.utc)

def run_budget(now, maximum):
    # Leave a minute to drain in-flight requests and save the checkpoint before the next six-hour window.
    remaining=(slot_for(now)+timedelta(hours=6)-now).total_seconds()
    return max(0,min(maximum,remaining-60))

def attempt(fn,item):
    try:return fn(item),None
    except Exception as e:
        # Não registrar URLs de conexão, credenciais nem traceback de provedores.
        known=str(e)
        safe=known if known.startswith(('http_','robots_','body_','invalid_','entry_','insufficient_','304_','too_many_','non_public_')) else type(e).__name__
        return None,safe[:120]

def sources(db,s3,slot,feeds,deadline):
    targets=db.execute('''SELECT f.* FROM news_feeds f WHERE f.rss_url=ANY(%s)
      AND NOT EXISTS(SELECT 1 FROM news_feed_runs r WHERE r.feed_id=f.id AND r.slot=%s AND r.status='ok')
      ORDER BY f.id''',([f['rss_url'] for f in feeds],slot)).fetchall()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0,len(targets),8):
            if time.monotonic()>deadline:break
            batch=targets[start:start+8]
            for f,(result,error) in zip(batch,pool.map(lambda f:attempt(fetch_source,f),batch)):
                # Uploads paralelos antes da transação: o banco nunca aponta para arquivo ausente.
                if not error:
                    status,h,items=result
                    def preserve(a):
                        if a['rss_content']:
                            _,a['rss_content_key'],_=archive(s3,a['url']+'#rss-source',a['rss_content'])
                        return a
                    uploads=list(pool.map(lambda a:attempt(preserve,a),items))
                    failures=[e for _,e in uploads if e]
                    if failures:error='storage_'+failures[0]
                with db.pipeline():
                    with db.transaction():
                        count=0
                        if not error:
                            status,h,items=result;count=len(items)
                            if status!=304:
                                db.execute('UPDATE news_article_feeds SET in_latest=false WHERE feed_id=%s',(f['id'],))
                            save_entries(db,f['id'],items)
                            from .observations import record as record_observations
                            record_observations(db,f,slot)
                            # 304 mantém a elegibilidade das páginas para checar revisões.
                            db.execute('''UPDATE news_articles SET last_seen_at=now() WHERE id IN
                              (SELECT article_id FROM news_article_feeds WHERE feed_id=%s AND in_latest)''',(f['id'],)) if status==304 else None
                            db.execute('''UPDATE news_feeds SET etag=%s,last_modified=%s,last_success_at=now() WHERE id=%s''',
                              (h.get('ETag',f['etag'] if status==304 else None),
                               h.get('Last-Modified',f['last_modified'] if status==304 else None),f['id']))
                        db.execute('''INSERT INTO news_feed_runs(slot,feed_id,status,items,error)
                          VALUES(%s,%s,%s,%s,%s) ON CONFLICT(slot,feed_id) DO UPDATE SET
                          status=EXCLUDED.status,items=EXCLUDED.items,error=EXCLUDED.error,checked_at=now()''',
                          (slot,f['id'],'error' if error else 'ok',count,error))
                print(json.dumps({'phase':'feeds','feed_id':f['id'],'status':error or 'ok','items':count}),flush=True)

def articles(db,s3,slot,deadline):
    from .article_batch import outcome,preserve,persist
    archived_bytes=0;processed=0
    workers=max(1,min(32,int(os.getenv('ARTICLE_WORKERS','16'))))
    def process(a):
        result,error=attempt(fetch_article,a)
        if error and a.get('rss_content_key'):
            from .rss_fallback import fetch as fetch_rss
            fallback,fallback_error=attempt(lambda _:fetch_rss(s3,a),None)
            if not fallback_error:result,error=fallback,None
        if not error:
            result,error=attempt(lambda _:preserve(s3,a,result),None)
            if error:error='storage_'+error
        return outcome(a,result,error,slot)
    # Keep workers occupied while persisting completed work without batch barriers.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending={};buffer=[];waiting=deque();last_flush=time.monotonic()
        while pending or time.monotonic()<deadline:
            if not waiting and time.monotonic()<deadline:
                exclude=[a['id'] for a in pending.values()]+[r['id'] for r in buffer]
                batch=db.execute("""WITH due AS (
                  SELECT *,row_number() OVER(PARTITION BY split_part(url,'/',3)
                    ORDER BY (content_key IS NOT NULL),attempts,next_attempt_at,id) domain_rank
                  FROM news_articles WHERE next_attempt_at<=now() AND NOT(id=ANY(%s::bigint[]))
                    AND (last_seen_at >= %s OR content_key IS NULL))
                  SELECT * FROM due ORDER BY domain_rank,(content_key IS NOT NULL),attempts,next_attempt_at,id LIMIT %s""",
                  (exclude,slot,256)).fetchall()
                waiting.extend(batch)
            while waiting and len(pending)<workers and time.monotonic()<deadline:
                a=waiting.popleft();pending[pool.submit(process,a)]=a
            if not pending:
                if buffer:archived_bytes+=persist(db,buffer);buffer=[]
                break
            done,_=wait(pending,timeout=2,return_when=FIRST_COMPLETED)
            for future in done:
                buffer.append(future.result());pending.pop(future);processed+=1
            if buffer and (len(buffer)>=32 or time.monotonic()-last_flush>=5 or not pending):
                archived_bytes+=persist(db,buffer)
                print(json.dumps({'phase':'articles','processed_this_run':processed,
                  'batch_extracted':sum(r['last_error'] is None for r in buffer),
                  'batch_failed':sum(r['last_error'] is not None for r in buffer)}),flush=True)
                buffer=[];last_flush=time.monotonic()
        if buffer:archived_bytes+=persist(db,buffer)
    return archived_bytes

def summary(db,slot,total,inventory_urls=None):
    inventory_urls=active_urls(db,slot) if inventory_urls is None else inventory_urls
    r=db.execute('''SELECT count(*) FILTER(WHERE status='ok') ok,
      count(*) FILTER(WHERE status='error') errors FROM news_feed_runs WHERE slot=%s AND feed_id IN (SELECT id FROM news_feeds WHERE rss_url=ANY(%s))''',(slot,inventory_urls)).fetchone()
    a=db.execute('''WITH current_articles AS (
      SELECT DISTINCT a.id,a.content_key,a.content_status FROM news_articles a
      JOIN news_article_feeds af ON af.article_id=a.id
      JOIN news_feeds f ON f.id=af.feed_id WHERE f.rss_url=ANY(%s))
      SELECT count(*) total,
      count(*) FILTER(WHERE content_key IS NOT NULL) content_key_total,
      count(*) FILTER(WHERE content_key IS NOT NULL AND content_status IN ('extracted','rss_content')) valid_text_bodies,
      count(*) FILTER(WHERE content_key IS NULL OR content_status NOT IN ('extracted','rss_content')) without_text,
      count(*) FILTER(WHERE content_status='pending') pending,
      count(*) FILTER(WHERE content_status='unavailable') unavailable,
      count(*) FILTER(WHERE content_status='invalid_reference') invalid_references,
      count(*) FILTER(WHERE content_status='extracted' AND content_key IS NOT NULL) page_texts,
      count(*) FILTER(WHERE content_status='rss_content' AND content_key IS NOT NULL) publisher_rss_texts,
      count(*) FILTER(WHERE content_key IS NULL AND content_status NOT IN ('pending','unavailable','invalid_reference')) title_summary_only
      FROM current_articles''',(inventory_urls,)).fetchone()
    # Backward-compatible key, explicitly paired with its limitation.
    a['extracted']=a['content_key_total']
    a['content_key_does_not_prove_integrality']=True
    pending=db.execute('''SELECT count(*) n FROM news_articles WHERE next_attempt_at<=now()
      AND (last_seen_at >= %s OR content_key IS NULL)''',(slot,)).fetchone()['n']
    return {'slot':slot.isoformat(),'expected_feeds':total,'feeds_ok':r['ok'],'feeds_errors':r['errors'],
      'feeds_not_attempted':max(0,total-r['ok']-r['errors']),'articles':a,'due_articles':pending}

def run(db,s3,feeds):
    now=datetime.now(timezone.utc)
    slot=slot_for(now)
    feeds=inventory_for_slot(db,slot,freeze=True,base_feeds=feeds)
    inventory_urls=[f['rss_url'] for f in feeds]
    deadline=time.monotonic()+run_budget(now,int(os.getenv('MAX_RUN_SECONDS','1800')))
    db.execute('''INSERT INTO news_runs(slot) VALUES(%s) ON CONFLICT(slot) DO UPDATE SET status='running',finished_at=NULL''',(slot,))
    from .repair_links import repair_dday
    print(json.dumps({'phase':'link_repair',**repair_dday(db)},ensure_ascii=False),flush=True)
    sources(db,s3,slot,feeds,deadline)
    size=articles(db,s3,slot,deadline)
    report=summary(db,slot,len(feeds),inventory_urls);report['compressed_bytes_written']=size
    status=('partial' if report['feeds_not_attempted'] or report['due_articles'] or report['articles']['pending']
      else 'complete_with_gaps' if report['feeds_errors'] or report['articles']['without_text'] else 'complete')
    report['status']=status
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    db.execute('UPDATE news_runs SET status=%s,finished_at=now(),report=%s WHERE slot=%s',(status,Jsonb(report),slot))
    Path('reports').mkdir(exist_ok=True)
    Path('reports/latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    feed_states=db.execute("""SELECT f.id,f.name,f.country,f.region,f.site_url,f.rss_url,
      coalesce(r.status,'not_attempted') status,r.error FROM news_feeds f
      LEFT JOIN news_feed_runs r ON r.feed_id=f.id AND r.slot=%s WHERE f.rss_url=ANY(%s) ORDER BY f.id""",(slot,inventory_urls)).fetchall()
    attempt_id=os.getenv('GITHUB_RUN_ID') or str(uuid.uuid4())
    db.execute('''INSERT INTO news_collection_attempts(id,slot,finished_at,report,feeds)
      VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING''',
      (attempt_id,slot,report['finished_at'],Jsonb(report),Jsonb(feed_states)))
    from .reporting import write_feed_report
    write_feed_report(db,s3,slot,report,inventory_urls)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('```json\n'+json.dumps(report,indent=2)+'\n```\n')
    # Partial is a checkpoint, not an infrastructure exception. Coverage remains explicit.
    if status!='complete':print('::warning::Coleta parcial; consulte cobertura e pendencias no relatorio.',flush=True)
    return 0

def preflight(db,s3):
    inventory_urls=active_urls(db,slot_for(datetime.now(timezone.utc)))
    count=db.execute('SELECT count(*) n FROM news_feeds WHERE rss_url=ANY(%s)',(inventory_urls,)).fetchone()['n']
    if count!=len(inventory_urls):raise ValueError('Inventário ativo ausente no banco')
    key='preflight/'+str(uuid.uuid4())+'.txt'
    s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=key,Body=b'boris-preflight')
    try:
        result=s3.get_object(Bucket=os.environ['R2_BUCKET'],Key=key)
        assert result['Body'].read()==b'boris-preflight'
        result['Body'].close()
    finally:s3.delete_object(Bucket=os.environ['R2_BUCKET'],Key=key)
    print(f'OK: Supabase, {count} feeds ativos e escrita/leitura/exclusão no R2')

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['setup','preflight','run']);args=p.parse_args()
    feeds=json.loads((ROOT/'data/feeds.json').read_text())
    if len(feeds)<600 or len({f['rss_url'] for f in feeds})!=len(feeds):raise ValueError('Inventário inválido')
    db,s3=connect()
    try:
        # Session pooler 5432 mantém o advisory lock por toda a conexão.
        if not db.execute('SELECT pg_try_advisory_lock(67426001) locked').fetchone()['locked']:
            print('Outra coleta está em execução; esta invocação não iniciou.');return 0
        if args.mode=='setup':
            db.execute((ROOT/'sql/001_schema.sql').read_text());seed(db,feeds);print('Schema e 600 feeds preparados.');return 0
        if args.mode=='preflight':preflight(db,s3);return 0
        seed(db,feeds)
        return run(db,s3,feeds)
    finally:db.close()

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        # Evita vazamento de DSN/segredos no log público do Actions.
        print('Falha operacional: '+type(e).__name__+'. Verifique secrets/conectividade e checkpoint no banco.',flush=True)
        raise SystemExit(1)
