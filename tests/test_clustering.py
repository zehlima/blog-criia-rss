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

def test_generic_same_language_similarity_needs_anchor():
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    titles=['Yapay zeka ile karmaşa da artıyor','Yapay zeka ile tam otonom ağlar dönemi']
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_multilingual_event_with_entity_anchor_is_kept():
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    titles=['Apple is reportedly working on iPhone game controllers',
            'Apple’ın iPhone için geliştirdiği oyun kumandaları ortaya çıktı']
    assert coherent_groups(vectors,titles,min_similarity=.72)[0]['indices']==[0,1]

@pytest.mark.parametrize('titles',[
    ["Știrile zilei despre tehnologie – 14 septembrie 2026",
     "비큐에이아이, 'K-ICT WEEK in BUSAN 2026'서 서비스 설명회 개최"],
    ['Apple iPhone Duo vs. Xiaomi 18 Fold: Software matters',
     'iPhone 18 Pro vs Google Pixel 11 Pro: lequel choisir?'],
    ['PISA 2025: qué dicen los resultados de Costa Rica',
     'Fuego de la libertad recorre Costa Rica'],
    ['Xiaomi Luncurkan Colokan Pintar dengan Beban Maksimal 2500W',
     'Xiaomi Pad 9 Pro Tanıtıldı! 11.000 mAh Batarya Kapasitesi Var'],
])
def test_single_generic_anchor_does_not_join_different_events(titles):
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_single_specific_anchor_needs_stronger_similarity():
    titles=['Bitcoin mining farm found in Mexico','Fazenda de mineração de Bitcoin descoberta no México']
    weak=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    strong=np.array([[1.,0.],[.82,(1-.82**2)**.5]])
    assert coherent_groups(weak,titles,min_similarity=.72)==[]
    assert coherent_groups(strong,titles,min_similarity=.72)[0]['indices']==[0,1]
