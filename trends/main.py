"""Build an immutable corpus snapshot, then publish scheduled geographic rankings."""
import argparse
import gzip
import hashlib
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path

from psycopg.types.json import Jsonb
from collector.storage import connect
from collector.inventory import urls as active_urls
from .core import continent,families,in_window,rankings

BUCKET=os.getenv('R2_BUCKET')
MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_REVISION='e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
VERSION='boris-topics-v14-editorial-event-form-and-calendar-gates-072'
# The semantic input is unchanged from v11; only the lexical/editorial gate
# changed, so reuse the pinned v11 vectors instead of recomputing 24k titles.
EMBEDDING_CACHE_VERSION='boris-topics-v11-event-context-active-inventory-072'


def log(**data):print(json.dumps(data,ensure_ascii=False,default=str),flush=True)

def get_object(s3,key):
    response=s3.get_object(Bucket=BUCKET,Key=key)
    try:return response['Body'].read()
    finally:response['Body'].close()

def optional(s3,key):
    from botocore.exceptions import ClientError
    try:return get_object(s3,key)
    except ClientError as exc:
        if exc.response['Error']['Code'] in ('NoSuchKey','404'):return None
        raise

def put_json(s3,key,value):
    body=gzip.compress(json.dumps(value,ensure_ascii=False,default=str).encode(),mtime=0)
    s3.put_object(Bucket=BUCKET,Key=key,Body=body,ContentType='application/json',ContentEncoding='gzip')
    return key

def get_json(s3,key):return json.loads(gzip.decompress(get_object(s3,key)))

def all_articles(db,cutoff):
    return db.execute('''SELECT a.id,a.url,a.title,a.summary,a.published_at,a.first_seen_at,
      a.content_key,a.content_status,
      jsonb_agg(jsonb_build_object('id',f.id,'name',f.name,
      'country',f.country,'region',f.region,'site_url',f.site_url,'rss_url',f.rss_url) ORDER BY f.id) sources
      FROM news_articles a JOIN news_article_feeds af ON af.article_id=a.id
      JOIN news_feeds f ON f.id=af.feed_id WHERE a.first_seen_at<=%s
        AND f.rss_url=ANY(%s)
        AND a.content_status<>'invalid_reference'
      GROUP BY a.id ORDER BY a.id''',(cutoff,active_urls())).fetchall()

def load_text(s3,a):
    text=a['title']+'\n'+(a['summary'] or '')
    a['text_basis']='title_summary'; a['text_read_error']=None
    if a['content_key']:
        try:
            body=gzip.decompress(get_object(s3,a['content_key'])).decode('utf-8')
            text=a['title']+'\n'+body;a['text_basis']='publisher_rss' if a.get('content_status')=='rss_content' else 'extracted_page'
        except Exception as exc:
            # Keep the article in the analysis, but never claim its body was read.
            a['text_read_error']=type(exc).__name__
    a['analysis_text']=text
    # Stable, focused representation: page boilerplate and broad product names
    # must not dominate the event identity.
    from .clustering import semantic_event_text
    a['semantic_text']=semantic_event_text(a['title'])
    a['input_hash']=hashlib.sha256((EMBEDDING_CACHE_VERSION+a['semantic_text']).encode()).hexdigest()
    return a

