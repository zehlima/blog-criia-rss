"""Pure contract and aggregation for daily reference comparison."""
import hashlib
import json
from collections import defaultdict
from urllib.parse import urlsplit
from trends.core import continent

VERSION='reference15-v1'

def host(url):return (urlsplit(url or '').hostname or '').lower().removeprefix('www.')
def report_key(closure_id,refs):
    digest=hashlib.sha256(json.dumps(refs,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:12]
    return f'reference-comparison/{VERSION}/{closure_id}-{digest}.json.gz'

def reference_names(article,refs):
    result=set()
    for ref in refs:
        domain=host(ref['site_url'])
        # Reddit is a specific community, never every reddit.com publication.
        if domain=='reddit.com':
            if any(s.get('rss_url')==ref['rss_url'] for s in article['sources']):result.add(ref['name'])
            continue
        def belongs(url):return host(url)==domain or host(url).endswith('.'+domain)
        if belongs(article.get('url')) or any(s.get('rss_url')==ref['rss_url'] or belongs(s.get('site_url')) for s in article['sources']):result.add(ref['name'])
    return sorted(result)

def partition(articles,refs):
    street,reference=[],[]
    for original in articles:
        a=dict(original);a['reference_names']=reference_names(a,refs)
        (reference if a['reference_names'] else street).append(a)
    assert not {a['id'] for a in street}&{a['id'] for a in reference}
    return street,reference

def family(a):return a.get('copy_family') or str(a['id'])
def subject(a):return a.get('subject_family') or family(a)
def locations(a,scope):
    return {'Globo'} if scope=='globe' else {s['country'] if scope=='country' else continent(s) for s in a['sources']}

def aggregate(street,reference,matches,scope):
    refs={a['id']:a for a in reference};edges=defaultdict(list)
    for edge in matches:edges[edge['street_id']].append(edge)
    places=defaultdict(list)
    for a in street:
        for place in locations(a,scope):places[place].append(a)
    if scope=='globe':places['Globo']
    ref_total=len({family(a) for a in reference})
    result={}
    for place,articles in sorted(places.items()):
        groups=defaultdict(list)
        for a in articles:groups[subject(a)].append(a)
        total=len({family(a) for a in articles});rows=[]
        for sid,items in groups.items():
            pairs=[p for a in items for p in edges[a['id']]]
            rids=sorted({p['reference_id'] for p in pairs})
            base_count=len({family(a) for a in items})
            ref_count=len({family(refs[rid]) for rid in rids})
            copied={p['reference_id'] for p in pairs if p['decision']=='duplicate'}
            rows.append({'subject_id':sid,'label':items[0]['title'],'street_article_ids':[a['id'] for a in items],
                'reference_article_ids':rids,'reference_sources':sorted({name for rid in rids for name in refs[rid]['reference_names']}),
                'status':'correspondence_found' if rids else 'no_match_observed',
                'street_distinct_texts':base_count,'reference_distinct_texts':ref_count,
                'street_share':round(base_count/total,6) if total else 0,
                'reference_share':round(ref_count/ref_total,6) if ref_total else 0,
                'share_difference_pp':round(100*(base_count/total-ref_count/ref_total),3) if total and ref_total else None,
                'copy_links':len(copied),'independent_confirmation_established':False,'angle_analysis':None,
                'evidence':pairs})
        rows.sort(key=lambda r:(-len(r['reference_sources']),-r['street_distinct_texts'],r['subject_id']))
        result[place]={'street_publications':len(articles),'street_distinct_texts':total,'reference_distinct_texts':ref_total,
            'topics':rows,'matched_topics':sum(r['status']=='correspondence_found' for r in rows)}
    return result

def build(closure,articles,refs,matches,source_coverage):
    street,reference=partition(articles,refs)
    street_ids={a['id'] for a in street};reference_ids={a['id'] for a in reference}
    if any(p['street_id'] not in street_ids or p['reference_id'] not in reference_ids for p in matches):raise ValueError('cross_side_contract_violation')
    matched={p['reference_id'] for p in matches}
    return {'schema_version':1,'version':VERSION,'closure_id':closure['id'],'day':str(closure['day']),
        'cutoff':str(closure['cutoff']),'mode':'closed_day_comparison','reference_manifest':refs,
        'source_coverage':source_coverage,'counts':{'street_articles':len(street),'reference_articles':len(reference),
            'reference_sources_with_articles':len({n for a in reference for n in a['reference_names']}),'matched_pairs':len(matches)},
        'method':{'basis':'title_and_opening_text','thresholds':{'title_similarity':.80,'lead_similarity':.80},
            'candidate_search':'all_cross_side_pairs_above_title_and_lead_thresholds','probabilities_calibrated':False,
            'same_url_self_confirmation_excluded':True,'copy_is_not_independent_confirmation':True,
            'absence_is_not_proof_of_noncoverage':True,'editorial_validation':'pending',
            'scope':'Editorial geography of street sources; compared with the same 15 worldwide references in each scope.',
            'frequency_note':'Shares count estimated distinct texts; reference topics may match multiple street groups and are not additive. Denominators have different editorial breadth.',
            'reference_dates':'Same civil day and frozen collection cutoff as the source closure.',
            'angles':'Not inferred in this version; semantic similarity does not establish differences of editorial stance.'},
        'scopes':{scope:aggregate(street,reference,matches,scope) for scope in ('country','continent','globe')},
        'reference_without_match':[a['id'] for a in reference if a['id'] not in matched],
        'articles':[{k:a.get(k) for k in ('id','title','url','sources','reference_names','text_basis','body_error')} for a in street+reference]}
