import hashlib
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from trends.core import continent, publisher

TZ = ZoneInfo('America/Sao_Paulo')
VERSION = 'daily-v2-title-lead-shared-body-guard'
LEAD_CHARS = 1200


def bounds(day):
    day = date.fromisoformat(day) if isinstance(day, str) else day
    start = datetime.combine(day, time.min, TZ)
    end = datetime.combine(day + timedelta(days=1), time.min, TZ)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def normalize(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text or '').casefold()))


def fingerprint(text):
    return hashlib.sha256(normalize(text).encode()).hexdigest()


def chargrams(text):
    text = normalize(text)
    return {text[i:i+5] for i in range(max(0, len(text)-4))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def numeric_conflict(a, b):
    # Different explicit quantities/model numbers are evidence against a copy.
    na = set(re.findall(r'\d+(?:[.,]\d+)*', unicodedata.normalize('NFKC', a)))
    nb = set(re.findall(r'\d+(?:[.,]\d+)*', unicodedata.normalize('NFKC', b)))
    return bool(na and nb and na != nb)


def compare(a, b, title_similarity, lead_similarity):
    ta, tb = normalize(a['title']), normalize(b['title'])
    la, lb = normalize(a.get('lead')), normalize(b.get('lead'))
    body = a.get('text_basis') in ('extracted_page', 'publisher_rss') and b.get('text_basis') in ('extracted_page', 'publisher_rss')
    enough = body and min(len(la), len(lb)) >= 200
    lexical = jaccard(a['_grams'] if '_grams' in a else chargrams(la), b['_grams'] if '_grams' in b else chargrams(lb))
    score = .4 * title_similarity + .6 * lead_similarity
    evidence = {'title_similarity': round(title_similarity, 5), 'lead_similarity': round(lead_similarity, 5),
                'lead_jaccard': round(lexical, 5), 'similarity_score': round(score, 5),
                'probability': None, 'score_calibrated': False}
    if numeric_conflict(ta, tb):
        return dict(evidence, decision='distinct', reason='different_explicit_numbers')
    if enough and a.get('body_hash') and a.get('body_hash') == b.get('body_hash'):
        if title_similarity>=.70 or ta==tb:
            return dict(evidence, decision='duplicate', reason='identical_normalized_body_compatible_title')
        return dict(evidence, decision='distinct', reason='shared_body_conflicting_titles')
    if enough and lexical >= .88 and (ta == tb or title_similarity >= .78):
        return dict(evidence, decision='duplicate', reason='near_identical_lead_and_compatible_title')
    # Semantic equivalence alone cannot prove that two publishers copied a text.
    if enough and title_similarity >= .90 and lead_similarity >= .93:
        return dict(evidence, decision='possible_republication', reason='semantic_match_requires_review')
    if ta and ta == tb:
        return dict(evidence, decision='possible_republication', reason='same_title_insufficient_body_evidence')
    if title_similarity >= .80 and lead_similarity >= .80:
        return dict(evidence, decision='same_subject_candidate', reason='similar_subject_not_duplicate')
    return dict(evidence, decision='distinct', reason='insufficient_evidence')


def candidate_pairs(articles, title_vectors, lead_vectors):
    import numpy as np
    from sklearn.neighbors import NearestNeighbors
    from datasketch import MinHash, MinHashLSH
    if len(articles) < 2:
        return []
    # Candidate generation is bounded and approximate; it is not a recall guarantee.
    combined = np.concatenate([title_vectors, lead_vectors], axis=1)
    neighbors = NearestNeighbors(n_neighbors=min(33, len(articles)), metric='cosine', n_jobs=2).fit(combined)
    pairs = set()
    for start in range(0, len(articles), 256):
        distances, indices = neighbors.kneighbors(combined[start:start+256])
        for offset, (ds, js) in enumerate(zip(distances, indices)):
            i = start + offset
            pairs.update(tuple(sorted((i, int(j)))) for d, j in zip(ds, js) if i != j and d <= .30)
    lsh = MinHashLSH(threshold=.75, num_perm=64)
    hashes = defaultdict(list)
    titles = defaultdict(list)
    for i, a in enumerate(articles):
        a['_grams'] = chargrams(a.get('lead', ''))
        if len(normalize(a.get('lead'))) >= 200:
            mh = MinHash(num_perm=64)
            for token in sorted(a['_grams']):
                mh.update(token.encode())
            for j in lsh.query(mh):
                pairs.add((int(j), i))
            lsh.insert(str(i), mh)
        if a.get('body_hash'):
            for j in hashes[a['body_hash']]:
                pairs.add((j, i))
            hashes[a['body_hash']].append(i)
        title = normalize(a['title'])
        for j in titles[title]:
            pairs.add((j, i))
        titles[title].append(i)
    return sorted(pairs)


def group_copies(articles, title_vectors, lead_vectors, pairs=None):
    import numpy as np
    # Consent/paywall/navigation bodies can be identical across unrelated pages.
    hashes=defaultdict(list)
    for i,a in enumerate(articles):
        if a.get('body_hash'):hashes[a['body_hash']].append(i)
    for indices in hashes.values():
        if len(indices)<3:continue
        titles=np.asarray(title_vectors)[indices]
        if float((titles@titles.T).min())<.55:
            for i in indices:
                articles[i].update(text_basis='untrusted_body',body_error='shared_body_with_divergent_titles',body_hash=None,lead='')
                lead_vectors[i]=0
    pairs = candidate_pairs(articles, title_vectors, lead_vectors) if pairs is None else pairs
    from collections import Counter
    from trends.clustering import anchors, compatible
    frequency=Counter(x for a in articles for x in anchors(a['title']))
    evidence, accepted, topic_edges = [], {}, {}
    for i, j in pairs:
        result = compare(articles[i], articles[j], float(np.dot(title_vectors[i], title_vectors[j])), float(np.dot(lead_vectors[i], lead_vectors[j])))
        if result['decision'] != 'distinct':
            evidence.append(dict(result, article_a=articles[i]['id'], article_b=articles[j]['id']))
        if result['decision'] == 'duplicate':
            accepted[(min(i, j), max(i, j))] = result['similarity_score']
        if result['decision']=='duplicate' or (
            result['decision'] in ('possible_republication','same_subject_candidate')
            and result['title_similarity']>=.80 and result['lead_similarity']>=.80
            and compatible(articles[i]['title'],articles[j]['title'],result['similarity_score'],
                           frequency=frequency,rare_limit=max(4,int(len(articles)*.001)))):
            topic_edges[(min(i,j),max(i,j))]=result['similarity_score']
    # All members must agree: never merge A~B~C when A and C differ.
    groups = {i: {i} for i in range(len(articles))}
    owner = list(range(len(articles)))
    for (i, j), score in sorted(accepted.items(), key=lambda x: (-x[1], x[0])):
        left, right = owner[i], owner[j]
        if left == right:
            continue
        if not all((min(a, b), max(a, b)) in accepted for a in groups[left] for b in groups[right]):
            continue
        merged = groups.pop(right)
        groups[left].update(merged)
        for index in merged:
            owner[index] = left
    for indices in groups.values():
        identity = '|'.join(sorted(str(articles[i]['id']) for i in indices))
        family = 'copy-' + hashlib.sha256((VERSION + identity).encode()).hexdigest()[:20]
        for i in indices:
            articles[i]['copy_family'] = family
    topic_groups={i:{i} for i in range(len(articles))}
    topic_owner=list(range(len(articles)))
    for (i,j),score in sorted(topic_edges.items(),key=lambda x:(-x[1],x[0])):
        left,right=topic_owner[i],topic_owner[j]
        if left==right:continue
        if not all((min(a,b),max(a,b)) in topic_edges for a in topic_groups[left] for b in topic_groups[right]):continue
        merged=topic_groups.pop(right);topic_groups[left].update(merged)
        for index in merged:topic_owner[index]=left
    for indices in topic_groups.values():
        identity='|'.join(sorted(str(articles[i]['id']) for i in indices))
        family='subject-'+hashlib.sha256((VERSION+identity).encode()).hexdigest()[:20]
        for i in indices:articles[i]['subject_family']=family
    return evidence


def accounting(articles, observations, scope, monitored_sources=()):
    def places(source):
        return 'Globo' if scope == 'globe' else source['country'] if scope == 'country' else continent(source)
    grouped = defaultdict(list)
    seen_observations = defaultdict(set)
    for s in monitored_sources:
        grouped[places(s)]
    if scope == 'globe':
        grouped['Globo']
    for a in articles:
        for place in {places(s) for s in a['sources']}:
            grouped[place].append(a)
    for o in observations:
        seen_observations[places(o['source'])].add((str(o['slot']), o['feed_id'], o['article_id']))
    result = {}
    for place in sorted(set(grouped) | set(seen_observations)):
        rows = grouped[place]
        families = defaultdict(list)
        for a in rows:
            families[a['copy_family']].append(a)
        ranks = []
        for family, copies in families.items():
            ids = {a['id'] for a in copies}
            sources = [s for a in copies for s in a['sources'] if places(s) == place]
            sightings = {o for o in seen_observations[place] if o[2] in ids}
            ranks.append({'family_id': family, 'label': copies[0]['title'], 'publications': len(ids),
                          'extra_copies_estimated': len(ids)-1, 'publishers': len({publisher(s) for s in sources}),
                          'feed_sightings': len(sightings), 'collection_slots': sorted({o[0] for o in sightings}),
                          'evidence': [{'id': a['id'], 'title': a['title'], 'url': a['url']} for a in copies]})
        result[place] = {'publications': len({a['id'] for a in rows}), 'distinct_texts_estimated': len(families),
                         'extra_copies_estimated': sum(len(v)-1 for v in families.values()),
                         'feed_sightings_all_articles': len(seen_observations[place]),
                         'publishers': len({publisher(s) for a in rows for s in a['sources'] if places(s) == place}),
                         'ranking': sorted(ranks, key=lambda x: (-x['publications'], -x['publishers'], x['family_id']))}
        subjects=defaultdict(list)
        for a in rows:subjects[a.get('subject_family',a['copy_family'])].append(a)
        result[place]['subjects_estimated']=len(subjects)
        result[place]['subject_ranking']=sorted([
            {'subject_id':key,'label':items[0]['title'],'publications':len({a['id'] for a in items}),
             'distinct_texts_estimated':len({a['copy_family'] for a in items}),
             'publishers':len({publisher(s) for a in items for s in a['sources'] if places(s)==place}),
             'evidence':[{'id':a['id'],'title':a['title'],'url':a['url']} for a in items]}
            for key,items in subjects.items()],key=lambda r:(-r['publishers'],-r['publications'],r['subject_id']))
        assert result[place]['publications'] == result[place]['distinct_texts_estimated'] + result[place]['extra_copies_estimated']
    return result
