"""Replace only R02/R06/R11 in a new manifest; never write to any v1 deliverable."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,html,json,re
from PIL import Image,ImageOps,ImageDraw,ImageFont
ALT=Path(__file__).resolve().parent;ROOT=ALT.parents[1];EVI=ALT/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def plain(s):return html.unescape(re.sub('<[^>]+>',' ',s or '')).strip()
def gps(ex):
 try:
  d=ex.get_ifd(34853);out=[]
  for key,ref in [(2,1),(4,3)]:
   a=d[key];v=float(a[0])+float(a[1])/60+float(a[2])/3600
   if d[ref] in ['S','W']:v=-v
   out.append(v)
  return {'lat':out[0],'lon':out[1],'source':'공식 제공 JPEG의 EXIF GPS','precision_note':'촬영기기 기록이며 측량/행정경계 GIS 검사는 아님'}
 except Exception:return None
def decode_copyright(x):
 try:return x.encode('latin1').decode('cp949')
 except Exception:return x

CONFIG={
2:{'place':'석촌호수 동호 수면·벚꽃 수변 원경','address':'서울특별시 송파구 석촌호수 동호 일대',
   'geo':'Commons 개별 File의 석촌호수공원2 설명, 카메라 좌표(37.510042,127.103775), 실제 수면·벚꽃 수변을 대조. 송파구 석촌호수 동호의 사진이며 잘못된127.03 좌표가 있는 별도 후보는 사용하지 않음.',
   'visual':'수면이 전경을 넓게 차지하고 벚꽃 수변과 멀리 있는 일반 도시 건물군이 배경이다. 롯데월드타워·놀이기구·조형물을 주피사체로 삼지 않는다. 저작권 표시 누락만을 근거로 하지 않고 실제 구도를 추가 확인.',
   'date':'2025-04-09 16:20:47','year':2025,'geo_urls':['https://parks.seoul.go.kr/park/detailView.do?key=2604070019&pIdx=118&tabTarget=1']},
6:{'place':'강남구 양재천 영동4교 인근 수변길','address':'서울특별시 강남구 양재천 영동4교 인근(세부 법정동·필지 확정 아님)',
   'geo':'서울연구원 원문 통합코드06A05509Bb60000의 대상지 영동4교·세부대상지 양재천을 확인. 강남구 공식 시설 주소의 양재천(영동4교) 개포동175 및 JPEG EXIF GPS와 대조. 서초/과천 구간 후보는 제외.',
   'visual':'갈대·수목·수변길이 주피사체이며 특정 신축 건물·미술 조형물은 화면 중심에 없다. 상부의 기능적 교량은 주변 맥락이다. 원거리 보행자의 신원·신혼부부 여부를 주장하지 않음.',
   'date':'2019-12-19 16:44:28.65 (JPEG XMP/EXIF 생성시점); 원문 촬영월2019/12','year':2019,
   'geo_urls':['https://www.gangnam.go.kr/contents/womansafe/2/view.do?mid=ID06_041611','https://data.si.re.kr/photo/06a05509bb60000']},
11:{'place':'노원구 경춘선숲길 산책로·옛 철로','address':'서울특별시 노원구 공릉동 경춘선숲길 구간',
   'geo':'서울연구원 원문 통합코드06I00312Ac30000의 경춘선숲길·촬영장소 짐앤아이유소년스포츠센터 및 JPEG EXIF GPS 확인. 노원구 공릉2동 공식 소개의 경춘선숲길 공릉동 구간과 대조.',
   'visual':'가로3:2 사진으로 산책로·옛 철로·벚꽃과 수목이 주피사체다. 기존 상계백병원 건축물 중심 구도가 사라졌다. 가까운 벤치 이용자 얼굴의 기관 제공 모자이크를1600px 파일에서도 확인. 부조작품·미술관 전시물은 주피사체가 아님.',
   'date':'2020-04-13 11:57:38 (JPEG XMP/EXIF 생성시점); 원문 촬영월2020/04','year':2020,
   'geo_urls':['https://www.nowon.kr/dong/intrcn/intrcn4/intrcn4_05.jsp','https://data.si.re.kr/node/58286']},
}

def main():
 now=datetime.now(timezone.utc).isoformat()
 basepath=ROOT/'photo_assets.json';base=json.loads(basepath.read_text(encoding='utf-8'));v2=copy.deepcopy(base)
 protected={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [basepath,ROOT/'photo_sources.md',ROOT/'photo_handoff.json',ROOT/'photos/TOP20_photo_contactsheet.jpg']}
 # Preserve original media bytes; reuse v1 inspection, do not re-decode unchanged photographs.
 for a in base['assets']:
  p=ROOT/a['actual_file'];assert sha(p)==a['sha256'],a['asset_id'];protected[a['actual_file']]=a['sha256']
 changes=[];newrows=[]
 for rank in [2,6,11]:
  old=next(a for a in base['assets'] if a['rank']==rank);a=copy.deepcopy(old);c=CONFIG[rank]
  receipt=json.loads((EVI/f'R{rank:02d}_alternate_receipt.json').read_text(encoding='utf-8'))
  file=ROOT/receipt['actual_file'];assert sha(file)==receipt['sha256']
  with Image.open(file) as im:
   im.load();ex=im.getexif();raw=list(im.size);dims=list(ImageOps.exif_transpose(im).size);exgps=gps(ex)
   comment=im.info.get('comment',b'');comment=comment.decode('cp949',errors='replace') if isinstance(comment,bytes) else comment
   copyright_text=decode_copyright(str(ex.get(33432,'')))
  assert max(dims)>=1200 and dims[0]>dims[1]
  if rank==2:
   p=receipt['source']['page'];ii=p['imageinfo'][0];metadata=ii['extmetadata'];val=lambda k:plain(metadata.get(k,{}).get('value',''))
   title=p['title'][5:];author=val('Artist');page=ii['descriptionurl'];version='1.0';license='CC0 1.0';licurl=val('LicenseUrl')
   cats=[x['title'] for x in p.get('categories',[])];wikitext=p['revisions'][0]['slots']['main']['content']
   forbidden=[x for x in cats if any(t in x.lower() for t in ['nofop','permission required','non-free'])]
   assert not forbidden and not re.search(r'\{\{\s*(NoFoP|Permission required|Non-free)',wikitext,re.I)
   assert val('LicenseShortName')=='CC0'
   basis='개별 File의 저작자 Own work·CC0 1.0 헌납, 전체 분류·위키텍스트 확인, 타워/조형물 중심을 피한 실제 수변 구도 확인.'
   fixed=f'https://commons.wikimedia.org/w/index.php?oldid={p["revisions"][0]["revid"]}'
   source={'provider':'Wikimedia Commons','title':title,'author':author,'file_page':page,'fixed_revision_url':fixed,
     'original_image_url':ii['url'],'actual_download_url':receipt['download_url'],'metadata_snapshot':'photos/alternates/evidence/R02_final_commons.json',
     'original_description':val('ImageDescription'),'author_html_original':metadata.get('Artist',{}).get('value','')}
   coords=p.get('coordinates',[]);changes_notice='Wikimedia 공식3840px 비율유지 CDN 사본. 로컬 크롭·색보정·생성 보정 없음.'
   api_dims=[ii['width'],ii['height']];variant='standard_cdn';original=False
  else:
   source=receipt['source'];page=source['file_page'];title=f'{"영동4교·양재천" if rank==6 else "경춘선숲길"} ({source["code"]})'
   author='서울특별시(서울경관기록화 사업 2020), 제공: 서울연구원 서울연구데이터서비스'
   license='CC BY 4.0 / 공공누리 제1유형';version='CC BY4.0·공공누리1';licurl='https://creativecommons.org/licenses/by/4.0/deed.ko'
   rawpage=(EVI/f'R{rank:02d}_SI_candidate.html').read_text(encoding='utf-8')
   assert 'https://www.kogl.or.kr/info/licenseType1.do' in rawpage and 'https://creativecommons.org/licenses/by/4.0/deed.ko' in rawpage
   assert '2020 ' in comment,comment
   basis='개별 사진 상세페이지에 공공누리1·CC BY4.0 표시가 함께 있음. 연결된 기관 저작권 정책이 해당 표시 자료는 서울시/산하기관 보유 공공저작물이며 상업 이용·변형을 허용한다고 설명. 제공 JPEG의2020사업 댓글·서울특별시 저작권 EXIF 확인.'
   fixed=page;source={'provider':'서울특별시·서울연구원','title':title,'author':author,'file_page':page,'fixed_revision_url':page,
      'original_image_url':receipt['download_url'],'actual_download_url':receipt['download_url'],
      'metadata_snapshot':f'photos/alternates/evidence/R{rank:02d}_SI_candidate.html',
      'rights_policy_url':'https://data.si.re.kr/node/65064#photo-rights','rights_policy_snapshot':'photos/alternates/evidence/SI_photo_rights_policy.html',
      'original_description':'생성형AI 설명은 위치·사실 검증 근거로 사용하지 않음. 통합코드·대상지·촬영월 등 원문 속성 및 실제 사진을 사용.',
      'embedded_copyright':copyright_text,'embedded_project_comment':comment,'individual_photographer_credit_note':'기관이 지정한 귀속문 사용. EXIF의 개인 연락처는 원장에 전재하지 않음.'}
   coords=[exgps] if exgps else []
   changes_notice='공식 공개 다운로드 버튼에서 제공된1600px JPEG 그대로 저장. 기관 제공 모자이크·비율 유지. 로컬 크롭·색보정·생성 보정 없음.'
   cats=[];forbidden=[];api_dims=None;variant='official_public_1600px_download';original=True
  attrib=f'사진: {author}, 「{title}」, {license}. 원문: {page} / 이용조건: {licurl} / 변형: {changes_notice}'
  reason='원본의 NoFoP-South Korea/건축물·제3자 권리 주의가 있는 주피사체를 피하고, 별도의 CC0 또는 기관 보유권리+개별 자유이용 표시가 확인되는 풍경 사진으로 교체.'
  oldlink={'manifest':'photo_assets.json','manifest_sha256':protected['photo_assets.json'],'asset_id':old['asset_id'],
    'actual_file':old['actual_file'],'sha256':old['sha256'],'old_license':old['license'],'old_inspection_notes':old['inspection']['notes'],
    'replacement_reason':reason,'old_file_retained':True,'v1_manifest_unchanged':True}
  a.update(asset_id=f'PHOTO_R{rank:02d}_ALT01',actual_place=c['place'],address_or_area=c['address'],photo_capture_year=c['year'],photo_capture_date_raw=c['date'],
    source_or_prompt=source,actual_file=receipt['actual_file'],absolute_file=file.as_posix(),bytes=receipt['bytes'],sha256=receipt['sha256'],
    download_variant=variant,is_original_published_file=original,upscaled=False,ai_generated=False,replaces=oldlink,
    purpose='해당 구의 실제 수변·산책로 주제 이미지. 신혼부부 실거주·전입 원인·단지입지·현재 시설 상태의 증거 아님.')
  a['license']={'name':license,'version':version,'license_url':licurl,'alternate_license_url':'https://www.kogl.or.kr/info/licenseType1.do' if rank!=2 else None,
    'copyright_permission_basis':basis,'commercial_copyright_use':True,'adaptation_allowed':True,'share_alike':False,
    'usage_conditions_ko':'원저작자·제목·원문·라이선스·변형 여부 표시. 기관/작가의 보증·후원을 암시하지 않음. 인물·표지·배경 건물을 주피사체로 확대하지 않고 이 수변/산책로 구도로 사용.',
    'attribution_ko':attrib,'changes_notice':changes_notice,'third_party_content_notes':[
      '권리표시가 없다는 이유만으로 모든 권리가 해결됐다고 판단하지 않음. 개별 라이선스·기관 보유권리 근거와 실제 주피사체/원문 주의표시를 함께 검토.',
      '이번 대체 구도에서는 원본과 같은 NoFoP/특정 건축물 중심의 미해결 트리거를 확인하지 않음. 모든 상황의 제3자 권리까지 포괄 보증하는 뜻은 아님.']}
  a['dimensions']={'width':dims[0],'height':dims[1],'stored_pixel_width':raw[0],'stored_pixel_height':raw[1],'exif_orientation':1,
      'api_original_dimensions':api_dims,'long_edge_at_least_1200':True,'aspect_ratio':'4:3' if rank==2 else '3:2 가로'}
  a['geography_verification']={'status':'named_place_and_source_location_matched','basis':c['geo'],'coordinates_from_source':coords,
      'coordinates_role':'원문/EXIF 카메라 위치. 대상지 전체의 대표점 아님.','gis_boundary_point_in_polygon_performed':False,
      'official_place_reference_urls':c['geo_urls'],'ai_generated_caption_used_as_evidence':False}
  a['inspection']={'decode_passed':True,'hash_verified':True,'pixel_visual_review':False,'source_license_checked':True,
    'same_unresolved_trigger_detected':False,'positive_copyright_permission_evidence':True,'visual_content_finding':c['visual'],
    'status':'pending_final_three_image_visual_review','independent_qa_performed':False,
    'notes':['통계2024-11-01과 촬영시점/2020사업연도를 분리.','후속 편집에서 인물/건축물/안내판을 주피사체로 재확대하면 이 확인 범위가 달라짐.']}
  a['replacement_release']={'status':'pending_final_pixel_check','same_trigger_remaining':False,'universal_third_party_rights_guarantee':False,
      'new_paid_generation':False,'private_contact_performed':False}
  i=next(i for i,x in enumerate(v2['assets']) if x['rank']==rank);v2['assets'][i]=a;newrows.append(a)
  changes.append({'region_id':a['region_id'],'scene_ids':a['scene_ids'],'old_asset_id':old['asset_id'],'new_asset_id':a['asset_id'],
      'reason':reason,'old_file':old['actual_file'],'new_file':a['actual_file'],'old_conditions_ref':f'assets[{i}].replaces.old_license'})
 v2.update(photo_revision='photo_assets_v2',updated_utc=now,base_manifest={'path':'photo_assets.json','sha256':protected['photo_assets.json']},
      replacement_scope=['R02','R06','R11'],replacement_log=changes,replacement_gaps=[],protected_v1_hashes=protected,
      replacement_status='pending_final_visual_review',three_alternate_contact_sheet='photos/alternates/R02_R06_R11_alternates_contactsheet.jpg')
 # v1 history remains evidence history, not counts or release status for the new set.
 v2['collection_issues']=copy.deepcopy(base['collection_issues'])
 v2['collection_issues'].append({'issue':'기존3장의NoFoP/건축물 권리 트리거','resolution':'R02/R06/R11 개별 사용권과 실제 풍경 구도를 확인한 별도 사진으로 교체. 기존 조건은 replaces에 보존.','unresolved':False})
 v2['active_counts']={'total':20,'replaced':3,'unchanged_rows':17}
 dump(ROOT/'photo_assets_v2.json',v2)
 w,h=700,590;sheet=Image.new('RGB',(w*3,h),'#20252b');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
 for i,a in enumerate(newrows):
  x=i*w;im=ImageOps.exif_transpose(Image.open(ROOT/a['actual_file'])).convert('RGB');im.thumbnail((680,430));sheet.paste(im,(x+(w-im.width)//2,120+(430-im.height)//2))
  d.text((x+10,9),f'{a["region_id"]}  {a["statistical_region_2024"]}',font=font,fill='white')
  d.text((x+10,40),a['actual_place'],font=small,fill='white')
  d.text((x+10,67),f'{a["dimensions"]["width"]}×{a["dimensions"]["height"]} / 촬영{a["photo_capture_year"]} / 통계2024',font=small,fill='#bfd4e5')
  d.text((x+10,94),a['license']['name'],font=small,fill='#bfd4e5')
 d.text((10,558),'검수용 축소본 · 개별 라이선스/출처: photo_sources_v2.md · 기관 제공 모자이크 유지 · AI 이미지 없음',font=small,fill='white')
 sheet.save(ALT/'R02_R06_R11_alternates_contactsheet.jpg',quality=94)
 dump(EVI/'v2_validation.json',{'phase':'before_final_contactsheet_review','protected_v1_hashes':protected,'unchanged_rows_17_equal':all(x==y for x,y in zip(base['assets'],v2['assets']) if x['rank'] not in [2,6,11]),
      'new_three_files_decoded':True,'new_three_hashes_verified':True,'new_three_landscape_and_1200px':True,'total_search_batches':6,'not_a_full_20_image_reinspection':True})
 print(json.dumps({'replaced':[x['region_id'] for x in newrows],'dimensions':[x['dimensions'] for x in newrows],'contactsheet':str(ALT/'R02_R06_R11_alternates_contactsheet.jpg')},ensure_ascii=False))
if __name__=='__main__':main()
