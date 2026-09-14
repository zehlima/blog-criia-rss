"""Midnight-triggered calendar-day closure; explicit previews never masquerade as final."""
import argparse
import gzip
import hashlib
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from collector.inventory import urls as active_urls
from collector.storage import connect
from psycopg.types.json import Jsonb
from trends.main import MODEL, MODEL_REVISION, get_object, optional, put_json
from .core import TZ, VERSION, LEAD_CHARS, bounds, fingerprint, group_copies, accounting


def log(**value):
    print(json.dumps(value, ensure_ascii=False, default=str), flush=True)


def choose_day(attempt, mode):
    slot = attempt['slot'].astimezone(TZ)
    if mode == 'auto':
        if slot.hour != 0 or attempt['report'].get('status') not in ('complete','complete_with_gaps'):
            return None
        return (slot.date()-timedelta(days=1)).isoformat(), 'closed'
    return attempt['finished_at'].astimezone(TZ).date().isoformat(), 'preview'


def corpus(db, start, end, cutoff):
    return db.execute('''SELECT a.id,a.url,a.title,a.summary,a.published_at,a.first_seen_at,a.content_key,a.content_status,
      jsonb_agg(jsonb_build_object('id',f.id,'name',f.name,'country',f.country,'region',f.region,
        'site_url',f.site_url,'rss_url',f.rss_url) ORDER BY f.id) sources
      FROM news_articles a JOIN news_article_feeds af ON af.article_id=a.id JOIN news_feeds f ON f.id=af.feed_id
      WHERE a.first_seen_at<=%s AND coalesce(a.published_at,a.first_seen_at)>=%s
        AND coalesce(a.published_at,a.first_seen_at)<%s AND coalesce(a.published_at,a.first_seen_at)<=%s
        AND a.content_status<>'invalid_reference' AND f.rss_url=ANY(%s)
      GROUP BY a.id ORDER BY a.id''', (cutoff,start,end,cutoff,active_urls())).fetchall()


def read_body(s3, article):
    article['text_basis'] = 'title_summary'
    article['body_hash'] = None
    article['body_error'] = None
    body = article.get('summary') or ''
    if article.get('content_key'):
        try:
            body = gzip.decompress(get_object(s3,article['content_key'])).decode('utf-8')
            article['text_basis'] = 'publisher_rss' if article['content_status']=='rss_content' else 'extracted_page'
            article['body_hash'] = fingerprint(body) if len(body.strip()) >= 200 else None
        except Exception as exc:
            article['body_error'] = type(exc).__name__
    # Preserve paragraph order; compare the opening, not a title repeated in the feed summary.
    article['lead'] = ' '.join(body.split())[:LEAD_CHARS]
    return article


def embeddings(s3, articles):
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
    # Text/model inputs are unchanged: retain the expensive v1 vector cache.
    key = 'daily/cache/daily-v1-title-lead-conservative.npz'
    raw = optional(s3,key)
    cache = {}
    if raw:
        with np.load(io.BytesIO(raw),allow_pickle=False) as old:
            cache = dict(zip(old['hashes'].tolist(),old['vectors']))
    texts = [(a['title'][:1000],a['lead']) for a in articles]
    def identity(text):
        return hashlib.sha256((MODEL_REVISION+'|256|'+text).encode()).hexdigest()
    missing = {identity(text):text for pair in texts for text in pair if identity(text) not in cache}
    log(phase='embeddings',missing=len(missing),articles=len(articles))
    if missing:
        model = SentenceTransformer(MODEL,revision=MODEL_REVISION,device='cpu',trust_remote_code=False)
        model.max_seq_length=256
        items = list(missing.items())
        for start in range(0,len(items),128):
            batch = items[start:start+128]
            vectors = model.encode([value for _,value in batch],batch_size=32,normalize_embeddings=True,show_progress_bar=False)
            cache.update({h:v.astype(np.float32) for (h,_),v in zip(batch,vectors)})
            if start%512==0 or start+128>=len(items):
                buf=io.BytesIO()
                np.savez_compressed(buf,hashes=np.array(list(cache)),vectors=np.array(list(cache.values()),dtype=np.float32))
                s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=key,Body=buf.getvalue())
                log(phase='embedding_checkpoint',done=min(start+128,len(items)),total=len(items))
    if not articles:
        return np.empty((0,384)),np.empty((0,384))
    return (np.array([cache[identity(title)] for title,_ in texts]),
            np.array([cache[identity(lead)] if lead else np.zeros(384,dtype=np.float32) for _,lead in texts]))


