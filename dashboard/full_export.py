"""Read-only complete explorer export. Credentials and object keys never leave the runner."""
import gzip
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from collector.storage import connect
from collector.inventory import urls as active_urls
from trends.core import continent
from reference_compare.core import report_key as reference_key
from collector.technology15 import manifest as reference_manifest
from botocore.exceptions import ClientError
from .export import build, COLLECTION_SQL, TRENDS_SQL

DEST=Path('frontend/data/explorer')
CACHE=Path('.dashboard-cache')
PRIVATE={'content_key','rss_content_key','report_key','snapshot_key'}

def public(value):
    if isinstance(value,dict):return {k:public(v) for k,v in value.items() if k not in PRIVATE}
    if isinstance(value,list):return [public(v) for v in value]
    return value

def write(name,value):
    data=json.dumps(public(value),ensure_ascii=False,default=str,separators=(',',':')).encode()
    if len(data)>24*1024*1024:raise ValueError('pages_file_too_large:'+name)
    (DEST/name).parent.mkdir(parents=True,exist_ok=True)
    (DEST/name).write_bytes(data)
    return name

def cached(s3,key):
    path=CACHE/(hashlib.sha256(key.encode()).hexdigest()+'.gz')
    if path.exists():return path.read_bytes()
    response=s3.get_object(Bucket=os.environ['R2_BUCKET'],Key=key)
    try:raw=response['Body'].read()
    finally:response['Body'].close()
    path.write_bytes(raw)
    return raw

def report(s3,key):return json.loads(gzip.decompress(cached(s3,key)))

def body(s3,a):
    result={'id':a['id'],'text':None,'text_basis':'title_summary','summary':a.get('summary') or ''}
    if a.get('content_key'):
        try:
            result['text']=gzip.decompress(cached(s3,a['content_key'])).decode('utf-8')
            result['text_basis']='publisher_rss' if a['content_status']=='rss_content' else 'extracted_page'
        except Exception as exc:result['read_error']=type(exc).__name__
    return result

def normalize_ranks(rows):
    result={}
    for place,value in rows.items():
        entry={k:v for k,v in value.items() if k not in ('ranking','subject_ranking')}
        for key in ('ranking','subject_ranking'):
            entry[key]=[{**{k:v for k,v in rank.items() if k!='evidence'},'article_ids':[a['id'] for a in rank.get('evidence',[])]} for rank in value.get(key,[])]
        result[place]=entry
    return result

