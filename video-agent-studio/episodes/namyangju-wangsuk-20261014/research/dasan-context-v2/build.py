import json,pathlib,collections
p=pathlib.Path(__file__).parent
raw=json.loads(p.joinpath('raw_osm.json').read_text(encoding='utf-8'))['elements']
features=[];roads=[];buildings=[];water=[]
def polygons(e):
 if 'geometry' in e:return [e['geometry']]
 if e['type']=='relation':return [x['geometry'] for x in e.get('members',[]) if x.get('role')=='outer' and 'geometry'in x]
 return []
for e in raw:
 t=e.get('tags',{});kind=None
 if t.get('landuse')=='residential':kind='housing'
 elif t.get('landuse') in ['commercial','retail']:kind='commerce'
 elif t.get('leisure')=='park':kind='park'
 if kind:
  for i,g in enumerate(polygons(e)):
   pts=[[v['lon'],v['lat']] for v in g]
   if len(pts)<3:continue
   features.append(dict(id=f"{e['type']}-{e['id']}-{i}",osm_id=e['id'],name=t.get('name',''),kind=kind,points=pts,lon=sum(v[0] for v in pts)/len(pts),lat=sum(v[1]for v in pts)/len(pts),source=f"https://www.openstreetmap.org/{e['type']}/{e['id']}",status='qualified',basis='OSM 실제폴리곤 태그;법정용도지역/현장영업검증아님'))
 if e['type']=='way' and 'geometry'in e:
  item=dict(id=e['id'],points=[[v['lon'],v['lat']] for v in e['geometry']])
  if t.get('highway'):roads.append(dict(item,highway=t['highway']))
  if t.get('building'):buildings.append(item)
  if t.get('waterway') or t.get('natural')=='water':water.append(item)
ctx=dict(revision='dasan-context-v2',checked_on='2026-10-15',bounds=[127.140,37.616,127.160,37.633],station=dict(name='다산역',lon=127.1497626,lat=37.6243286,source='https://www.openstreetmap.org/node/11942201671',official_source='https://app.ncuc.or.kr/main/2439',status='qualified_geometry_verified_station'),features=features,roads=roads,buildings=buildings,water=water,attribution='© OpenStreetMap contributors · ODbL',title='다산역 주변 배치 현황 · 공개 지도 기준',legend=[dict(kind='housing',label='아파트·주거'),dict(kind='commerce',label='상업·판매시설'),dict(kind='park',label='공원')],plan_asset=None,notes=['법정토지이용계획도가 아닌OSM현재등록된주변배치현황.','미등록/미확인필지는색칠하지않는다.','공식운영사에서다산역주변아파트·복합주거지역및상권형성,다산중앙/선형/수변공원안내확인.','geometry조회시점2026-10-15;상가별영업·아파트입주완료시점표시아님.'])
p.joinpath('context.json').write_text(json.dumps(ctx,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(feature_counts=dict(collections.Counter(f['kind']for f in features)),building_count=len(buildings),road_count=len(roads)),ensure_ascii=True))
