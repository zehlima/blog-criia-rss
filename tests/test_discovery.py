from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
import ast
import inspect

import pytest
from pglast import parse_sql
from collector import discovery, discovery_store as store, discovery_policy as policy, network

NOW = datetime(2026,9,17,10,tzinfo=timezone.utc)


class Rows:
    def __init__(self,rows): self.rows=rows
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return self.rows


class DB:
    def __init__(self,rows=()): self.rows=list(rows); self.calls=[]
    def transaction(self): return nullcontext()
    def execute(self,query,params=None):
        self.calls.append((query,params))
        return Rows(self.rows)


def observation(at, samples=None):
    return {'observed_at':at,'payload':{'http_status':200,'item_count':2,
        'samples':samples or [
            {'url':'https://news.example/a','extraction':'usable','body_hash':'one'},
            {'url':'https://news.example/b','extraction':'usable','body_hash':'two'}]}}


def test_reviewer_requires_spaced_observations_and_distinct_article_bodies():
    assert not policy.assess([observation(NOW)])['technical_ready']
    assert not policy.assess([observation(NOW),observation(NOW+timedelta(hours=5))])['technical_ready']
    result=policy.assess([observation(NOW),observation(NOW+timedelta(hours=6))])
    assert result['technical_ready'] and result['ai_evaluated'] is False
    assert result['editorial_approval'] is False
    assert result['required_next_step']=='human_editorial_review'
    duplicate=[{'url':'https://news.example/a','extraction':'usable','body_hash':'copy'},
               {'url':'https://news.example/b','extraction':'usable','body_hash':'copy'}]
    assert not policy.assess([observation(NOW,duplicate),observation(NOW+timedelta(hours=6),duplicate)])['technical_ready']


def test_revisions_of_same_article_are_not_two_independent_articles():
    first=[{'url':'https://news.example/a','extraction':'usable','body_hash':'old'}]
    second=[{'url':'https://news.example/a','extraction':'usable','body_hash':'new'}]
    assert not policy.assess([observation(NOW,first),observation(NOW+timedelta(hours=6),second)])['technical_ready']


def test_discovery_keeps_advertised_feeds_and_excludes_comments_and_private_schemes():
    page=b'''<html><head><link type="application/rss+xml" href="/rss"/></head><body>
      <a href="/comments/feed">Comments</a><a href="https://other.example/news">Editorial link</a>
      <a href="javascript:alert(1)">No</a><link type="application/feed+json" href="/feed.json"/>
      <a href="https://secret:password@other.example/rss">No</a></body></html>'''
    result=policy.discover_links(page,'https://news.example/')
    assert result['feeds']==['https://news.example/feed.json','https://news.example/rss']
    assert result['sites']==['https://other.example/']
    assert policy.discover_links(page,'https://news.example/',4)['sites']==[]


def test_crawl_cursor_reaches_links_beyond_first_page_budget():
    page=('<html>'+''.join(f'<a href="https://publisher{i:03}.example/">news</a>' for i in range(250))+'</html>').encode()
    fetch=lambda *a,**k:(200,{},page,'https://news.example/')
    a=policy.scan_site({'url':'https://news.example/'},None,fetch=fetch)
    b=policy.scan_site({'url':'https://news.example/','link_cursor':a['next_link_cursor']},None,fetch=fetch)
    assert len(a['sites'])==200 and a['truncated_links']
    assert len(b['sites'])==50 and b['next_link_cursor']==0
    assert len(set(a['sites']+b['sites']))==250


def test_feed_parser_rejects_html_200_and_json_feed_without_supported_adapter():
    task={'url':'https://news.example/rss'}
    for body,reason in [(b'<html>Error</html>','invalid_or_malformed_feed'),
                        (b'{"version":"https://jsonfeed.org/version/1.1"}','unsupported_json_feed')]:
        with pytest.raises(ValueError,match=reason):
            policy.scan_feed(task,None,fetch=lambda *a,**k:(200,{},body,task['url']))