def main():
    DEST.mkdir(parents=True,exist_ok=True);CACHE.mkdir(exist_ok=True)
    db,s3=connect()
    try:
        with db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            articles=db.execute('''SELECT a.id,a.title,a.url,a.summary,a.published_at,a.first_seen_at,a.content_status,a.content_key,
                coalesce(jsonb_agg(jsonb_build_object('id',f.id,'name',f.name,'country',f.country,'region',f.region,'rss_url',f.rss_url,'site_url',f.site_url)) FILTER(WHERE f.id IS NOT NULL),'[]') sources
                FROM news_articles a LEFT JOIN news_article_feeds af ON af.article_id=a.id
                LEFT JOIN news_feeds f ON f.id=af.feed_id GROUP BY a.id
                ORDER BY coalesce(a.published_at,a.first_seen_at)>CURRENT_TIMESTAMP,coalesce(a.published_at,a.first_seen_at) DESC,a.id''').fetchall()
            collections=db.execute(COLLECTION_SQL).fetchall()
            trends=db.execute(TRENDS_SQL).fetchall()
            closures=db.execute('SELECT id,day,mode,cutoff,report_key,coverage FROM news_daily_closures ORDER BY day DESC,cutoff DESC').fetchall()
            runs=db.execute('SELECT id,status,finished_at,coverage,snapshot_key FROM news_analysis_runs ORDER BY finished_at DESC NULLS LAST').fetchall()
            attempts=db.execute('SELECT id,slot,finished_at,report FROM news_collection_attempts ORDER BY finished_at DESC').fetchall()
        manifest={'schema_version':2,'generated_at':datetime.now(timezone.utc).isoformat(),'total_articles':len(articles),'article_chunks':[],'closures':[],'analyses':[],'operations':build([],collections,trends)['operations'],'export_errors':[]}
        active=set(active_urls())
        for start in range(0,len(articles),250):
            batch=articles[start:start+250]
            with ThreadPoolExecutor(max_workers=32) as pool:texts=list(pool.map(lambda a:body(s3,a),batch))
            textfile=write(f'texts/{start//250}.json',{str(a['id']):a for a in texts})
            index=[]
            for a,b in zip(batch,texts):
                item=public(a);item['summary']=(item.get('summary') or '')[:500]
                item['country']=', '.join(sorted({s['country'] for s in item['sources'] if s.get('country')}))
                item['source']=', '.join(sorted({s['name'] for s in item['sources'] if s.get('name')}))
                item['continents']=sorted({continent(s) for s in item['sources']})
                item['active']=any(s.get('rss_url') in active for s in item['sources'])
                item['text_file']=textfile;item['has_text']=bool(b['text']);item['text_basis']=b['text_basis']
                if b.get('read_error'):item['read_error']=b['read_error']
                index.append(item)
            manifest['article_chunks'].append(write(f'articles/{start//250}.json',index))
            if start%2500==0:print(json.dumps({'phase':'export_articles','done':min(start+250,len(articles)),'total':len(articles)}),flush=True)
        for i,c in enumerate(closures):
            entry=public(c)
            try:
                payload=report(s3,c['report_key'])
                entry['scopes']={scope:write(f'daily/{i}-{scope}.json',normalize_ranks(rows)) for scope,rows in payload['results'].items()}
                entry['pairs']=write(f'daily/{i}-pairs.json',payload.get('pair_evidence',[]))
                entry['audit']=write(f'daily/{i}-audit.json',payload.get('article_audit',[]))
                raw=gzip.compress(json.dumps(public(payload),ensure_ascii=False,default=str).encode())
                name=f'daily/{i}-complete.json.gz'
                if len(raw)>24*1024*1024:raise ValueError('report_too_large')
                (DEST/name).write_bytes(raw);entry['download']=name
            except Exception as exc:
                entry['error']=type(exc).__name__;manifest['export_errors'].append({'type':'daily','id':c['id'],'error':entry['error']})
            if c['mode']=='closed':
                try:
                    comparison=report(s3,reference_key(c['id'],reference_manifest()))
                    # Export geography separately to stay below the Pages file limit.
                    scopes=comparison.pop('scopes')
                    comparison['scope_files']={scope:write(f'reference/{i}-{scope}.json',rows) for scope,rows in scopes.items()}
                    entry['reference_comparison']=write(f'reference/{i}.json',comparison)
                except ClientError as exc:
                    if exc.response['Error']['Code'] not in ('NoSuchKey','404'):raise
                    entry['reference_status']='waiting_for_comparison'
            manifest['closures'].append(entry)
        for i,r in enumerate(runs):
            entry=public(r)
            if r.get('snapshot_key'):
                try:
                    payload=report(s3,r['snapshot_key'])
                    entry['file']=write(f'analyses/{i}.json',payload)
                    for audit in ('cluster-audit','corpus'):
                        try:entry[audit]=write(f'analyses/{i}-{audit}.json',report(s3,'analysis/runs/'+str(r['id'])+'/'+audit+'.json.gz'))
                        except Exception as exc:entry[audit+'_error']=type(exc).__name__
                except Exception as exc:
                    entry['error']=type(exc).__name__;manifest['export_errors'].append({'type':'analysis','id':r['id'],'error':entry['error']})
            manifest['analyses'].append(entry)
        manifest['attempts']=write('attempts.json',attempts)
        write('manifest.json',manifest)
        print(json.dumps({'phase':'complete','articles':len(articles),'closures':len(closures),'analyses':len(runs),'errors':manifest['export_errors']}),flush=True)
        if manifest['export_errors']:raise RuntimeError('incomplete_report_export')
    finally:db.close()

if __name__=='__main__':main()
