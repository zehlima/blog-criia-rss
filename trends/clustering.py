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
 'costa','rica','colombia','colômbia','mexico','méxico','brasil','brazil','argentina',
 'panama','panamá','chile','peru','venezuela','china','india','italia','italy','france','spain','españa',
 'germany','europe','europa','africa','áfrica','asia','ásia','australia','united','states'}
# A single broad brand/product family is not an event identity. Two anchors can
# still establish a concrete event (for example Apple+iPhone).
BROAD={'apple','iphone','xiaomi','samsung','google','microsoft','openai','meta','amazon',
       'sony','lg','oppo','vivo','huawei','android','windows','xbox','playstation','galaxy'}

def anchors(title):
    text=unicodedata.normalize('NFKC',title).casefold()
    return {x for x in re.findall(r'[a-z0-9][a-z0-9+.#]*',text)
            if not x.isdigit() and (len(x)>=3 or any(c.isdigit() for c in x)) and x not in GENERIC}

def compatible(a,b,similarity,anchor_a=None,anchor_b=None,frequency=None,rare_limit=0):
    na=' '.join(a.casefold().split());nb=' '.join(b.casefold().split())
    if na==nb:return True
    shared=(anchor_a if anchor_a is not None else anchors(a)) & (anchor_b if anchor_b is not None else anchors(b))
    specific=shared-BROAD
    if len(shared)>=2 and specific:return True
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
        frequency=Counter(x for values in anchor_sets for x in values)
        rare_limit=max(3,int(len(titles)*.005))
        for i in range(len(vectors)):
            for j in range(i):
                if not compatible(titles[i],titles[j],float(similarity[i,j]),
                                  anchor_sets[i],anchor_sets[j],frequency,rare_limit):
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
