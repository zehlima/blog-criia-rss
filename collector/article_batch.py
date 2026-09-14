"""Batch persistence: archive first, then commit successful versions and checkpoints."""
from datetime import datetime,timedelta,timezone
from psycopg.types.json import Jsonb
from .storage import archive
from .extract import digest


def outcome(a,result,error,slot):
    now=datetime.now(timezone.utc)
    row={k:a.get(k) for k in ('id','content_hash','content_key','content_chars','content_status','extracted_at','final_url','page_etag','page_last_modified')}
    row.update(page_checked_at=now,write_version=False,bytes_written=0)
    if error:
        row.update(last_error=error,attempts=a['attempts']+1,
           content_status='unavailable' if not a['content_key'] else a['content_status'],
           next_attempt_at=now+timedelta(seconds=min(86400,3600*2**min(a['attempts'],5))))
    else:
        status,h,text,url,stored=result
        if text is not None:
            content_hash,key,size=stored
            row.update(content_hash=content_hash,content_key=key,content_chars=len(text),
               extracted_at=now,write_version=True,bytes_written=size)
        row.update(content_status='rss_content' if h.get('X-Content-Basis')=='publisher_rss' else 'extracted',last_error=None,attempts=0,final_url=url,
           page_etag=h.get('ETag',a['page_etag'] if status==304 else None),
           page_last_modified=h.get('Last-Modified',a['page_last_modified'] if status==304 else None),
           next_attempt_at=max(slot+timedelta(hours=6),now+timedelta(hours=1)))
    return row


def preserve(s3,a,result):
    status,h,text,url=result
    stored=None
    if text is not None:
        hashed=digest(text)
        stored=archive(s3,a['url'],text) if hashed!=a['content_hash'] else (hashed,a['content_key'],0)
    return status,h,text,url,stored


DEFINITION='''id bigint,content_hash text,content_key text,content_chars integer,content_status text,
 extracted_at timestamptz,final_url text,page_etag text,page_last_modified text,page_checked_at timestamptz,
 write_version boolean,last_error text,attempts integer,next_attempt_at timestamptz'''


def persist(db,rows):
    serialized=[{k:v.isoformat() if isinstance(v,datetime) else v for k,v in row.items()} for row in rows]
    data=Jsonb(serialized)
    with db.transaction():
        db.execute('''INSERT INTO news_article_versions(article_id,content_hash,content_key)
          SELECT id,content_hash,content_key FROM jsonb_to_recordset(%s::jsonb) AS x('''+DEFINITION+''')
          WHERE write_version AND content_key IS NOT NULL ON CONFLICT DO NOTHING''',(data,))
        db.execute('''UPDATE news_articles a SET content_hash=x.content_hash,content_key=x.content_key,
          content_chars=x.content_chars,content_status=x.content_status,extracted_at=x.extracted_at,
          final_url=x.final_url,page_etag=x.page_etag,page_last_modified=x.page_last_modified,
          page_checked_at=x.page_checked_at,last_error=x.last_error,attempts=x.attempts,next_attempt_at=x.next_attempt_at
          FROM jsonb_to_recordset(%s::jsonb) AS x('''+DEFINITION+''') WHERE a.id=x.id''',(data,))
    return sum(r['bytes_written'] for r in rows)
