import threading
from datetime import datetime,timezone
import time
from collector.main import articles

def test_slow_article_does_not_block_other_worker(monkeypatch):
    release=threading.Event();finished=[];saved=[]
    rows=[{'id':i,'url':f'https://source{i}.example/a'} for i in range(4)]
    class Result:
        def __init__(self,rows):self.rows=rows
        def fetchall(self):return self.rows
    class DB:
        def execute(self,sql,params):
            excluded,slot,capacity=params
            return Result([r for r in rows if r['id'] not in excluded and r['id'] not in saved][:capacity])
    def fetch(a):
        if a['id']==0:assert release.wait(3),'a slow request blocked independent articles'
        else:
            finished.append(a['id'])
            if len(finished)==3:release.set()
        return a
    monkeypatch.setenv('ARTICLE_WORKERS','2')
    monkeypatch.setattr('collector.main.fetch_article',fetch)
    monkeypatch.setattr('collector.article_batch.preserve',lambda s,a,r:r)
    monkeypatch.setattr('collector.article_batch.outcome',lambda a,r,e,s:{'id':a['id'],'last_error':e})
    def persist(db,batch):
        saved.extend(r['id'] for r in batch)
        assert all(r['last_error'] is None for r in batch)
        return 0
    monkeypatch.setattr('collector.article_batch.persist',persist)
    articles(DB(),None,datetime.now(timezone.utc),time.monotonic()+4)
    assert sorted(saved)==[0,1,2,3]

def test_rss_summary_is_never_promoted_to_full_article():
    import json
    from collector.rss_fallback import publisher_text
    assert publisher_text(json.dumps([{'type':'feed_summary','value':'Long summary '*100}])) is None
    text=publisher_text(json.dumps([{'type':'text/html','value':'<p>'+'Publisher text '*100+'</p><script>bad()</script>'}]))
    assert text and 'bad()' not in text and '<p>' not in text

def test_recoverable_xml_and_partial_entries_keep_good_news():
    from collector.extract import entries
    body=b'<rss version="2.0"><channel><title>News</title><item><title>Research & development</title><link>https://example.com/a</link></item><item><title>incomplete</title></item></channel></rss>'
    with __import__('pytest').warns(RuntimeWarning):items=entries(body,'https://example.com')
    assert len(items)==1 and items[0]['url']=='https://example.com/a'

def test_empty_rss_is_not_counted_as_populated():
    from collector.extract import entries
    import pytest
    with pytest.raises(ValueError,match='invalid_empty'):
        entries(b'<rss version="2.0"><channel><title>empty</title></channel></rss>','https://example.com')

def test_robots_server_failure_is_not_a_publisher_disallow(monkeypatch):
    from collector import network
    import pytest
    monkeypatch.setattr(network,'_robots',{})
    def fail(*a,**kw):raise ValueError('http_503')
    monkeypatch.setattr(network,'get',fail)
    for _ in range(2):
        with pytest.raises(ValueError,match='robots_unavailable_http_503'):
            network.allowed('https://example.com/article')
