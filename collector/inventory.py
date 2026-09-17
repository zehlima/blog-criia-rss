"""Static sources plus approved discoveries, frozen for each collection window.

BORIS_DYNAMIC_INVENTORY=1 is an explicit, post-migration rollout gate. When it is
off, existing snapshots still apply; no new admissions or snapshots are added.
Before migration only a schema-presence lookup is needed for legacy operation.
Database errors propagate: an outage is not an empty inventory. Only the
collector freezes new windows; readers never rewrite them.
"""
import json
import os
from .discovery_settings import enabled
from datetime import timedelta
from pathlib import Path


def _validate(data):
    if (not isinstance(data,list) or not data or
        any(not isinstance(f,dict) or not isinstance(f.get('rss_url'),str) or not f['rss_url'].strip() for f in data) or
        len({f['rss_url'] for f in data})!=len(data)):
        raise ValueError('invalid_inventory')
    return data


def feeds():
    data=json.loads((Path(__file__).resolve().parent.parent/'data/feeds.json').read_text())
    return _validate(data)


def dynamic_enabled():
    return enabled('BORIS_DYNAMIC_INVENTORY')


def _slot(slot):
    if slot is None or slot.tzinfo is None or slot.utcoffset() is None:
        raise ValueError('invalid_inventory_slot')
    return slot


def _capture_schema_exists(db):
    # A missing migration is compatible with the disabled rollout. Connection,
    # permission and SQL errors are not: do not catch them as "no inventory".
    return db.execute("SELECT to_regclass('public.news_collection_inventory') IS NOT NULL AS present").fetchone()['present']


def _merge(base,extra):
    # A discovered URL already in the curated manifest must not replace its
    # approved geography/name or increase the expected collection count.
    result={f['rss_url']:f for f in _validate(base)}
    for feed in extra:
        result.setdefault(feed['rss_url'],feed)
    return _validate(list(result.values()))


def _captured(db,slot,cutoff=None):
    row=db.execute('''SELECT feeds FROM news_collection_inventory WHERE slot=%s
      AND (%s::timestamptz IS NULL OR captured_at<=%s)''',(slot,cutoff,cutoff)).fetchone()
    if row:
        return _validate(row['feeds']),'snapshot'
    # Existing attempts already contain their complete inventory. This preserves
    # a pre-migration window when a recovery crosses the rollout boundary.
    row=db.execute('''SELECT feeds FROM news_collection_attempts WHERE slot=%s
      AND (%s::timestamptz IS NULL OR finished_at<=%s)
      ORDER BY finished_at,id LIMIT 1''',(slot,cutoff,cutoff)).fetchone()
    return (_validate(row['feeds']),'legacy_attempt') if row else (None,None)


def for_slot(db,slot,*,freeze=False,base_feeds=None):
    """Read the exact window inventory; collector may capture a new one.

    A read without a previous capture returns the prospective inventory for
    preflight. It does not insert a historical snapshot or hide database errors.
    Approved additions are effective only at or before the requested boundary.
    """
    base=feeds() if base_feeds is None else _validate(base_feeds)
    if not dynamic_enabled():
        if _capture_schema_exists(db):
            selected,_=_captured(db,_slot(slot))
            return selected if selected is not None else base
        return base
    _slot(slot)
    selected,basis=_captured(db,slot)
    if basis=='snapshot':
        return selected
    if selected is None:
        extra=db.execute('''SELECT f.id,f.rss_url,f.name,f.region,f.country,f.site_url,f.justification
          FROM news_feed_admissions a JOIN news_feeds f ON f.id=a.feed_id
          WHERE a.effective_at<=%s AND a.admitted_at<=%s
            AND (a.revoked_at IS NULL OR a.revoked_at>%s)
          ORDER BY a.effective_at,f.id''',(slot,slot,slot)).fetchall()
        selected=_merge(base,extra)
    if not freeze:
        return selected
    from psycopg.types.json import Jsonb
    # DO NOTHING, then reread: a concurrent capture always wins intact. There is
    # no update path that could enlarge a running/recovering window.
    db.execute('''INSERT INTO news_collection_inventory(slot,feeds)
      VALUES(%s,%s) ON CONFLICT(slot) DO NOTHING''',(slot,Jsonb(selected)))
    row=db.execute('SELECT feeds FROM news_collection_inventory WHERE slot=%s',(slot,)).fetchone()
    if row is None:
        raise RuntimeError('inventory_capture_missing')
    return _validate(row['feeds'])


def attempt_feeds(attempt):
    """Collection attempts are authoritative even if the rollout gate changes."""
    return _validate(attempt['feeds'])


def day_inventory(db,start,end,cutoff,closing_feeds):
    """Count each day's four actual inventories rather than 4 x the latest size.

    Missing historical windows are explicitly incomplete, and are never written
    retrospectively. Their expected count uses the unchanged static manifest.
    """
    closing_feeds=_validate(closing_feeds)
    if not dynamic_enabled() and not _capture_schema_exists(db):
        return {'feeds':closing_feeds,'expected_batches':4*len(closing_feeds),
                'complete':True,'slots':[],'basis':'legacy_closing_inventory'}
    _slot(start);_slot(end)
    selected=[];windows=[];slot=start
    while slot<end:
        captured,basis=_captured(db,slot,cutoff)
        rows=captured if captured is not None else feeds()
        selected.extend(rows)
        windows.append({'slot':slot.isoformat(),'feeds':len(rows),
                        'basis':basis or 'missing_legacy_baseline'})
        slot+=timedelta(hours=6)
    # Include the collector's closing source inventory in the corpus, retaining
    # legacy treatment of delayed articles collected after midnight. It is not
    # used to inflate the preceding day's expected observation count.
    merged=_merge(closing_feeds,selected)
    return {'feeds':merged,'expected_batches':sum(s['feeds'] for s in windows),
            'complete':all(s['basis']!='missing_legacy_baseline' for s in windows),
            'slots':windows,'basis':'per_collection_window'}


def urls(db=None,slot=None):
    selected=feeds() if db is None else for_slot(db,slot)
    return [f['rss_url'] for f in selected]
