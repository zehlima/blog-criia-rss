"""Bounded-diameter event groups with lexical anchors for editorial precision."""
import re
import unicodedata
from collections import Counter
import numpy as np

GENERIC={'the','and','for','with','from','this','that','new','news','tech','technology',
 'und','oder','mit','von','diese','zum','beim','der','die','das','auf','aus','eine','einer',
 'sparen','kosten','gelten',
 'del','los','las','una','para','con','por','que','esta','este','hoy','vivo','video',
 'domingo','septiembre','september','today',
 'uma','com','come','per','une','des','les','pour','avec',
 'artificial','intelligence','inteligencia','inteligência','yapay','zeka','ile','ai','pro','max',
 '2024','2025','2026','4k','5g','6g','ssd','hdd','panel','monitor','cyber',
 'gutscheine','rabattcodes','loteria','lottery','nacional','national','sorteo','resultados',
 'eylul','sifir','arac','fiyat','listesi','guncel','kampanyalar','kredi','firsatlari',
 'indirimli','otomobiller','indirimler','series','serie','serisi','model','models',
 'costa','rica','colombia','colômbia','mexico','méxico','brasil','brazil','argentina',
 'panama','panamá','chile','peru','venezuela','china','india','italia','italy','france','spain','españa',
 'germany','europe','europa','africa','áfrica','asia','ásia','australia','united','states'}
# A single broad brand/product family is not an event identity. Two anchors can
# still establish a concrete event (for example Apple+iPhone).
BROAD={'apple','iphone','xiaomi','samsung','google','microsoft','openai','meta','amazon',
       'sony','lg','oppo','vivo','huawei','android','windows','xbox','playstation','galaxy',
       'honor','snapdragon','blizzard','diablo','duo','gen'}

GENERIC.update({'risk','risks','risky','warning','warnings','warns','safety','security',
 'riesgo','riesgos','advertencia','advertencias','alerta','alertas','advierte','seguridad',
 'risco','riscos','alerta','alertas','adverte','seguranca','segurança'})
BROAD.add('anthropic')

ROMAN={'i':'1','ii':'2','iii':'3','iv':'4','v':'5','vi':'6','vii':'7','viii':'8','ix':'9','x':'10'}
VERSIONED_PRODUCTS={'iphone','ios','windows','galaxy','diablo','playstation','xbox'}

def semantic_event_text(title):
    """Keep the event predicate while down-weighting broad product identity.

    The lexical gate still sees the original headline.  Embeddings see this
    title-derived context so two unrelated Windows/iPhone stories are not
    grouped merely because the shared product name dominates the vector.
    """
    text=unicodedata.normalize('NFKC',title)
    products='|'.join(sorted(VERSIONED_PRODUCTS,key=len,reverse=True))
    text=re.sub(rf'(?i)\b(?:{products})\s+(?:[a-z]?\d+|[ivx]+)\b',' ',text)
    broad='|'.join(sorted(BROAD|{'ios'},key=len,reverse=True))
    text=re.sub(rf'(?i)\b(?:{broad})\b',' ',text)
    text=re.sub(r'\s+',' ',text).strip(' -—–:;,.|/')
    return text if len(text)>=8 else title.strip()

def _tokens(title):
    # Fold diacritics so the template vocabulary behaves consistently across
    # Portuguese, Spanish and Turkish headlines.
    text=''.join(c for c in unicodedata.normalize('NFKD',title).casefold()
                 if not unicodedata.combining(c))
    text=text.translate(str.maketrans({'ı':'i','ş':'s','ğ':'g','ø':'o','ł':'l','đ':'d'}))
    return [ROMAN.get(x,x) for x in re.findall(r'[a-z0-9][a-z0-9+.#]*',text)]

def anchors(title):
    tokens=_tokens(title)
    atomic={x for x in tokens if not x.isdigit()
            and (len(x)>=3 or any(c.isdigit() for c in x)) and x not in GENERIC}
    # Preserve narrow product/event identities such as "iPhone Duo Max",
    # "Honor Magic 9" and "Diablo 5".  A generic two-word family such as
    # "iPhone Duo" is intentionally insufficient.
    compound=set()
    for width in (2,3):
        for start in range(len(tokens)-width+1):
            parts=tokens[start:start+width]
            meaningful=[x for x in parts if x not in GENERIC and not x.isdigit()]
            model_number=any(x.isdigit() and not (len(x)==4 and 1900<=int(x)<=2100) for x in parts)
            if (width==3 and len(meaningful)>=2) or (model_number and meaningful):
                compound.add('~'+'_'.join(parts))
    return atomic|compound

