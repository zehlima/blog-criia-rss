"""Idempotent repairs for historical article links produced by known parser ambiguity."""
from psycopg.types.json import Jsonb
from .extract import fetch_source
from .storage import save_entries

DDAY_RSS='https://www.dday.it/rss'

def repair_dday(db):
    feed=db.execute('SELECT * FROM news_feeds WHERE rss_url=%s',(DDAY_RSS,)).fetchone()
    if not feed:return {'source':'DDay.it','mapped':0,'invalidated':0,'reason':'feed_not_seeded'}
    _,_,items=fetch_source(feed)
    links={a['title']:a['url'] for a in items}
    data=Jsonb([{'title':title,'url':url} for title,url in links.items()])
    with db.transaction():
        moved=db.execute("""WITH incoming AS (
          SELECT * FROM jsonb_to_recordset(%s::jsonb) AS i(title text,url text)
        ), candidates AS (
          SELECT DISTINCT ON (a.id) a.id,i.url FROM news_articles a
          JOIN news_article_feeds af ON af.article_id=a.id AND af.feed_id=%s
          JOIN incoming i ON i.title=a.title
          WHERE split_part(a.url,'/',3)='images.dday.it'
        )
        UPDATE news_articles a SET url=c.url,content_status=CASE WHEN a.content_key IS NULL THEN 'pending' ELSE a.content_status END,
          last_error=NULL,next_attempt_at=now()
        FROM candidates c WHERE a.id=c.id
          AND NOT EXISTS(SELECT 1 FROM news_articles current WHERE current.url=c.url)
        RETURNING a.id""",(data,feed['id'])).fetchall()
        # Insert/update canonical rows and make them current for the publisher.
        save_entries(db,feed['id'],items)
        pairs=db.execute("""WITH incoming AS (
          SELECT * FROM jsonb_to_recordset(%s::jsonb) AS i(title text,url text)
        )
        SELECT broken.id broken_id,correct.id correct_id
        FROM news_articles broken
        JOIN news_article_feeds af ON af.article_id=broken.id AND af.feed_id=%s
        JOIN incoming i ON i.title=broken.title
        JOIN news_articles correct ON correct.url=i.url
        WHERE split_part(broken.url,'/',3)='images.dday.it'""",(data,feed['id'])).fetchall()
        for pair in pairs:
            db.execute("""UPDATE news_articles correct SET
              rss_content_key=COALESCE(correct.rss_content_key,broken.rss_content_key)
              FROM news_articles broken WHERE correct.id=%s AND broken.id=%s""",
              (pair['correct_id'],pair['broken_id']))
            db.execute("""INSERT INTO news_article_feeds(article_id,feed_id,in_latest)
              VALUES(%s,%s,true) ON CONFLICT(article_id,feed_id) DO UPDATE SET in_latest=true""",
              (pair['correct_id'],feed['id']))
            db.execute("""UPDATE news_article_feeds SET in_latest=false
              WHERE article_id=%s AND feed_id=%s""",(pair['broken_id'],feed['id']))
            db.execute("""UPDATE news_articles SET content_status='invalid_reference',
              last_error='rss_media_link_replaced',next_attempt_at='infinity'
              WHERE id=%s""",(pair['broken_id'],))
    return {'source':'DDay.it','mapped':len(moved),'invalidated':len(pairs),'feed_items':len(items)}
