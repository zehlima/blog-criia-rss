"""Inventory rollout, recovery and daily coverage tests; no remote services."""
from copy import deepcopy
from contextlib import nullcontext
from datetime import datetime,timedelta,timezone
from pathlib import Path

import pytest
from pglast import parse_sql

from collector import inventory


SLOT=datetime(2026,9,17,3,tzinfo=timezone.utc)


def feed(name):
    return {'rss_url':f'https://{name}.example/rss','site_url':f'https://{name}.example',
            'name':name,'country':'Brasil','region':'América do Sul','justification':'Reviewed source'}


class Rows:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return deepcopy(self.rows[0]) if self.rows else None
    def fetchall(self):return deepcopy(self.rows)


class InventoryDB:
    """Stateful capture/attempt fixture; SQL itself is also parsed below."""
    def __init__(self):
        self.snapshots={};self.attempts={};self.additions=[];self.queries=[]
        self.concurrent_snapshot=None
        self.schema_exists=True

    def execute(self,sql,params=None):
        self.queries.append((sql,params))
        if sql.startswith('SELECT to_regclass'):
            return Rows([{'present':self.schema_exists}])
        if sql.startswith('INSERT INTO news_collection_inventory'):
            slot,payload=params
            self.snapshots.setdefault(slot,deepcopy(self.concurrent_snapshot or payload.obj))
            return Rows([])
        if 'FROM news_collection_inventory' in sql:
            value=self.snapshots.get(params[0])
            return Rows([{'feeds':value}] if value is not None else [])
        if 'FROM news_collection_attempts' in sql:
            value=self.attempts.get(params[0])
            return Rows([{'feeds':value}] if value is not None else [])
        if 'FROM news_feed_admissions' in sql:
            slot=params[0]
            return Rows([a['feed'] for a in self.additions if a['effective_at']<=slot
                         and a['admitted_at']<=slot
                         and (a.get('revoked_at') is None or a['revoked_at']>slot)])
        raise AssertionError('Unexpected test query')


@pytest.fixture
def base(monkeypatch):
    base=[feed('curated')]
    monkeypatch.setattr(inventory,'feeds',lambda:deepcopy(base))
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','1')
    return base


def admission(name,effective=SLOT,admitted=None,revoked=None):
    return {'feed':feed(name),'effective_at':effective,
            'admitted_at':admitted or effective-timedelta(hours=1),'revoked_at':revoked}


