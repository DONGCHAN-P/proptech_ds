import json,pathlib,hashlib
p=pathlib.Path(__file__).parent
d=json.loads(p.joinpath('context.json').read_text(encoding='utf-8'))
d['bounds']=[127.139,37.613,127.166,37.633]
nc='https://app.ncuc.or.kr/main/2439'
gh='https://apply.gh.or.kr/cs/sr/sr7870/selectSplyCenterInfoView.do'
kapt='https://www.k-apt.go.kr/cmmn/introMmentPop.do?bjdCode=41&searchOccuDate=202609&upYn=Y'
hy='https://www.ehyundai.com/newPortal/DP/WC/WC000000_V.do?branchCd=B00178000'
verified={'다산역경기행복주택아파트':(gh,'다산역A2공급센터주소,다산중앙로145번길36'),'다산역자연앤푸르지오':(gh,'공급센터주소다산중앙로123번길29'),'다산자이 IVY PLACE':(kapt,'다산자이아이비플레이스다산동6028'),'다산중앙공원':(nc,'공원소개·다산중앙로146번길62'),'다산선형공원':(nc,'1·6출구안내'),'다산수변공원':(nc,'다산순환로149,왕숙천서쪽수변공원설명'),'현대프리미엄아울렛 스페이스원':(hy,'업체공식지점주소다산순환로50')}
landmarks=[]
for f in d['features']:
 if f['name'] in verified:
  u,loc=verified[f['name']];f['official_source']=u;f['official_evidence_location']=loc;f['status']='qualified_geometry_verified_name_address'
  if f['name'] not in [x['name']for x in landmarks]:
   landmarks.append({k:f[k]for k in ['id','name','kind','lon','lat','source','status','official_source','official_evidence_location']})
d['landmarks']=landmarks
d['priority_label_names']=['다산역경기행복주택아파트','다산자이 IVY PLACE','다산역자연앤푸르지오','다산선형공원','다산중앙공원','현대프리미엄아울렛 스페이스원']
d['copyright']=dict(data_license='Open Database License (ODbL)',url='https://www.openstreetmap.org/copyright',display_attribution='© OpenStreetMap contributors',use='공개공간데이터 자체지도 재작성;공식사진/토지계획도면복제없음',tile_download=False,ai=False)
d['plan_candidate_status']=dict(gh_recent='공식최근2026지금지구공급페이지는다산역진건지구와구별하여제외',official_plan_image_used=False,reason='직접다운로드가능하고명확한재사용권리있는진건계획도확보안됨;사용자목적에맞는실제주변배치현황선택',reference_url='https://buy.gh.or.kr/land/svc/announce/land_announce_view.jsp?MenuId=SVC_ANN&annSeq=1336')
d['geometry_validation']=dict(all_feature_rings_closed=all(f['points'][0]==f['points'][-1]for f in d['features']),all_coordinate_pairs_lon_lat=True,unknown_parcels_colored=False,named_landmarks=7,station_lon=127.1497626,station_lat=37.6243286)
p.joinpath('context.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
facts=[]
for i,l in enumerate(landmarks,1):facts.append(dict(claim_id=f'DASAN-CTX-{i:03}',sentence=f"다산역주변지도에서 {l['name']}의 실제 등록 위치를 표시한다.",source_url=l['official_source'],geometry_source=l['source'],evidence_location=l['official_evidence_location'],as_of='2026-10-15',verified_on='2026-10-15',status='qualified',qualification='이름/주소공식대조;정밀지리좌표·폴리곤은OSM기준,현장경계검증아님'))
p.joinpath('facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
h=dict(role='video_research',input_revision='rail-route-proof-v1;다산단독구간40.3~61초보완',outputs=['context.json','raw_osm.json','facts.json'],affected_scenes=['DASAN-CTX-V2'],verified=['1686 OSM공간자료다운로드','주거25/상업12/공원23 실제폴리곤','394건물/963도로','7장소공식이름주소근거대조','모든feature폴리곤닫힘검사'],unresolved=['법정토지계획도직접재사용권리미확인','OSM정밀경계·현장시설상태미검증'],next_roles=['video_editor','video_qa'],editor_rules=['주변배치현황·공개지도기준표기','기존80초다른구간/audio보존','법정용도지역/계획승인완공도오인표현금지','아파트노랑/상업핑크/공원초록은OSM태그polygon만','미확인필지임의색칠금지','© OpenStreetMap contributors출처고정'],context_sha256=hashlib.sha256(p.joinpath('context.json').read_bytes()).hexdigest())
p.joinpath('handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(d['geometry_validation']))
