import gzip
from datetime import datetime,timezone
from pathlib import Path
import json
import pytest
from pglast import parse_sql
from collector.main import slot_for,attempt
from collector.extract import entries,fetch_article,digest
from collector.network import canonical
from collector.storage import archive

@pytest.mark.parametrize('hour,expected',[(2,21),(3,3),(8,3),(9,9),(15,15),(21,21),(23,21)])
def test_brasilia_windows(hour,expected):
    now=datetime(2026,9,14,hour,tzinfo=timezone.utc)
    got=slot_for(now)
    assert got.hour==expected
    assert got.day==(13 if hour==2 else 14)

def test_inventory_all600():
    f=json.loads(Path('data/feeds.json').read_text())
    assert len(f)==len({x['rss_url'] for x in f})==600

def test_rss_and_atom():
    rss=b'<rss version="2.0"><channel><title>x</title><item><title>A</title><link>https://example.com/a#part</link><description>Resumo</description></item></channel></rss>'
    a=entries(rss,'https://example.com')[0]
    assert a['url']=='https://example.com/a'
    assert a['published_at'] is None
    atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><title>x</title><entry><title>B</title><link href="https://example.com/b"/><updated>2026-09-14T03:00:00Z</updated></entry></feed>'
    assert entries(atom,'https://example.com')[0]['source_updated_at'].hour==3

def test_malformed_is_not_empty_success():
    with pytest.raises(ValueError):entries(b'<html>Blocked</html>','https://example.com')
    with pytest.raises(ValueError):entries(b'<rss version="2.0"><channel><item><title>lost</title></item></channel></rss>','https://example.com')

def test_archive_is_deterministic_and_versioned(monkeypatch):
    monkeypatch.setenv('R2_BUCKET','test')
    class S3:
        def put_object(self,**kwargs):self.last=kwargs
    s=S3()
    h,key,size=archive(s,'https://example.com/a','Texto original')
    assert gzip.decompress(s.last['Body']).decode()=='Texto original'
    assert archive(s,'https://example.com/a','Texto original')[1]==key
    assert archive(s,'https://example.com/a','Texto corrigido')[1]!=key
    assert h==digest('Texto original')

def test_304_requires_preexisting_archive(monkeypatch):
    monkeypatch.setattr('collector.extract.get',lambda *a,**kw:(304,{},b'','https://example.com'))
    with pytest.raises(ValueError):fetch_article({'url':'https://example.com'})
    assert fetch_article({'url':'https://example.com','content_key':'key'})[2] is None

def test_short_extraction_is_pending_not_full(monkeypatch):
    monkeypatch.setattr('collector.extract.get',lambda *a,**kw:(200,{},b'<html>Access denied</html>','https://example.com'))
    with pytest.raises(ValueError,match='insufficient_text'):fetch_article({'url':'https://example.com'})

def test_article_body_extraction(monkeypatch):
    text='Uma reportagem sobre tecnologia e inovação descreve os avanços da pesquisa e seus impactos na sociedade. '
    body=('<html><head><title>Reportagem</title></head><body><article><h1>Reportagem</h1><p>'+text*20+'</p></article></body></html>').encode()
    monkeypatch.setattr('collector.extract.get',lambda *a,**kw:(200,{},body,'https://example.com'))
    assert len(fetch_article({'url':'https://example.com'})[2])>200

def test_errors_do_not_expose_credentials():
    def fail(_):raise RuntimeError('postgresql://user:secret@host')
    assert attempt(fail,{})==(None,'RuntimeError')

def test_url_and_sql_syntax():
    assert canonical('/x?q=1#fragment','https://example.com')=='https://example.com/x?q=1'
    with pytest.raises(ValueError):canonical('javascript:alert(1)')
    assert len(parse_sql(Path('sql/001_schema.sql').read_text()))>10
