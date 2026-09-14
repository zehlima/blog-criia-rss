import calendar
import hashlib
import json
from datetime import datetime,timezone
import feedparser
import trafilatura
from .network import canonical,get
from .parsing import serialized_parser

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def iso_date(value):
    return datetime.fromtimestamp(calendar.timegm(value),timezone.utc) if value else None

def entry_url(entry,base):
    """Prefer the article alternate link over enclosures/media chosen by some parsers."""
    for link in entry.get('links',[]):
        if link.get('rel')=='alternate' and (link.get('type') or 'text/html').split(';',1)[0].strip()=='text/html':
            return canonical(link['href'],base)
    candidate=entry.get('id') or entry.get('link')
    if not candidate:raise ValueError('entry_without_article_link')
    return canonical(candidate,base)

def entries(body, base):
    parsed=feedparser.parse(body)
    if not parsed.get('version'):
        raise ValueError('invalid_or_malformed_feed')
    if parsed.get('bozo'):
        # XML/encoding warnings do not invalidate otherwise readable syndication.
        # Verify the recovered root, disable entities/network, retain a visible warning.
        from lxml import etree
        import warnings
        try:
            root=etree.fromstring(body,parser=etree.XMLParser(recover=True,resolve_entities=False,no_network=True))
            if root is None or etree.QName(root).localname.lower() not in ('rss','rdf','feed'):
                raise ValueError('invalid_or_malformed_feed')
        except (etree.LxmlError,TypeError):
            raise ValueError('invalid_or_malformed_feed')
        warnings.warn('RSS recovered: '+type(parsed.get('bozo_exception')).__name__,RuntimeWarning)
    result=[]
    for e in parsed.entries:
        if not e.get('title'):
            continue
        try:url=entry_url(e,base)
        except (ValueError,KeyError):continue
        a={'url':url,'title':e.title,
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
    if not result:raise ValueError('invalid_empty_feed_or_entries')
    return result

def fetch_source(feed):
    headers={}
    if feed.get('etag'):headers['If-None-Match']=feed['etag']
    if feed.get('last_modified'):headers['If-Modified-Since']=feed['last_modified']
    # Long publisher RSS feeds may exceed the page-body budget. Keep a bounded 32 MiB ceiling.
    try:
        status,h,body,url=get(feed['rss_url'],headers,max_bytes=32*1024*1024)
        if status==304 and not headers:raise ValueError('invalid_304_without_validators')
        return status,h,[] if status==304 else entries(body,url)
    except (ValueError, OSError) as original:
        # Respect rate limits; the existing hourly checkpoint recovery retries later.
        if str(original)=='http_429':raise
        from .publisher_listing import ALTERNATIVES, LISTINGS, alternative_feed, public_listing
        if feed['rss_url'] not in ALTERNATIVES and feed['rss_url'] not in LISTINGS:
            raise
        errors=[]
        if feed['rss_url'] in ALTERNATIVES:
            try:
                return alternative_feed(feed, entries)
            except Exception as exc:
                errors.append(str(exc) if str(exc).startswith(('http_','invalid_')) else type(exc).__name__)
        if feed['rss_url'] in LISTINGS:
            try:
                return public_listing(feed)
            except Exception as exc:
                errors.append(str(exc) if str(exc).startswith(('http_','robots_','invalid_')) else type(exc).__name__)
        raise ValueError('invalid_alternative_feeds:' + ','.join(errors)) from original

def fetch_article(a):
    headers={}
    if a.get('content_key'):
        if a.get('page_etag'):headers['If-None-Match']=a['page_etag']
        if a.get('page_last_modified'):headers['If-Modified-Since']=a['page_last_modified']
    status,h,body,url=get(a['url'],headers,check_robots=True)
    if status==304:
        if not a.get('content_key'):raise ValueError('304_without_content')
        return status,h,None,url
    text=page_text(body,url)
    return status,h,text,url


@serialized_parser
def page_text(body,url):
    options={'url':url,'include_comments':False,'include_tables':True}
    text=trafilatura.extract(body,**options,favor_precision=True)
    # Some valid publisher layouts are too sparse for precision mode. Recall mode
    # is still a structured article extractor (not raw page text), and is accepted
    # only when it returns a substantial body.
    if not text or len(text.strip())<200:
        recalled=trafilatura.extract(body,**options,favor_recall=True)
        if recalled and len(recalled.strip())>=400:text=recalled
    if not text or len(text.strip())<200:raise ValueError('insufficient_text')
    # 'extracted' significa extração automática, não garantia de integralidade editorial.
    return text.strip()
