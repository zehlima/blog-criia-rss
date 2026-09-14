"""Publisher-documented feed alternatives; retain one source identity in storage."""
from .network import get

# Official syndication pages are recorded in the research report.
ALTERNATIVES = {
    'https://36kr.com/feed': ['https://www.36kr.com/feed'],
    'https://gizmodo.com/feed': ['https://gizmodo.com/tech/feed', 'https://gizmodo.com/rss'],
}

def alternative_feed(feed, parse):
    errors=[]
    for endpoint in ALTERNATIVES.get(feed['rss_url'], []):
        try:
            status, headers, body, final = get(endpoint, max_bytes=32*1024*1024)
            items=parse(body,final)
            # Validators from an alternative URL must never be sent to the primary URL.
            return status, {'X-Collection-Method':'official_alternative_rss',
                            'X-Collection-URL':final}, items
        except Exception as exc:
            errors.append(str(exc) if str(exc).startswith(('http_','invalid_')) else type(exc).__name__)
    raise ValueError('invalid_alternative_feeds:' + ','.join(errors))

LISTINGS = {
    'https://gizmodo.com/feed': ('https://gizmodo.com/', r'^/[^/]+-\d{5,}/?$'),
    'https://venturebeat.com/feed': ('https://venturebeat.com/', r'^/(?:ai|technology|security|data|infrastructure|business|programming-development)/[^/]+/?$'),
}

def listing_entries(body, base, pattern):
    import re
    from urllib.parse import urlsplit
    from lxml import html
    from xml.etree.ElementTree import Element, SubElement, tostring
    from .network import canonical
    from .extract import entries
    page=html.fromstring(body)
    candidates=page.xpath('//h2//a[@href] | //h3//a[@href] | //a[@href][.//h2 or .//h3]')
    channel=SubElement(Element('rss',version='2.0'),'channel')
    seen=set()
    for node in candidates:
        title=' '.join(node.text_content().split())
        try:url=canonical(node.get('href'),base)
        except ValueError:continue
        if len(title)<15 or urlsplit(url).hostname!=urlsplit(base).hostname or not re.match(pattern,urlsplit(url).path) or url in seen:
            continue
        seen.add(url); item=SubElement(channel,'item')
        SubElement(item,'title').text=title;SubElement(item,'link').text=url
    if len(seen)<2:raise ValueError('invalid_empty_publisher_listing')
    # Use the canonical parser contract. Headlines are not represented as full text.
    root=Element('rss',version='2.0');root.append(channel)
    return entries(tostring(root,encoding='utf-8'),base)

def public_listing(feed):
    endpoint,pattern=LISTINGS[feed['rss_url']]
    status,headers,body,final=get(endpoint,check_robots=True)
    items=listing_entries(body,final,pattern)
    return status,{'X-Collection-Method':'publisher_html_listing','X-Collection-URL':final},items
