"""Real PostgreSQL execution via optional PGlite, never a production DSN."""
import json,os,re,subprocess,uuid
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from collector import discovery_store as store,inventory
pytestmark=pytest.mark.skipif(not os.getenv('BORIS_PGLITE_MODULE'),reason='Local PostgreSQL verifier requires BORIS_PGLITE_MODULE')

class Rows:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return self.rows[0] if self.rows else None
    def fetchall(self):return self.rows
def decoded(value):
    if isinstance(value,list):return [decoded(v) for v in value]
    if isinstance(value,dict):return {k:decoded(v) for k,v in value.items()}
    if isinstance(value,str) and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z',value):
        return datetime.fromisoformat(value.replace('Z','+00:00'))
    return value
class Postgres:
    def __init__(self):
        self.p=subprocess.Popen(['node','tests/discovery_pg_bridge.mjs'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=os.environ)
    def call(self,request):
        self.p.stdin.write(json.dumps(request)+'\n');self.p.stdin.flush()
        line=self.p.stdout.readline()
        if not line:raise RuntimeError(self.p.stderr.read())
        result=json.loads(line)
        if not result['ok']:raise RuntimeError(result['error'])
        return Rows(decoded(result['rows']))
    def execute(self,sql,params=None):
        n=iter(range(1,100));sql=re.sub(r'%s',lambda _:'$'+str(next(n)),sql).replace('%%','%')
        cooked=[]
        for value in params or []:
            if hasattr(value,'obj'):value=json.dumps(value.obj)
            elif isinstance(value,datetime):value=value.isoformat()
            elif isinstance(value,timedelta):value=str(value.total_seconds())+' seconds'
            elif isinstance(value,uuid.UUID):value=str(value)
            cooked.append(value)
        return self.call({'sql':sql,'params':cooked})
    def exec(self,sql):return self.call({'sql':sql,'exec':True})
    @contextmanager
    def transaction(self):
        self.execute('BEGIN')
        try:yield
        except Exception:self.execute('ROLLBACK');raise
        else:self.execute('COMMIT')
    def close(self):
        self.p.stdin.write('{"close":true}\n');self.p.stdin.flush();self.p.wait(timeout=15)
@pytest.fixture
def db():
    db=Postgres();db.exec('CREATE ROLE anon; CREATE ROLE authenticated;')
    for name in ('001_schema.sql','002_continuous_discovery.sql','003_dynamic_inventory.sql'):
        db.exec((Path('sql')/name).read_text())
    try:yield db
    finally:db.close()

def test_real_queue_reclaims_lease_and_rejects_old_completion(db):
    store.enqueue(db,'site','https://publisher.example/')
    first=store.claim(db)
    assert first['status']=='leased' and store.claim(db) is None
    db.execute("UPDATE news_discovery_tasks SET lease_until=now()-interval '1 second' WHERE id=%s",(first['id'],))
    second=store.claim(db)
    assert second['lease_token']!=first['lease_token'] and second['attempts']==2
    with pytest.raises(ValueError,match='lease_lost'):
        store.finish_site(db,first,{'feeds':[],'sites':[],'final_url':first['url']})
    store.finish_site(db,second,{'feeds':['https://publisher.example/rss'],'sites':['https://another.example/'],
        'final_url':second['url'],'next_link_cursor':200,'truncated_links':True})
    assert db.execute('SELECT count(*) n FROM news_discovery_tasks').fetchone()['n']==3
    assert db.execute('SELECT link_cursor FROM news_discovery_tasks WHERE id=%s',(first['id'],)).fetchone()['link_cursor']==200

def test_real_budget_enforces_shared_daily_request_and_byte_ceilings(db):
    budget=store.Budget(db,requests=30)
    db.execute("INSERT INTO news_discovery_budget(day,requests_reserved,bytes_reserved) VALUES((now() AT TIME ZONE 'UTC')::date,119,0)")
    budget.reserve(1000)
    with pytest.raises(store.BudgetExhausted):budget.reserve(1000)
    assert db.execute('SELECT requests_reserved n FROM news_discovery_budget').fetchone()['n']==120
    db.execute('UPDATE news_discovery_budget SET requests_reserved=0,bytes_reserved=134217720')
    with pytest.raises(store.BudgetExhausted):store.Budget(db).reserve(1000)
    assert db.execute('SELECT bytes_reserved n FROM news_discovery_budget').fetchone()['n']==134217720

def test_real_observation_review_admission_and_next_window_inventory(db,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','1')
    base=[{'rss_url':'https://curated.example/rss','site_url':'https://curated.example/','name':'Curated',
        'country':'Brasil','region':'América do Sul','justification':'Curated source'}]
    monkeypatch.setattr(inventory,'feeds',lambda:base)
    store.enqueue(db,'feed','https://publisher.example/rss')
    payload={'http_status':200,'item_count':2,'final_url':'https://publisher.example/rss','samples':[
        {'url':'https://publisher.example/a','extraction':'usable','body_hash':'a'},
        {'url':'https://publisher.example/b','extraction':'usable','body_hash':'b'}]}
    first=store.claim(db);assert store.finish_feed(db,first,payload)=='observing'
    db.execute("UPDATE news_discovery_observations SET observed_at=now()-interval '7 hours'")
    db.execute('UPDATE news_discovery_tasks SET next_attempt_at=now()')
    second=store.claim(db);assert store.finish_feed(db,second,payload)=='awaiting_editorial_review'
    candidate=db.execute('SELECT * FROM news_discovery_candidates').fetchone()
    approved=store.review(db,candidate['id'],'editor@example.com','Verified independent news publisher',
        ['https://publisher.example/about'],accept=True,metadata={'name':'Publisher','country':'Brasil','region':'América do Sul'})
    effective=datetime.fromisoformat(approved['effective_at'])
    assert inventory.for_slot(db,effective-timedelta(hours=6))==base
    included=inventory.for_slot(db,effective,freeze=True)
    assert len(included)==2 and included[1]['name']=='Publisher'
    assert db.execute('SELECT count(*) n FROM news_discovery_audit').fetchone()['n']==1
    with pytest.raises(ValueError,match='already_reviewed'):
        store.review(db,candidate['id'],'editor@example.com','Verified independent news publisher',['https://publisher.example/about'])
    assert len(inventory.for_slot(db,effective,freeze=True))==2

def test_real_rejection_never_activates_source(db):
    store.enqueue(db,'feed','https://nonnews.example/rss')
    task=store.claim(db);store.fail_task(db,task,'invalid_or_malformed_feed')
    candidate=db.execute('SELECT * FROM news_discovery_candidates').fetchone()
    assert store.review(db,candidate['id'],'editor@example.com','Not a news source; advertising only',
        ['https://nonnews.example/about'])['status']=='rejected'
    assert db.execute('SELECT count(*) n FROM news_feeds').fetchone()['n']==0
    assert db.execute('SELECT count(*) n FROM news_feed_admissions').fetchone()['n']==0
    assert db.execute('SELECT count(*) n FROM news_discovery_audit').fetchone()['n']==1

def test_real_dispatch_prioritizes_feeds_without_starving_sites(db):
    for i in range(10):store.enqueue(db,'site',f'https://site{i}.example/')
    for i in range(10):store.enqueue(db,'feed',f'https://feed{i}.example/rss')
    assert [store.claim(db)['kind'] for _ in range(6)]==['feed','feed','site','feed','feed','site']

def test_new_tables_are_not_public_and_use_rls(db):
    for role in ('anon','authenticated'):
        assert not db.execute("SELECT has_table_privilege(%s,'public.news_discovery_candidates','SELECT') allowed",(role,)).fetchone()['allowed']
    names=['news_discovery_tasks','news_discovery_candidates','news_discovery_observations','news_discovery_budget',
        'news_discovery_audit','news_discovery_dispatch','news_feed_admissions','news_collection_inventory']
    rows=db.execute("SELECT relname,relrowsecurity FROM pg_class WHERE relname=ANY(%s::text[])",(names,)).fetchall()
    assert len(rows)==8 and all(r['relrowsecurity'] for r in rows)
