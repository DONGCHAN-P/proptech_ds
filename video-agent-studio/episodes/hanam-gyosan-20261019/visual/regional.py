import json,gzip,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[4];V=pathlib.Path(__file__).parent
atlas=R/'video-agent-studio/map-atlas/web/assets/data/atlas.json.gz';A=json.load(gzip.open(atlas,'rt',encoding='utf8'))
O=json.loads((R/'video-agent-studio/map-atlas/layers/processed/overlays.json').read_text(encoding='utf8'))
# One fixed north-up local projection in source EPSG:5179 metres.
b=[963000,1940000,979000,1956000]
def xy(p):return [round((p[0]-b[0])/(b[2]-b[0])*1000,2),round((b[3]-p[1])/(b[3]-b[1])*1000,2)]
def inside(p):return b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]
def path(rs):return ' '.join('M'+' L'.join(f'{x},{y}' for x,y in map(xy,r)) for r in rs)
boundary=[]
for f in A['boundary']['features']:
 if f['properties']['name'] in ['하남시','강동구','송파구','강남구']:
  c=f['geometry']['coordinates'];rs=[r for p in c for r in p] if f['geometry']['type']=='MultiPolygon' else c
  boundary.append(dict(name=f['properties']['name'],d=path(rs)))
plans=[dict(name=p['name'],d=path(p['rings']),xy=xy([(p['bbox'][0]+p['bbox'][2])/2,(p['bbox'][1]+p['bbox'][3])/2])) for p in O['plans'] if p['district']=='105176']
routes=[dict(name=p['name'],color=p['color'],d=path([r for r in p['segments'] if any(inside(q) for q in r)])) for p in O['routes'] if p['name'] in ['5호선','3호선','8호선','9호선']]
names=['하남검단산','하남시청','하남풍산','미사','상일동','강동','천호','강동구청','올림픽공원','오금','수서']
stations=[dict(name=s['name'],line=s['line'],xy=xy(s['xy']),address=s['address']) for s in A['transit']['stations'] if any(s['name'].startswith(n) for n in names) and s['line'] in ['5호선','3호선','8호선','9호선'] and inside(s['xy'])]
cn=['감일한라비발디','미사강변푸르지오','위례롯데캐슬','하남자이','꿈동산신안','미사레스티아','대명강변타운']
complexes=[dict(name=x['name'],xy=xy(x['xy']),address=x['addr'],approved=x['approved'],id=x['id']) for x in A['items'] if x['code']=='41450' and x['name'] in cn]
for x in A['items']:
 if x['code']=='41450' and any('미사레스티아' in n.replace(' ','') for n in x['names']):
  complexes.append(dict(name='미사레스티아',source_name=x['name'],aliases=x['names'],xy=xy(x['xy']),address=x['addr'],approved=x['approved'],id=x['id']))
houses=[dict(d=path(x['rings'])) for x in A['items'] if inside(x['xy'])]
out=dict(boundary=boundary,plans=plans,routes=routes,stations=stations,complexes=complexes,houses=houses,meta=dict(bounds=b,crs='EPSG:5179',atlas_sha256=hashlib.sha256(atlas.read_bytes()).hexdigest(),boundary_credit=A['boundary']['credit'],station_source=A['transit']['meta'],rail_source=O['meta'],coordinate_note='단지·역 중심 대표점이며 출입구·도보동선 아님'))
for p in [V/'regional.json',R/'video/src/gyosan-production-v1/regional.json']:p.write_text(json.dumps(out,ensure_ascii=False),encoding='utf8')
print(json.dumps({'stations':stations,'complexes':complexes},ensure_ascii=False))

