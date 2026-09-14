"""Read-only, repeatable snapshot for the public monitoring dashboard."""
import json
from pathlib import Path
from datetime import datetime, timezone

ARTICLES_SQL = """SELECT a.id,a.title,a.url,a.published_at,
 string_agg(DISTINCT f.name, ', ') source,
 string_agg(DISTINCT f.country, ', ') country
 FROM (SELECT * FROM news_articles ORDER BY coalesce(published_at,first_seen_at) DESC LIMIT 2000) a
 JOIN news_article_feeds af ON af.article_id=a.id JOIN news_feeds f ON f.id=af.feed_id
 GROUP BY a.id,a.title,a.url,a.published_at,a.first_seen_at
 ORDER BY coalesce(a.published_at,a.first_seen_at) DESC"""
COLLECTION_SQL = 'SELECT id,finished_at,report,feeds FROM news_collection_attempts ORDER BY finished_at DESC LIMIT 1'
TRENDS_SQL = """SELECT s.scope,s.place,s.payload,s.run_id,r.finished_at,r.coverage
 FROM news_topic_snapshots s JOIN news_analysis_runs r ON r.id=s.run_id
 WHERE s.run_id=(SELECT id FROM news_analysis_runs WHERE status='ready' AND EXISTS
 (SELECT 1 FROM news_topic_snapshots WHERE run_id=news_analysis_runs.id)
 ORDER BY finished_at DESC NULLS LAST LIMIT 1)"""

def build(articles, collections, trends):
    now=datetime.now(timezone.utc).isoformat()
    c=collections[0] if collections else {}
    r=c.get('report') or {}; a=r.get('articles') or {}
    feeds=c.get('feeds') or []
    if isinstance(feeds,dict): feeds=list(feeds.values())
    errors=[{k:f.get(k) for k in ('name','country','error','status')} for f in feeds if isinstance(f,dict) and f.get('status')!='ok']
    metrics={'feeds_attempted':r.get('expected_feeds',0)-r.get('feeds_not_attempted',0),'feeds_ok':r.get('feeds_ok'),
     'feeds_errors':r.get('feeds_errors'),'articles':a.get('total'),'extracted':a.get('page_texts'),
     'pending':a.get('pending'),'rss_texts':a.get('publisher_rss_texts'),'extraction_errors':a.get('unavailable')}
    return {'schema_version':1,'generated_at':now,'articles':articles,
     'operations':{'schema_version':1,'status':'partial' if r.get('status')!='complete' else 'ready','as_of':c.get('finished_at'),'run_id':c.get('id'),'data':{'metrics':metrics,'errors':errors}},
     'trends':trends,'article_limit':2000,'editorial_validation':'pending'}

def main():
    from collector.storage import database_connection
    with database_connection() as db:
        with db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            payload=build(db.execute(ARTICLES_SQL).fetchall(),db.execute(COLLECTION_SQL).fetchall(),db.execute(TRENDS_SQL).fetchall())
    dest=Path('frontend/data');dest.mkdir(exist_ok=True)
    (dest/'dashboard.json').write_text(json.dumps(payload,ensure_ascii=False,default=str))
    print(json.dumps({'articles':len(payload['articles']),'trend_places':len(payload['trends']),'generated_at':payload['generated_at']}))

if __name__=='__main__': main()