def test_feed_sample_uses_real_parser_and_extractor_and_preserves_failed_articles():
    rss=b'<rss version="2.0"><channel><item><title>First</title><link>https://news.example/a</link></item><item><title>Second</title><link>https://news.example/b</link></item></channel></rss>'
    article=('<html><body><article><h1>Reporter explains research</h1>'+''.join('<p>Researchers gathered reliable evidence about the changing ecosystem and discussed several conclusions with independent experts. Their work provides detailed information about the experimental methods and the scientific limitations.</p>' for _ in range(6))+'</article></body></html>').encode()
    def fetch(url,**kwargs):
        assert kwargs['check_robots'] is True
        if url.endswith('/rss'):return 200,{},rss,url
        if url.endswith('/a'):return 200,{},article,url
        raise ValueError('http_403')
    result=policy.scan_feed({'url':'https://news.example/rss'},None,fetch=fetch)
    assert result['item_count']==2
    assert result['samples'][0]['extraction']=='usable'
    assert len(result['samples'][0]['body_hash'])==64
    assert result['samples'][1]['error']=='http_403'
    assert not result['ai_evaluated'] and not result['editorial_approval']


def test_budget_failure_propagates_without_becoming_a_successful_partial_observation():
    with pytest.raises(store.BudgetExhausted):
        policy.scan_feed({'url':'https://news.example/rss'},None,
            fetch=lambda *a,**k:(_ for _ in ()).throw(store.BudgetExhausted('discovery_daily_budget_exhausted')))


def test_budget_reserves_before_io_and_does_not_refund_failed_requests():
    db=DB([{'day':'2026-09-17'}]); budget=store.Budget(db,requests=1)
    budget.reserve(1024)
    assert len(db.calls)==1 and budget.remaining==0
    with pytest.raises(store.BudgetExhausted):budget.reserve(1024)
    assert len(db.calls)==1
    with pytest.raises(store.BudgetExhausted):store.Budget(DB()).reserve(1024)


def test_disabled_tick_never_connects_or_crawls(monkeypatch,capsys):
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','0')
    monkeypatch.setattr(discovery,'database_connection',lambda:pytest.fail('unexpected database connection'))
    assert discovery.main(['tick'])==0
    assert 'disabled' in capsys.readouterr().out
    db=DB();assert discovery.tick(db)['status']=='disabled';assert not db.calls


def test_tick_pauses_and_releases_task_on_exhausted_budget(monkeypatch):
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','1')
    db=DB([{'locked':True}]); task={'id':4,'kind':'site'}; failures=[]
    monkeypatch.setattr(discovery,'claim',lambda db:task)
    monkeypatch.setattr(discovery,'fail_task',lambda db,t,e,**kw:failures.append((t,e,kw)))
    class Budget:remaining=1;deadline=float('inf')
    def exhaust(*a):raise store.BudgetExhausted('discovery_daily_budget_exhausted')
    result=discovery.tick(db,budget=Budget(),site_scan=exhaust)
    assert result['status']=='budget_paused' and result['processed']==0
    assert failures[0][2]['budget_pause']
    assert 'pg_advisory_unlock' in db.calls[-1][0]


def test_expired_or_wrong_lease_cannot_commit_results():
    db=DB()
    with pytest.raises(ValueError,match='discovery_lease_lost'):
        store.finish_site(db,{'id':1,'lease_token':'wrong'},{'feeds':[],'sites':[]})
    assert len(db.calls)==1


@pytest.mark.parametrize('candidate',[
    {'status':'observing','technical_evaluation':{}},
    {'status':'awaiting_editorial_review','technical_evaluation':{'technical_ready':True},'last_error':'http_503','last_checked_at':NOW},
    {'status':'awaiting_editorial_review','technical_evaluation':{'technical_ready':True},'last_error':None,'last_checked_at':NOW-timedelta(days=3)},
])
def test_human_cannot_admit_without_current_technical_evidence(candidate):
    db=DB([candidate])
    with pytest.raises(ValueError,match='discovery_technical_review_required'):
        store.review(db,1,'editor','Source reviewed by editor',['https://news.example/about'],
            accept=True,metadata={'name':'News','country':'Brasil','region':'América do Sul'},now=NOW)
    assert len(db.calls)==1


