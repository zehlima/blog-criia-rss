import json
from pathlib import Path
import pytest
from collector.extract import fetch_source

RSS=b'<rss version="2.0"><channel><item><title>Technology news</title><link>https://www.36kr.com/p/123</link></item></channel></rss>'

def test_primary_rss_error_uses_official_alternative_without_old_validators(monkeypatch):
    monkeypatch.setattr('collector.extract.get',lambda *a,**k: (200,{},b'<html>not rss</html>',a[0]))
    calls=[]
    def get(url, **kw):
        calls.append((url,kw))
        return 200,{'ETag':'alternative-tag'},RSS,url
    monkeypatch.setattr('collector.publisher_listing.get',get)
    status,h,items=fetch_source({'rss_url':'https://36kr.com/feed','etag':'old-primary-tag'})
    assert len(items)==1 and status==200
    assert calls[0][0]=='https://www.36kr.com/feed'
    assert 'headers' not in calls[0][1]
    assert 'ETag' not in h
    assert h['X-Collection-Method']=='official_alternative_rss'

def test_failed_fallback_never_becomes_empty_success(monkeypatch):
    def fail(*a,**k):raise ValueError('http_403')
    monkeypatch.setattr('collector.extract.get',fail)
    monkeypatch.setattr('collector.publisher_listing.get',fail)
    with pytest.raises(ValueError,match='invalid_alternative_feeds'):
        fetch_source({'rss_url':'https://gizmodo.com/feed'})

def test_technology_panel_has_15_distinct_sources():
    panel=json.loads(Path('data/technology15.json').read_text())
    assert len(panel)==len({f['rss_url'] for f in panel})==15
    assert sum(f['source_type']=='community' for f in panel)==1
    assert {'en','de','zh'}=={f['language'] for f in panel}

def test_listing_excludes_navigation_duplicates_and_external_links():
    from collector.publisher_listing import listing_entries
    body=b'''<html><h2><a href="/a-123456">First actual headline</a></h2>
    <a href="/b-234567"><h3>Second actual headline</h3></a>
    <h2><a href="/a-123456">First actual headline again</a></h2>
    <h2><a href="/about">Navigation is not news</a></h2>
    <h2><a href="https://other.example/a-123456">External headline</a></h2></html>'''
    rows=listing_entries(body,'https://gizmodo.com/',r'^/[^/]+-\d{5,}/?$')
    assert len(rows)==2
    assert all(a['published_at'] is None and a['rss_content'] is None for a in rows)
