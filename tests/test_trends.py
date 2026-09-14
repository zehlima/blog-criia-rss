from datetime import datetime,timezone
from trends.core import rankings,in_window,continent
from collector.reporting import classify

def source(country='Brasil',region='América do Sul',site='https://example.com'):
    return {'id':1,'name':'Example','country':country,'region':region,'site_url':site,'rss_url':site+'/rss'}

def article(id=1,sources=None):
    return {'id':id,'title':'Tema','url':'https://example.com/a','sources':sources or [source()],
            'topic_id':'t1','topic_label':'Tema','family':'copy1','text_basis':'title_summary'}

def test_global_does_not_sum_country_counts():
    a=article(sources=[source(),source('Portugal','Europa Ocidental','https://other.com')])
    assert rankings([a],'globe')['Globo']['ranking'][0]['articles']==1
    assert rankings([a],'globe')['Globo']['ranking'][0]['publishers']==2
    assert set(rankings([a],'country'))=={'Brasil','Portugal'}

def test_republication_keeps_volume_but_counts_one_family():
    r=rankings([article(1),article(2)],'globe')['Globo']['ranking'][0]
    assert r['articles']==2 and r['republication_families_estimated']==1 and r['publishers']==1
    assert r['full_texts']==0

def test_country_publishers_are_scoped():
    a=article(sources=[source(),source('Portugal','Europa Ocidental','https://other.com')])
    assert rankings([a],'country')['Brasil']['ranking'][0]['publishers']==1

def test_old_or_future_stories_not_trending_today():
    now=datetime(2026,9,14,12,tzinfo=timezone.utc)
    assert not in_window({'published_at':'2026-01-01T00:00:00+00:00'},now)
    assert not in_window({'published_at':'2026-09-15T00:00:00+00:00'},now)
    assert in_window({'published_at':None,'first_seen_at':now},now)

def test_geography_does_not_call_middle_east_a_continent():
    assert continent(source('Israel','Oriente Médio'))=='Ásia'
    assert continent(source('Egito','Oriente Médio'))=='África'
    assert continent(source('Turquia','Oriente Médio'))=='Europa/Ásia (transcontinental)'

def test_unclustered_is_visible_not_ranked():
    a=article();a['topic_id']='outlier'
    r=rankings([a],'globe')['Globo']
    assert r['outliers']==1 and r['ranking']==[] and r['articles']==1

def test_feed_error_classification():
    assert classify('AttributeError')[0]=='coletor'
    assert classify('http_404')[0]=='endpoint'
    assert classify('http_403')[0]=='acesso'

def test_empty_feed_returns_format_error_not_attribute_error():
    from collector.extract import entries
    import pytest
    with pytest.raises(ValueError,match='invalid_or_malformed_feed'):entries(b'', 'https://example.com')
