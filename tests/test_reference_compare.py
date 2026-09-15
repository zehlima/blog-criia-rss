import pytest
from reference_compare.core import build,partition,report_key,reference_names
REFS=[dict(name='Ref',site_url='https://ref.example',rss_url='https://ref.example/rss')]
def article(i,ref=False,country='Brasil',family=None):
    return dict(id=i,title='SpaceX launches Starship',url=f'https://{"ref" if ref else "street"}.example/{i}',sources=[dict(name='Ref' if ref else 'Street',country=country,region='América do Sul',site_url=f'https://{"ref" if ref else "street"}.example',rss_url='')],copy_family=family or str(i),subject_family='topic',lead='Starship launch '+('rocket flight '*30),text_basis='extracted_page')
def report(items,pairs=[]):return build(dict(id='c',day='2026-09-14',cutoff='2026-09-15'),items,REFS,pairs,[])
def test_holdout_excludes_reference_url_even_if_shared_with_street_feed():
    a=article(1,True);a['sources'].append(article(2)['sources'][0])
    street,ref=partition([a,article(2)],REFS)
    assert [x['id'] for x in street]==[2]
    assert [x['id'] for x in ref]==[1]
def test_global_count_not_sum_of_geographies_and_copies_not_independence():
    a=article(1);a['sources'].append(dict(a['sources'][0],country='Argentina'))
    r=report([a,article(2,True)], [dict(street_id=1,reference_id=2,decision='duplicate')])
    assert r['scopes']['globe']['Globo']['street_publications']==1
    assert len(r['scopes']['country'])==2
    topic=r['scopes']['globe']['Globo']['topics'][0]
    assert topic['copy_links']==1 and topic['independent_confirmation_established'] is False
    assert topic['angle_analysis'] is None
    assert r['reference_without_match']==[]
def test_missing_matches_are_observations_not_proof_of_absence():
    r=report([article(1),article(2,True)])
    assert r['reference_without_match']==[2]
    assert r['scopes']['globe']['Globo']['topics'][0]['status']=='no_match_observed'
    assert r['method']['absence_is_not_proof_of_noncoverage']
def test_self_edges_rejected():
    with pytest.raises(ValueError):report([article(1,True)],[dict(street_id=1,reference_id=1)])
def test_manifest_changes_invalidate_report_key():
    assert report_key('c',REFS)!=report_key('c',REFS+[dict(name='Other')])
def test_subdomain_accepted_but_lookalike_domain_not():
    a=article(1);a['url']='https://news.ref.example/one'
    assert reference_names(a,REFS)==['Ref']
    a['url']='https://fakeref.example/one'
    assert reference_names(a,REFS)==[]
def test_reddit_only_designated_community():
    ref=[dict(name='Reddit',site_url='https://reddit.com/r/technology',rss_url='https://reddit.com/r/technology/.rss')]
    a=article(1);a['url']='https://reddit.com/r/other/post'
    assert reference_names(a,ref)==[]
    a['sources'][0]['rss_url']=ref[0]['rss_url']
    assert reference_names(a,ref)==['Reddit']
def test_missing_bodies_and_numeric_conflicts_cannot_match():
    np=pytest.importorskip('numpy')
    from reference_compare.main import match
    a,b=article(1),article(2,True)
    vec=np.ones((2,1),dtype=np.float32)
    a.update(text_basis='title_summary',lead='')
    assert match([a,b],vec,vec,REFS)==[]
    a=article(1);a['title']='Starship 12 launch';b['title']='Starship 15 launch'
    assert match([a,b],vec,vec,REFS)==[]
def test_duplicate_match_records_both_article_ids():
    np=pytest.importorskip('numpy')
    from reference_compare.main import match
    a,b=article(1),article(2,True)
    a['body_hash']=b['body_hash']='same'
    vec=np.ones((2,1),dtype=np.float32)
    pairs=match([a,b],vec,vec,REFS)
    assert len(pairs)==1 and pairs[0]['decision']=='duplicate'
    assert pairs[0]['street_id']==1 and pairs[0]['reference_id']==2
