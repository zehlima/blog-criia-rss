"""Bounded source exploration and technical evidence, never editorial approval."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit
from lxml import html
from urllib3.exceptions import HTTPError
from .network import canonical, get
from .extract import entries, page_text, digest

POLICY = 'boris-discovery-v1-human-admission'
MAX_DEPTH = 4
MAX_LINKS = 200
OBSERVATION_HOURS = 6


def normalized_url(value, base=None):
    url = canonical(value, base)
    if len(url) > 2048:
        raise ValueError('invalid_url_length')
    u = urlsplit(url)
    host = (u.hostname or '').lower().rstrip('.')
    if u.port not in (None, 80, 443):
        raise ValueError('invalid_url_port')
    authority = '[' + host + ']' if ':' in host else host
    if u.port and not ((u.scheme == 'https' and u.port == 443) or (u.scheme == 'http' and u.port == 80)):
        authority += ':' + str(u.port)
    return urlunsplit((u.scheme.lower(), authority, u.path or '/', u.query, ''))


def site_origin(value):
    u = urlsplit(normalized_url(value))
    return urlunsplit((u.scheme, u.netloc, '/', '', ''))


def discover_links(body, base, depth=0):
    """Use advertised feeds and editorial-page links. No guessed endpoints."""
    tree = html.fromstring(body)
    feeds, sites = set(), set()
    for element in tree.xpath('//link[@href] | //a[@href]'):
        href = element.get('href', '')
        try:
            url = normalized_url(href, base)
        except (ValueError, TypeError):
            continue
        kind = (element.get('type') or '').lower().split(';')[0].strip()
        lowered = url.lower()
        if '/comments/' in lowered or 'feed=comments' in lowered:
            continue
        if kind in ('application/rss+xml', 'application/atom+xml', 'application/feed+json') or (
            element.tag == 'a' and any(token in urlsplit(url).path.lower() for token in ('/rss', '/feed', '/atom'))
        ):
            feeds.add(url)
        elif element.tag == 'a' and depth < MAX_DEPTH and site_origin(url) != site_origin(base):
            # Store the actual referring page. Admission never follows merely
            # from being linked: advertisements and non-news sites stay candidates.
            sites.add(site_origin(url))
    return {'feeds': sorted(feeds), 'sites': sorted(sites), 'policy': POLICY}


def scan_site(task, budget, fetch=get):
    status, headers, body, final_url = fetch(task['url'], max_bytes=2*1024*1024,
        check_robots=True, budget=budget)
    if status != 200 or not body:
        raise ValueError('invalid_site_response')
    result = discover_links(body, final_url, task.get('depth', 0))
    # Bound one operation, preserving an explicit diagnostic when the page
    # contains more candidates. This is a crawler budget, not an editorial cap.
    links = [('feed',url) for url in result['feeds']]+[('site',url) for url in result['sites']]
    cursor = task.get('link_cursor',0)
    cursor = cursor if cursor<len(links) else 0
    batch = links[cursor:cursor+MAX_LINKS]
    result['truncated_links'] = cursor+len(batch)<len(links)
    result['next_link_cursor'] = cursor+len(batch) if result['truncated_links'] else 0
    result['feeds'] = [url for kind,url in batch if kind=='feed']
    result['sites'] = [url for kind,url in batch if kind=='site']
    result['final_url'] = final_url
    return result


def scan_feed(task, budget, fetch=get, extract=page_text):
    status, headers, body, final_url = fetch(task['url'], max_bytes=4*1024*1024,
        check_robots=True, budget=budget)
    if status != 200:
        raise ValueError('invalid_feed_response')
    if body.lstrip().startswith(b'{'):
        # Existing Bóris ingestion accepts RSS/Atom, not JSON Feed. Retain
        # the candidate with this reason instead of admitting an unreadable feed.
        raise ValueError('unsupported_json_feed')
    items = entries(body, final_url)
    samples = []
    cursor = task.get('sample_cursor',0)
    cursor = cursor if cursor<len(items) else 0
    budget_paused = False
    processed = 0
    for item in items[cursor:cursor+3]:
        sample = {'url': item['url'], 'title': item['title'][:300],
            'published_at': item['published_at'].isoformat() if item['published_at'] else None}
        try:
            code, _, raw, article_url = fetch(normalized_url(item['url']), max_bytes=2*1024*1024,
                check_robots=True, budget=budget)
            if code != 200:
                raise ValueError('invalid_article_response')
            text = extract(raw, article_url)
            sample.update(final_url=article_url, body_chars=len(text), body_hash=digest(text),
                excerpt=text[:1200], extraction='usable')
        except (ValueError, OSError, HTTPError) as exc:
            sample.update(extraction='unavailable', error=safe_error(exc))
        except RuntimeError as exc:
            if not str(exc).startswith('discovery_') or 'budget_exhausted' not in str(exc):
                raise
            budget_paused = True
            break
        samples.append(sample)
        processed += 1
    return {'http_status': status, 'format': 'rss_or_atom', 'final_url': normalized_url(final_url),
        'item_count': len(items), 'samples': samples, 'policy': POLICY,
        'ai_evaluated': False, 'editorial_approval': False,'budget_paused':budget_paused,
        'sample_batch_complete':not budget_paused,
        'next_sample_cursor':cursor+processed if cursor+processed<len(items) else 0}


def safe_error(exc):
    value = str(exc)
    allowed = ('http_', 'robots_', 'body_', 'invalid_', 'entry_', 'insufficient_',
        'too_many_', 'non_public_', 'unsupported_', 'discovery_')
    return value[:120] if value.startswith(allowed) else type(exc).__name__


def assess(observations):
    """Technical readiness is evidence for a human, never a trust probability."""
    latest = max((o['observed_at'] for o in observations),default=None)
    good = sorted([o for o in observations if o['payload'].get('http_status') == 200
        and latest is not None and o['observed_at']>=latest-timedelta(days=7)
        and o['payload'].get('item_count', 0) > 0]
        ,key=lambda o:o['observed_at'])
    times = sorted(o['observed_at'] for o in good)
    span = (times[-1]-times[0]).total_seconds()/3600 if len(times) > 1 else 0
    by_article = {s.get('final_url',s['url']):s['body_hash'] for o in good
        for s in o['payload'].get('samples', [])
        if s.get('extraction') == 'usable' and s.get('body_hash')}
    bodies = set(by_article.values())
    reasons = []
    if not good or not any(s.get('extraction')=='usable' for s in good[-1]['payload'].get('samples',[])):
        reasons.append('latest_observation_has_no_usable_article')
    if len(good) < 2 or span < OBSERVATION_HOURS:
        reasons.append('needs_spaced_observations')
    if len(bodies) < 2:
        reasons.append('needs_two_distinct_usable_articles')
    return {'policy': POLICY, 'technical_ready': not reasons, 'reasons': reasons,
        'successful_observations': len(good), 'observation_span_hours': span,
        'distinct_usable_bodies': len(bodies), 'ai_evaluated': False,
        'editorial_approval': False, 'required_next_step': 'human_editorial_review'}


def next_window(now):
    # Bóris windows start at 03/09/15/21 UTC (00/06/12/18 Brasília).
    shifted = now.astimezone(timezone.utc)-timedelta(hours=3)
    start = shifted.replace(hour=(shifted.hour//6)*6, minute=0, second=0, microsecond=0)
    return start+timedelta(hours=9)


def retry_delay(attempts, error):
    if error in ('http_404', 'http_410', 'unsupported_json_feed'):
        return timedelta(days=7)
    return timedelta(minutes=min(24*60, 30*(2**min(max(attempts-1, 0), 6))))
