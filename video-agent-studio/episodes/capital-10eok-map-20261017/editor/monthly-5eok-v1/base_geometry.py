from pathlib import Path
import json,hashlib,sys,time,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];O=E/'outputs/monthly-5eok-v1';F=E/'visual/map-preview-v1';sys.path.insert(0,str(P));from geometry import rings,inside
PACK=E/'research/annual-map-v2/map_packet_v2.json';pkt=json.loads(PACK.read_text(encoding='utf8'));B=R/'assets/geo/sudogwon_sgg.geojson';boundary=json.loads(B.read_text(encoding='utf8'));assert pkt['map_catalog']==8288 and not pkt['coordinate_legacy_geocoder_used'];stats={r['year']:r for r in pkt['coverage']};navy='#030914';land='#091426';edge='#20364c';white='#eff5ff';muted='#8498af';orange='#ffb56f';dim='#334b62';fontcache={}
def font(size,bold=False):
 if (size,bold) not in fontcache:fontcache[size,bold]=ImageFont.truetype(str(F/('Pretendard-Bold.ttf' if bold else 'Pretendard-Regular.ttf')),size)
 return fontcache[size,bold]
rr=[(f,r) for f in boundary['features'] for r in rings(f['geometry'])];main=[(f,r) for f,r in rr if sum(x for x,y in r)/len(r)>=900000];remote=[(f,r) for f,r in rr if sum(x for x,y in r)/len(r)<900000];xy={c['complex_id']:(c['x_5179'],c['y_5179']) for c in pkt['complexes']};points=[p for f,r in main for p in r]+list(xy.values());ext=[min(x for x,y in points)-2500,min(y for x,y in points)-2500,max(x for x,y in points)+2500,max(y for x,y in points)+2500];W,H=1080,1110;maptop=690;scale=min((W-20)/(ext[2]-ext[0]),(H-20)/(ext[3]-ext[1]));pr=lambda p:(W/2+(p[0]-(ext[0]+ext[2])/2)*scale,H/2-(p[1]-(ext[1]+ext[3])/2)*scale);scl=2
base=Image.new('RGB',(W*scl,H*scl),navy);bd=ImageDraw.Draw(base)
for f,r in main:
 pts=[(pr(p)[0]*scl,pr(p)[1]*scl) for p in r];bd.polygon(pts,fill=land);bd.line(pts+[pts[0]],fill=edge,width=2)
# Distant islands do not distort the main scale; a native-geometry inset preserves their contextual location.
if remote:
 pp=[p for f,r in remote for p in r];rb=[min(x for x,y in pp),min(y for x,y in pp),max(x for x,y in pp),max(y for x,y in pp)];rk=min(112/(rb[2]-rb[0]),76/(rb[3]-rb[1]));rp=lambda p:((105+(p[0]-(rb[0]+rb[2])/2)*rk)*scl,(H-75-(p[1]-(rb[1]+rb[3])/2)*rk)*scl);bd.rounded_rectangle([35*scl,(H-130)*scl,175*scl,(H-25)*scl],radius=12,outline=edge,width=2)
 for f,r in remote:bd.polygon([rp(p) for p in r],fill=land,outline=edge)
def representative(f):
 rs=rings(f['geometry']);ps=[p for r in rs for p in r];lo=min(p[1] for p in ps);hi=max(p[1] for p in ps);best=None
 for fract in [.3,.4,.5,.6,.7]:
  y=lo+(hi-lo)*fract;xs=[]
  for r in rs:
   for a,b in zip(r,r[1:]+r[:1]):
    if (a[1]>y)!=(b[1]>y):xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
  xs.sort()
  for a,b in zip(xs[::2],xs[1::2]):
   point=((a+b)/2,y)
   if inside(point,f['geometry']) and (best is None or b-a>best[0]):best=(b-a,point)
 assert best;return best[1]
labels=[]
for text,name,offset in [('서울','종로구',(-60,-60)),('인천','부평구',(-110,22)),('수원','수원시 팔달구',(65,42)),('성남','성남시 중원구',(90,-15)),('고양','고양시 덕양구',(-94,-38))]:
 f=next(f for f in boundary['features'] if f['properties']['name']==name);p=representative(f);labels.append({'text':text,'anchor_feature':name,'native_anchor':list(p),'offset':offset})