def test_admission_effective_only_in_the_next_collection_window():
    assert policy.next_window(NOW)==datetime(2026,9,17,15,tzinfo=timezone.utc)
    assert policy.next_window(datetime(2026,9,17,21,tzinfo=timezone.utc))==datetime(2026,9,18,3,tzinfo=timezone.utc)


def test_secret_exception_details_are_never_in_operational_error():
    assert policy.safe_error(RuntimeError('postgres://user:secret@host/db'))=='RuntimeError'
    assert policy.safe_error(ValueError('http_429'))=='http_429'


def test_new_schema_and_queries_parse_as_postgres():
    for module in (store,discovery):
        tree=ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                and node.func.attr=='execute' and node.args and isinstance(node.args[0],ast.Constant)
                and isinstance(node.args[0].value,str)):
                parse_sql(node.args[0].value.replace('%s','NULL').replace('%%','%'))
    schema=Path('sql/002_continuous_discovery.sql').read_text();parse_sql(schema)
    assert 'ENABLE ROW LEVEL SECURITY' in schema
    assert 'FROM PUBLIC,anon,authenticated' in schema


def test_network_budget_includes_robots_redirect_hops_and_body_limit(monkeypatch):
    monkeypatch.setattr(network,'public_destination',lambda u:'93.184.216.34')
    monkeypatch.setattr(network,'_next',{});monkeypatch.setattr(network,'_robots',{})
    monkeypatch.setattr(network.time,'sleep',lambda _:None)
    calls=[];reservations=[]
    class Budget:
        def reserve(self,n):reservations.append(n)
    class Response:
        def __init__(self,url):
            self.url=url;self.is_redirect=url.endswith('/old');self.status_code=302 if self.is_redirect else 200
            self.headers={'Location':'/rss'} if self.is_redirect else {}
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def iter_content(self,n):yield b'User-agent: *\nAllow: /' if self.url.endswith('/robots.txt') else b'feed'
    monkeypatch.setattr(network,'pinned_request',lambda url,address,**kw:(calls.append(url) or Response(url)))
    assert network.get('https://news.example/old',check_robots=True,budget=Budget(),max_bytes=100)[3]=='https://news.example/rss'
    assert calls==['https://news.example/robots.txt','https://news.example/old','https://news.example/rss']
    assert reservations==[512*1024+65536,100+65536,100+65536]


def test_stale_body_evidence_and_current_failed_extraction_do_not_pass():
    old=[observation(NOW-timedelta(days=11)),observation(NOW-timedelta(days=10))]
    failed=observation(NOW,[{'url':'https://news.example/a','extraction':'unavailable','error':'http_403'}])
    assert not policy.assess(old+[failed])['technical_ready']
    recent=observation(NOW-timedelta(hours=7))
    assert not policy.assess([recent,failed])['technical_ready']


def test_latest_hash_wins_even_when_observations_are_returned_descending():
    now=observation(NOW,[{'url':'https://news.example/a','extraction':'usable','body_hash':'same'},
        {'url':'https://news.example/b','extraction':'usable','body_hash':'same'}])
    assert not policy.assess([now,observation(NOW-timedelta(hours=7))])['technical_ready']


def test_pinned_tls_transport_keeps_original_host_sni_and_ignores_proxy_environment(monkeypatch):
    monkeypatch.setenv('HTTPS_PROXY','http://127.0.0.1:9999')
    captured={}
    class Response:
        status=200;headers={}
        def close(self):captured['response_closed']=True
        def stream(self,*a,**kw):return iter([b'ok'])
    class Pool:
        def __init__(self,address,**kwargs):captured.update(address=address,options=kwargs)
        def urlopen(self,method,path,**kwargs):captured.update(method=method,path=path,request=kwargs);return Response()
        def close(self):captured['pool_closed']=True
    monkeypatch.setattr(network.urllib3,'HTTPSConnectionPool',Pool)
    with network.pinned_request('https://publisher.example/news?x=1','93.184.216.34',{'Host':'evil.example'}) as response:
        assert list(response.iter_content(10))==[b'ok']
    assert captured['address']=='93.184.216.34'
    assert captured['options']['assert_hostname']=='publisher.example'
    assert captured['options']['server_hostname']=='publisher.example'
    assert captured['options']['cert_reqs']=='CERT_REQUIRED'
    assert captured['request']['headers']['Host']=='publisher.example'
    assert captured['path']=='/news?x=1'
    assert captured['request']['redirect'] is False


