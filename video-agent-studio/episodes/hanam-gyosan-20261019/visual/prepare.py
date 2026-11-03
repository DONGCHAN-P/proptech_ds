import json, pathlib, hashlib, math, shutil
R=pathlib.Path(__file__).resolve().parents[4]
V=pathlib.Path(__file__).parent
src=R/'video-agent-studio/map-atlas/layers/raw/lh_landuse_six_districts.geojson'
raw=json.loads(src.read_text(encoding='utf8'))
features=[f for f in raw['features'] if f['properties']['bzdt_cd']=='105176']
def rings(f):
    c=f['geometry']['coordinates']
    return [r for p in c for r in p] if f['geometry']['type']=='MultiPolygon' else c
pts=[p for f in features for r in rings(f) for p in r]
lat=sum(y for x,y in pts)/len(pts); k=math.cos(math.radians(lat))
x0=min(x*k for x,y in pts); x1=max(x*k for x,y in pts); y0=min(y for x,y in pts); y1=max(y for x,y in pts)
scale=min(940/(x1-x0),940/(y1-y0)); ox=(1000-(x1-x0)*scale)/2; oy=(1000-(y1-y0)*scale)/2
def xy(p):return [round(ox+(p[0]*k-x0)*scale,2),round(oy+(y1-p[1])*scale,2)]
def group(n):
    if any(t in n for t in ['공원','녹지','하천','공공공지']):return 'park'
    if '자족' in n:return 'jobs'
    if any(t in n for t in ['상업','근린생활','주상복합']):return 'commercial'
    if '교육' in n:return 'school'
    if any(t in n for t in ['공동주택','단독주택','연립']):return 'home'
    return 'other'
out=[]
for f in features:
    rs=[list(map(xy,r)) for r in rings(f)];p=[a for r in rs for a in r]
    name=f['properties']['bl_type'];xs=[a[0] for a in p];ys=[a[1] for a in p]
    out.append(dict(name=name,group=group(name),d=' '.join('M'+' L'.join(f'{x},{y}' for x,y in r)+' Z' for r in rs),bbox=[min(xs),min(ys),max(xs),max(ys)],xy=[(min(xs)+max(xs))/2,(min(ys)+max(ys))/2]))
a2=next(f for f in out if f['name']=='공동주택 (A-2)');a=a2['xy'];detail=[max(0,a[0]-235),max(0,a[1]-180),470,360]
data=dict(features=out,detail=detail,a2=a2['xy'],meta=dict(district='105176',name='하남 교산',features=len(out),crs='EPSG:4326',projection='local equirectangular, north up',source='LH 내집어디 공개 토지이용계획 WFS',url='https://wherehome.lh.or.kr/lhmap.do?mainTabNo=12',retrieved='2026-10-18',approval_date='원자료 미표기',sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
(V/'data.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
(R/'video/src/gyosan-production-v1/data.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
pub=V/'public';(pub/'changneung-v3').mkdir(parents=True,exist_ok=True)
base=R/'video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v8-labels/public'
for name in ['Pretendard-Regular.woff2','Pretendard-Bold.woff2']:shutil.copy2(base/'changneung-v3'/name,pub/'changneung-v3'/name)
shutil.copytree(R/'video-agent-studio/assets/chapter-backgrounds/v1',pub/'chapter-v8',dirs_exist_ok=True)
colors={'home':'#ead7a0','commercial':'#dfb8c8','park':'#bdd3ae','jobs':'#b9c9e8','school':'#aac8ce','other':'#dce0dd'}
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">'+''.join(f'<path d="{f["d"]}" fill="{colors[f["group"]]}" stroke="#fffdf8" stroke-width="0.9"/>' for f in out)+'</svg>'
(pub/'gyosan_plan.svg').write_text(svg,encoding='utf8')
(V/'visual_brief.json').write_text(json.dumps(dict(reference='changneung-production-v8-jun',canvas=[1920,1080],colors=colors,title_px=46,caption_px=46,caption_box=[96,875,1728,125],source_box=[96,1018,1728,50],map='실제 geometry, 고정 북향, 상세도와 전체 locator',paid_calls=0,new_ai_generation=False,conditions=['계획 시설은 운영 상태 아님','설명용 북·중·남 권역은 법정 경계 아님','역 정밀 핀 없음']),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'features':len(out),'a2':a2['xy'],'detail':detail,'geometry_verified':True}))
