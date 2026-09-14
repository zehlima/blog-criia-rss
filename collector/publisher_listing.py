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
