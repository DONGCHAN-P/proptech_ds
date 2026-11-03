"""Public Commons GET collection only; all output stays inside the assigned photo folder."""
import argparse
import concurrent.futures
import hashlib
import html
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / 'photos'
EVIDENCE = PHOTOS / 'evidence'
API = 'https://commons.wikimedia.org/w/api.php'
UA = 'RealEstateVideoResearch/1.0 (Wikimedia Commons public photo research; no upload)'
TARGETS = [
 (1, '청라호수공원/청라 아파트', '"청라호수공원" OR "Cheongna Lake" OR "Cheongna" apartment'),
 (2, '석촌호수·롯데월드타워', 'Seokchon Lake Lotte'),
 (3, '스타필드 고양/삼송/원흥/행신', 'intitle:"Starfield Goyang" -Volvo -Hyundai -BMW'),
 (4, '마곡 서울식물원', 'intitle:"서울식물원" OR intitle:"Seoul Botanical"'),
 (5, '부평역·부평 도시풍경', '"Bupyeong station"'),
 (6, '테헤란로·코엑스', '"Teheran-ro"'),
 (7, '고덕/암사/강동 도시풍경', '"Godeok" OR "Amsa-dong"'),
 (8, '여의도', '"Yeouido" skyline'),
 (9, '판교/분당 신도시', '"Pangyo" -train -station -bus'),
 (10, '주안/도화/문학경기장', '"Incheon Munhak Stadium"'),
 (11, '상계/중계/경춘선숲길', '"Sanggye" OR "Gyeongchun Line Forest"'),
 (12, '광교 원천호수', '"Gwanggyo Lake Park" OR "Woncheon"'),
 (13, '호매실/권선구 도시풍경', '"Homaesil" OR "호매실" OR "Gwonseon"'),
 (14, '은평뉴타운/진관한옥마을', '"Eunpyeong Hanok" OR "은평뉴타운"'),
 (15, '신도림/G밸리', '"Sindorim"'),
 (16, '구월/소래습지', '"Sorae Ecology" OR "Sorae Wetland"'),
 (17, '송도센트럴파크', '"Songdo Central Park"'),
 (18, '동백호수/구성역', '"Dongbaek Lake" OR "Guseong station"'),
 (19, '신내/중랑장미공원', '"Sinnae" OR "Jungnang Rose"'),
 (20, '중동/상동/부천중앙공원', '"Bucheon Central Park" OR "중동신도시" OR "Sang-dong"'),
]

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30) as r:
        return r.read()

def api(params):
    params = dict(params, format='json', formatversion=2)
    url = API + '?' + urllib.parse.urlencode(params)
    return json.loads(fetch(url)), url

def plain(s):
    return html.unescape(re.sub('<[^>]+>', ' ', s or '')).strip()

def discover(target, query=None):
    rank, place, default_query = target
    query = query or default_query
    data, url = api(dict(action='query', generator='search', gsrsearch=query, gsrnamespace=6,
                        gsrlimit=10, prop='imageinfo|coordinates|categories', cllimit=20,
                        iiprop='url|size|extmetadata|timestamp|sha1', iiurlwidth=1600,
                        iiextmetadatalanguage='en', colimit='max'))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha256(query.encode()).hexdigest()[:7]
    dest = EVIDENCE / f'R{rank:02d}_search_{tag}.json'
    dest.write_text(json.dumps({'request_url':url,'query':query,'response':data},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[]
    for p in sorted(data.get('query',{}).get('pages',[]),key=lambda x:x.get('index',99)):
        ii=p.get('imageinfo',[{}])[0]; ex=ii.get('extmetadata',{})
        val=lambda k: plain(ex.get(k,{}).get('value',''))
        lines.append(dict(title=p['title'],size=[ii.get('width'),ii.get('height')],
                          license=val('LicenseShortName'),date=val('DateTimeOriginal'),
                          description=val('ImageDescription')[:600],
                          coordinates=p.get('coordinates'),file_page=ii.get('descriptionurl'),
                          metadata=str(dest.relative_to(ROOT))))
    return {'rank':rank,'place':place,'query':query,'candidates':lines,'error':data.get('error')}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--rank',type=int);parser.add_argument('--query');parser.add_argument('--ranks')
    args=parser.parse_args()
    ranks=set(map(int,args.ranks.split(','))) if args.ranks else None
    targets=[t for t in TARGETS if (args.rank is None or t[0]==args.rank) and (ranks is None or t[0] in ranks)]
    for i,t in enumerate(targets):
        if i: time.sleep(2.5)
        try:
            result=discover(t,args.query)
            for c in result['candidates']: c.pop('description',None);c.pop('file_page',None);c.pop('metadata',None)
            print(json.dumps(result,ensure_ascii=False),flush=True)
        except Exception as e: print(json.dumps({'rank':t[0],'error':str(e)},ensure_ascii=False),flush=True)

if __name__=='__main__': main()
