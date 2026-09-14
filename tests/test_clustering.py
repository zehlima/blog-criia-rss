import pytest
np=pytest.importorskip('numpy')
pytest.importorskip('sklearn')
from trends.clustering import coherent_groups

def test_transitive_similarity_does_not_merge_unrelated_ends():
    angles=np.deg2rad([0,20,40])
    vectors=np.array([[np.cos(x),np.sin(x)] for x in angles])
    groups=coherent_groups(vectors,min_similarity=.9)
    assert all(not ({0,2}<=set(g['indices'])) for g in groups)
    assert sum(len(g['indices']) for g in groups)==2

def test_singletons_not_forced_into_topics():
    assert coherent_groups(np.eye(3))==[]
    assert coherent_groups(np.array([[1.,0.]]))==[]

def test_identical_stories_are_grouped():
    groups=coherent_groups(np.array([[1.,0.],[1.,0.],[0.,1.]]))
    assert len(groups)==1 and groups[0]['indices']==[0,1]