def product_versions(title):
    tokens=_tokens(title)
    found={}
    for left,right in zip(tokens,tokens[1:]):
        if left in VERSIONED_PRODUCTS and right.isdigit():
            found.setdefault(left,set()).add(right)
    return found

def is_multi_story_digest(title):
    # Daily roundups commonly concatenate unrelated headlines with slashes.
    # They may participate only through exact-title syndication.
    parts=[x for x in re.split(r'\s[/|｜]\s|[/|｜]',title) if x.strip()]
    return len(parts)>=3

def is_template_listing(title):
    # Conference/catalogue prefixes identify a venue or content type, not the
    # same announcement. Exact syndication is handled before this gate.
    return bool(re.match(r'(?i)^\s*(?:\[\s*virtual event\s*\]|gisec\s+20\d{2}\s*:)',title))

def compatible(a,b,similarity,anchor_a=None,anchor_b=None,frequency=None,rare_limit=0,
               versions_a=None,versions_b=None,digest_a=None,digest_b=None):
    na=' '.join(a.casefold().split());nb=' '.join(b.casefold().split())
    if na==nb:return True
    if is_template_listing(a) or is_template_listing(b):return False
    if (is_multi_story_digest(a) if digest_a is None else digest_a) or (is_multi_story_digest(b) if digest_b is None else digest_b):return False
    versions_a=product_versions(a) if versions_a is None else versions_a
    versions_b=product_versions(b) if versions_b is None else versions_b
    for product in versions_a.keys()&versions_b.keys():
        if versions_a[product]!=versions_b[product]:return False
    shared=(anchor_a if anchor_a is not None else anchors(a)) & (anchor_b if anchor_b is not None else anchors(b))
    compounds={x for x in shared if x.startswith('~')}
    if compounds:return similarity>=.735
    atomic={x for x in shared if not x.startswith('~')}
    specific=atomic-BROAD
    # Two common words are still a subject, not necessarily one story. At least
    # one shared atom must be uncommon in this corpus before it can identify an
    # event across translations.
    if len(atomic)>=2 and any(frequency and frequency[x]<=rare_limit for x in specific):return True
    # A single unusually specific token can connect translations, but only with
    # a materially stronger semantic match. Broad brands never qualify alone.
    return similarity>=.78 and any(frequency and frequency[x]<=rare_limit for x in specific)

def coherent_groups(embeddings,titles=None,min_similarity=.72):
    from sklearn.cluster import AgglomerativeClustering
    if len(embeddings)<2:return []
    vectors=np.asarray(embeddings,dtype=np.float32)
    vectors=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
    similarity=vectors@vectors.T
    distance=1-similarity
    if titles is not None:
        if len(titles)!=len(vectors):raise ValueError('title_vector_length_mismatch')
        anchor_sets=[anchors(title) for title in titles]
        version_sets=[product_versions(title) for title in titles]
        digests=[is_multi_story_digest(title) for title in titles]
        frequency=Counter(x for values in anchor_sets for x in values)
        rare_limit=max(4,int(len(titles)*.001))
        for i in range(len(vectors)):
            for j in range(i):
                if not compatible(titles[i],titles[j],float(similarity[i,j]),
                                  anchor_sets[i],anchor_sets[j],frequency,rare_limit,
                                  version_sets[i],version_sets[j],digests[i],digests[j]):
                    distance[i,j]=distance[j,i]=2.0
    # Complete linkage prevents A~B~C chains from merging A and C when unrelated.
    labels=AgglomerativeClustering(n_clusters=None,metric='precomputed',linkage='complete',
                                  distance_threshold=1-min_similarity).fit_predict(distance)
    groups=[]
    for label in sorted(set(labels)):
        idx=np.flatnonzero(labels==label)
        if len(idx)<2:continue
        pairwise=similarity[np.ix_(idx,idx)]
        floor=float(pairwise.min())
        if floor+1e-6<min_similarity:raise ValueError('cluster_diameter_violation')
        representative=int(idx[np.argmax(pairwise.mean(axis=1))])
        groups.append({'indices':idx.tolist(),'representative':representative,'min_similarity':floor})
    return groups
