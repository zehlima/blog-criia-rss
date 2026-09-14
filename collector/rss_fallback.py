"""Read publisher-provided RSS content, explicitly distinguished from page extraction."""
import gzip,json,os
from html import unescape
from lxml import html

def publisher_text(raw):
    blocks=json.loads(raw)
    result=[]
    for block in blocks:
        # Long summaries remain summaries, irrespective of their character count.
        if block.get('type')=='feed_summary':continue
        value=block.get('value','')
        if not isinstance(value,str):continue
        try:
            node=html.fromstring(value)
            for excluded in node.xpath('//script|//style|//noscript'):excluded.drop_tree()
            text=node.text_content()
        except (ValueError,TypeError):text=unescape(value)
        text=' '.join(text.split())
        if len(text)>=200:result.append(text)
    return max(result,key=len) if result else None

def fetch(s3,article):
    if not article.get('rss_content_key'):raise ValueError('insufficient_rss_content')
    obj=s3.get_object(Bucket=os.environ['R2_BUCKET'],Key=article['rss_content_key'])
    try:raw=gzip.decompress(obj['Body'].read()).decode('utf-8')
    finally:obj['Body'].close()
    text=publisher_text(raw)
    if not text:raise ValueError('insufficient_rss_content')
    return 200,{'X-Content-Basis':'publisher_rss'},text,article['url']