def vectors(s3,articles,progress=None):
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import model_info
    torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
    manifest_raw=optional(s3,'analysis/cache/manifest.json.gz')
    manifest=json.loads(gzip.decompress(manifest_raw)) if manifest_raw else {}
    revision=MODEL_REVISION
    cache={}
    if manifest.get('version')==EMBEDDING_CACHE_VERSION and manifest.get('key'):
        with np.load(io.BytesIO(get_object(s3,manifest['key'])),allow_pickle=False) as data:
            cache=dict(zip(data['hashes'].tolist(),data['vectors']))
    missing=[a for a in articles if a['input_hash'] not in cache]
    log(phase='embeddings',articles=len(articles),cached=len(articles)-len(missing),pending=len(missing),model=MODEL,revision=revision)
    if progress:progress({'phase':'embeddings','articles':len(articles),'done':len(articles)-len(missing)})
    if missing:
        model=SentenceTransformer(MODEL,revision=revision,device='cpu',trust_remote_code=False)
        model.max_seq_length=128
        for start in range(0,len(missing),64):
            batch=missing[start:start+64]
            embedded=model.encode([a['semantic_text'] for a in batch],batch_size=32,
                                 normalize_embeddings=True,show_progress_bar=False)
            for a,v in zip(batch,embedded):cache[a['input_hash']]=v.astype(np.float32)
            if start%512==0 or start+64>=len(missing):
                buf=io.BytesIO();np.savez_compressed(buf,hashes=np.array(list(cache)),vectors=np.array(list(cache.values()),dtype=np.float32))
                body=buf.getvalue();key='analysis/cache/'+hashlib.sha256(body).hexdigest()+'.npz'
                s3.put_object(Bucket=BUCKET,Key=key,Body=body)
                old_key=manifest.get('key')
                manifest={'version':EMBEDDING_CACHE_VERSION,'model':MODEL,'revision':revision,'key':key}
                put_json(s3,'analysis/cache/manifest.json.gz',manifest)
                # Superseded cache is reproducible; immutable analysis snapshots stay retained.
                if old_key and old_key!=key:s3.delete_object(Bucket=BUCKET,Key=old_key)
                log(phase='embeddings_checkpoint',done=min(start+64,len(missing)),total=len(missing))
                if progress:progress({'phase':'embeddings','articles':len(articles),'done':len(articles)-len(missing)+min(start+64,len(missing))})
    return np.array([cache[a['input_hash']] for a in articles]),revision

