"""python -m collector.main setup|preflight|run. Segredos somente por ambiente."""
import argparse
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
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
                with db.transaction():
                    count=0
                    if not error:
                        status,h,items=result;count=len(items)
                        if status!=304:
                            db.execute('UPDATE news_article_feeds SET in_latest=false WHERE feed_id=%s',(f['id'],))
                        save_entries(db,f['id'],items)
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
    archived_bytes=0
    with ThreadPoolExecutor(max_workers=8) as pool:
        while time.monotonic()<deadline:
            batch=db.execute('''SELECT * FROM news_articles WHERE next_attempt_at<=now()
              AND (last_seen_at >= %s OR content_key IS NULL)
              ORDER BY (content_key IS NOT NULL),attempts,next_attempt_at,id LIMIT 24''',(slot,)).fetchall()
            if not batch:break
            for a,(result,error) in zip(batch,pool.map(lambda a:attempt(fetch_article,a),batch)):
                if error:
                    db.execute('''UPDATE news_articles SET last_error=%s,attempts=attempts+1,
                      content_status=CASE WHEN content_key IS NULL THEN 'unavailable' ELSE content_status END,
                      page_checked_at=now(),next_attempt_at=now()+make_interval(secs => %s) WHERE id=%s''',
                      (error,min(86400,3600*2**min(a['attempts'],5)),a['id']))
                    continue
                status,h,text,url=result
                content_hash=a['content_hash'];key=a['content_key'];chars=a['content_chars']
                if text is not None:
                    content_hash=digest(text);chars=len(text)
                    if content_hash!=a['content_hash']:
                        # O objeto imutável é escrito ANTES de o banco apontar para ele.
                        content_hash,key,size=archive(s3,a['url'],text);archived_bytes+=size
                with db.transaction():
                    if text is not None:
                        db.execute('''INSERT INTO news_article_versions(article_id,content_hash,content_key)
                          VALUES(%s,%s,%s) ON CONFLICT DO NOTHING''',(a['id'],content_hash,key))
                    db.execute('''UPDATE news_articles SET content_hash=%s,content_key=%s,content_chars=%s,
                      content_status='extracted',extracted_at=CASE WHEN %s THEN now() ELSE extracted_at END,
                      final_url=%s,page_etag=%s,page_last_modified=%s,page_checked_at=now(),
                      attempts=0,last_error=NULL,next_attempt_at=%s WHERE id=%s''',
                      (content_hash,key,chars,text is not None,url,
                       h.get('ETag',a['page_etag'] if status==304 else None),
                       h.get('Last-Modified',a['page_last_modified'] if status==304 else None),
                       max(slot+timedelta(hours=6),datetime.now(timezone.utc)+timedelta(hours=1)),a['id']))
    return archived_bytes

def summary(db,slot,total):
    r=db.execute('''SELECT count(*) FILTER(WHERE status='ok') ok,
      count(*) FILTER(WHERE status='error') errors FROM news_feed_runs WHERE slot=%s''',(slot,)).fetchone()
    a=db.execute('''SELECT count(*) total,count(*) FILTER(WHERE content_key IS NOT NULL) extracted,
      count(*) FILTER(WHERE content_key IS NULL) without_text FROM news_articles''').fetchone()
    pending=db.execute('''SELECT count(*) n FROM news_articles WHERE next_attempt_at<=now()
      AND (last_seen_at >= %s OR content_key IS NULL)''',(slot,)).fetchone()['n']
    return {'slot':slot.isoformat(),'expected_feeds':total,'feeds_ok':r['ok'],'feeds_errors':r['errors'],
      'feeds_not_attempted':max(0,total-r['ok']-r['errors']),'articles':a,'due_articles':pending}

def run(db,s3,feeds):
    slot=slot_for(datetime.now(timezone.utc))
    deadline=time.monotonic()+int(os.getenv('MAX_RUN_SECONDS','1800'))
    db.execute('''INSERT INTO news_runs(slot) VALUES(%s) ON CONFLICT(slot) DO UPDATE SET status='running',finished_at=NULL''',(slot,))
    sources(db,s3,slot,feeds,deadline)
    size=articles(db,s3,slot,deadline)
    report=summary(db,slot,len(feeds));report['compressed_bytes_written']=size
    status='complete' if not (report['feeds_errors'] or report['feeds_not_attempted'] or report['due_articles'] or report['articles']['without_text']) else 'partial'
    report['status']=status
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    db.execute('UPDATE news_runs SET status=%s,finished_at=now(),report=%s WHERE slot=%s',(status,Jsonb(report),slot))
    Path('reports').mkdir(exist_ok=True)
    Path('reports/latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    from .reporting import write_feed_report
    write_feed_report(db,s3,slot,report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('```json\n'+json.dumps(report,indent=2)+'\n```\n')
    # Partial is a checkpoint, not an infrastructure exception. Coverage remains explicit.
    if status=='partial':print('::warning::Coleta parcial; consulte cobertura e pendencias no relatorio.',flush=True)
    return 0

def preflight(db,s3):
    count=db.execute('SELECT count(*) n FROM news_feeds').fetchone()['n']
    if count!=600:raise ValueError('Esperados 600 feeds no banco dedicado')
    key='preflight/'+str(uuid.uuid4())+'.txt'
    s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=key,Body=b'boris-preflight')
    try:
        result=s3.get_object(Bucket=os.environ['R2_BUCKET'],Key=key)
        assert result['Body'].read()==b'boris-preflight'
        result['Body'].close()
    finally:s3.delete_object(Bucket=os.environ['R2_BUCKET'],Key=key)
    print('OK: Supabase, 600 feeds e escrita/leitura/exclusão no R2')

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['setup','preflight','run']);args=p.parse_args()
    feeds=json.loads((ROOT/'data/feeds.json').read_text())
    if len(feeds)!=600 or len({f['rss_url'] for f in feeds})!=600:raise ValueError('Inventário inválido')
    db,s3=connect()
    try:
        # Session pooler 5432 mantém o advisory lock por toda a conexão.
        if not db.execute('SELECT pg_try_advisory_lock(67426001) locked').fetchone()['locked']:
            print('Outra coleta está em execução; esta invocação não iniciou.');return 0
        if args.mode=='setup':
            db.execute((ROOT/'sql/001_schema.sql').read_text());seed(db,feeds);print('Schema e 600 feeds preparados.');return 0
        if args.mode=='preflight':preflight(db,s3);return 0
        return run(db,s3,feeds)
    finally:db.close()

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        # Evita vazamento de DSN/segredos no log público do Actions.
        print('Falha operacional: '+type(e).__name__+'. Verifique secrets/conectividade e checkpoint no banco.',flush=True)
        raise SystemExit(1)
