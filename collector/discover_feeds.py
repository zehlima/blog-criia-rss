"""Discover explicitly advertised public RSS endpoints for sources under repair."""
import json
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from lxml import html
from .network import get,canonical
from .inventory import feeds
from .revalidate import check

ROOT=Path('research/rss-review-2026-09-14')

def discover(f):
    result={'name':f['name'],'country':f['country'],'original':f['rss_url'],'candidates':[]}
    try:
        _,_,body,base=get(f['site_url'],check_robots=True)
        tree=html.fromstring(body)
        links=tree.xpath('//link[contains(@type,"rss") or contains(@type,"atom")]/@href')
        links+=tree.xpath('//a[contains(translate(@href,"RSSATOM","rssatom"),"rss")]/@href')
        urls=[]
        for link in links:
            try:u=canonical(link,base)
            except ValueError:continue
            # Comment feeds are not editorial article sources.
            if '/comments/' in u or 'feed=comments' in u:continue
            if u not in urls and u!=f['rss_url']:urls.append(u)
        for url in urls[:5]:result['candidates'].append({'url':url,**check(url)})
    except Exception as e:result['error']=type(e).__name__+': '+str(e)[:160]
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    failed={r['url'] for r in json.loads((ROOT/'failures-after-675-validation.json').read_text())}
    with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(discover,[f for f in feeds() if f['rss_url'] in failed]))
    Path('reports').mkdir(exist_ok=True)
    Path('reports/feed-discovery.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