def test_gate_off_preserves_pre_migration_collector_with_only_schema_lookup(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    db=InventoryDB();db.schema_exists=False
    assert inventory.for_slot(db,SLOT,freeze=True)==base
    assert len(db.queries)==1
    assert db.queries[0][0].startswith('SELECT to_regclass')


def test_gate_disabled_during_recovery_preserves_existing_snapshot(base,monkeypatch):
    db=InventoryDB();db.additions=[admission('already_admitted')]
    expected=inventory.for_slot(db,SLOT,freeze=True)
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    db.queries=[];db.additions.append(admission('later'))
    assert inventory.for_slot(db,SLOT,freeze=True,base_feeds=[feed('changed_manifest')])==expected
    assert not any('FROM news_feed_admissions' in sql or sql.startswith('INSERT') for sql,_ in db.queries)


def test_gate_off_never_adds_admissions_or_captures_new_windows(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    db=InventoryDB();db.additions=[admission('eligible_but_disabled')]
    assert inventory.for_slot(db,SLOT,freeze=True)==base
    assert db.snapshots=={}
    assert not any('FROM news_feed_admissions' in sql or sql.startswith('INSERT') for sql,_ in db.queries)


def test_gate_off_does_not_treat_database_error_as_missing_schema(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    class BrokenDB:
        def execute(self,*args):raise RuntimeError('database_unavailable')
    with pytest.raises(RuntimeError,match='database_unavailable'):
        inventory.for_slot(BrokenDB(),SLOT,freeze=True)


def test_invalid_rollout_flag_is_explicit(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','treu')
    with pytest.raises(ValueError,match='invalid_dynamic_inventory_gate'):
        inventory.for_slot(InventoryDB(),SLOT)


def test_gate_on_does_not_hide_schema_or_database_failure(base):
    class BrokenDB:
        def execute(self,*args):raise RuntimeError('schema_not_applied')
    with pytest.raises(RuntimeError,match='schema_not_applied'):
        inventory.for_slot(BrokenDB(),SLOT,freeze=True)


def test_curated_and_approved_sources_enter_together_only_when_effective(base):
    db=InventoryDB()
    db.additions=[admission('new'),admission('tomorrow',SLOT+timedelta(hours=6))]
    result=inventory.for_slot(db,SLOT,freeze=True)
    assert [f['name'] for f in result]==['curated','new']
    assert db.snapshots[SLOT]==result


def test_recovery_uses_frozen_inventory_despite_new_admission_and_manifest_change(base):
    db=InventoryDB()
    first=inventory.for_slot(db,SLOT,freeze=True)
    db.additions=[admission('later')]
    recovered=inventory.for_slot(db,SLOT,freeze=True,base_feeds=[feed('changed_manifest')])
    assert recovered==first
    following=inventory.for_slot(db,SLOT+timedelta(hours=6),freeze=True)
    assert [f['name'] for f in following]==['curated','later']


def test_discovery_does_not_replace_curated_source_metadata(base):
    db=InventoryDB();discovered=admission('curated')
    discovered['feed']['country']='Wrong country'
    db.additions=[discovered]
    assert inventory.for_slot(db,SLOT,freeze=True)==base


def test_revocation_does_not_change_current_snapshot_but_applies_next_window(base):
    db=InventoryDB();db.additions=[admission('new')]
    first=inventory.for_slot(db,SLOT,freeze=True)
    db.additions[0]['revoked_at']=SLOT+timedelta(hours=1)
    assert inventory.for_slot(db,SLOT,freeze=True)==first
    assert inventory.for_slot(db,SLOT+timedelta(hours=6),freeze=True)==base


def test_legacy_partial_attempt_is_preserved_at_rollout_boundary(base):
    db=InventoryDB();db.attempts[SLOT]=[feed('old_manifest')]
    db.additions=[admission('new')]
    assert inventory.for_slot(db,SLOT,freeze=True)==db.attempts[SLOT]
    assert db.snapshots[SLOT]==db.attempts[SLOT]
    assert not any('FROM news_feed_admissions' in q for q,_ in db.queries)


def test_concurrent_capture_wins_without_being_overwritten(base):
    db=InventoryDB();db.concurrent_snapshot=[feed('winner')]
    assert inventory.for_slot(db,SLOT,freeze=True)==[feed('winner')]
    assert all('DO UPDATE' not in sql for sql,_ in db.queries)


def test_preflight_is_read_only_and_does_not_capture_a_window(base):
    db=InventoryDB();db.additions=[admission('new')]
    assert inventory.urls(db,SLOT)==[feed('curated')['rss_url'],feed('new')['rss_url']]
    assert db.snapshots=={}
    assert all(not sql.startswith('INSERT') for sql,_ in db.queries)


def test_frozen_attempt_remains_authoritative_for_downstream_when_gate_off(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    rows=base+[feed('new')]
    assert inventory.attempt_feeds({'feeds':rows})==rows


def test_empty_or_duplicated_snapshot_is_never_silently_accepted(base):
    db=InventoryDB()
    for invalid in ([],[feed('duplicate'),feed('duplicate')],None):
        if invalid is None:
            with pytest.raises(ValueError,match='invalid_inventory'):
                inventory.attempt_feeds({'feeds':invalid})
        else:
            db.snapshots[SLOT]=invalid
            with pytest.raises(ValueError,match='invalid_inventory'):
                inventory.for_slot(db,SLOT,freeze=True)


def test_day_coverage_sums_changing_window_sizes_and_never_writes_history(base):
    db=InventoryDB()
    db.snapshots={SLOT:base,SLOT+timedelta(hours=6):base+[feed('new')],
                  SLOT+timedelta(hours=12):base+[feed('new')],
                  SLOT+timedelta(hours=18):base+[feed('new'),feed('newer')]}
    closing=base+[feed('new'),feed('newer'),feed('next_day')]
    result=inventory.day_inventory(db,SLOT,SLOT+timedelta(days=1),SLOT+timedelta(hours=25),closing)
    assert result['expected_batches']==8  # 1 + 2 + 2 + 3; not 4 x 4.
    assert result['complete'] is True
    assert len(result['feeds'])==4
    assert all(not sql.startswith('INSERT') for sql,_ in db.queries)


def test_day_coverage_marks_missing_window_not_reconstructed(base):
    db=InventoryDB();db.attempts[SLOT]=base+[feed('legacy_admitted')]
    result=inventory.day_inventory(db,SLOT,SLOT+timedelta(days=1),SLOT+timedelta(hours=25),base)
    assert result['expected_batches']==5
    assert result['complete'] is False
    assert result['slots'][0]['basis']=='legacy_attempt'
    assert result['slots'][1]['basis']=='missing_legacy_baseline'
    assert len(result['feeds'])==2


def test_day_coverage_preserves_snapshots_after_rollout_gate_disabled(base,monkeypatch):
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
    db=InventoryDB()
    db.snapshots={SLOT:base,SLOT+timedelta(hours=6):base+[feed('new')],
                  SLOT+timedelta(hours=12):base+[feed('new')],
                  SLOT+timedelta(hours=18):base+[feed('new')]}
    result=inventory.day_inventory(db,SLOT,SLOT+timedelta(days=1),SLOT+timedelta(hours=25),base)
    assert result['expected_batches']==7
    assert result['complete'] is True
    assert len(result['feeds'])==2
    assert not any('FROM news_feed_admissions' in sql or sql.startswith('INSERT') for sql,_ in db.queries)


def test_inventory_queries_and_additive_schema_parse_as_postgres(base):
    import ast,inspect
    tree=ast.parse(inspect.getsource(inventory))
    sqls=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
          and isinstance(node.func,ast.Attribute) and node.func.attr=='execute'
          and isinstance(node.args[0],ast.Constant)]
    assert len(sqls)==6
    for sql in sqls:parse_sql(sql.replace('%s','NULL'))
    schema=Path('sql/003_dynamic_inventory.sql').read_text()
    parse_sql(schema)
    assert 'ENABLE ROW LEVEL SECURITY' in schema
    assert 'FROM PUBLIC,anon,authenticated' in schema
    assert 'UPDATE news_daily_closures' not in schema


def test_dashboard_exports_sources_from_completed_attempt(base,monkeypatch,tmp_path):
    from dashboard import export
    rows=base+[feed('discovered')]
    attempt={'id':'completed','feeds':rows,'report':{'status':'complete','expected_feeds':2}}
    queried=[]
    class DB:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def transaction(self):return nullcontext()
        def execute(self,sql,params=None):
            if sql==export.COLLECTION_SQL:return Rows([attempt])
            if "to_regclass('public.news_discovery_tasks')" in sql:return Rows([{'ready':False}])
            if sql==export.ARTICLES_SQL:queried.append(params)
            return Rows([])
    monkeypatch.setattr('collector.storage.database_connection',lambda:DB())
    monkeypatch.chdir(tmp_path);(tmp_path/'frontend').mkdir()
    export.main()
    urls=[f['rss_url'] for f in rows]
    assert queried==[(urls,urls)]
    assert (tmp_path/'frontend/data/dashboard.json').exists()


def test_trends_prepare_uses_completed_attempt_inventory(base,monkeypatch,tmp_path):
    np=pytest.importorskip('numpy')
    pytest.importorskip('sklearn');pytest.importorskip('datasketch')
    from trends import main
    rows=[{**f,'status':'ok'} for f in base+[feed('discovered')]]
    attempt={'id':'completed','slot':SLOT,'finished_at':SLOT+timedelta(hours=1),
             'feeds':rows,'report':{'status':'complete'}}
    queried=[]
    class DB:
        def execute(self,sql,params=None):
            if sql.startswith('SELECT * FROM news_collection_attempts'):return Rows([attempt])
            return Rows([])
    def corpus(db,cutoff,urls):queried.append(urls);return []
    monkeypatch.setattr(main,'all_articles',corpus)
    monkeypatch.setattr(main,'vectors',lambda *args:(np.empty((0,384)),'test'))
    monkeypatch.setattr(main,'assign_topics',lambda *args:None)
    monkeypatch.setattr(main,'families',lambda *args:[])
    monkeypatch.setattr(main,'put_json',lambda s3,key,value:key)
    monkeypatch.delenv('COLLECTION_FINISHED_AT',raising=False)
    monkeypatch.chdir(tmp_path)
    assert main.prepare(DB(),None,'analysis-test') is True
    assert queried==[[f['rss_url'] for f in rows]]


def test_existing_daily_closure_returns_before_inventory_or_recomputation(base,monkeypatch):
    pytest.importorskip('numpy');pytest.importorskip('sklearn');pytest.importorskip('datasketch')
    from daily import main
    attempt={'id':'completed','slot':SLOT,'finished_at':SLOT+timedelta(hours=1),
             'feeds':base,'report':{'status':'complete'}}
    class DB:
        def execute(self,sql,params=None):
            if sql.startswith('SELECT * FROM news_collection_attempts'):return Rows([attempt])
            if sql.startswith('SELECT id FROM news_daily_closures'):return Rows([{'id':'closed'}])
            raise AssertionError('Closed days must not query or mutate inventory')
    def forbidden(*args):raise AssertionError('Closed days must not be recomputed')
    monkeypatch.setattr(main,'day_inventory',forbidden)
    monkeypatch.setattr(main,'corpus',forbidden)
    main.run(DB(),None,'auto')
