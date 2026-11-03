"""Freeze selected public-domain/CC photographs and their exact source metadata."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import sys
from PIL import Image
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_photos import ROOT, PHOTOS, EVIDENCE, api, fetch, plain

SELECTED = {
 2: ('File:Lotte World morning view 8.jpg','송파_석촌호수_롯데타워'),
 3: ('File:Samsong-Jichuk, Goyang 20211114 163247.jpg','덕양_삼송도시풍경'),
 4: ('File:서울식물원 야외.jpg','강서_서울식물원'),
 5: ('File:Korail-Bupyeong Stn-Exterior.jpg','부평_부평역'),
 6: ('File:Teheran-ro Yeongdong-daero crossing 6.jpg','강남_테헤란로'),
 7: ('File:Seoul-metro-552-Godeok-station-entrance-4-20180914-124006.jpg','강동_고덕역일대'),
 8: ('File:Skyline of Yeouido, a prominent finance district in Seoul.jpg','영등포_여의도'),
 9: ('File:눈오는 판교4 - panoramio.jpg','분당_판교겨울도시풍경'),
 10: ('File:SSG 랜더스 문학경기장 문학스타디움 전경 2024.jpg','미추홀_문학경기장'),
 11: ('File:Danghyeoncheon and Inje University Sanggye Paik Hospital.jpg','노원_상계당현천'),
 12: ('File:광교호수공원 (3).jpg','영통_광교원천호수'),
 13: ('File:Suwon Bus Terminal.jpeg','권선_권선동도시풍경'),
 14: ('File:Eunpyeong Newtown.jpg','은평_은평뉴타운'),
 15: ('File:Seoul-metro-Sindorim-station-entrance-1-20181121-093808.jpg','구로_신도림'),
 16: ('File:소래습지생태공원 갈대밭.jpg','남동_소래습지'),
 17: ('File:Songdo Central Park in 2021.jpg','연수_송도센트럴파크'),
 18: ('File:구성역 5번출구 주변.jpg','기흥_구성역주변'),
 19: ('File:Sinnae station exit3 bus.jpg','중랑_신내역일대'),
 20: ('File:Sangdong2025.jpg','원미_상동'),
}

def get_metadata(ranks=None):
    keys=ranks or list(SELECTED)
    for i in range(0,len(keys),7):
        if i: time.sleep(3)
        chunk=keys[i:i+7]
        data,url=api(dict(action='query',titles='|'.join(SELECTED[r][0] for r in chunk),
            prop='imageinfo|coordinates|revisions|categories', cllimit=50,
            rvprop='ids|timestamp|content',rvslots='main',
            iiprop='url|size|extmetadata|timestamp|sha1|mime',iiurlwidth=1600,
            iiextmetadatalanguage='en',colimit='max'))
        for p in data.get('query',{}).get('pages',[]):
            rank=next(r for r in chunk if SELECTED[r][0].replace('_',' ')==p['title'].replace('_',' '))
            EVIDENCE.mkdir(parents=True,exist_ok=True)
            d=EVIDENCE/f'R{rank:02d}_selected_commons.json'
            if d.exists():
                old=json.loads(d.read_text(encoding='utf-8'))
                if old['page']['title'] != p['title']:
                    (EVIDENCE/f'R{rank:02d}_earlier_{old["page"]["pageid"]}_commons.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
            d.write_text(json.dumps({'request_url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'page':p},ensure_ascii=False,indent=2),encoding='utf-8')
            ii=p.get('imageinfo',[{}])[0]; ex=ii.get('extmetadata',{});val=lambda k:plain(ex.get(k,{}).get('value',''))
            print(json.dumps({'rank':rank,'title':p['title'],'size':[ii.get('width'),ii.get('height')],
                'license':val('LicenseShortName'),'artist':val('Artist'),'license_url':val('LicenseUrl'),
                'date':val('DateTimeOriginal'),'description':val('ImageDescription'),'coords':p.get('coordinates'),
                'categories':[x['title'] for x in p.get('categories',[])]},ensure_ascii=False),flush=True)
        if 'error' in data: print(json.dumps(data))

def download(ranks,preview=False,cdn=False):
    cdn_infos={}
    if cdn:
        for size in (1280,3840):
            group=[r for r in ranks if (r==19)==(size==1280)]
            if not group: continue
            data,request_url=api(dict(action='query',titles='|'.join(SELECTED[r][0] for r in group),prop='imageinfo',
                iiprop='url|size|mime',iiurlwidth=size))
            (EVIDENCE/f'cdn_{size}_metadata.json').write_text(json.dumps({'request_url':request_url,'response':data},ensure_ascii=False,indent=2),encoding='utf-8')
            for p in data['query']['pages']:
                rank=next(r for r in group if SELECTED[r][0].replace('_',' ')==p['title'].replace('_',' '))
                cdn_infos[rank]=p['imageinfo'][0]
            time.sleep(3)
    for i,rank in enumerate(ranks):
        if i: time.sleep(1.5)
        try:
            p=json.loads((EVIDENCE/f'R{rank:02d}_selected_commons.json').read_text(encoding='utf-8'))['page']
            ii=p['imageinfo'][0]; ex=ii['extmetadata']; license=plain(ex.get('LicenseShortName',{}).get('value',''))
            if not (license.startswith(('CC BY ','CC BY-SA ','CC0')) or license=='Public domain'):
                raise ValueError('License requires manual review: '+license)
            desc=plain(ex.get('ImageDescription',{}).get('value',''))
            if any(t in desc.lower() for t in ('may not be manipulated','non-commercial','all rights reserved')):
                raise ValueError('Conflicting restrictive description')
            if cdn: ii=cdn_infos[rank]
            url=ii['thumburl'] if preview or cdn else ii['url']
            folder=PHOTOS/'previews' if preview else PHOTOS
            folder.mkdir(parents=True,exist_ok=True)
            dst=folder/f'R{rank:02d}_{SELECTED[rank][1]}.jpg'
            if not dst.exists(): dst.write_bytes(fetch(url))
            with Image.open(dst) as im: im.load();dims=im.size
            digest=hashlib.sha256(dst.read_bytes()).hexdigest()
            record={'rank':rank,'path':str(dst.relative_to(ROOT)),'download_url':url,'width':dims[0],'height':dims[1],
                    'sha256':digest,'bytes':dst.stat().st_size,'original':not (preview or cdn),'decoded':True,
                    'variant':'standard_cdn' if cdn else 'original'}
            (EVIDENCE/f'R{rank:02d}_{"preview" if preview else "download"}_receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(record,ensure_ascii=False),flush=True)
        except Exception as e: print(json.dumps({'rank':rank,'error':str(e)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['metadata','preview','download','cdn']);parser.add_argument('--ranks')
    args=parser.parse_args()
    if args.action=='metadata': get_metadata([int(x) for x in args.ranks.split(',')] if args.ranks else None)
    else: download([int(x) for x in args.ranks.split(',')] if args.ranks else list(SELECTED),preview=args.action=='preview',cdn=args.action=='cdn')
