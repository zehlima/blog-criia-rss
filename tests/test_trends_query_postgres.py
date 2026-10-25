"""Corpus equality in isolated PostgreSQL; no production, R2 or model calls."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import runpy
import os

import pytest
from trends.main import all_articles
from trends.core import in_window
from test_discovery_postgres import db  # existing isolated PostgreSQL fixture

pytestmark = pytest.mark.skipif(not os.getenv('BORIS_PGLITE_MODULE'),
                              reason='Requires isolated PostgreSQL via PGlite')
ROOT = Path(__file__).resolve().parents[1]
LEGACY = runpy.run_path(str(ROOT/'tests/fixtures/trends_all_articles_9bf3783.py'))['all_articles']
CUTOFF = datetime(2026, 10, 24, 19, 25, tzinfo=timezone.utc)


def feeds(db, count=3):
    db.execute("""INSERT INTO news_feeds(rss_url,name,region,country,site_url,justification)
      SELECT 'https://fixture-'||g||'.example/rss','Fixture '||g,'Region','Country',
      'https://fixture.example','isolated' FROM generate_series(1,%s) g""", (count,))
    return [r['rss_url'] for r in db.execute('SELECT rss_url FROM news_feeds ORDER BY id').fetchall()]


@pytest.mark.parametrize('page_size', [1, 7, 1000])
def test_full_row_and_source_equivalence_at_window_boundaries(db, page_size):
    urls = feeds(db)
    cases = [(CUTOFF-timedelta(hours=24), CUTOFF, 'pending'),
             (CUTOFF, CUTOFF, 'pending'), (None, CUTOFF, 'pending'),
             (CUTOFF-timedelta(hours=24, milliseconds=1), CUTOFF, 'pending'),
             (CUTOFF+timedelta(milliseconds=1), CUTOFF, 'pending'),
             (CUTOFF, CUTOFF+timedelta(milliseconds=1), 'pending'),
             (CUTOFF, CUTOFF, 'invalid_reference')]
    cases += [(CUTOFF-timedelta(hours=2), CUTOFF, 'extracted')]*11
    for n, (published, seen, status) in enumerate(cases):
        row = db.execute("""INSERT INTO news_articles(url,title,summary,published_at,first_seen_at,metadata_hash,content_status)
          VALUES(%s,%s,'fixture summary',%s,%s,'fixture',%s) RETURNING id""",
          (f'https://fixture.example/{n}', f'Fixture {n}', published, seen, status)).fetchone()
        for feed_id in (3, 2, 1):
            db.execute('INSERT INTO news_article_feeds(article_id,feed_id,in_latest) VALUES(%s,%s,false)', (row['id'], feed_id))
    expected = [r for r in LEGACY(db, CUTOFF, urls[:2]) if in_window(r, CUTOFF)]
    actual = all_articles(db, CUTOFF, urls[:2], page_size=page_size)
    assert actual == expected and len(actual) == 14
    assert len({r['id'] for r in actual}) == len(actual)
    assert all([s['id'] for s in r['sources']] == [1, 2] for r in actual)
    assert all_articles(db, CUTOFF, []) == []


def test_large_history_matches_legacy_window_without_migration_005(db):
    count, recent = 100000, 10000
    urls = feeds(db, 678)
    db.execute("""INSERT INTO news_articles(url,title,summary,published_at,first_seen_at,metadata_hash)
      SELECT 'https://fixture.example/article/'||g,'Article '||g,'fixture summary',
        CASE WHEN g<=%s THEN '2020-01-01'::timestamptz ELSE %s::timestamptz END,
        CASE WHEN g<=%s THEN '2020-01-01'::timestamptz ELSE %s::timestamptz END,'fixture'
      FROM generate_series(1,%s) g""", (count-recent, CUTOFF, count-recent, CUTOFF, count))
    db.execute("""INSERT INTO news_article_feeds(article_id,feed_id,in_latest)
      SELECT id,1+id%678,false FROM news_articles UNION ALL
      SELECT id,1+(id+1)%678,true FROM news_articles""")
    db.exec('ANALYZE')
    assert db.execute("SELECT to_regclass('public.news_collection_executions') AS ledger").fetchone()['ledger'] is None
    old = LEGACY(db, CUTOFF, urls)
    assert len(old) == count
    expected = [row for row in old if in_window(row, CUTOFF)]
    assert all_articles(db, CUTOFF, urls) == expected
    assert len(expected) == recent
