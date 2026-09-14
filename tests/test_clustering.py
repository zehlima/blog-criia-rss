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

def test_two_broad_multilingual_anchors_are_not_forced():
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    titles=['Apple is reportedly working on iPhone game controllers',
            'Apple’ın iPhone için geliştirdiği oyun kumandaları ortaya çıktı']
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

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

def test_high_vector_similarity_without_anchor_does_not_group_cjk_headlines():
    titles=[
        "SC제일은행, '거래 공백' 고객 잡는다…파킹통장 혜택 찾아보니",
        "가습기살균제 피해자 43명 추가 인정…구제급여 지급 대상자 총 6080명",
    ]
    vectors=np.array([[1.,0.],[.95,(1-.95**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_coupon_template_is_not_an_event():
    titles=['Hawesko-Gutscheine und Rabattcodes','Shop-Apotheke-Gutscheine und Rabattcodes']
    vectors=np.array([[1.,0.],[.85,(1-.85**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_coupon_template_with_function_words_is_not_an_event():
    titles=['Rebuy-Gutscheine und Rabattcodes zum Sparen beim Elektronikkauf',
            'Temu-Gutscheine und Rabattcodes zum Sparen']
    vectors=np.array([[1.,0.],[.85,(1-.85**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_lottery_date_template_does_not_cross_countries():
    titles=['Resultados del sorteo dominical de la Lotería Nacional de Panamá',
            'Lotería Nacional de Costa Rica: ganadores del domingo 13 de septiembre']
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_two_broad_product_names_are_not_enough():
    titles=['Samsung usa Tim Cook em anúncio do Galaxy Z Fold8',
            'Samsung estabelece novo padrão com a série Galaxy Z8']
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

@pytest.mark.parametrize('titles',[
    ['Honor представила смартфон Play 11 с чипсетом Qualcomm Snapdragon 4 Gen 4',
     'Honor Magic 9 получит Snapdragon 8 Elite Gen 6 Pro'],
    ['Blizzard Announces Diablo V, Sanctuary Has Fallen And Diablo Won',
     'Blizzard поверне класику Diablo в новому сезоні Diablo IV'],
    ['CUPRA Eylül 2026 Sıfır Araç Fiyat Listesi: Güncel Kampanyalar',
     'Opel Eylül 2026 Sıfır Araç Fiyat Listesi: Güncel Kampanyalar'],
    ['iPhone Duo first impressions: Apple enters foldables',
     'iPhone Duo Max reportedly planned with a bigger screen'],
])
def test_same_brand_or_template_does_not_merge_different_events(titles):
    vectors=np.array([[1.,0.],[.77,(1-.77**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

@pytest.mark.parametrize('titles',[
    ['Apple plans a larger iPhone Duo Max',
     'Apple iPhone Duo Max için çalışmalara başladı'],
    ['Honor Magic 9 Super Edition leaks with 11000 mAh battery',
     'Honor Magic 9 Super Edition tem bateria gigante'],
    ['Blizzard announces Diablo V at BlizzCon',
     'Blizzard sorprende y anuncia Diablo 5'],
])
def test_narrow_product_identity_survives_multilingual_headlines(titles):
    vectors=np.array([[1.,0.],[.75,(1-.75**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)[0]['indices']==[0,1]
