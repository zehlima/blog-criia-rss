"""One recorded appearance per article/feed/six-hour slot, including HTTP 304."""

def record(db, feed, slot):
    from psycopg.types.json import Jsonb
    source = {k: feed[k] for k in ('id', 'name', 'country', 'region', 'site_url', 'rss_url')}
    db.execute('''INSERT INTO news_article_observations(slot,feed_id,article_id,source,title,summary)
      SELECT %s,%s,a.id,%s,a.title,a.summary FROM news_articles a
      JOIN news_article_feeds af ON af.article_id=a.id WHERE af.feed_id=%s AND af.in_latest
      ON CONFLICT(slot,feed_id,article_id) DO NOTHING''', (slot, feed['id'], Jsonb(source), feed['id']))
    db.execute('''INSERT INTO news_observation_batches(slot,feed_id,articles)
      SELECT %s,%s,count(*) FROM news_article_observations WHERE slot=%s AND feed_id=%s
      ON CONFLICT(slot,feed_id) DO NOTHING''', (slot, feed['id'], slot, feed['id']))
