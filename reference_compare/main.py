"""Consumes immutable daily closures, writes a versioned comparison, never recollects news."""
import gzip
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from collector.storage import connect
from collector.technology15 import manifest
from daily.main import embeddings,read_body
from daily.core import bounds,compare
from trends.clustering import anchors,compatible
from trends.main import get_json,optional,put_json
from .core import VERSION,report_key,partition,build

def log(**value):print(json.dumps(value,ensure_ascii=False,default=str),flush=True)

def match(articles,title,lead,refs):
    import numpy as np
    from collections import Counter
    street,reference=partition(articles,refs)
    index={a['id']:i for i,a in enumerate(articles)}
    usable=lambda a: a.get("text_basis") in ("extracted_page","publisher_rss") and len(a.get("lead") or "")>=200
    reference=[a for a in reference if usable(a)]
    street=[a for a in street if usable(a)]
    ris=[index[a['id']] for a in reference]
    if not ris:return []
    freq=Counter(t for a in articles for t in anchors(a['title']));pairs=[]
    for start in range(0,len(street),256):
        sis=[index[a['id']] for a in street[start:start+256]]
        ts=title[sis]@title[ris].T;ls=lead[sis]@lead[ris].T
        for x,y in np.argwhere((ts>=.80)&(ls>=.80)):
            a,b=articles[sis[x]],articles[ris[y]]
            result=compare(a,b,float(ts[x,y]),float(ls[x,y]))
            if result['decision']=='distinct':continue
            if result['decision']!='duplicate' and not compatible(a['title'],b['title'],result['similarity_score'],frequency=freq,rare_limit=max(4,int(len(articles)*.001))):continue
            pairs.append(dict(result,street_id=a['id'],reference_id=b['id']))
    return pairs

def coverage(db,closure,refs,articles):
    start,end=bounds(closure['day'])
    rows=db.execute('''SELECT f.rss_url,r.slot,r.status,r.items,r.error,r.checked_at
       FROM news_feeds f JOIN news_feed_runs r ON r.feed_id=f.id
       WHERE f.rss_url=ANY(%s) AND r.slot>=%s AND r.slot<=%s AND r.checked_at<=%s
       ORDER BY r.slot''',([r['rss_url'] for r in refs],start,end,closure['cutoff'])).fetchall()
    _,reference=partition(articles,refs)
    result=[]
    for r in refs:
        checks=[x for x in rows if x['rss_url']==r['rss_url']]
        items=[a for a in reference if r['name'] in a['reference_names']]
        ok_slots={str(x['slot']) for x in checks if x['status']=='ok'}
        result.append({'name':r['name'],'rss_url':r['rss_url'],'source_type':r.get('source_type'),
           'checks':checks,'successful_slots':len(ok_slots),'expected_day_and_closing_slots':5,
           'day_articles':len(items),'body_texts':sum(a.get('text_basis') in ('extracted_page','publisher_rss') for a in items),
           'coverage':'observed_slots_complete' if len(ok_slots)==5 else 'partial_or_unverifiable',
           'note':'A feed check does not prove exhaustive publisher coverage. Checks updated after the frozen cutoff are excluded.'})
    return result

def run():
    db,s3=connect();refs=manifest()
    try:
        if not db.execute('SELECT pg_try_advisory_lock(67426004) locked').fetchone()['locked']:raise RuntimeError('reference_comparison_busy')
        closures=db.execute("SELECT id,day,cutoff,report_key FROM news_daily_closures WHERE mode='closed' ORDER BY day").fetchall()
        if not closures:log(phase='waiting_for_closed_day');return
        for closure in closures:
            key=report_key(closure['id'],refs)
            if optional(s3,key):log(phase='already_saved',day=closure['day']);continue
            daily=get_json(s3,closure['report_key']);articles=daily['article_audit']
            # The closure audit freezes IDs, source memberships and acquisition cutoff.
            with ThreadPoolExecutor(max_workers=16) as pool:
                def load(a):
                    untrusted=a.get('text_basis')=='untrusted_body'
                    value=read_body(s3,dict(a))
                    if untrusted:value.update(text_basis='untrusted_body',lead='',body_hash=None,body_error='shared_body_with_divergent_titles')
                    return value
                articles=list(pool.map(load,articles))
            source_coverage=coverage(db,closure,refs,articles)
            title,lead=embeddings(s3,articles)
            pairs=match(articles,title,lead,refs)
            payload=build(closure,articles,refs,pairs,source_coverage)
            payload['generated_at']=datetime.now(timezone.utc).isoformat()
            payload['source_closure_coverage']=daily['coverage']
            saved=put_json(s3,key,payload)
            check=get_json(s3,saved)
            if check['counts']!=payload['counts']:raise RuntimeError('reference_readback_failed')
            folder=Path('reports/reference15');folder.mkdir(parents=True,exist_ok=True)
            (folder/(str(closure['day'])+'.json')).write_text(json.dumps(payload,ensure_ascii=False,default=str))
            log(phase='comparison_saved',day=closure['day'],counts=payload['counts'],coverage=[{'name':r['name'],'coverage':r['coverage'],'articles':r['day_articles']} for r in source_coverage])
    finally:db.close()

if __name__=='__main__':run()
