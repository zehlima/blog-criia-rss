"""Audit the 15 technology sources with the same parser and HTTP client as production."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from .extract import fetch_source

ROOT = Path(__file__).resolve().parent.parent

def manifest():
    return json.loads((ROOT/'data/technology15.json').read_text())

def check(feed):
    result = {'name': feed['name'], 'rss_url': feed['rss_url'],
              'source_type': feed['source_type'], 'checked_at': datetime.now(timezone.utc).isoformat()}
    try:
        try:
            status, headers, items = fetch_source(feed)
        except ValueError as exc:
            if str(exc) != 'http_429':
                raise
            time.sleep(30)
            status, headers, items = fetch_source(feed)
        result.update(status='ok', http_status=status, items=len(items),
                      method=headers.get('X-Collection-Method','rss_atom'),
                      collected_url=headers.get('X-Collection-URL',feed['rss_url']),
                      latest_title=items[0]['title'] if items else None,
                      latest_url=items[0]['url'] if items else None)
    except Exception as exc:
        error = str(exc)
        result.update(status='error', items=0,
                      error=error if error.startswith(('http_','robots_','invalid_','body_')) else type(exc).__name__)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    with ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(check,manifest()))
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'total':len(results),
            'ok':sum(r['status']=='ok' for r in results),'sources':results}
    target=ROOT/'reports/technology15';target.mkdir(parents=True,exist_ok=True)
    (target/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('TECHNOLOGY15_SUMMARY '+json.dumps({k:v for k,v in report.items() if k!='sources'}),flush=True)
    # Coverage failures remain visible and cause an unsuccessful audit.
    return 0 if report['ok']==report['total']==15 else 1

if __name__=='__main__':
    raise SystemExit(main())
