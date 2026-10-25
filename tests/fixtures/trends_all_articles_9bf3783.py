"""Original query from 9bf3783 for isolated corpus-equivalence tests."""
from collector.inventory import urls as active_urls

def all_articles(db,cutoff,inventory_urls=None):
    inventory_urls=active_urls() if inventory_urls is None else inventory_urls
    return db.execute('''SELECT a.id,a.url,a.title,a.summary,a.published_at,a.first_seen_at,
      a.content_key,a.content_status,
      jsonb_agg(jsonb_build_object('id',f.id,'name',f.name,
      'country',f.country,'region',f.region,'site_url',f.site_url,'rss_url',f.rss_url) ORDER BY f.id) sources
      FROM news_articles a JOIN news_article_feeds af ON af.article_id=a.id
      JOIN news_feeds f ON f.id=af.feed_id WHERE a.first_seen_at<=%s
        AND f.rss_url=ANY(%s)
        AND a.content_status<>'invalid_reference'
      GROUP BY a.id ORDER BY a.id''',(cutoff,inventory_urls)).fetchall()
