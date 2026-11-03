from pathlib import Path
import sys,json,hashlib,math,time
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];O=E/'outputs/map-preview-v2';V=E/'visual/map-preview-v1';sys.path.insert(0,str(P));from geometry import rings,inside
packet_path=E/'research/annual-map-v2/map_packet_v2.json';pkt=json.loads(packet_path.read_text(encoding='utf8'));assert pkt['preview_only'] and pkt['map_catalog']==8288 and not pkt['coordinate_legacy_geocoder_used'];B=R/'assets/geo/sudogwon_sgg.geojson';boundary=json.loads(B.read_text(encoding='utf8'));safe=[156,448,816,1160];cfg=json.loads((R/'config/vertical_video_safe_area.json').read_text(encoding='utf8'));assert list(cfg['profiles'][cfg['default_profile']]['critical_rect'].values())==safe
cream='#f6f4ef';ink='#173348';blue='#286cda';gray='#b4bdbb';muted='#647780';fontcache={}
def font(n,bold=False):
 k=(n,bold)
 if k not in fontcache:fontcache[k]=ImageFont.truetype(str(V/('Pretendard-Bold.ttf' if bold else 'Pretendard-Regular.ttf')),n)
 return fontcache[k]
allrings=[(f,r) for f in boundary['features'] for r in rings(f['geometry'])];main=[(f,r) for f,r in allrings if sum(x for x,y in r)/len(r)>=900000];remote=[(f,r) for f,r in allrings if sum(x for x,y in r)/len(r)<900000];xy={c['complex_id']:(c['x_5179'],c['y_5179']) for c in pkt['complexes']};points=[p for f,r in main for p in r]+list(xy.values());extent=[min(x for x,y in points)-2500,min(y for x,y in points)-2500,max(x for x,y in points)+2500,max(y for x,y in points)+2500];W,H=660,344;scale=min((W-24)/(extent[2]-extent[0]),(H-16)/(extent[3]-extent[1]));pr=lambda p:(W/2+(p[0]-(extent[0]+extent[2])/2)*scale,H/2-(p[1]-(extent[1]+extent[3])/2)*scale)
def representative(f):
 rr=rings(f['geometry']);ps=[p for r in rr for p in r];lo=min(p[1] for p in ps);hi=max(p[1] for p in ps);best=None
 for fct in [.3,.4,.5,.6,.7]:
  y=lo+(hi-lo)*fct;xs=[]
  for r in rr:
   for a,b in zip(r,r[1:]+r[:1]):
    if (a[1]>y)!=(b[1]>y):xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
  xs.sort()
  for a,b in zip(xs[::2],xs[1::2]):
   p=((a+b)/2,y)
   if inside(p,f['geometry']) and (best is None or b-a>best[0]):best=(b-a,p)
 assert best;return best[1]
# Label anchors derive from actual named district geometry, not invented city coordinates.
label_defs=[('서울','종로구',(-52,-48)),('인천','부평구',(-118,7)),('수원','수원시 팔달구',(52,35)),('고양','고양시 덕양구',(-105,-36)),('성남','성남시 중원구',(65,-7))];labels=[]
for name,feature,offset in label_defs:
 f=next(f for f in boundary['features'] if f['properties']['name']==feature);anchor=representative(f);assert inside(anchor,f['geometry']);labels.append({'text':name,'anchor_feature':feature,'anchor_5179':list(anchor),'offset_px':list(offset)})
S=2;base=Image.new('RGB',(W*S,H*S),cream);d=ImageDraw.Draw(base)
for f,r in main:d.polygon([(pr(p)[0]*S,pr(p)[1]*S) for p in r],fill={'서울':'#e0e7e6','인천':'#ece5d7','경기':'#ecebe3'}[f['properties']['region']],outline='#bbc7c6',width=2)
# Remote islands are a fixed contextual inset. Eligible observation points use their native position in main extent.
if remote:
 ps=[p for f,r in remote for p in r];rb=[min(x for x,y in ps),min(y for x,y in ps),max(x for x,y in ps),max(y for x,y in ps)];rk=min(106/(rb[2]-rb[0]),72/(rb[3]-rb[1]));rpr=lambda p:((76+(p[0]-(rb[0]+rb[2])/2)*rk)*S,(H-46-(p[1]-(rb[1]+rb[3])/2)*rk)*S);d.rounded_rectangle([12*S,(H-88)*S,140*S,(H-5)*S],radius=12,fill='#eeece5',outline='#cbd1cf',width=2)
 for f,r in remote:d.polygon([rpr(p) for p in r],fill='#dfdfd4',outline='#bbc7c6')
