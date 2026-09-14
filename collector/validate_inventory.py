"""Validate active feeds and diagnose parser failures without changing the database."""
import json,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .inventory import feeds
from .network import get
from .extract import entries
import feedparser

def check(f):
    r={'name':f['name'],'country':f['country'],'url':f['rss_url']}
    try:
        status,h,body,url=get(f['rss_url'],max_bytes=32*1024*1024)
        parsed=feedparser.parse(body)
        r.update(http=status,version=parsed.get('version'),parsed_items=len(parsed.entries),
                 parser_warning=type(parsed.get('bozo_exception')).__name__ if parsed.get('bozo') else None)
        try:
            items=entries(body,url);r.update(ok=bool(items),items=len(items))
        except Exception as e:r.update(ok=False,error=str(e))
    except Exception as e:r.update(ok=False,error=str(e)[:160])
    print(json.dumps(r,ensure_ascii=False),flush=True)
    return r

def main():
    with ThreadPoolExecutor(max_workers=12) as pool:rows=list(pool.map(check,feeds()))
    Path('reports').mkdir(exist_ok=True)
    Path('reports/active-feed-validation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print(json.dumps({'total':len(rows),'ok':sum(r['ok'] for r in rows),'failed':sum(not r['ok'] for r in rows)}))
if __name__=='__main__':main()
