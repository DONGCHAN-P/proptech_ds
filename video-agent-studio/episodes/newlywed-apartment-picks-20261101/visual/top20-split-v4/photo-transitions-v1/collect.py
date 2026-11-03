"""Public Commons GETs only; all writes are scoped to this task directory."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
EPISODE = ROOT.parents[2]
OLD = EPISODE / 'visual/top20-8min-v2'
EVIDENCE = ROOT / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
UA = 'RealEstateVideoVisual/1.0 (public Commons photo collection, no upload)'

def plain(s):
    return html.unescape(re.sub('<[^>]*>', ' ', str(s or ''))).strip()

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=35) as r:
        return r.read()

def api(params):
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(params, format='json', formatversion=2))
    return json.loads(fetch(url)), url

def search(item):
    rank, query = item
    d, url = api(dict(action='query', generator='search', gsrsearch=query,
                      gsrnamespace=6, gsrlimit=8, prop='imageinfo|coordinates',
                      iiprop='url|size|extmetadata|sha1', iiurlwidth=1920, colimit='max'))
    tag=hashlib.sha256(query.encode()).hexdigest()[:7]
    (EVIDENCE / f'R{rank:02d}_search_{tag}.json').write_text(json.dumps({'url':url, 'query':query, 'response':d}, ensure_ascii=False, indent=2), 'utf-8')
    rows=[]
    for p in sorted(d.get('query',{}).get('pages',[]), key=lambda p:p.get('index',99)):
        ii=p.get('imageinfo',[{}])[0]; ex=ii.get('extmetadata',{})
        rows.append({'id':p['pageid'],'title':p['title'],'size':[ii.get('width'),ii.get('height')],
                     'license':plain(ex.get('LicenseShortName',{}).get('value')),
                     'description':plain(ex.get('ImageDescription',{}).get('value'))[:180]})
    return {'rank':rank, 'candidates':rows}

if __name__ == '__main__':
    queries=[(20, 'intitle:"Bucheon" -actress -festival -football -film -cinema -map -logo -banner'),
             (18, 'intitle:"동백호수"')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(search, queries):
            print(json.dumps(result, ensure_ascii=False), flush=True)
