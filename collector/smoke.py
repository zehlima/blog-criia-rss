"""Live connectivity, pipeline and manifest checks; no article mutation."""
import json,time
from .storage import connect,seed
from .inventory import feeds,urls
from .main import preflight

def main():
    db,s3=connect()
    try:
        start=time.monotonic();seed(db,feeds())
        with db.pipeline():
            with db.transaction():
                a=db.execute('SELECT 1 AS n')
                b=db.execute('SELECT count(*) AS n FROM news_feeds WHERE rss_url=ANY(%s)',(urls(),))
        assert a.fetchone()['n']==1
        assert b.fetchone()['n']==len(feeds())
        preflight(db,s3)
        print(json.dumps({'status':'passed','active_feeds':len(feeds()),'seconds':round(time.monotonic()-start,3),'pipeline':True}))
    finally:db.close()
if __name__=='__main__':main()
