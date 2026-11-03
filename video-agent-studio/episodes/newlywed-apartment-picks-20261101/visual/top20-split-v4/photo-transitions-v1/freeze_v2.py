"""Offline freeze of two publicly downloaded replacement photos; preserve v1."""
import copy
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from PIL import Image,ImageOps,ImageDraw,ImageFont

P=Path(__file__).resolve().parent
E=P/'evidence_v2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def load(f):return json.loads(f.read_text('utf-8-sig'))
def write(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf-8')
def plain(s):return html.unescape(re.sub('<[^>]*>',' ',str(s or ''))).strip()

v1=load(P/'assets.json');v1hash=sha(P/'assets.json')
oldhash={a['rank']:sha(Path(a['file'])) for a in v1}
pages={}
for f in E.glob('search_*.json'):
    for p in load(f)['response'].get('query',{}).get('pages',[]):pages[p['title']]=(p,f)
choices={
14:('File:Tongil-ro at Gupabal Station.jpg','구파발역 인근 통일로·고층 주거 경관','R14_hero_v2_Gupabal.jpg'),
19:('File:ROK National Route 6 Manguro Mangu Crossroad(Westward Dir) 1.jpg','망우로 망우사거리 서쪽 방향 도시 가로·고층 경관','R19_hero_v2_Mangu.jpg')}
rows=copy.deepcopy(v1);credits=[];checks=[]
sheet=Image.new('RGB',(1280,800),'#162330');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',21)
for n,r in enumerate([14,19]):
    title,place,name=choices[r];page,meta=pages[title];i=page['imageinfo'][0];e=i['extmetadata'];v=lambda k:plain(e.get(k,{}).get('value'))
    a=next(x for x in rows if x['rank']==r);dest=P/'photos'/name
    assert not dest.exists(),'새 파일명만 사용'
    shutil.copy2(E/f'preview_{page["pageid"]}.jpg',dest)
    with Image.open(dest) as im:
        im.load();im=ImageOps.exif_transpose(im).convert('RGB');w,h=im.size
        sheet.paste(ImageOps.fit(im,(1280,350)),(0,n*400+50))
    a.update(actual_place=place,file=dest.as_posix(),sha256=sha(dest),width=w,height=h,author=v('Artist'),
             license_name=v('LicenseShortName'),license_url=v('LicenseUrl'),source_url=i['descriptionurl'],
             photo_date=v('DateTimeOriginal'),distinct_from_existing_body_photo=True,
             crop_note=('16:9 중앙 크롭 확인. 통일로·도로 양쪽 고층 주거의 넓은 맥락 보존. 2021년 촬영 자료.' if r==14 else
                        '16:9 중앙 크롭 확인. 망우사거리 서쪽 방향 가로·고층건물 맥락 보존. 2016년 자료; 당시 거리·버스·광고를 현재 현황으로 표현하지 않음.'))
    assert w>=1600 and h>=900
    assert a['license_name'].startswith(('CC BY ','CC BY-SA ','CC0'))
    assert all(a[k] for k in ['author','license_url','source_url','photo_date'])
    receipt={'rank':r,'source_page':page,'metadata_input':meta.as_posix(),'public_download_url':i['thumburl'],
             'file':dest.as_posix(),'sha256':a['sha256'],'dimensions':[w,h],'ai_generated':False,'upscaled':False,
             'selection':'지역명·원문 설명과 실제 후보 픽셀을 대조. 공사장·역사 단독·식생 근경 대신 넓은 도시 가로를 선택.'}
    write(E/f'R{r}_v2_receipt.json',receipt)
    draw.text((12,n*400+6),f"{r}위 {a['region']} · {a['photo_date']} · {w}×{h}",font=font,fill='white')
    credits.append({k:a[k] for k in ['rank','region_id','actual_place','author','license_name','license_url','source_url','photo_date']})
    checks.append({'rank':r,'decode_hash_dimensions':'pass','source_title':title,'evidence':f'evidence_v2/R{r}_v2_receipt.json','pixel_review':'교체 후보 실제 픽셀 확인; 최종 2장 연락시트 별도 확인'})
assert len(rows)==10
assert all(x==next(y for y in v1 if y['rank']==x['rank']) for x in rows if x['rank'] not in choices)
assert sha(P/'assets.json')==v1hash
assert all(sha(Path(a['file']))==oldhash[a['rank']] for a in v1)
write(P/'assets_v2.json',rows)
write(P/'credits_v2_replacements.json',credits)
sheet.save(P/'contactsheet_v2_replacements.jpg',quality=92)
write(P/'handoff_v2.json',{'task_id':'part1-clean-maps-photo-transitions-v1','revision':'hero-replacements-v2',
      'status':'ready_for_parent_review','changed_region_ids':['R14','R19'],
      'outputs':['assets_v2.json','photos/R14_hero_v2_Gupabal.jpg','photos/R19_hero_v2_Mangu.jpg','contactsheet_v2_replacements.jpg','credits_v2_replacements.json'],
      'input_assets_sha256':v1hash,'checks':checks,'unchanged_eight_rows_exact':True,'all_v1_photo_hashes_unchanged':True,
      'source_date_note':'R14 2021-05-02. R19 2016-08-06으로 2018+ 선호에는 못 미치나, 구도 우선으로 망우사거리 도시 가로 선택.',
      'license_note':'CC BY-SA: 작가·출처·라이선스 링크와 크롭/줌 변형 표기 및 동일·호환 조건 반영. 기존 8장 크레디트는 credits.json 그대로 유지.',
      'paid_cloud_upload_telegram':False,'independent_qa':False,'next_role':'director/editor: 두 region_id만 새 file 경로로 연결'})
print(json.dumps({'status':'ready','rows':10,'changed':[14,19],'unchanged':8,'v1_preserved':True,'replacement_files':[(a['rank'],a['width'],a['height'],a['photo_date']) for a in rows if a['rank'] in choices]},ensure_ascii=False))
