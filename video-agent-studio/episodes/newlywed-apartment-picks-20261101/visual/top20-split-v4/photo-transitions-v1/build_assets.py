"""Freeze ten regional photographs; no source edits, paid services or uploads."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect import ROOT, OLD, EVIDENCE, fetch, plain

SELECTED = {
 20: ('File:Bucheon Stadium Station 2.JPG','원미구','춘의동 부천종합운동장역 2번출구 주변'),
 19: ('File:Sinnae Station 20131228 104952.JPG','중랑구','신내역 역사·주변 철도 생활권'),
 18: ('File:구성역 5번 출구 엘리베이터.jpg','기흥구','구성역 5번출구 엘리베이터와 주변 가로'),
 17: ('File:송도동, Incheon, South Korea (Unsplash).jpg','연수구','송도 센트럴파크 수변과 고층 도시경관'),
 16: ('File:Windmills In The Sunrise (191852353).jpeg','남동구','소래습지생태공원 풍차와 습지 일출'),
 15: ('File:Q43298 Sindorim B01.JPG','구로구','신도림역 경부선 역사 외관'),
 14: ('File:Gupabalcheon Stream 20220612 104.jpg','은평구','진관동 구파발천과 은평뉴타운 생활권'),
 13: ('File:Gwonseon-gu office.JPG','권선구','권선구청과 주변 녹지'),
 12: ('File:광교호수공원.jpg','영통구','광교호수공원 수변'),
 11: ('File:Wide view of Nowon-gu Apartment buildings.jpg','노원구','노원구 아파트 주거지 전경'),
}

def get_pages():
    pages={}
    for f in list((OLD/'photos/evidence').glob('R*.json'))+list(EVIDENCE.glob('R*_search*.json')):
        d=json.loads(f.read_text('utf-8-sig'))
        ps=[d['page']] if 'page' in d else d.get('response',{}).get('query',{}).get('pages',[])
        for p in ps:
            if p.get('imageinfo'): pages[p['title']] = (p,f)
    return pages

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def download_one(args):
    rank, selected, pages, body = args
    dest=ROOT/'photos'/f'R{rank:02d}_hero.jpg'
    dest.parent.mkdir(exist_ok=True)
    if selected is None:
        old=body[rank];src=OLD/old['actual_file'];shutil.copy2(src,dest)
        row=dict(rank=rank,region_id=f'R{rank:02d}',region='원미구',actual_place=old['actual_place'],file=dest.as_posix(),
                 sha256=sha(dest),width=0,height=0,author=old['source_or_prompt']['author'],license_name=old['license']['name'],
                 license_url=old['license']['license_url'],source_url=old['source_or_prompt']['file_page'],
                 photo_date=old['photo_capture_date_raw'],crop_note='기존 본문 사진 재사용 fallback. 원본 비율 유지 후 16:9 중앙 크롭; 현재 현황으로 표현하지 않음.',
                 distinct_from_existing_body_photo=False)
        evidence={'origin':'local_body_photo_fallback','source_manifest':(OLD/'photo_assets_v2.json').as_posix(),
                  'original_file':src.as_posix(),'metadata':old['source_or_prompt']}
    else:
        title,region,place=selected;p,meta_file=pages[title];ii=p['imageinfo'][0];ex=ii['extmetadata']
        val=lambda k:plain(ex.get(k,{}).get('value'))
        license_name=val('LicenseShortName')
        if not license_name.startswith(('CC BY ','CC BY-SA ','CC0')):raise ValueError(license_name)
        use_cdn=rank in {20,18,17,16,15,14,13,12}
        download_url=ii['thumburl'] if use_cdn else ii['url']
        receipt=EVIDENCE/f'R{rank:02d}_receipt.json'
        cached=json.loads(receipt.read_text('utf-8')) if receipt.exists() else {}
        cache_ok=(dest.exists() and cached.get('page',{}).get('title')==title
                  and cached.get('sha256')==sha(dest) and sha(dest)!=body[rank]['sha256']
                  and cached.get('download_url')==download_url)
        if not cache_ok:
            dest.write_bytes(fetch(download_url))
        digest=hashlib.sha1(dest.read_bytes()).hexdigest()
        if not use_cdn and ii.get('sha1') and digest!=ii['sha1']:
            raise ValueError(f'{rank}: original SHA1 does not match source')
        row=dict(rank=rank,region_id=f'R{rank:02d}',region=region,actual_place=place,file=dest.as_posix(),sha256=sha(dest),
                 width=0,height=0,author=val('Artist'),license_name=license_name,license_url=val('LicenseUrl'),
                 source_url=ii['descriptionurl'],photo_date=val('DateTimeOriginal') or '촬영일 미상',
                 crop_note='원본 보존. 16:9 중앙 크롭 제안; 촬영 당시 자료이며 현재 모습으로 단정하지 않음.',
                 distinct_from_existing_body_photo=title.removeprefix('File:')!=body[rank]['source_or_prompt']['title'] and sha(dest)!=body[rank]['sha256'])
        evidence={'origin':'public_commons_original','metadata_input':meta_file.as_posix(),'page':p,
                  'download_url':download_url,'download_utc':datetime.now(timezone.utc).isoformat(),
                  'source_sha1_match':None if use_cdn else True,'download_variant':'public_cdn' if use_cdn else 'original'}
    with Image.open(dest) as im:
        im.load();im=ImageOps.exif_transpose(im);row['width'],row['height']=im.size
    evidence.update(file=dest.as_posix(),sha256=row['sha256'],dimensions=[row['width'],row['height']])
    (EVIDENCE/f'R{rank:02d}_receipt.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'rank':rank,'size':[row['width'],row['height']],'distinct':row['distinct_from_existing_body_photo']},ensure_ascii=False),flush=True)
    return row

def contactsheet(rows):
    w,h=640,410
    sheet=Image.new('RGB',(w*2,h*5),'#15202b')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    d=ImageDraw.Draw(sheet)
    for n,a in enumerate(rows):
        x=n%2*w;y=n//2*h
        with Image.open(a['file']) as im:
            im=ImageOps.exif_transpose(im).convert('RGB')
            im=ImageOps.fit(im,(w,360),centering=(.5,.5))
            sheet.paste(im,(x,y+50))
        suffix='' if a['distinct_from_existing_body_photo'] else ' [본문 재사용]'
        d.text((x+10,y+3),f"{a['rank']}위 {a['region']}{suffix}",font=font,fill='white')
        d.text((x+10,y+29),f"{a['width']}×{a['height']} · {a['photo_date'][:26]}",font=small,fill='#b8c9da')
    sheet.save(ROOT/'contactsheet.jpg',quality=91)

def main():
    body={a['rank']:a for a in json.loads((OLD/'photo_assets_v2.json').read_text('utf-8-sig'))['assets']}
    pages=get_pages();rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(download_one,(r,s,pages,body)):r for r,s in SELECTED.items()}
        for f in concurrent.futures.as_completed(futures):
            r=futures[f]
            try: rows.append(f.result())
            except Exception as e:
                print(json.dumps({'rank':r,'error':str(e)},ensure_ascii=False),flush=True)
                (EVIDENCE/f'R{r:02d}_failure.json').write_text(json.dumps({'rank':r,'error':str(e)},ensure_ascii=False),'utf-8')
    rows.sort(key=lambda a:-a['rank'])
    (ROOT/'assets.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf-8')
    contactsheet(rows)
    print(json.dumps({'manifest_rows':len(rows),'distinct':sum(a['distinct_from_existing_body_photo'] for a in rows),'manifest':(ROOT/'assets.json').as_posix()},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
