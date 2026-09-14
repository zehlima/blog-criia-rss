"""Prime technology sources through the existing storage/checkpoint path, under its lock."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from .technology15 import manifest
from .storage import connect, seed
from .main import sources, slot_for

def main():
    feeds=manifest();db,s3=connect()
    try:
        if not db.execute('SELECT pg_try_advisory_lock(67426001) locked').fetchone()['locked']:
            print('TECHNOLOGY15_INGEST deferred: existing global collector holds the lock')
            return 0
        slot=slot_for(datetime.now(timezone.utc));seed(db,feeds)
        sources(db,s3,slot,feeds,time.monotonic()+300)
        rows=db.execute('''SELECT f.name,f.rss_url,coalesce(r.status,'not_attempted') status,
            r.items,r.error,(SELECT count(*) FROM news_article_feeds af WHERE af.feed_id=f.id) stored_articles
            FROM news_feeds f LEFT JOIN news_feed_runs r ON r.feed_id=f.id AND r.slot=%s
            WHERE f.rss_url=ANY(%s) ORDER BY f.name''',(slot,[f['rss_url'] for f in feeds])).fetchall()
        report={'slot':slot.isoformat(),'sources':rows,'total':len(rows),
                'ok':sum(r['status']=='ok' for r in rows),
                'note':'Feed metadata persisted; complete page extraction continues in the global collector.'}
        target=Path('reports/technology15');target.mkdir(parents=True,exist_ok=True)
        (target/'ingestion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('TECHNOLOGY15_INGEST '+json.dumps(report,ensure_ascii=False),flush=True)
        return 0 if report['ok']==15 else 1
    finally:db.close()

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('TECHNOLOGY15_INGEST_ERROR '+type(exc).__name__,flush=True)
        raise SystemExit(1)