receipts=[];stats={s['year']:s for s in pkt['coverage']};started=time.perf_counter()
for year in [2006,2025,2026]:
 im=Image.new('RGB',(1080,1920),cream);dd=ImageDraw.Draw(im);bounds=[]
 def text(name,txt,x,y,size,kind='conditions',bold=False,color=ink):
  fo=font(size,bold);b=dd.textbbox((x,y),txt,font=fo,anchor='lt');assert b[0]>=safe[0] and b[1]>=safe[1] and b[2]<=safe[2] and b[3]<=safe[3],(name,b,txt);dd.text((x,y),txt,font=fo,anchor='lt',fill=color);bounds.append({'name':name,'text':txt,'font_px':size,'kind':kind,'bbox':list(b)})
 st=stats[year];text('title','10억으로 살 수 있던 아파트',156,448,44,'title',True);text('year',str(year)+('년 · 부분연도' if year==2026 else '년'),156,502,48,'key_value',True,blue);text('counter',f"{st['map_under']:,} / {st['map_observed']:,}단지",156,557,48,'key_value',True);text('counter_definition','10억 이하 / 당해 거래관측 · 지도 연결 단지',156,613,24)
 layer=base.copy();ld=ImageDraw.Draw(layer);drawn={'under':0,'no_trade':0};outside=0
 for state,color,radius in [('no_trade',gray,1.45),('under',blue,1.9)]:
  for c in pkt['complexes']:
   v=c['years'][str(year)]
   if v['status']!=state:continue
   assert year>=c['first_valid_trade_year'];x,y=pr(xy[c['complex_id']]);assert 0<=x<W and 0<=y<H,(c['name'],x,y);ld.ellipse([(x-radius)*S,(y-radius)*S,(x+radius)*S,(y+radius)*S],fill=color);drawn[state]+=1
 # City labels stay at geometry-derived leader origins and are drawn in a separate readable layer.
 for lab in labels:
  x,y=pr(lab['anchor_5179']);tx=x+lab['offset_px'][0];ty=y+lab['offset_px'][1];fo=font(28*S,True);bb=ld.textbbox((tx*S,ty*S),lab['text'],font=fo,anchor='mm');bb=[bb[0]-8,bb[1]-5,bb[2]+8,bb[3]+5];assert min(bb)>=0 and bb[2]<=W*S and bb[3]<=H*S;ld.line([(x*S,y*S),(tx*S,ty*S)],fill='#758b93',width=2);ld.ellipse([(x-2)*S,(y-2)*S,(x+2)*S,(y+2)*S],fill=ink);ld.rounded_rectangle(bb,radius=10,fill=cream);ld.text((tx*S,ty*S),lab['text'],font=fo,anchor='mm',fill=ink);bounds.append({'name':'place_'+lab['text'],'kind':'place_label','text':lab['text'],'font_px':28,'bbox':[156+bb[0]/S,650+bb[1]/S,156+bb[2]/S,650+bb[3]/S],'anchor_feature':lab['anchor_feature'],'anchor_5179':lab['anchor_5179']})
 im.paste(layer.resize((W,H),Image.Resampling.LANCZOS),(156,650));assert drawn['under']==st['map_under'] and drawn['no_trade']==st['map_no_trade'];text('legend_under','10억 이하',178,1007,24,color=muted);text('legend_no_trade','당해 거래 없음',365,1007,24,color=muted);text('legend_hidden','초과 숨김',645,1007,24,color=muted);dd.ellipse([156,1013,168,1025],fill=blue);dd.ellipse([343,1013,355,1025],fill=gray);text('condition','83≤전용<85㎡ · 연중위값 · 취소 제외',156,1044,24,color=muted);text('source','국토부 실거래 · 부동산원 단지(2025)',156,1074,24,color=muted);text('exclusions','SGIS·statgarten(MIT) · 미연결 884개',156,1104,24,color=muted);text('period','2026은 부분연도 · 최대 계약일 10.10',156,1134,24,color=muted)
 fn=f'year_{year}.png';im.save(O/fn);(O/f'layout_bounds_{year}.json').write_text(json.dumps({'safe_rect':safe,'elements':bounds},ensure_ascii=False,indent=2),encoding='utf8');receipts.append({'year':year,'file':fn,'sha256':hashlib.sha256((O/fn).read_bytes()).hexdigest(),'drawn':drawn,'above_threshold_drawn':0,'first_observation_rule_passed':True,'source_statistics':st})
receipt={'preview_only':True,'years':[2006,2025,2026],'actual_data_frames':receipts,'safe_rect':safe,'fixed_viewport':[156,650,816,994],'projection':'native EPSG5179 direct, no geographic round trip','boundary_projection':'existing SGIS-derived simplified boundary native coordinates; provenance-linked EPSG5179 assumption independently checked by prior map QA','packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),'boundary_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),'fixed_extent_5179':extent,'coordinate_source':'official 2025 REB housing-complex geometry','city_label_anchors':labels,'all_points_inside_viewport':True,'zooms':False,'actual_listening':False,'continuous_playback':False,'render_seconds':time.perf_counter()-started};(O/'preview_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'years':[2006,2025,2026],'seconds':receipt['render_seconds']},ensure_ascii=False))