def assign_topics(s3,articles,embeddings,run_id):
    from .clustering import coherent_groups
    groups=coherent_groups(embeddings,[a['title'] for a in articles])
    for a in articles:a.update(topic_id='outlier',topic_label='Sem outra matéria suficientemente semelhante',topic_min_similarity=None)
    audit=[]
    for group in groups:
        indices=group['indices'];representative=articles[group['representative']]
        # Derive the label from THIS snapshot. Never reuse a stale representative title.
        identity='|'.join(sorted(str(articles[i]['id']) for i in indices))
        topic='topic-'+hashlib.sha256((VERSION+identity).encode()).hexdigest()[:16]
        for i in indices:
            articles[i].update(topic_id=topic,topic_label=representative['title'],
                               topic_min_similarity=group['min_similarity'])
        audit.append({'topic_id':topic,'label':representative['title'],
                      'min_similarity':group['min_similarity'],
                      'evidence':[{'id':articles[i]['id'],'title':articles[i]['title']} for i in indices]})
    put_json(s3,'analysis/runs/'+run_id+'/cluster-audit.json.gz',audit)
    Path('reports').mkdir(exist_ok=True)
    Path('reports/cluster-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    log(phase='topics',topics=len(groups),outliers=sum(a['topic_id']=='outlier' for a in articles))

def prepare(db,s3,run_id):
    existing=db.execute('SELECT * FROM news_analysis_runs WHERE id=%s',(run_id,)).fetchone()
    if existing and existing['status']=='ready':
        log(phase='already_ready',run_id=run_id);return True
    parent=os.getenv('SOURCE_COLLECTION_RUN_ID')
    attempt=db.execute('SELECT * FROM news_collection_attempts WHERE id=%s',(parent,)).fetchone() if parent else db.execute('SELECT * FROM news_collection_attempts ORDER BY finished_at DESC LIMIT 1').fetchone()
    if parent and not attempt:
        log(phase='skipped',reason='parent_did_not_finish_a_collection',parent=parent)
        return False
    row={'slot':attempt['slot'],'finished_at':attempt['finished_at'],'status':attempt['report']['status']} if attempt else db.execute("SELECT * FROM news_runs WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1").fetchone()
    if not row:raise RuntimeError('no_finished_collection')
    # An explicit workflow parent timestamp links this snapshot to its collection invocation.
    cutoff=datetime.fromisoformat(os.getenv('COLLECTION_FINISHED_AT') or row['finished_at'].isoformat())
    if cutoff.tzinfo is None:cutoff=cutoff.replace(tzinfo=timezone.utc)
    from collector.main import slot_for
    source_slot=slot_for(cutoff)
    # Prefer the actual collector slot when finish crossed a six-hour boundary.
    source_slot=row['slot']
    db.execute('''INSERT INTO news_analysis_runs(id,collection_slot,collection_finished_at,status,model_version)
      VALUES(%s,%s,%s,'building',%s) ON CONFLICT(id) DO UPDATE SET status='building',error=NULL''',(run_id,source_slot,cutoff,VERSION))
    sources=attempt['feeds'] if attempt else db.execute('''SELECT f.id,f.name,f.country,f.region,f.site_url,f.rss_url,
       coalesce(r.status,'not_attempted') status,r.error FROM news_feeds f
       LEFT JOIN news_feed_runs r ON r.feed_id=f.id AND r.slot=%s WHERE f.rss_url=ANY(%s) ORDER BY f.id''',(source_slot,active_urls())).fetchall()
    articles=all_articles(db,cutoff)
    log(phase='corpus',articles=len(articles),cutoff=cutoff)
    with ThreadPoolExecutor(max_workers=16) as pool:articles=list(pool.map(lambda a:load_text(s3,a),articles))
    def progress(state):
        db.execute('UPDATE news_analysis_runs SET coverage=%s WHERE id=%s',(Jsonb(state),run_id))
    embedding,revision=vectors(s3,articles,progress)
    import numpy as np
    ids=[i for i,a in enumerate(articles) if in_window(a,cutoff)]
    recent=[articles[i] for i in ids]
    assign_topics(s3,recent,embedding[ids],run_id)
    fam=families([a['analysis_text'] for a in recent])
    for a,f in zip(recent,fam):a['family']=f
    coverage={'clustering_method':'complete_linkage_cosine',
      'minimum_pairwise_similarity':.72,
      'semantic_basis':'title_derived_event_context_without_broad_product_identity',
      'lexical_gate':'exact_title_or_narrow_compound_at_0735_or_two_anchors_with_rare_specific_term; product_versions_must_match; multi_story_digests_event_templates_sales_vs_review_and_cross_brand_comparisons_excluded',
      'calibration_status':'Known v4-v11 false-positive patterns separated in tests; targeted sample only, not a general benchmark',
      'editorial_status':'automatic_groups_require_editorial_review',
      'ungrouped_articles':sum(a['topic_id']=='outlier' for a in recent),
      'corpus_articles':len(articles),'window_articles':len(recent),
      'full_texts_read':sum(a['text_basis']=='extracted_page' for a in articles),
      'window_full_texts_read':sum(a['text_basis']=='extracted_page' for a in recent),
      'publisher_rss_texts_read':sum(a['text_basis']=='publisher_rss' for a in articles),
      'body_read_errors':sum(bool(a['text_read_error']) for a in articles),
      'date_fallback_articles':sum(a['published_at'] is None for a in recent),
      'feeds_total':len(sources),'feeds_ok':sum(s['status']=='ok' for s in sources),
      'feeds_error':sum(s['status']=='error' for s in sources),
      'feeds_not_attempted':sum(s['status']=='not_attempted' for s in sources),
      'regions_present':sorted({s['region'] for s in sources}),
      'missing_continents':[c for c in ['América do Sul','África','América do Norte','Europa','Ásia','Oceania'] if c not in {continent(s) for s in sources}],
      'collection_status':row['status'],'scope_definition':'País editorial dos veículos monitorados; não país do acontecimento.',
      'growth_status':'Histórico comparável ainda não validado; ranking mede frequência observada, não previsão.'}
    compact=[{k:a[k] for k in ['id','url','title','sources','topic_id','topic_label','topic_min_similarity','family','text_basis','published_at','first_seen_at']} for a in recent]
    payload={'run_id':run_id,'as_of':cutoff.isoformat(),'window_hours':24,'coverage':coverage,'articles':compact,'feeds':sources,'model':MODEL,'revision':revision}
    key=put_json(s3,'analysis/runs/'+run_id+'/snapshot.json.gz',payload)
    # Full-corpus processing audit includes historical articles, but old stories do not count as today's topics.
    put_json(s3,'analysis/runs/'+run_id+'/corpus.json.gz',[{'id':a['id'],'input_hash':a['input_hash'],'text_basis':a['text_basis'],'text_read_error':a['text_read_error']} for a in articles])
    db.execute('''UPDATE news_analysis_runs SET status='ready',finished_at=now(),snapshot_key=%s,coverage=%s,model_revision=%s WHERE id=%s''',(key,Jsonb(coverage),revision,run_id))
    Path('reports').mkdir(exist_ok=True)
    Path('reports/analysis_coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
    log(phase='ready',run_id=run_id,coverage=coverage)
    return True

def render(payload,scope,result,scheduled_at,started_at):
    md=f'# Tendências — {scope}\n\nCorte: {payload["as_of"]}. Janela: 24 horas.\n\n'
    md+='País = origem editorial do veículo. Temas semânticos estimados; não eventos confirmados.\n\n'
    md+='```json\n'+json.dumps(payload['coverage'],ensure_ascii=False,indent=2)+'\n```\n\n'
    md+=f'Programado para: {scheduled_at}. Início real: {started_at}.\n\n'
    for place,data in result.items():
        md+=f'## {place}\n\n{data["articles"]} matérias; {data["outliers"]} sem agrupamento.\n\n'
        md+='| Tema (título representativo) | Matérias | Veículos | Famílias estimadas |\n|---|---:|---:|---:|\n'
        for t in data['ranking'][:20]:
            label=t['label'].replace('|','/').replace('\n',' ')
            md+=f'| {label} | {t["articles"]} | {t["publishers"]} | {t["republication_families_estimated"]} |\n'
        md+='\n'
    return md

def publish(db,s3,run_id,scope,delay):
    row=db.execute('SELECT * FROM news_analysis_runs WHERE id=%s',(run_id,)).fetchone()
    if not row or row['status']!='ready':raise RuntimeError('snapshot_not_ready')
    if (row.get('coverage') or {}).get('editorial_status')=='rejected_by_review':
        raise RuntimeError('snapshot_rejected_by_editorial_review')
    scheduled=row['collection_finished_at']+timedelta(minutes=delay)
    while (scheduled-datetime.now(timezone.utc)).total_seconds()>0:
        time.sleep(min(30,(scheduled-datetime.now(timezone.utc)).total_seconds()))
    started=datetime.now(timezone.utc)
    payload=get_json(s3,row['snapshot_key'])
    result=rankings(payload['articles'],scope)
    places={'Globo'} if scope=='globe' else {s['country'] if scope=='country' else continent(s) for s in payload['feeds']}
    for place in places:result.setdefault(place,{'articles':0,'outliers':0,'ranking':[]})
    md=render(payload,scope,result,scheduled.isoformat(),started.isoformat())
    key=put_json(s3,f'analysis/runs/{run_id}/{scope}.json.gz',{'coverage':payload['coverage'],'results':result})
    s3.put_object(Bucket=BUCKET,Key=f'analysis/runs/{run_id}/{scope}.md',Body=md.encode(),ContentType='text/markdown; charset=utf-8')
    with db.transaction():
        for place,data in result.items():
            db.execute('''INSERT INTO news_topic_snapshots(run_id,scope,place,scheduled_at,started_at,report_key,payload)
              VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id,scope,place) DO UPDATE SET
              report_key=EXCLUDED.report_key,payload=EXCLUDED.payload,started_at=EXCLUDED.started_at''',
              (run_id,scope,place,scheduled,started,key,Jsonb(data)))
    Path('reports').mkdir(exist_ok=True)
    Path(f'reports/trends_{scope}.md').write_text(md)
    Path(f'reports/trends_{scope}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(md[:500000])
    log(phase='published',scope=scope,places=len(result),run_id=run_id,delay_seconds=max(0,(started-scheduled).total_seconds()))

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','publish']);p.add_argument('--run-id',required=True)
    p.add_argument('--scope',choices=['country','continent','globe']);p.add_argument('--delay',type=int,default=0);args=p.parse_args()
    db,s3=connect()
    try:
        if args.mode=='prepare':
            if not db.execute('SELECT pg_try_advisory_lock(67426002) locked').fetchone()['locked']:raise RuntimeError('analysis_lock_busy')
            ready=prepare(db,s3,args.run_id)
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('ready='+str(bool(ready)).lower()+'\n')
        else:publish(db,s3,args.run_id,args.scope,args.delay)
    except Exception as exc:
        if args.mode=='prepare':db.execute("UPDATE news_analysis_runs SET status='failed',error=%s WHERE id=%s",(type(exc).__name__,args.run_id))
        # Only class and code location: no credentials or article bodies in public CI logs.
        import traceback
        frames=traceback.extract_tb(exc.__traceback__)
        log(phase='failed',error=type(exc).__name__,location=[f'{Path(f.filename).name}:{f.lineno}:{f.name}' for f in frames[-6:]])
        raise SystemExit(1)
    finally:db.close()

if __name__=='__main__':main()
