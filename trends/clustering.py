"""Bounded-diameter event groups with lexical anchors for editorial precision."""
import re
import unicodedata
import numpy as np

GENERIC={'the','and','for','with','from','this','that','new','news','tech','technology',
 'artificial','intelligence','inteligencia','inteligência','yapay','zeka','ile','ai','pro','max'}

def anchors(title):
    text=unicodedata.normalize('NFKC',title).casefold()
    return {x for x in re.findall(r'[a-z0-9][a-z0-9+.#-]*',text)
            if (len(x)>=3 or any(c.isdigit() for c in x)) and x not in GENERIC}

def compatible(a,b,similarity):
    na=' '.join(a.casefold().split());nb=' '.join(b.casefold().split())
    return na==nb or bool(anchors(a)&anchors(b)) or similarity>=.90

def coherent_groups(embeddings,titles=None,min_similarity=.72):
    from sklearn.cluster import AgglomerativeClustering
    if len(embeddings)<2:return []
    vectors=np.asarray(embeddings,dtype=np.float32)
    vectors=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
    similarity=vectors@vectors.T
    distance=1-similarity
    if titles is not None:
        if len(titles)!=len(vectors):raise ValueError('title_vector_length_mismatch')
        for i in range(len(vectors)):
            for j in range(i):
                if not compatible(titles[i],titles[j],float(similarity[i,j])):
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
