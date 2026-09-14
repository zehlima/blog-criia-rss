import threading
import time
from concurrent.futures import ThreadPoolExecutor


def test_parser_guard_serializes_native_calls_and_releases_after_error():
    from collector.parsing import serialized_parser
    active=0
    peak=0
    @serialized_parser
    def parse(i):
        nonlocal active,peak
        active+=1
        peak=max(peak,active)
        try:
            time.sleep(.002)
            if i==0:raise ValueError('test')
            return i
        finally:active-=1
    def run(i):
        try:return parse(i)
        except ValueError:return 0
    with ThreadPoolExecutor(max_workers=16) as pool:
        assert list(pool.map(run,range(40)))==list(range(40))
    assert peak==1


def test_network_requests_remain_concurrent_outside_parser_guard(monkeypatch):
    from collector import extract
    barrier=threading.Barrier(4)
    def get(url,*args,**kwargs):
        barrier.wait(timeout=3)
        return 200,{},b'<html></html>',url
    monkeypatch.setattr(extract,'get',get)
    monkeypatch.setattr(extract.trafilatura,'extract',lambda *a,**k:'Valid body '*40)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(extract.fetch_article,[{'url':f'https://example.org/{i}'} for i in range(4)]))
    assert len(rows)==4 and all(len(row[2])>=200 for row in rows)
