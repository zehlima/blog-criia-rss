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
