"""HTTP com corpo limitado, timeout, redirects verificados e cadência por domínio."""
import ipaddress
import socket
import threading
import time
from urllib.parse import urlsplit, urljoin, urlunsplit
from urllib.robotparser import RobotFileParser
from contextlib import contextmanager
import certifi
import urllib3

UA = 'BorisNewsCollector/2.0'
_lock = threading.Lock()
_next = {}
_robots = {}

def canonical(url, base=None):
    u = urlsplit(urljoin(base or '', url))
    if u.scheme not in ('https','http') or not u.hostname or u.username or u.password:
        raise ValueError('invalid_url')
    # Fragmentos não identificam matérias; parâmetros são preservados.
    return urlunsplit((u.scheme,u.netloc,u.path or '/',u.query,''))

def public_destination(url):
    host = urlsplit(url).hostname
    answers = socket.getaddrinfo(host, None)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        raise ValueError('non_public_destination')
    return answers[0][4][0]


@contextmanager
def pinned_request(url,address,headers):
    """Connect to the validated address, retaining the publisher's Host/SNI.

    Direct urllib3 pools do not use HTTP_PROXY/HTTPS_PROXY environment settings.
    DNS is resolved once per hop: it is not repeated after the public-IP check.
    TLS certificates are still checked against the original hostname.
    """
    u=urlsplit(url)
    options={'port':u.port or (443 if u.scheme=='https' else 80),
             'timeout':urllib3.Timeout(connect=10,read=20),'retries':False}
    if u.scheme=='https':
        pool=urllib3.HTTPSConnectionPool(address,assert_hostname=u.hostname,
            server_hostname=u.hostname,cert_reqs='CERT_REQUIRED',ca_certs=certifi.where(),**options)
    else:pool=urllib3.HTTPConnectionPool(address,**options)
    response=None
    try:
        response=pool.urlopen('GET',urlunsplit(('','',u.path or '/',u.query,'')),
            headers={**headers,'Host':u.netloc},redirect=False,preload_content=False,retries=False)
        class Response:
            status_code=response.status
            headers=response.headers
            is_redirect=300<=response.status<400 and response.headers.get('Location') is not None
            def iter_content(self,size):return response.stream(size,decode_content=True)
        yield Response()
    finally:
        if response is not None:response.close()
        pool.close()

def get(url, headers=None, max_bytes=8*1024*1024, check_robots=False, budget=None):
    url = canonical(url)
    for _ in range(6):
        address=public_destination(url)
        if check_robots and not allowed(url, budget=budget):
            raise ValueError('robots_disallowed')
        host = urlsplit(url).netloc
        with _lock:
            at = max(time.monotonic(), _next.get(host,0))
            _next[host] = at + 1.0
        time.sleep(max(0,at-time.monotonic()))
        # Discovery reserves before every HTTP request, including robots and
        # redirect hops. Existing collection callers remain unaffected.
        # iter_content may receive one final chunk before the size guard fires.
        if budget is not None: budget.reserve(max_bytes+65536)
        with pinned_request(url,address,headers={'User-Agent':UA,'Accept-Encoding':'identity',**(headers or {})}) as r:
            if r.is_redirect:
                url = canonical(r.headers['Location'],url)
                continue
            if r.status_code == 304:
                return r.status_code,r.headers.copy(),b'',url
            if r.status_code >= 400:
                raise ValueError(f'http_{r.status_code}')
            body = bytearray()
            start = time.monotonic()
            for chunk in r.iter_content(65536):
                body.extend(chunk)
                if len(body)>max_bytes: raise ValueError('body_too_large')
                if time.monotonic()-start>45: raise ValueError('body_timeout')
            return r.status_code,r.headers.copy(),bytes(body),url
    raise ValueError('too_many_redirects')

def allowed(url, budget=None):
    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
    with _lock:
        cached = _robots.get(origin)
    if cached is None:
        try:
            _,_,body,_ = get(origin+'/robots.txt',max_bytes=512*1024,budget=budget)
            p=RobotFileParser(); p.parse(body.decode('utf-8','replace').splitlines())
            cached=p
        except ValueError as e:
            # Ausência de robots permite acesso; 403/429/5xx não são ignorados.
            cached = True if str(e) in ('http_404','http_410') else 'robots_unavailable_'+(str(e) if str(e).startswith('http_') else type(e).__name__)
        except urllib3.exceptions.HTTPError as exc:
            cached='robots_unavailable_'+type(exc).__name__
        with _lock: _robots[origin]=cached
    if isinstance(cached,str):raise ValueError(cached)
    return cached if isinstance(cached,bool) else cached.can_fetch(UA,url)