def markdown(payload):
    text=f'# Fechamento diário — {payload["day"]}\n\nModo: **{payload["mode"]}**. Fuso: America/Sao_Paulo.\n\n'
    text+='Publicações = URLs distintas; textos distintos e cópias são estimativas conservadoras.\n'
    text+='Aparições em feeds contam uma vez por URL, feed e janela de seis horas. Não são novas publicações.\n'
    text+='Similaridade não é probabilidade calibrada. Mesma pauta não prova republicação.\n\n'
    text+='```json\n'+json.dumps(payload['coverage'],ensure_ascii=False,indent=2)+'\n```\n\n'
    for scope,label in [('country','País'),('continent','Continente'),('globe','Globo')]:
        text+=f'## {label}\n\n| Local | Publicações | Textos distintos estimados | Cópias adicionais estimadas | Aparições nos feeds |\n|---|---:|---:|---:|---:|\n'
        for place,r in payload['results'][scope].items():
            text+=f'| {place} | {r["publications"]} | {r["distinct_texts_estimated"]} | {r["extra_copies_estimated"]} | {r["feed_sightings_all_articles"]} |\n'
        text+='\n'
    text+='## Republicações estimadas no mundo\n\n'
    for family in payload['results']['globe']['Globo']['ranking'][:40]:
        if family['publications']<2:continue
        text+=f'### {family["label"]}\n\n{family["publications"]} publicações; {family["publishers"]} veículos.\n\n'
        for a in family['evidence']:
            text+=f'- [{a["title"]}]({a["url"]})\n'
        text+='\n'
    return text


