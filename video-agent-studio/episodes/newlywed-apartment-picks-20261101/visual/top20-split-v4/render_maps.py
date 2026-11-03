"""Render factual overview/detail plates from local frozen geographic layers."""
from pathlib import Path
from collections import Counter
import json,sys,math,hashlib,argparse,re
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
sys.path.insert(0,str(R/'tools/gis_vendor'))
from pyproj import Transformer
sys.path.insert(0,str(E/'research/top20-explain-v3/prices'))
from calculate_prices import shape_rings
C=D/'atlas-context';OUT=D/'maps';OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
S=2;BG='#F6F4EF';INK='#173348';BLUE='#286CDA';LAND='#EEF0E8'
def font(n,bold=False):return ImageFont.truetype(str(R/'assets/fonts'/('Pretendard-Bold.woff2' if bold else 'Pretendard-Regular.woff2')),round(n*S))
F={};AUDIT=[]
FEATURE_STATIONS={'R19':['신내'],'R18':['구성'],'R15':['신도림'],'R10':['주안'],'R07':['고덕'],'R03':['삼송']}
def station_key(name):return re.sub(r'\([^)]*\)','',name).replace('역','').strip()
def txt(im,xy,text,size=24,fill=INK,bold=False):
    draw=ImageDraw.Draw(im);f=F.setdefault((size,bold),font(size,bold));p=tuple(round(v*S) for v in xy)
    box=draw.textbbox(p,text,font=f);assert box[0]>=0 and box[1]>=0 and box[2]<=im.width and box[3]<=im.height,(text,box)
    draw.text(p,text,font=f,fill=fill);return box
def money(v):
    value=int(round(v));a,b=divmod(value,10000)
    return (f'{a}억'+(f' {b:,}만원' if b else '원')) if a else f'{b:,}만원'
def closed(p):return len(p)>=4 and p[0]==p[-1]
def rawpaths(e):
    if e.get('geometry'):return [[(p['lon'],p['lat']) for p in e['geometry'] if p and 'lon' in p]]
    out=[]
    for m in e.get('members',[]):
        run=[]
        for p in m.get('geometry',[]):
            if p and 'lon' in p:run.append((p['lon'],p['lat']))
            else:
                if len(run)>1:out.append(run)
                run=[]
        if len(run)>1:out.append(run)
    return out

class Panel:
    def __init__(self,w,h,bbox):
        self.w=w;self.h=h;self.im=Image.new('RGB',(w*S,h*S),LAND);self.d=ImageDraw.Draw(self.im);self.bbox=bbox
        a,b,c,d=bbox;self.scale=min((w-24)/(c-a),(h-24)/(d-b));self.cx=(a+c)/2;self.cy=(b+d)/2;self.labels=[];self.label_names=[]
    def pos(self,p):return ((p[0]-self.cx)*self.scale+self.w/2,(self.cy-p[1])*self.scale+self.h/2)
    def px(self,p):return tuple(round(v*S) for v in self.pos(p))
    def inside(self,p,pad=8):
        x,y=self.pos(p);return pad<x<self.w-pad and pad<y<self.h-pad
    def line(self,pts,color,width=1):
        if len(pts)>1:self.d.line([self.px(p) for p in pts],fill=color,width=max(1,round(width*S)),joint='curve')
    def polygon(self,pts,color):
        if len(pts)>2:self.d.polygon([self.px(p) for p in pts],fill=color)
    def label(self,p,name,fill=INK,size=18,priority=False):
        x,y=self.pos(p);f=F.setdefault((size,False),font(size))
        for dx,dy in [(14,-20),(14,8),(-14,-20),(-14,12),(10,-42)]:
            xx=(x+dx)*S;yy=(y+dy)*S;bb=self.d.textbbox((xx,yy),name,font=f,stroke_width=2*S)
            if dx<0:xx-=bb[2]-bb[0];bb=self.d.textbbox((xx,yy),name,font=f,stroke_width=2*S)
            if bb[0]<8*S or bb[1]<8*S or bb[2]>(self.w-8)*S or bb[3]>(self.h-8)*S:continue
            if any(not (bb[2]+6*S<a or bb[0]-6*S>c or bb[3]+4*S<b or bb[1]-4*S>d) for a,b,c,d in self.labels):continue
            self.d.text((xx,yy),name,font=f,fill=fill,stroke_width=2*S,stroke_fill='#FFFFFF');self.labels.append(bb);self.label_names.append(name);return True
        return False
    def square(self,p,color,symbol,small=False):
        x,y=self.px(p);r=(6 if small else 10)*S;self.d.rounded_rectangle((x-r,y-r,x+r,y+r),radius=3*S,fill=color,outline='#FFFFFF',width=(1 if small else 2)*S)
        if not small:
            f=F.setdefault((13,True),font(13,True));self.d.text((x-6*S,y-8*S),symbol,font=f,fill='#FFFFFF')

