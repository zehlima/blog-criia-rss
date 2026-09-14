"""Bounded-diameter event groups. No forced assignment of unrelated articles."""
import numpy as np

def coherent_groups(embeddings,min_similarity=.89):
    from sklearn.cluster import AgglomerativeClustering
    if len(embeddings)<2:return []
    vectors=np.asarray(embeddings,dtype=np.float32)
    vectors=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
    # Complete linkage prevents A~B~C chains from merging A and C when unrelated.
    labels=AgglomerativeClustering(n_clusters=None,metric='cosine',linkage='complete',
                                  distance_threshold=1-min_similarity).fit_predict(vectors)
    groups=[]
    for label in sorted(set(labels)):
        idx=np.flatnonzero(labels==label)
        if len(idx)<2:continue
        pairwise=vectors[idx]@vectors[idx].T
        floor=float(pairwise.min())
        if floor+1e-6<min_similarity:raise ValueError('cluster_diameter_violation')
        representative=int(idx[np.argmax(pairwise.mean(axis=1))])
        groups.append({'indices':idx.tolist(),'representative':representative,'min_similarity':floor})
    return groups
