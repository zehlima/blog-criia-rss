"""Deterministic aggregation, geography, coverage and deduplication helpers."""
import hashlib
import re
import unicodedata
from collections import defaultdict
from datetime import datetime,timedelta
from urllib.parse import urlsplit

REGIONS={
 'América do Norte':'América do Norte','América Central e Caribe':'América do Norte',
 'América do Sul':'América do Sul','Europa Ocidental':'Europa',
 'Europa Oriental (Leste Europeu)':'Europa','Ásia (Leste Asiático e Sudeste Asiático)':'Ásia',
 'Oriente Médio':'Ásia','África':'África','Oceania':'Oceania'}

def continent(source):
    if source['country']=='Egito':return 'África'
    if source['country'] in ('Rússia','Turquia'):return 'Europa/Ásia (transcontinental)'
    return REGIONS.get(source['region'],'Não mapeado')

def normalized(text):
    return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',text).casefold()))

def shingles(text):
    words=normalized(text).split()
    return {' '.join(words[i:i+5]) for i in range(max(1,len(words)-4))}

def families(docs):
    # MinHash proposes candidates; exact Jaccard verifies similarity to the representative.
    from datasketch import MinHash,MinHashLSH
    lsh=MinHashLSH(threshold=.8,num_perm=64);reps={}; result=[]
    for doc in docs:
        tokens=shingles(doc); mh=MinHash(num_perm=64)
        for token in sorted(tokens):mh.update(token.encode())
        matches=[k for k in lsh.query(mh) if len(tokens & reps[k])/max(1,len(tokens | reps[k]))>=.85]
        family=min(matches) if matches else hashlib.sha256(normalized(doc).encode()).hexdigest()[:20]
        if family not in reps:reps[family]=tokens;lsh.insert(family,mh)
        result.append(family)
    return result

def in_window(article,as_of,hours=24):
    date=article.get('published_at') or article['first_seen_at']
    if isinstance(date,str):date=datetime.fromisoformat(date)
    return as_of-timedelta(hours=hours)<=date<=as_of

def publisher(source):
    return (urlsplit(source.get('site_url') or source['rss_url']).hostname or source['name']).removeprefix('www.')

def rankings(articles,scope):
    groups=defaultdict(list)
    for a in articles:
        places={'Globo'} if scope=='globe' else {s['country'] if scope=='country' else continent(s) for s in a['sources']}
        for place in places:groups[place].append(a)
    output={}
    for place,rows in sorted(groups.items()):
        topics=defaultdict(list)
        for a in rows:topics[a['topic_id']].append(a)
        ranked=[]
        for topic,items in topics.items():
            if topic=='outlier':continue
            sources=[s for a in items for s in a['sources'] if scope=='globe' or (s['country'] if scope=='country' else continent(s))==place]
            ranked.append({'topic_id':topic,'label':items[0]['topic_label'],
              'articles':len({a['id'] for a in items}),'publishers':len({publisher(s) for s in sources}),
              'countries':sorted({s['country'] for s in sources}),
              'continents':sorted({continent(s) for s in sources}),
              'republication_families_estimated':len({a['family'] for a in items}),
              'full_texts':sum(a['text_basis']=='extracted_page' for a in items),
              'evidence':[{'id':a['id'],'title':a['title'],'url':a['url']} for a in items[:5]]})
        output[place]={'articles':len({a['id'] for a in rows}),'outliers':sum(a['topic_id']=='outlier' for a in rows),
          'ranking':sorted(ranked,key=lambda r:(-r['publishers'],-r['articles'],r['topic_id']))}
    return output
