import json,pathlib,collections,hashlib
p=pathlib.Path(__file__).parent;ep=p.parent.parent
r=json.loads(ep.joinpath('research/rail-route-proof-v1/raw_osm.json').read_text(encoding='utf-8'))['elements']
if p.joinpath('raw_byeollae_south_osm.json').exists():r+=json.loads(p.joinpath('raw_byeollae_south_osm.json').read_text(encoding='utf-8'))['elements']
r=list({(e['type'],e['id']):e for e in r}.values())
features=[];roads=[];buildings=[];water=[];pois=[]
bounds=[127.110,37.638,127.134,37.667]
def within(g):return any(bounds[0]<v['lon']<bounds[2]and bounds[1]<v['lat']<bounds[3]for v in g)
official={
 '별내동익미라벨아파트':('https://www.nyj.go.kr/www/contents.do?key=2761','동익미라벨38·39단지목록'),
 '별내역파라곤스퀘어':('https://www.nyj.go.kr/main/selectBbsNttView.do?bbsNo=62&key=2481&nttNo=402635','행사장소별내역파라곤스퀘어순화궁로249'),
 '별내 체육공원':('https://www.nyj.go.kr/culture/viewTnResrceU.do?cpn=2&key=4506&rcpp=6&resrceNo=395&si1=1&si2=42','별내체육공원별내동861'),
 '남양주별내 대원칸타빌':('https://www.gbis.go.kr/gbis2014/schBusAPI.action?cmd=searchRouteJson&routeId=241347009','공식정류장명별가람고등학교.대원칸타빌;단지정문단정금지'),
 '이마트 별내점':('https://eapp.emart.com/brandbranch/main.do','공식점포안내별내점순화궁로167')}
for e in r:
 t=e.get('tags',{});g=e.get('geometry',[])
 if e['type']=='node':
  if t.get('shop')=='supermarket' and '이마트'in t.get('name',''):
   pois.append(dict(id=f"node-{e['id']}",name='이마트 별내점',kind='commerce',lon=e['lon'],lat=e['lat'],source=f"https://www.openstreetmap.org/node/{e['id']}",official_source=official['이마트 별내점'][0],status='qualified_geometry_verified_name_address'))
  continue
 if e['type']!='way' or not g or not within(g):continue
 pts=[[v['lon'],v['lat']]for v in g];item=dict(id=e['id'],points=pts)
 if t.get('highway'):roads.append(dict(item,highway=t['highway']))
 if t.get('building'):buildings.append(item)
 if t.get('waterway')or t.get('natural')=='water':water.append(item)
 kind='housing'if t.get('landuse')=='residential'else 'commerce'if t.get('landuse')in ['commercial','retail']or t.get('shop')=='supermarket'else 'park'if t.get('leisure')=='park'else None
 if not kind or pts[0]!=pts[-1]:continue
 f=dict(id=f"way-{e['id']}",name=t.get('name',''),kind=kind,points=pts,lon=sum(v[0]for v in pts)/len(pts),lat=sum(v[1]for v in pts)/len(pts),source=f"https://www.openstreetmap.org/way/{e['id']}",status='qualified',basis='OSM등록실제폴리곤;법정용도지역아님')
 if f['name']in official:f['official_source'],f['official_evidence_location']=official[f['name']];f['status']='qualified_geometry_verified_name_address'
 features.append(f)
landmarks=[{k:f[k]for k in ['id','name','kind','lon','lat','source','status','official_source','official_evidence_location']}for f in features if 'official_source'in f]+pois
ctx=dict(revision='byeollae-context-v4',checked_on='2026-10-15',bounds=bounds,station=dict(name='별내역',lon=127.1278172,lat=37.6420348,source='https://www.openstreetmap.org/node/11942201672',official_source='https://app.ncuc.or.kr/main/2438',status='qualified_geometry_verified_station'),features=features,roads=roads,buildings=buildings,water=water,landmarks=landmarks,pois=pois,priority_label_names=[l['name']for l in landmarks],title='별내 생활권 주변 배치 현황 · 공개 지도 기준',attribution='© OpenStreetMap contributors · ODbL',legend=[dict(kind='housing',label='주거구역'),dict(kind='commerce',label='상업·판매시설'),dict(kind='park',label='공원')],notes=['별내전체시설을모두수집한전수지도아님.등록확인된구역만색칠.','표시범위는별내생활권예시이며모든단지가별내역도보권이라는뜻아님.','대원칸타빌·별내체육공원은북쪽에위치;역바로앞으로옮기지않음.','시세·면적·입주연식·역보행거리동일조건비교를보여주는자료아님.','실제현장경계·준공/영업시점은미검증.'],copyright=dict(data_license='ODbL',url='https://www.openstreetmap.org/copyright',ai=False,tile_download=False))
p.joinpath('byeollae_context.json').write_text(json.dumps(ctx,ensure_ascii=False,indent=2),encoding='utf-8')
facts=[dict(claim_id=f'REGION-CTX-{i+1:03}',sentence=l['name']+'의공식이름/주소또는정류장근거를실제OSM위치와대조한생활권예시이다.',source_url=l['official_source'],geometry_source=l['source'],evidence_location=l.get('official_evidence_location','공식점포주소'),as_of='2026-10-15',verified_on='2026-10-15',status='qualified',qualification='이름주소근거대조;정밀경계·실제역접근성·현장보행가능성검증아님')for i,l in enumerate(landmarks)]
p.joinpath('facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
counts=dict(collections.Counter(f['kind']for f in features))
h=dict(role='video_research',inputs=['video/src/namyangju-v2/project.json','research/rail-route-proof-v1/raw_osm.json','research/dasan-context-v2/context.json'],outputs=['audit.json','byeollae_context.json','facts.json'],affected_scenes=['V2-054'],unchanged_scenes=['V2-009','V2-034'],validated=dict(polygon_counts=counts,all_rings_closed=all(f['points'][0]==f['points'][-1]for f in features),named_official_landmarks=len(landmarks)),unresolved=['별내시설전수조사아님','지역시세동일조건미확인','진접산단정밀경계미확인'],editor_instructions=['다산→별내→진접명확구도전환','다산context를다른지역으로재라벨링금지','V2-054내진접은기존광역기준점만','공식왕숙계획도원본유지','본문음성/대본새생성없음'],next_roles=['video_editor','video_qa'],sha256=hashlib.sha256(p.joinpath('byeollae_context.json').read_bytes()).hexdigest())
p.joinpath('handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(counts=counts,landmarks=len(landmarks),buildings=len(buildings),roads=len(roads))))