def draw_panel(context,bbox,w,h,detail,osm,polys,rep,prices=True):
    panel=Panel(w,h,bbox);ll=Transformer.from_crs(4326,5179,always_xy=True)
    commercial=[];roads=[]
    for item in osm:
        tags=item['tags'];paths=item['paths']
        if tags.get('natural')=='water':
            for p in paths:
                if closed(p):panel.polygon(p,'#BED9E5')
        if tags.get('leisure') in ['park','garden']:
            for p in paths:
                if closed(p):panel.polygon(p,'#CDDDB8')
        if tags.get('landuse') in ['retail','commercial']:
            for p in paths:
                if closed(p):panel.polygon(p,'#EEDDC3')
        if tags.get('waterway') in ['river','canal','stream']:
            for p in paths:panel.line(p,'#A9CADB',3 if tags['waterway']!='stream' else 1.6)
        if tags.get('highway'):roads.append(item)
        if tags.get('shop') in ['mall','department_store','supermarket'] or tags.get('amenity')=='marketplace':
            if item.get('point'):commercial.append(item)
    for r in polys:
        for ring in r:panel.polygon(ring,'#DFE3DD');panel.line(ring,'#CCD4CB',.65)
    for item in roads:
        kind=item['tags']['highway'];width={'motorway':5,'trunk':4.4,'primary':3.7,'secondary':3.1,'tertiary':2.5}.get(kind,1.25)
        for p in item['paths']:panel.line(p,'#CCD0C8',width+1.0);panel.line(p,'#FFFFFF',width)
    for route in context['rail_routes']:
        for p in route['segments']:panel.line(p,'#FFFFFF',4.5);panel.line(p,route['color'],2.1)
    for f in context['boundary']['features']:
        g=f['geometry'];parts=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in parts:
            for ring in poly:panel.line([ll.transform(*p) for p in ring], '#8CA4AA',1.4)
    if prices:
        for point in sorted(context['complex_points'],key=lambda r:r['median_manwon']):
            p=(point['x_5179'],point['y_5179'])
            if not panel.inside(p,2):continue
            x,y=panel.px(p);radius=(6.1 if detail else 4.9)*S
            panel.d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=point['color'],outline='#FFFFFF',width=2*S)
    st=sorted(context['stations'],key=lambda s:math.dist(s['xy'],rep))
    named_stations=set()
    if not detail:
        for wanted in FEATURE_STATIONS.get(context['region']['region_id'],[]):
            target=next((s for s in st if station_key(s['name'])==wanted and panel.inside(s['xy'],18)),None)
            assert target is not None,('Missing feature station source',context['region']['region_id'],wanted)
            panel.square(target['xy'],'#384C5C','역',small=True)
            assert panel.label(target['xy'],wanted+'역',fill=BLUE,size=20,priority=True),('Feature station label fit',wanted)
            named_stations.add(wanted)
    seen=[]
    for s in st:
        if not panel.inside(s['xy'],12) or any(math.dist(s['xy'],xy)<100 for xy in seen):continue
        seen.append(s['xy']);panel.square(s['xy'],'#384C5C','역',small=not detail)
        key=station_key(s['name'])
        if key not in named_stations and len(panel.label_names)<(8 if detail else 3):
            if panel.label(s['xy'],s['name'].removesuffix('역')+'역',size=20 if detail else 17):named_stations.add(key)
    sc=sorted(context['schools'],key=lambda s:math.dist(s['xy'],rep))
    schools_shown=0
    for i,s in enumerate(sc):
        if not panel.inside(s['xy'],12):continue
        if detail or i<4:
            if detail and schools_shown>=12:continue
            schools_shown+=1
            panel.square(s['xy'],'#648373','학',small=not detail)
            if detail and len([n for n in panel.label_names if n.endswith('학교')])<4:panel.label(s['xy'],s['name'],size=18)
    commercial_shown=0
    def commerce_order(item):
        tag=item['tags'];major=0 if tag.get('shop') in ['mall','department_store'] else (1 if tag.get('amenity')=='marketplace' else 2)
        return major,math.dist(item['point'],rep)
    for item in sorted(commercial,key=commerce_order):
        p=item['point']
        if not panel.inside(p,12):continue
        if not detail and item['tags'].get('shop') not in ['mall','department_store'] and item['tags'].get('amenity')!='marketplace':continue
        if commercial_shown>=(8 if detail else 6):continue
        commercial_shown+=1
        x,y=panel.px(p);r=(8 if detail else 5)*S;panel.d.polygon([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],fill='#9B774F',outline='#FFFFFF',width=S)
        if detail and len([n for n in panel.label_names if n.startswith('상업:')])<3:
            name=item['tags'].get('name:ko') or item['tags'].get('name')
            if name and len(name)<23:panel.label(p,'상업: '+name,size=18)
    if panel.inside(rep,18):
        x,y=panel.px(rep);r=10*S;panel.d.ellipse((x-r,y-r,x+r,y+r),outline=BLUE,width=2*S)
    # Metric scale uses the same projected scale as the geographic content.
    metres=500 if detail else 2000;length=metres*panel.scale
    if length>w*.5:metres/=2;length/=2
    panel.d.line((20*S,(h-24)*S,(20+length)*S,(h-24)*S),fill=INK,width=2*S)
    panel.d.text((20*S,(h-48)*S),f'{int(metres)} m',font=F.setdefault((16,False),font(16)),fill=INK,stroke_width=S,stroke_fill='#FFFFFF')
    return panel

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--regions',nargs='+');args=ap.parse_args()
    coverage=read(E/'research/top20-split-v4/prices/coverage.json')['regions'];bands=read(E/'research/top20-split-v4/prices/legend.json')['bands']
    reps={r['region_id']:r for r in read(E/'research/top20-explain-v3/prices/final-api-20261103-v2/representatives.json')['rows']}
    tr=Transformer.from_crs(4326,5179,always_xy=True)
    assets=read(D/'map_assets.json')['assets'] if args.regions and (D/'map_assets.json').exists() else []
    if args.regions:assets=[a for a in assets if a['region_id'] not in args.regions]
    for row in coverage:
        if args.regions and row['region_id'] not in args.regions:continue
        rid=row['region_id'];c=read(C/f'{rid}_context.json');rep=reps[rid];centre=tr.transform(float(rep['longitude']),float(rep['latitude']))
        rawpath=C/'osm'/f'{rid}.json';osm=[]
        if rawpath.exists():
            for e in read(rawpath)['elements']:
                tags=e.get('tags',{});paths=[[tr.transform(*p) for p in ps] for ps in rawpaths(e) if len(ps)>1]
                point=tr.transform(e['lon'],e['lat']) if 'lon'in e else None
                if point is None and paths:
                    pp=[p for ps in paths for p in ps];point=(sum(p[0] for p in pp)/len(pp),sum(p[1] for p in pp)/len(pp))
                osm.append({'tags':tags,'paths':paths,'point':point})
        polys=[shape_rings(p['official_record_index']) for p in c['complex_points']]
        a,b,x,y=c['bounds_5179'];pad=max(x-a,y-b)*.05
        overview=[a-pad,b-pad,x+pad,y+pad];detail=[centre[0]-1800,centre[1]-1110,centre[0]+1800,centre[1]+1110]
        for mode in ['context','prices']:
            im=Image.new('RGB',(1920*S,1080*S),BG);d=ImageDraw.Draw(im)
            txt(im,(60,28),'데이터로 보는 부동산 | 신혼부부가 사는 곳',23)
            display_region='옛 서구(2024년)' if rid=='R01' else row['region']
            txt(im,(60,83),f"{row['rank']}위 · {c['region']['province']} {display_region}",43,bold=True)
            txt(im,(1080,95),f"84㎡ 지역 중위값 {money(row['region_median_manwon'])}",27,BLUE,True)
            txt(im,(60,153),f"구 전체 · 위치 확인 {row['mapped_complexes']}단지 / 거래 관측 {row['observed_complexes']}단지",23)
            txt(im,(760,153),f"생활권 상세 · {rep['apt_name_raw']}",24,bold=True)
            left=draw_panel(c,overview,640,625,False,osm,polys,centre,mode=='prices')
            right=draw_panel(c,detail,1100,625,True,osm,polys,centre,mode=='prices')
            im.paste(left.im,(60*S,205*S));im.paste(right.im,(760*S,205*S))
            # Same geographic detail rectangle on the overview, constrained to that panel.
            lp=[left.pos((detail[0],detail[1])),left.pos((detail[2],detail[3]))]
            ax=60+max(2,min(lp[0][0],lp[1][0]));bx=60+min(638,max(lp[0][0],lp[1][0]));ay=205+max(2,min(lp[0][1],lp[1][1]));by=205+min(623,max(lp[0][1],lp[1][1]))
            if bx>ax and by>ay:d.rectangle((ax*S,ay*S,bx*S,by*S),outline=BLUE,width=2*S)
            txt(im,(60,850),'단지별 중위가격',21,bold=True)
            for i,band in enumerate(bands):
                px=245+i*176;d.ellipse(((px)*S,855*S,(px+15)*S,870*S),fill=band['color'],outline='#FFFFFF',width=S)
                txt(im,(px+24,849),band['label'],22)
            for px,label,symbol,color in [(1380,'학교','학','#648373'),(1510,'역','역','#384C5C')]:
                d.rounded_rectangle((px*S,850*S,(px+22)*S,874*S),radius=3*S,fill=color)
                txt(im,(px+3,852),symbol,15,'#FFFFFF',True);txt(im,(px+30,849),label,21)
            d.polygon([(1628*S,862*S),(1637*S,853*S),(1646*S,862*S),(1637*S,871*S)],fill='#9B774F')
            txt(im,(1655,849),'상업시설',21)
            txt(im,(60,893),'2026.05~10 계약 · 전용 83~85㎡ · 11월 3일 조회',20)
            txt(im,(970,895),'지도: © OpenStreetMap contributors · ODbL / 학교·역: 공공 위치자료',16,fill='#576C75')
            d.rounded_rectangle((96*S,950*S,1824*S,1052*S),radius=12*S,fill='#FFFFFF')
            caption='점 하나는 거래와 위치가 확인된 아파트 단지입니다. 같은 색은 같은 가격대입니다.' if mode=='prices' else '단지와 역, 학교, 주요 상업시설의 위치를 함께 살펴봅니다.'
            f=font(32);bb=d.textbbox((0,0),caption,font=f);d.text(((1920*S-(bb[2]-bb[0]))/2,980*S),caption,font=f,fill=INK)
            file=OUT/f'{rid}_{mode}.png';im.resize((1920,1080),Image.Resampling.LANCZOS).save(file)
            assets.append({'region_id':rid,'mode':mode,'file':str(file.relative_to(E)),'width':1920,'height':1080,'source_osm_available':rawpath.exists(),'point_count':len(c['complex_points']) if mode=='prices' else 0,'detail_bounds_5179':detail,'overview_bounds_5179':overview,'displayed_detail_labels':right.label_names,'displayed_overview_labels':left.label_names,'price_bins_fixed':True,'timing':'not_locked_static_plate'})
        print(rid+' map plates saved'+('' if rawpath.exists() else ' (OSM base layer pending)'),flush=True)
    assets.sort(key=lambda a:(a['region_id'],a['mode']))
    (D/'map_assets.json').write_text(json.dumps({'revision':'top20-split-v4','assets':assets,'actual_narration_or_video_generated':False,'font':'existing Pretendard OFL woff2 via FreeType','sources':'atlas-context/coverage.json and osm/ledger.json; existing official apartment geometry and v4 price ledger'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
