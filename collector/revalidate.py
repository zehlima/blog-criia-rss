"""Read-only production-parser validation of the explorer's proposed corrections."""
import csv
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from .extract import fetch_source

ROOT = Path('research/rss-review-2026-09-14')

def inventory():
    rows = list(csv.DictReader((ROOT/'revision.csv').open(encoding='utf-8-sig'), delimiter=';'))
    old = json.loads(Path('data/feeds.json').read_text())
    proposed = json.loads((ROOT/'proposed-feeds.json').read_text())
    by_old = {f['rss_url']: f for f in old}
    by_new = {f['rss_url']: f for f in proposed}
    assert len(rows) == 121 and len(proposed) == len(by_new) == 600
    assert len({r['RSS_anterior'] for r in rows}) == 121
    for r in rows:
        assert r['RSS_revisado'] in by_new
        assert r['RSS_anterior'] in by_old or r['RSS_revisado'] in by_old
        assert by_new[r['RSS_revisado']]['name'] == r['Veiculo_revisado']
    changed = {r['RSS_anterior'] for r in rows}
    assert all(f == by_new.get(f['rss_url']) for f in old if f['rss_url'] not in changed and f['rss_url'] in by_new)
    return rows

def check(url):
    try:
        status, _, articles = fetch_source({'rss_url': url})
        return {'ok': status == 200 and bool(articles), 'http': status, 'items': len(articles), 'error': '' if articles else 'empty_feed'}
    except Exception as exc:
        # Feed URLs are public; exception class/message contain no credentials.
        return {'ok': False, 'items': 0, 'error': type(exc).__name__ + ': ' + str(exc)[:300]}

def run():
    rows = inventory()
    urls = sorted({r[k] for r in rows for k in ('RSS_anterior', 'RSS_revisado')})
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(urls, pool.map(check, urls)))
    output = []
    for row in rows:
        original, candidate = results[row['RSS_anterior']], results[row['RSS_revisado']]
        output.append({**row, 'production_original': original, 'production_candidate': candidate,
                       'decision': 'candidate_passed_pending_application' if candidate['ok'] else 'keep_pending_investigation'})
    count = sum(r['production_candidate']['ok'] for r in output)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'run_id': os.getenv('GITHUB_RUN_ID'),
              'candidate_ok': count, 'candidate_failed': len(rows)-count,
              'database_changed': False, 'rows': output}
    Path('reports').mkdir(exist_ok=True)
    Path('reports/rss-revalidation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    with Path('reports/rss-revalidation.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        flat = [{**{k: v for k,v in r.items() if not isinstance(v, dict)},
                 'original_ok': r['production_original']['ok'], 'candidate_ok': r['production_candidate']['ok'],
                 'candidate_items': r['production_candidate']['items'], 'candidate_error': r['production_candidate']['error']} for r in output]
        writer = csv.DictWriter(stream, fieldnames=list(flat[0])); writer.writeheader(); writer.writerows(flat)
    summary = f'# Revalidação RSS\n\n{count}/121 candidatos aprovados pelo parser de produção; {121-count} com falha.\n\nBanco e inventário ativo ainda não alterados. Relatório detalhado no artefato desta execução.\n'
    Path('reports/rss-revalidation.md').write_text(summary)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream: stream.write(summary)
    print(summary, flush=True)
    for r in output:
        print(json.dumps({'id':r['ID_relatorio'],'url':r['RSS_revisado'],**r['production_candidate']}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    run()
