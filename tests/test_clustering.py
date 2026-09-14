import pytest
np=pytest.importorskip('numpy')
pytest.importorskip('sklearn')
from trends.clustering import coherent_groups,semantic_event_text

@pytest.mark.parametrize(('title','kept','removed'),[
    ('Windows 11 has a secret way to skip the Microsoft account requirement','skip the account requirement','windows'),
    ('Samsung Galaxy S27 Ultra gets an audio fix','gets an audio fix','samsung'),
    ('OpenAI delays its IPO over safety risks','delays its IPO over safety risks','openai'),
])
def test_semantic_event_text_downweights_product_identity(title,kept,removed):
    text=semantic_event_text(title)
    assert kept.casefold() in text.casefold()
    assert removed.casefold() not in text.casefold()

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

def test_different_version_sets_do_not_merge_even_at_high_similarity():
    titles=['Blizzard cancels Diablo 4 expansions after announcing Diablo 5',
            'Blizzard brings a classic season to Diablo IV']
    vectors=np.array([[1.,0.],[.84,(1-.84**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_same_cross_generation_story_can_group():
    titles=['Diablo 5 announcement disappoints the Diablo 4 community',
            'Diablo V est une mauvaise nouvelle pour Diablo IV']
    vectors=np.array([[1.,0.],[.81,(1-.81**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)[0]['indices']==[0,1]

def test_multi_story_daily_digest_is_not_folded_into_one_of_its_items():
    titles=['iPhone 18 Pro demand is lower than last year',
            'Morning brief | iPhone 18 Pro sold out / OpenAI delays IPO / new ice cream reviewed']
    vectors=np.array([[1.,0.],[.82,(1-.82**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

@pytest.mark.parametrize('titles',[
    ['GISEC 2026: Saviynt to showcase AI identity security',
     'GISEC 2026: du to showcase sovereign AI cloud'],
    ['[Virtual Event] Securing cloud assets in the age of AI',
     '[Virtual Event] Building a secure AI strategy for enterprise'],
])
def test_shared_event_or_catalogue_prefix_is_not_one_story(titles):
    vectors=np.array([[1.,0.],[.85,(1-.85**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_product_identity_with_weak_event_similarity_is_not_one_story():
    titles=['Huawei Pura X View sales exceed 300,000 units',
            'Huawei Pura X View hands-on review and price']
    vectors=np.array([[1.,0.],[.73,(1-.73**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_product_sales_and_hands_on_are_different_stories_even_with_high_similarity():
    titles=['HUAWEI Pura X View 開賣 5 日破 30 萬部',
            'Trên tay Huawei Pura X View: Điện thoại lạ mắt, giá gần 30 triệu đồng']
    vectors=np.array([[1.,0.],[.785,(1-.785**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_cross_brand_inspiration_is_not_the_source_brand_story():
    titles=['Apple tají rozlišení selfie kamery pod displejem iPhone Duo',
            'HONOR si ispira ad Apple: nuova selfie cam quadrata per YouTube e Reel']
    vectors=np.array([[1.,0.],[.79,(1-.79**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

@pytest.mark.parametrize('titles',[
    ['Midea PortaSplit bekommt ein wichtiges Sicherheitsupdate',
     'Midea PortaSplit: Was das nahende EU-Verbot bedeutet'],
    ['HUAWEI WATCH GT 7 review: 21 day battery',
     'HUAWEI WATCH GT 7 series specifications and performance'],
])
def test_same_product_with_different_story_form_is_not_one_event(titles):
    vectors=np.array([[1.,0.],[.79,(1-.79**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_distinct_daily_programmes_are_not_grouped_by_calendar_date():
    titles=['Extranegocios del Lunes 14 de setiembre de 2026',
            'Concolón, lunes 14 de septiembre de 2026']
    vectors=np.array([[1.,0.],[.79,(1-.79**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_specific_interview_is_not_broad_company_warning_story():
    titles=['Ex-Anthropic researcher tells BBC employees are terrified by AI risks',
            'Anthropic and OpenAI warn they may lose control of AI']
    vectors=np.array([[1.,0.],[.76,(1-.76**2)**.5]])
    assert coherent_groups(vectors,titles,min_similarity=.72)==[]

def test_event_metadata_is_precomputed_for_pairwise_matrix(monkeypatch):
    import trends.clustering as clustering
    original=clustering.product_versions
    calls=[]
    def counted(title):
        calls.append(title);return original(title)
    monkeypatch.setattr(clustering,'product_versions',counted)
    titles=[f'Windows 11 audio update report {i}' for i in range(20)]
    coherent_groups(np.eye(20),titles,min_similarity=.72)
    assert len(calls)==len(titles)

def test_story_form_metadata_is_precomputed_for_pairwise_matrix(monkeypatch):
    import trends.clustering as clustering
    original=clustering.story_form_flags
    calls=[]
    def counted(title):
        calls.append(title);return original(title)
    monkeypatch.setattr(clustering,'story_form_flags',counted)
    titles=[f'Huawei product update report {i}' for i in range(20)]
    coherent_groups(np.eye(20),titles,min_similarity=.72)
    assert len(calls)==len(titles)
