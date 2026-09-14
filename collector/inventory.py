"""Active manifest; historical feed rows and article links are never deleted."""
import json
from pathlib import Path

def feeds():
    data=json.loads((Path(__file__).resolve().parent.parent/'data/feeds.json').read_text())
    if not data or len({f['rss_url'] for f in data})!=len(data):
        raise ValueError('invalid_inventory')
    return data

def urls():
    return [f['rss_url'] for f in feeds()]