def test_dns_rebinding_cannot_change_socket_address_after_public_validation(monkeypatch):
    resolved=[];sockets=[]
    def dns(host,port):
        resolved.append(host)
        return [(2,1,6,'',('93.184.216.34' if len(resolved)==1 else '127.0.0.1',0))]
    monkeypatch.setattr(network.socket,'getaddrinfo',dns)
    monkeypatch.setattr(network.time,'sleep',lambda _:None)
    class Response:
        status_code=200;headers={};is_redirect=False
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def iter_content(self,n):return iter([b'body'])
    monkeypatch.setattr(network,'pinned_request',lambda url,address,**kw:(sockets.append(address) or Response()))
    network.get('https://publisher.example/')
    assert sockets==['93.184.216.34'] and len(resolved)==1


def test_article_timeout_preserves_earlier_usable_sample():
    from urllib3.exceptions import ReadTimeoutError
    rss=b'<rss version="2.0"><channel><item><title>A</title><link>https://news.example/a</link></item><item><title>B</title><link>https://news.example/b</link></item></channel></rss>'
    def fetch(url,**kwargs):
        if url.endswith('/rss'):return 200,{},rss,url
        if url.endswith('/a'):return 200,{},b'HTML',url
        raise ReadTimeoutError(None,url,'timed out')
    result=policy.scan_feed({'url':'https://news.example/rss'},None,fetch=fetch,extract=lambda *a:'Text '*100)
    assert result['samples'][0]['extraction']=='usable'
    assert result['samples'][1]['error']=='ReadTimeoutError'


def test_partial_sampling_saves_cursor_when_budget_exhausts_after_first_article():
    rss=b'<rss version="2.0"><channel><item><title>A</title><link>https://news.example/a</link></item><item><title>B</title><link>https://news.example/b</link></item></channel></rss>'
    def fetch(url,**kwargs):
        if url.endswith('/rss'):return 200,{},rss,url
        if url.endswith('/a'):return 200,{},b'HTML',url
        raise store.BudgetExhausted('discovery_run_budget_exhausted')
    result=policy.scan_feed({'url':'https://news.example/rss'},None,fetch=fetch,extract=lambda *a:'Text '*100)
    assert len(result['samples'])==1 and result['samples'][0]['extraction']=='usable'
    assert result['budget_paused'] and result['next_sample_cursor']==1
    assert result['sample_batch_complete'] is False


def test_tick_deadline_stops_pre_io_failures_without_claiming_again(monkeypatch):
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','1')
    times=iter([0,200]);monkeypatch.setattr(discovery.time,'monotonic',lambda:next(times))
    claimed=[]
    monkeypatch.setattr(discovery,'claim',lambda db:(claimed.append(1) or {'id':1,'kind':'site'}))
    monkeypatch.setattr(discovery,'fail_task',lambda *a,**kw:None)
    class Budget:remaining=15;deadline=180
    def blocked(*a):raise ValueError('robots_disallowed')
    result=discovery.tick(DB([{'locked':True}]),budget=Budget(),site_scan=blocked)
    assert result['processed']==1 and result['status']=='budget_paused' and len(claimed)==1


def test_versioned_switches_enable_without_repository_variables_and_env_can_pause(monkeypatch,tmp_path):
    from collector import discovery_settings
    config=tmp_path/'discovery.json'
    config.write_text('{"schema_version":1,"discovery_enabled":true,"dynamic_inventory_enabled":true}')
    monkeypatch.setattr(discovery_settings,'CONFIG',config)
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','')
    monkeypatch.delenv('BORIS_DYNAMIC_INVENTORY')
    assert discovery_settings.enabled('BORIS_DISCOVERY_ENABLED')
    assert discovery_settings.enabled('BORIS_DYNAMIC_INVENTORY')
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','0')
    assert not discovery_settings.enabled('BORIS_DISCOVERY_ENABLED')
