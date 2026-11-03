import json,gzip,pathlib,hashlib,re,math
V=pathlib.Path(__file__).parent;R=V.parents[3];S=R/'video/src/gyosan-production-v1'
G=json.loads((V/'data.json').read_text(encoding='utf8'));F=G['features'];ap=R/'video-agent-studio/map-atlas/web/assets/data/atlas.json.gz';A=json.load(gzip.open(ap,'rt',encoding='utf8'));O=json.loads((R/'video-agent-studio/map-atlas/layers/processed/overlays.json').read_text(encoding='utf8'))
b=[954000,1930000,979000,1956000]
def xy(p):return [round((p[0]-b[0])/(b[2]-b[0])*1000,3),round((b[3]-p[1])/(b[3]-b[1])*1000,3)]
def path(rs):return ' '.join('M'+' L'.join(f'{x},{y}' for x,y in map(xy,r))+' Z' for r in rs)
bound=[]
for f in A['boundary']['features']:
 if f['properties']['name'] in ['강남구','송파구','강동구','서초구','하남시','성남시 분당구','성남시 수정구','성남시 중원구','광주시']:
  c=f['geometry']['coordinates'];rs=[r for p in c for r in p] if f['geometry']['type']=='MultiPolygon' else c
  bound.append(dict(name=f['properties']['name'],d=path(rs)))
stations=[]
for name,line,label in [('강남','2호선','강남역'),('잠실(송파구청)','2호선','잠실역'),('판교','신분당선','판교역')]:
 s=next(s for s in A['transit']['stations'] if s['name']==name and s['line']==line)
 stations.append(dict(label=label,xy=xy(s['xy']),source_xy=s['xy'],source_name=s['name'],line=line,address=s['address'],source_id=s['id']))
ps=[p for p in O['plans'] if p['district']=='105176'];bb=[min(p['bbox'][0] for p in ps),min(p['bbox'][1] for p in ps),max(p['bbox'][2] for p in ps),max(p['bbox'][3] for p in ps)]
anchor=xy([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2]);plans=[dict(d=path(p['rings'])) for p in ps]
def rings(f):return [[tuple(map(float,p.split(','))) for p in q.strip().replace('L',' ').split()] for q in f['d'].split('M') if q.strip() for q in [q.replace('Z','')]]
def inside(p,rs):
 c=False;x,y=p
 for r in rs:
  for a,z in zip(r,r[1:]+r[:1]):
   if (a[1]>y)!=(z[1]>y) and x<(z[0]-a[0])*(y-a[1])/(z[1]-a[1])+a[0]:c=not c
 return c
def interior(f):
 rs=rings(f);p=f['xy']
 if inside(p,rs):return p
 x0,y0,x1,y1=f['bbox'];pts=[(x0+(x1-x0)*i/40,y0+(y1-y0)*j/40) for i in range(1,40) for j in range(1,40)]
 return list(min((p for p in pts if inside(p,rs)),key=lambda q:math.dist(q,f['xy'])))
def pick(name,near):return min((f for f in F if f['name']==name),key=lambda f:math.dist(f['xy'],near))
details={}
for block,view,defs in [('C2',[160,420,330,220],[('교육시설 (초5)','초등학교 예정 부지'),('공원 (수5)','수변공원 예정 부지'),('교육시설 (고2)','고등학교 예정 부지'),('근린생활시설용지 (근생)','근린생활시설 예정 부지')]),('B2',[330,360,310,200],[('근린생활시설용지 (근생)','근린생활시설 예정 부지'),('공원 (근8)','근린공원 예정 부지'),('교육시설 (초6)','초등학교 예정 부지'),('교육시설 (유5)','유치원 예정 부지')])]:
 f=next(f for f in F if f['name']==f'공동주택 ({block})');labels=[]
 for n,label in defs:
  z=pick(n,f['xy']);p=interior(z);labels.append(dict(source_name=n,display_label=label,feature_index=F.index(z),point=p,point_inside=inside(p,rings(z))))
 labels.sort(key=lambda q:q['point'][1]);details[block]=dict(view=view,block_point=interior(f),labels=labels)
out=dict(external=dict(bounds=b,boundaries=bound,stations=stations,plans=plans,anchor=anchor),details=details,meta=dict(crs='EPSG:5179 external / local equirectangular detail',atlas_sha256=hashlib.sha256(ap.read_bytes()).hexdigest(),station_source=A['transit']['meta'],boundary_credit=A['boundary']['credit'],LH=G['meta'],notes=['업무지 핀은 KRIC 대표역 중심점, 직장/출입구/경로 아님','교산 anchor는 지구 기하 bbox 중심의 방향 설명 기준점','상세 라벨 점은 해당 실제 계획 필지 내부 여부를 point-in-polygon으로 검증','학교·공원·상업은 계획 용도이며 개교·개장·배정을 보장하지 않음']))
for p in [V/'data_r3.json',S/'data_r3.json']:p.write_text(json.dumps(out,ensure_ascii=False),encoding='utf8')
def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
checks={}
for name,z in details.items():
 v=z['view'];s=min(920/v[2],510/v[3]);ox=(920-v[2]*s)/2;oy=(510-v[3]*s)/2
 ls=[([ox+(a['point'][0]-v[0])*s,oy+(a['point'][1]-v[1])*s],[975,65+i*115]) for i,a in enumerate(z['labels'])]
 intersections=[]
 for i,(a,bp) in enumerate(ls):
  for j,(c,e) in enumerate(ls[i+1:],i+1):
   if orient(a,bp,c)*orient(a,bp,e)<0 and orient(c,e,a)*orient(c,e,bp)<0:intersections.append([i,j])
 box=next(f['bbox'] for f in F if f['name']==f'공동주택 ({name})')
 checks[name]=dict(leader_intersections=intersections,all_label_points_inside=all(a['point_inside'] for a in z['labels']),block_bbox_fully_inside_view=box[0]>=v[0] and box[1]>=v[1] and box[2]<=v[0]+v[2] and box[3]<=v[1]+v[3],leader_segments=ls)
 assert not intersections and checks[name]['block_bbox_fully_inside_view']
(V/'geometry_checks_r3.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(stations=stations,detail_labels={k:v['labels'] for k,v in details.items()}),ensure_ascii=False))

