import calendar
import hashlib
import json
from datetime import datetime,timezone
import feedparser
import trafilatura
from .network import canonical,get

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def iso_date(value):
    return datetime.fromtimestamp(calendar.timegm(value),timezone.utc) if value else None

def entries(body, base):
    parsed=feedparser.parse(body)
    if not parsed.version or parsed.bozo:
        raise ValueError('invalid_or_malformed_feed')
    result=[]
    for e in parsed.entries:
        if not e.get('link') or not e.get('title'):
            raise ValueError('entry_without_title_or_link')
        a={'url':canonical(e.link,base),'title':e.title,
           'summary':e.get('summary',''), 'published_at':iso_date(e.get('published_parsed')),
           'source_updated_at':iso_date(e.get('updated_parsed'))}
        # Resumo em texto. Corpo integral é extraído da página e arquivado no R2.
        from html import unescape
        import re
        raw_summary=a['summary']
        a['summary']=unescape(re.sub(r'<[^>]+>',' ',a['summary'])).strip()[:2000]
        a['metadata_hash']=digest(json.dumps(a,sort_keys=True,default=str,ensure_ascii=False))
        # Preserva conteúdo fornecido pelo próprio RSS, mesmo se a página falhar.
        content=e.get('content') or ([{'type':'feed_summary','value':raw_summary}] if len(raw_summary)>2000 else [])
        a['rss_content']=json.dumps(content,ensure_ascii=False) if content else None
        a['rss_content_key']=None
        result.append(a)
    return result

def fetch_source(feed):
    headers={}
    if feed.get('etag'):headers['If-None-Match']=feed['etag']
    if feed.get('last_modified'):headers['If-Modified-Since']=feed['last_modified']
    status,h,body,url=get(feed['rss_url'],headers)
    if status==304 and not headers:raise ValueError('invalid_304_without_validators')
    return status,h,[] if status==304 else entries(body,url)

def fetch_article(a):
    headers={}
    if a.get('content_key'):
        if a.get('page_etag'):headers['If-None-Match']=a['page_etag']
        if a.get('page_last_modified'):headers['If-Modified-Since']=a['page_last_modified']
    status,h,body,url=get(a['url'],headers,check_robots=True)
    if status==304:
        if not a.get('content_key'):raise ValueError('304_without_content')
        return status,h,None,url
    text=trafilatura.extract(body,url=url,include_comments=False,include_tables=True,
                            favor_precision=True)
    if not text or len(text.strip())<200:raise ValueError('insufficient_text')
    # 'extracted' significa extração automática, não garantia de integralidade editorial.
    return status,h,text.strip(),url
