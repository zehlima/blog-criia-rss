import gzip
import os
from urllib.parse import urlsplit, unquote, quote
import boto3
import psycopg
from botocore.config import Config
from psycopg.rows import dict_row
from .extract import digest

REQUIRED=['R2_ENDPOINT_URL','R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY','R2_BUCKET']

def database_connection():
    """Senha separada evita erros com @, :, / e outros caracteres na URI."""
    if os.getenv('DATABASE_PASSWORD'):
        return psycopg.connect(
            host=os.environ['DATABASE_HOST'], port=5432,
            user=os.environ['DATABASE_USER'], dbname='postgres',
            password=os.environ['DATABASE_PASSWORD'],
            sslmode='require', connect_timeout=15,
            row_factory=dict_row, autocommit=True)
    overrides={'host':os.environ['DATABASE_HOST']} if os.getenv('DATABASE_HOST') else {}
    uri=os.environ['DATABASE_URL']
    parsed=urlsplit(uri)
    if parsed.scheme in ('postgres','postgresql') and parsed.password is not None:
        # Normaliza @ literal na senha antes de entregar a URI ao libpq.
        user=quote(unquote(parsed.username or ''),safe='')
        password=quote(unquote(parsed.password),safe='')
        host=parsed.hostname or ''
        if ':' in host:host='['+host+']'
        authority=f'{user}:{password}@{host}'
        if parsed.port is not None:authority+=f':{parsed.port}'
        uri=parsed._replace(netloc=authority).geturl()
    return psycopg.connect(uri,**overrides,sslmode='require',
                           connect_timeout=15,row_factory=dict_row,autocommit=True)

def connect():
    missing=[k for k in REQUIRED if not os.getenv(k)]
    if missing:raise ValueError('Secrets ausentes: '+', '.join(missing))
    db=database_connection()
    s3=boto3.client('s3',endpoint_url=os.environ['R2_ENDPOINT_URL'],region_name='auto',
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        config=Config(connect_timeout=10,read_timeout=20,retries={'max_attempts':2},
            request_checksum_calculation='when_required',response_checksum_validation='when_required'))
    return db,s3

def archive(s3,url,text):
    h=digest(text)
    key=f'articles/{digest(url)}/{h}.txt.gz'
    data=gzip.compress(text.encode('utf-8'),mtime=0)
    s3.put_object(Bucket=os.environ['R2_BUCKET'],Key=key,Body=data,
                  ContentType='text/plain; charset=utf-8',ContentEncoding='gzip')
    return h,key,len(data)

def seed(db,feeds):
    from psycopg.types.json import Jsonb
    # One round trip, preserving all historical source identities.
    db.execute("""INSERT INTO news_feeds(rss_url,name,region,country,site_url,justification)
      SELECT rss_url,name,region,country,site_url,justification
      FROM jsonb_to_recordset(%s::jsonb) AS f(rss_url text,name text,region text,country text,site_url text,justification text)
      ON CONFLICT(rss_url) DO NOTHING""",(Jsonb(feeds),))

def save_entry(db,feed_id,a):
    row=db.execute('''INSERT INTO news_articles(url,title,summary,published_at,source_updated_at,metadata_hash,rss_content_key)
      VALUES(%(url)s,%(title)s,%(summary)s,%(published_at)s,%(source_updated_at)s,%(metadata_hash)s,%(rss_content_key)s)
      ON CONFLICT(url) DO UPDATE SET title=EXCLUDED.title,summary=EXCLUDED.summary,
        published_at=COALESCE(EXCLUDED.published_at,news_articles.published_at),
        source_updated_at=COALESCE(EXCLUDED.source_updated_at,news_articles.source_updated_at),
        metadata_hash=EXCLUDED.metadata_hash,last_seen_at=now(),
        rss_content_key=COALESCE(EXCLUDED.rss_content_key,news_articles.rss_content_key)
      RETURNING id''',a).fetchone()
    db.execute('INSERT INTO news_article_feeds(article_id,feed_id) VALUES(%s,%s) ON CONFLICT(article_id,feed_id) DO UPDATE SET in_latest=true',
               (row['id'],feed_id))

# Uma viagem ao banco por lote; conserva a mesma política de atualização por URL.
BATCH_SQL = """WITH incoming AS (
 SELECT * FROM jsonb_to_recordset(%(items)s::jsonb) AS x(
 url text,title text,summary text,published_at timestamptz,source_updated_at timestamptz,
 metadata_hash text,rss_content_key text)
), saved AS (
 INSERT INTO news_articles(url,title,summary,published_at,source_updated_at,metadata_hash,rss_content_key)
 SELECT url,title,summary,published_at,source_updated_at,metadata_hash,rss_content_key FROM incoming
 ON CONFLICT(url) DO UPDATE SET title=EXCLUDED.title,summary=EXCLUDED.summary,
 published_at=COALESCE(EXCLUDED.published_at,news_articles.published_at),
 source_updated_at=COALESCE(EXCLUDED.source_updated_at,news_articles.source_updated_at),
 metadata_hash=EXCLUDED.metadata_hash,last_seen_at=now(),
 rss_content_key=COALESCE(EXCLUDED.rss_content_key,news_articles.rss_content_key)
 RETURNING id
)
INSERT INTO news_article_feeds(article_id,feed_id)
SELECT id,%(feed_id)s FROM saved
ON CONFLICT(article_id,feed_id) DO UPDATE SET in_latest=true"""

def save_entries(db, feed_id, items):
    from psycopg.types.json import Jsonb
    fields=('url','title','summary','published_at','source_updated_at','metadata_hash','rss_content_key')
    unique={a['url']:a for a in items}
    records=[]
    for a in unique.values():
        row={k:a.get(k) for k in fields}
        for k in ('published_at','source_updated_at'):
            if row[k] is not None and hasattr(row[k],'isoformat'):
                row[k]=row[k].isoformat()
        records.append(row)
    for start in range(0,len(records),250):
        db.execute(BATCH_SQL,{'items':Jsonb(records[start:start+250]),'feed_id':feed_id})
