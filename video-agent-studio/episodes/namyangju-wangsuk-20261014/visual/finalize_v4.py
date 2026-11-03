from pathlib import Path
import json,shutil,re,sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8');root=Path(__file__).parent;workspace=Path('C:/projects/realestate_reco')
read=lambda f:json.loads((root/f).read_text('utf-8'))
assets=read('assets_v3.json');assets['revision']='visual-v4';photos=read('photos_v4.json')
url='https://gnews.gg.go.kr/news/news_detail.do?number=202408091541247972C048&s_code=C109'
for id,desc,fileurl in [('PHOTO015','2024.8.9 별내역 플랫폼 별내선 개통행사','20240809053454916710042'),('PHOTO016','2024.8.9 별내선 시승, 공식 기사 제공 사진','20240814011217031831063')]:
 file=root/f'outputs/photos_v4/{id}.jpg';im=Image.open(file);photos.append({'asset_id':id,'title':desc,'source_url':url,'download_url':f'https://gnews.gg.go.kr/OP_UPDATA/UP_DATA/_FILEZ/202408/{fileurl}.jpg','actual_file':f'visual/outputs/photos_v4/{id}.jpg','dimensions':list(im.size),'license':'KOGL Type 1','license_url':'https://www.kogl.or.kr/info/licenseType1.do','author_html':'경기도','photographed':'2024-08-09 행사; 정확한 촬영시각 미표기','description_html':desc,'status':'downloaded_license_verified_visual_reviewed','rights_evidence':'visual/gnews_byeollae_20240809.html'})
for p in photos:
 p['visual_review']='contact sheet 실제 확인' if p['asset_id'] not in ['PHOTO015','PHOTO016'] else '원본 실제 이미지 직접 확인'
 p['status']='downloaded_license_verified_visual_reviewed';p['type']='real_photo';p['AI']=False
 p['actual_place']={'PHOTO001':'별내역 8호선 승강장','PHOTO002':'별내역 경춘선 역명표','PHOTO009':'다산역 승강장','PHOTO010':'남양주다산초등학교 기존 건물','PHOTO015':'별내역 개통행사 플랫폼','PHOTO016':'별내선 시승열차 내부(별내선 노선 기사 맥락; 열차 내 정확한 좌표 미확인)'}[p['asset_id']]
 p['scene_ids']=['S002','S004'] if p['asset_id']!='PHOTO010' else ['S006']
 p['usage_conditions']='출처·저작자·라이선스 URL 유지. CC BY-SA는 해당 사진의 crop/pan/zoom 등 변경 표기 및 사진 부분에 동일라이선스 유지. 2026현재사진·왕숙계획시설로 표현 금지.'
 p['motion']='still_motion_candidate; image pan/zoom 1.00~1.04 only, original photo not actual video'
 if p['asset_id']=='PHOTO001':p['editor_note']='원본이 회전돼 보임. CC0이므로 편집에서90도 방향 확인해 정상표시; 8호선 표기 유지.'
 if p['asset_id']=='PHOTO002':p['editor_note']='경춘선 역명표만 촬영한 사진. 별내역 외부 전경으로 표현 금지.'
 if p['asset_id']=='PHOTO010':p['editor_note']='기존 다산초 실제건물. 왕숙 신설 학교·배정학교로 오인시키지 않음. 기존생활과 신설목표를 비교할때만.'
 assets['assets'].append(p)
