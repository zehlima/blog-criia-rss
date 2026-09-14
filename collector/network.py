"""HTTP com corpo limitado, timeout, redirects verificados e cadência por domínio."""
import ipaddress
import socket
import threading
import time
from urllib.parse import urlsplit, urljoin, urlunsplit
from urllib.robotparser import RobotFileParser
import requests

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

def get(url, headers=None, max_bytes=8*1024*1024, check_robots=False):
    url = canonical(url)
    for _ in range(6):
        public_destination(url)
        if check_robots and not allowed(url):
            raise ValueError('robots_disallowed')
        host = urlsplit(url).netloc
        with _lock:
            at = max(time.monotonic(), _next.get(host,0))
            _next[host] = at + 1.0
        time.sleep(max(0,at-time.monotonic()))
        with requests.get(url,headers={'User-Agent':UA,'Accept-Encoding':'identity',**(headers or {})},
                          timeout=(10,20),allow_redirects=False,stream=True) as r:
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

def allowed(url):
    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
    with _lock:
        cached = _robots.get(origin)
    if cached is None:
        try:
            _,_,body,_ = get(origin+'/robots.txt',max_bytes=512*1024)
            p=RobotFileParser(); p.parse(body.decode('utf-8','replace').splitlines())
            cached=p
        except ValueError as e:
            # Ausência de robots permite acesso; 403/429/5xx não são ignorados.
            cached = True if str(e) in ('http_404','http_410') else False
        except requests.RequestException:
            cached=False
        with _lock: _robots[origin]=cached
    return cached if isinstance(cached,bool) else cached.can_fetch(UA,url)