def run(db,s3,mode):
    parent=os.getenv('SOURCE_COLLECTION_RUN_ID')
    attempt=db.execute('SELECT * FROM news_collection_attempts WHERE id=%s',(parent,)).fetchone() if parent else db.execute('SELECT * FROM news_collection_attempts ORDER BY finished_at DESC LIMIT 1').fetchone()
    if not attempt:
        log(phase='skipped',reason='no_completed_collection');return
    selected=choose_day(attempt,mode)
    if not selected:
        log(phase='skipped',reason='wait_for_finished_midnight_collection',source_attempt=attempt['id']);return
    day,mode=selected
    start,end=bounds(day)
    cutoff=attempt['finished_at']
    run_id=f'{VERSION}-{day}' if mode=='closed' else f'{VERSION}-{day}-preview-{os.getenv("GITHUB_RUN_ID","local")}'
    if db.execute('SELECT id FROM news_daily_closures WHERE id=%s',(run_id,)).fetchone():
        log(phase='already_closed',run_id=run_id);return
    with db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        articles=corpus(db,start,end,cutoff)
        observations=db.execute('SELECT slot,feed_id,article_id,source FROM news_article_observations WHERE slot>=%s AND slot<%s AND observed_at<=%s',(start,end,cutoff)).fetchall()
        batches=db.execute('SELECT count(*) n FROM news_observation_batches WHERE slot>=%s AND slot<%s AND recorded_at<=%s',(start,end,cutoff)).fetchone()['n']
        first_ledger=db.execute('SELECT min(recorded_at) first_recorded FROM news_observation_batches').fetchone()['first_recorded']
    log(phase='corpus',day=day,mode=mode,articles=len(articles),observations=len(observations))
    with ThreadPoolExecutor(max_workers=16) as pool:
        articles=list(pool.map(lambda a:read_body(s3,a),articles))
    title_vec,lead_vec=embeddings(s3,articles)
    evidence=group_copies(articles,title_vec,lead_vec)
    sources=attempt['feeds']
    results={scope:accounting(articles,observations,scope,sources) for scope in ('country','continent','globe')}
    coverage={'mode':mode,'day_start':start.isoformat(),'day_end_exclusive':end.isoformat(),'collection_cutoff':cutoff.isoformat(),
              'source_attempt':attempt['id'],'articles':len(articles),
              'body_texts':sum(a['text_basis'] in ('extracted_page','publisher_rss') for a in articles),
              'title_summary_only':sum(a['text_basis'] in ('title_summary','untrusted_body') for a in articles),
              'untrusted_body_texts':sum(a['text_basis']=='untrusted_body' for a in articles),
              'body_read_errors':sum(bool(a['body_error']) for a in articles),
              'date_fallback':sum(a['published_at'] is None for a in articles),
              'feed_errors_at_closure':attempt['report'].get('feeds_errors'),
              'observation_batches':batches,'expected_full_day_feed_batches':4*len(sources),
              'observation_history_started':str(first_ledger) if first_ledger else None,
              'observation_history_complete':batches>=4*len(sources),
              'historical_sightings_not_reconstructed':True,
              'probabilities_calibrated':False,'editorial_validation':'pending',
              'candidate_search':'top32_semantic_neighbors_plus_minhash_and_exact_hash; recall_not_guaranteed',
              'lead_characters':LEAD_CHARS,'model_max_tokens':256,
              'possible_republication_pairs':sum(e['decision']=='possible_republication' for e in evidence),
              'scope_note':'País editorial do veículo. Totais globais recalculados; não soma dos países.'}
    payload={'run_id':run_id,'day':day,'mode':mode,'version':VERSION,'model':MODEL,'model_revision':MODEL_REVISION,
             'coverage':coverage,'results':results,'pair_evidence':evidence,
             'article_audit':[{k:v for k,v in a.items() if k not in ('_grams','lead','summary')} for a in articles]}
    root='daily/runs/'+run_id
    key=put_json(s3,root+'/report.json.gz',payload)
    text=markdown(payload)
    s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=root+'/report.md',Body=text.encode(),ContentType='text/markdown; charset=utf-8')
    # Verify durable storage before advertising a completed accounting run.
    reread=json.loads(gzip.decompress(get_object(s3,key)))
    if reread['run_id']!=run_id or reread['coverage']['articles']!=len(articles):
        raise RuntimeError('report_readback_failed')
    summary={scope:{place:{k:v for k,v in r.items() if k not in ('ranking','subject_ranking')} for place,r in rows.items()} for scope,rows in results.items()}
    db.execute('''INSERT INTO news_daily_closures(id,day,mode,source_attempt,version,cutoff,report_key,summary,coverage)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING''',(run_id,day,mode,attempt['id'],VERSION,cutoff,key,Jsonb(summary),Jsonb(coverage)))
    dest=Path('reports/daily');dest.mkdir(parents=True,exist_ok=True)
    (dest/'report.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str))
    (dest/'report.md').write_text(text)
    (dest/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(text[:500000])
    log(phase='accounting_saved',run_id=run_id,mode=mode,global_totals=summary['globe']['Globo'],coverage=coverage)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['auto','preview'],default='auto');args=parser.parse_args()
    db,s3=connect()
    try:
        if not db.execute('SELECT pg_try_advisory_lock(67426003) locked').fetchone()['locked']:
            raise RuntimeError('daily_accounting_busy')
        run(db,s3,args.mode)
    except Exception as exc:
        import traceback
        log(phase='failed',error=type(exc).__name__,locations=[f'{Path(f.filename).name}:{f.lineno}' for f in traceback.extract_tb(exc.__traceback__)[-5:]])
        raise SystemExit(1)
    finally:
        db.close()


if __name__=='__main__':main()