(root/'photos_verified_v4.json').write_text(json.dumps(photos,ensure_ascii=False,indent=2),'utf-8')
prior=root/'outputs/previous_owned_v4';prior.mkdir(exist_ok=True)
for id,name,scene in [('AIPREV001','04m05s_철도_연결_AI.png',['S004']),('AIPREV002','09m00s_근거를_확인하는_책상_AI.png',['S007'])]:
 src=workspace/'video/public/asset-pack-v9/01_images'/name;dst=prior/(id+'.png');shutil.copy2(src,dst);im=Image.open(dst)
 assets['assets'].append({'asset_id':id,'scene_ids':scene,'type':'ai_concept','source_or_prompt':'사용자 제공 기존 asset-pack-v9; 전편v14 사용, video/out/newtown-v14-sources.md 및 AssetCutsV11.tsx','dimensions':list(im.size),'actual_file':'visual/outputs/previous_owned_v4/'+id+'.png','actual_place':None,'AI':True,'AI_label':'AI 개념 이미지 · 실제 왕숙 촬영 아님','usage_conditions':'기존 사용자 제공 소재 재사용; 실제 남양주역·단지·시설 증거로 금지. 새 생성·비용 없음.','review_status':'원본 이미지 직접 육안확인','motion':'still_motion_candidate'})
prev=read('assets_v3.json')['assets'];assets['assets'].append({'asset_id':'PREV_V14','scene_ids':['S001','S008'],'type':'prev_excerpt','source_or_prompt':'config/current_video.json v14 및 video/out/newtown-v14-sources.md','actual_file':'C:/projects/realestate_reco/video/out/newtown-v14-release.mp4','actual_place':'광교·동탄','AI':'mixed_previous_video','usage_conditions':'짧은 전편 회고로 도시명 광교·동탄 명시. 남양주 실사로 재사용 금지. 기존 출처 유지.','review_status':'설정·소스·코드 텍스트 확인; 이번 단계 실제 연속재생/프레임추출 안함','dimensions':[1920,1080]})
raw=read('regional_osm_v3.json');meta=read('regional_meta_v3.json');features=[]
for e in raw['elements']:
 if e['type']=='way':
  coords=[[p['lon'],p['lat']] for p in e.get('geometry',[]) if p is not None]
  if len(coords)>1:features.append({'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'osm_id':e['id'],'osm_type':'way',**e.get('tags',{})}})
for p in meta['place_points']:features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[p['lon'],p['lat']]},'properties':{'name':p['name'],'osm_id':p['osm_id'],'marker_meaning':'지역명 기준점·행정경계아님'}})
(root/'regional_geo_v4.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False),'utf-8')
nodes={p['name']:p for p in meta['place_points']};camera={'scene_id':'S002','source':'regional_geo_v4.geojson','projection':'equirectangular cos(37.7) corrected; north up','bounds':meta['bounds'],'motion':'raw geographic layers + camera pan + staged12labels, avoid fullscreen card','camera_targets':[{'name':n,'coordinates':[nodes[n]['lon'],nodes[n]['lat']],'relative_order':i,'zoom_relative':z} for i,(n,z) in enumerate([('별내동',1.8),('다산동',1.8),('진접읍',1.6),('오남읍',1.6),('호평동',1.6),('화도읍',1.4)])],'restrictions':['no Wangsuk arbitrary outline/pin','no commute time/entrance/walking radius','rail geometry not operating-status evidence'],'attribution':'© OpenStreetMap contributors | ODbL | https://www.openstreetmap.org/copyright'}
(root/'map_motion_v4.json').write_text(json.dumps(camera,ensure_ascii=False,indent=2),'utf-8')
assets['known_limitations']=['별내별가람·진접·도시전경 Commons 사진은HTTP429 Retry-After600초로 다운미확보','남양주시 왕숙현장 기사KOGL4 상업금지·변경금지라 채택안함','학교 사진은 기존다산초이며 왕숙신설학교 근거아님','ROOT 신규GPT생성파일은별도명세로추가예정','사진6장만으로최종영상충족주장안함; shotplan+motion+AI+data native integration 필요']
(root/'assets_v4.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),'utf-8')
assert all(Path(x['actual_file']).exists() if Path(x['actual_file']).is_absolute() else (root.parent/x['actual_file']).exists() for x in assets['assets'])
print(json.dumps({'assets':len(assets['assets']),'real_photos':len(photos),'prior_ai':2,'geo_features':len(features)},ensure_ascii=False))
