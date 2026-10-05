from datetime import datetime, timedelta, timezone
from dashboard.full_export import ARTICLES_SQL,SOURCES_SQL,article_sort_key,load_articles,normalize_ranks,public,body

class _Rows:
    def __init__(self, rows):
        self._rows=rows
    def fetchall(self):
        return self._rows

class _FakeDb:
    def __init__(self, pages, sources):
        self.pages=pages
        self.sources=sources
        self.calls=[]
    def execute(self, sql, params=None):
        self.calls.append((sql,params))
        if sql==ARTICLES_SQL:
            after,limit=params
            return _Rows([row for row in self.pages if row['id']>after][:limit])
        if sql==SOURCES_SQL:
            ids=set(params[0])
            return _Rows([row for row in self.sources if row['article_id'] in ids])
        raise AssertionError(sql)

def test_normalization_preserves_all_evidence_not_only_first_five():
    rows={'Globo':{'publications':20,'ranking':[{'label':'A','evidence':[{'id':i} for i in range(20)]}], 'subject_ranking':[]}}
    result=normalize_ranks(rows)
    assert result['Globo']['ranking'][0]['article_ids']==list(range(20))
    assert result['Globo']['publications']==20

def test_export_never_contains_private_object_keys():
    assert public({'content_key':'private','nested':[{'report_key':'private','id':1}]})=={'nested':[{'id':1}]}

def test_unavailable_body_preserves_summary_and_does_not_claim_full_text():
    value=body(None,{'id':1,'summary':'RSS summary'})
    assert value['text'] is None
    assert value['summary']=='RSS summary'
    assert value['text_basis']=='title_summary'

def test_article_queries_stay_paginated_and_avoid_full_table_join():
    assert 'LEFT JOIN news_article_feeds' not in ARTICLES_SQL
    assert 'GROUP BY' not in ARTICLES_SQL
    assert 'ANY(%s)' in SOURCES_SQL

def test_load_articles_pages_and_preserves_sort_and_orphan_sources():
    now=datetime(2026,10,5,tzinfo=timezone.utc)
    pages=[
        {'id':1,'title':'old','url':'https://a.test/1','summary':'','published_at':now-timedelta(days=2),'first_seen_at':now,'content_status':'ok','content_key':None},
        {'id':2,'title':'future','url':'https://a.test/2','summary':'','published_at':now+timedelta(days=1),'first_seen_at':now,'content_status':'ok','content_key':None},
        {'id':3,'title':'recent','url':'https://a.test/3','summary':'','published_at':now-timedelta(hours=1),'first_seen_at':now,'content_status':'ok','content_key':None},
    ]
    sources=[{'article_id':1,'sources':[{'id':9,'name':'Fonte','country':'BR','region':'Americas','rss_url':'https://a.test/rss','site_url':'https://a.test'}]}]
    db=_FakeDb(pages,sources)
    articles=load_articles(db,page_size=2,now=now)
    assert [a['id'] for a in articles]==[3,1,2]
    assert articles[1]['sources'][0]['name']=='Fonte'
    assert articles[0]['sources']==[]
    article_calls=[params for sql,params in db.calls if sql==ARTICLES_SQL]
    assert article_calls==[(0,2),(2,2)]

def test_future_dates_sort_after_published_past():
    now=datetime(2026,10,5,tzinfo=timezone.utc)
    past={'id':1,'published_at':now-timedelta(days=1),'first_seen_at':now}
    future={'id':2,'published_at':now+timedelta(hours=2),'first_seen_at':now}
    assert article_sort_key(past,now)<article_sort_key(future,now)
