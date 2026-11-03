from pathlib import Path
import sys,json,hashlib,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]/'tools/gis_vendor'))
from pyproj import Transformer
tr=Transformer.from_crs(4326,5179,always_xy=True)
names={'105142':'고양 창릉','105175':'남양주 왕숙1','105311':'남양주 왕숙2','105232':'부천 대장','105130':'인천 계양','105176':'하남 교산'}
p=H/'raw/lh_landuse_six_districts.geojson';raw=json.loads(p.read_text(encoding='utf8'));plans=[]
for f in raw['features']:
 prop=f['properties'];g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
 for n,poly in enumerate(polys):
  rings=[[[round(v,2) for v in tr.transform(*point[:2],errcheck=True)] for point in ring] for ring in poly];pts=[p for r in rings for p in r]
  plans.append({'id':f['id']+':'+str(n),'district':prop['bzdt_cd'],'name':prop['bl_type'],'color':prop.get('color_cd') or '#cccccc','rings':rings,'bbox':[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]})
railpath=H/'raw/rail_routes_geometry_osm.json';rail=json.loads(railpath.read_text(encoding='utf8'));assert rail.get('elements') and not rail.get('remark')
routes={};seen=set();excluded=[]
def canonical(name):
 if '인천' in name and '1호선' in name:return '인천1호선'
 if '인천' in name and '2호선' in name:return '인천2호선'
 for word,label in [('신분당','신분당선'),('수인','수인분당선'),('분당','수인분당선'),('경의','경의중앙선'),('경춘','경춘선'),('경강','경강선'),('서해','서해선'),('공항','공항철도'),('에버','에버라인'),('용인','에버라인'),('의정부','의정부경전철'),('우이','우이신설선'),('신림','신림선'),('김포','김포골드라인')]:
  if word in name:return label
 m=re.search(r'([1-9])호선',name)
 if m:return m[1]+'호선'
 m=re.search(r'GTX[ -]?([ABC])',name,re.I)
 return 'GTX-'+m[1].upper() if m else None
for e in rail['elements']:
 tags=e.get('tags',{});name=tags.get('name:ko') or tags.get('name','');key=canonical(name)
 if not key or tags.get('service') in {'high_speed','international'}:excluded.append(e['id']);continue
 color=tags.get('colour') or tags.get('color') or '#65758b'
 if not re.fullmatch('#[0-9a-fA-F]{6}',color):color='#65758b'
 route=routes.setdefault(key,{'name':key,'color':color,'segments':[],'relations':[]});route['relations'].append(e['id'])
 for m in e.get('members',[]):
  if m.get('type')!='way' or m.get('role','').startswith(('platform','stop')):continue
  geom=m.get('geometry') or []
  points=[]
  for g in geom:
   if g and 'lon' in g:
    lon,lat=g['lon'],g['lat']
    if not 125.8<lon<128.1 or not 36.6<lat<38.6:
     if len(points)>1:route['segments'].append(points)
     points=[];continue
    points.append([round(v,2) for v in tr.transform(lon,lat,errcheck=True)])
  ident=(key,m['ref'])
  if len(points)>1 and ident not in seen:seen.add(ident);route['segments'].append(points)
routes=[r for r in routes.values() if r['segments']];assert routes
meta={'crs':'EPSG:5179','plans_source':'LH 내집어디 공개 토지이용계획 WFS','plans_url':'https://wherehome.lh.or.kr/lhmap.do?mainTabNo=12','plans_retrieved':'2026-10-18','plans_approval_date':'원자료 미표기','plans_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_source':'OpenStreetMap route relation member ways','rail_license':'ODbL 1.0 · © OpenStreetMap contributors','rail_url':'https://www.openstreetmap.org/copyright','rail_timestamp':rail.get('osm3s',{}).get('timestamp_osm_base'),'rail_sha256':hashlib.sha256(railpath.read_bytes()).hexdigest(),'rail_note':'커뮤니티 경로 도형. 일부 누락·시점 차이 가능. 역 점은 별도의 KRIC 자료이며 출입구/정밀 선형을 보장하지 않음.'}
out={'meta':meta,'districts':names,'plans':plans,'routes':routes};(H/'processed/overlays.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf8')
v={'plans':len(plans),'district_counts':dict(collections.Counter(x['district'] for x in plans)),'routes':{r['name']:len(r['segments']) for r in routes},'excluded_relation_count':len(excluded),'meta':meta};(H/'overlay_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in v.items() if k!='meta'},ensure_ascii=False))
