"""Read-only diagnostics for observed extraction failures; no article bodies in logs."""
import json
import feedparser,trafilatura
from lxml import html
from .network import get

def main():
 _,_,body,url=get('https://www.dday.it/rss',max_bytes=32*1024*1024)
 parsed=feedparser.parse(body)
 for e in parsed.entries[:5]:
  print(json.dumps({'kind':'rss_links','title':e.get('title'),'link':e.get('link'),'links':e.get('links'),'id':e.get('id')},ensure_ascii=False),flush=True)
 urls=[
 'https://proceso.hn/0-1-de-haaland-a-donnarruma-el-city-tambien-fue-irreductible-con-diez/',
 'https://www.stuff.co.nz/business/361033224/he-called-himself-nzs-donald-trump-now-29-his-companies-are-liquidation',
 'https://www.svetandroida.cz/alzapower-boost-ultra-anc-sleva-zari-2026/',
 ]
 for u in urls:
  try:
   status,h,body,final=get(u,check_robots=True)
   tree=html.fromstring(body)
   row={'kind':'page','url':u,'status':status,'type':h.get('Content-Type'),'bytes':len(body),'title':tree.xpath('string(//title)')[:160],'h1':tree.xpath('//h1/text()')[:3],
        'precision_chars':len(trafilatura.extract(body,url=final,favor_precision=True) or ''),'recall_chars':len(trafilatura.extract(body,url=final,favor_recall=True) or ''),
        'body_text_chars':len(' '.join(tree.xpath('//body//text()[not(ancestor::script) and not(ancestor::style)]'))),
        'challenge_markers':[m for m in ['access denied','enable javascript','captcha','verify you are human','adblock','subscribe'] if m in body.decode('utf-8','replace').lower()]}
  except Exception as e:row={'kind':'page','url':u,'error':type(e).__name__+': '+str(e)[:100]}
  print(json.dumps(row,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
