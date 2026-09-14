from datetime import datetime, timezone
import numpy as np
from daily.core import bounds, compare, fingerprint, group_copies, accounting, chargrams


BODY='A fabricante Aurora anunciou uma bateria de sódio para ônibus urbanos. Os testes realizados em Recife registraram autonomia de trezentos quilômetros e recarga rápida. O projeto será produzido na fábrica local em parceria com a universidade. '


def article(i,title='Aurora anuncia bateria de sódio para ônibus',body=BODY,sources=None):
    return {'id':i,'title':title,'url':f'https://example.org/{i}','lead':body[:1200],
            'body_hash':fingerprint(body),'text_basis':'extracted_page',
            'sources':sources or [source('Brasil','América do Sul','br.example')]}


def source(country,region,host):
    return {'country':country,'region':region,'site_url':'https://'+host,'rss_url':'https://'+host+'/rss','name':host}


def test_day_is_brasilia_calendar_not_rolling_24h():
    start,end=bounds('2026-09-14')
    assert start.isoformat()=='2026-09-14T03:00:00+00:00'
    assert end.isoformat()=='2026-09-15T03:00:00+00:00'
    assert start<=datetime(2026,9,15,2,59,tzinfo=timezone.utc)<end
    assert not start<=end<end


def test_identical_body_different_title_is_copy():
    result=compare(article(1),article(2,'Empresa Aurora apresenta nova bateria para transporte público'),.75,.99)
    assert result['decision']=='duplicate'
    assert result['probability'] is None


def test_same_title_different_text_not_copy():
    other='A análise independente aponta que o produto é inviável. A tecnologia existente apresenta riscos e depende de materiais importados. Os pesquisadores contestam as promessas comerciais. '*3
    assert compare(article(1),article(2,body=other),1,.5)['decision']!='duplicate'


def test_translated_semantic_match_requires_review_not_automatic_copy():
    other='Aurora presented sodium batteries for urban buses in Recife. The announcement describes a joint research project and local production with a university partner. The vehicles will support rapid charging and extended autonomy. '*2
    result=compare(article(1),article(2,'Aurora launches sodium battery for buses',other),.96,.97)
    assert result['decision']=='possible_republication'
    assert not result['score_calibrated']


def test_numbers_distinguish_other_versions():
    a=article(1,'Aurora battery 2 launched')
    b=article(2,'Aurora battery 3 launched',BODY+' Atualização nova.')
    assert compare(a,b,.98,.98)['decision']=='distinct'


def test_missing_body_never_proves_copy():
    a=article(1);b=article(2)
    a['text_basis']=b['text_basis']='title_summary'
    assert compare(a,b,1,1)['decision']=='possible_republication'


def test_cjk_shingles_are_not_one_word():
    assert len(chargrams('中国宣布新的电池技术将在明年投入生产'))>5


def test_copy_groups_do_not_chain():
    articles=[article(i) for i in range(3)]
    vectors=np.ones((3,1))
    group_copies(articles,vectors,vectors,pairs=[(0,1),(1,2)])
    assert articles[0]['copy_family']==articles[1]['copy_family']
    assert articles[0]['copy_family']!=articles[2]['copy_family']


def test_global_recomputed_and_feed_rereads_separated():
    br=source('Brasil','América do Sul','br.example')
    us=source('Estados Unidos','América do Norte','us.example')
    articles=[article(1,sources=[br,us]),article(2,sources=[br])]
    vectors=np.ones((2,1));group_copies(articles,vectors,vectors,pairs=[(0,1)])
    obs=[{'slot':'2026-09-14T09:00:00Z','feed_id':1,'article_id':1,'source':br},
         {'slot':'2026-09-14T15:00:00Z','feed_id':1,'article_id':1,'source':br}]
    obs.append(obs[0])
    countries=accounting(articles,obs,'country')
    world=accounting(articles,obs,'globe')['Globo']
    assert sum(x['publications'] for x in countries.values())==3
    assert world['publications']==2
    assert world['distinct_texts_estimated']==1
    assert world['extra_copies_estimated']==1
    assert world['feed_sightings_all_articles']==2


def test_empty_day_not_error():
    assert accounting([],[],'globe')['Globo']['publications']==0


def test_candidate_generation_detects_copy_with_low_title_similarity():
    articles=[article(1),article(2,'Aurora apresenta tecnologia de sódio')]
    vectors=np.array([[1.,0.],[.71,.7042]])
    group_copies(articles,vectors,vectors)
    assert articles[0]['copy_family']==articles[1]['copy_family']


def test_common_site_body_with_divergent_titles_is_quarantined():
    rows=[article(1,'A new battery'),article(2,'A music concert'),article(3,'A software vulnerability')]
    vectors=np.eye(3)
    group_copies(rows,vectors,vectors.copy())
    assert all(a['text_basis']=='untrusted_body' for a in rows)
    assert len({a['copy_family'] for a in rows})==3


def test_midnight_gate_closes_previous_calendar_day_only():
    from daily.main import choose_day
    attempt={'slot':datetime(2026,9,15,3,tzinfo=timezone.utc),'finished_at':datetime(2026,9,15,4,tzinfo=timezone.utc),'report':{'status':'complete_with_gaps'}}
    assert choose_day(attempt,'auto')==('2026-09-14','closed')
    attempt['slot']=datetime(2026,9,15,9,tzinfo=timezone.utc)
    assert choose_day(attempt,'auto') is None
    attempt['slot']=datetime(2026,9,15,3,tzinfo=timezone.utc)
    attempt['report']['status']='partial'
    assert choose_day(attempt,'auto') is None
    assert choose_day(attempt,'preview')==('2026-09-15','preview')
