from pathlib import Path
import json,hashlib,sys,time,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];O=E/'outputs/full-short-v1';F=E/'visual/map-preview-v1';sys.path.insert(0,str(P));from geometry import rings,inside
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
chart=[(y,stats[y]['map_under']/stats[y]['map_observed']*100) for y in range(2006,2027)];assert all(70<=r<=100 for y,r in chart);cx0,cx1,cy0,cy1=70,878,435,557;cp=lambda y,r:(cx0+(y-2006)/20*(cx1-cx0),cy1-(r-70)/30*(cy1-cy0));allreceipts=[]
for year in range(2006,2027):
 im=Image.new('RGB',(1080,1920),navy);d=ImageDraw.Draw(im);bounds=[];st=stats[year];ratio=st['map_under']/st['map_observed']*100
 def text(name,s,x,y,size,bold=False,color=white,kind='text'):
  fo=font(size,bold);box=d.textbbox((x,y),s,font=fo,anchor='lt');assert box[0]>=48 and box[2]<=920 and box[1]>=0 and box[3]<=1920,(name,box);d.text((x,y),s,font=fo,fill=color,anchor='lt');bounds.append({'name':name,'text':s,'bbox':list(box),'font_px':size,'kind':kind,'position':[x,y],'bold':bold,'color':color})
 text('title','수도권, 10억으로 어디까지?',64,274,54,True);text('scope','84㎡급 · 연중위값 · 연결 8,288 / 제외 884',66,346,30,color=muted);text('trend_label','10억 이하 비율',66,395,28,color=muted);text('trend_ratio',f'{ratio:.1f}%',710,389,40,True,orange)
 d.line([(cx0,cy0),(cx1,cy0)],fill='#18283d',width=1);d.line([(cx0,cy1),(cx1,cy1)],fill='#18283d',width=1)
 # True annual observations, piecewise straight line; explicit y-axis is 70%..100%.
 d.line([cp(y,r) for y,r in chart],fill='#263a50',width=3)
 active=[cp(y,r) for y,r in chart if y<=year]
 if len(active)>1:d.line(active,fill='#ff9f5b',width=4)
 px,py=cp(year,ratio);d.ellipse([px-6,py-6,px+6,py+6],fill=orange);text('ymax','100%',66,436,22,color=muted);text('ymin','70%',66,535,22,color=muted);text('firstyear','2006',66,570,25,color=muted);text('lastyear','2026',816,570,25,color=muted)
 text('year',str(year),64,612,82,True);text('large_counter',f"{st['map_under']:,} / {st['map_observed']:,}",433,623,48,True,orange);text('counter_label','10억 이하 / 당해 관측 단지',435,681,28,color=muted)
 layer=base.copy();ld=ImageDraw.Draw(layer);counts={'under':0,'no_trade':0}
 for state,color,radius in [('no_trade',dim,1.55),('under',orange,2.3)]:
  for c in pkt['complexes']:
   if c['years'][str(year)]['status']!=state:continue
   assert year>=c['first_valid_trade_year'];x,y=pr(xy[c['complex_id']]);assert 0<=x<W and 0<=y<H;ld.ellipse([(x-radius)*scl,(y-radius)*scl,(x+radius)*scl,(y+radius)*scl],fill=color);counts[state]+=1
 for lab in labels:
  x,y=pr(lab['native_anchor']);tx=x+lab['offset'][0];ty=y+lab['offset'][1];fo=font(35*scl,True);box=ld.textbbox((tx*scl,ty*scl),lab['text'],font=fo,anchor='mm');box=[box[0]-10,box[1]-6,box[2]+10,box[3]+6];ld.line([(x*scl,y*scl),(tx*scl,ty*scl)],fill='#7d91a7',width=2);ld.rounded_rectangle(box,radius=12,fill=navy);ld.text((tx*scl,ty*scl),lab['text'],font=fo,anchor='mm',fill=white);bounds.append({'name':'place_'+lab['text'],'text':lab['text'],'bbox':[box[0]/scl,maptop+box[1]/scl,box[2]/scl,maptop+box[3]/scl],'font_px':35,'kind':'map_label','anchor_native':lab['native_anchor'],'anchor_feature':lab['anchor_feature']})
 assert counts['under']==st['map_under'] and counts['no_trade']==st['map_no_trade'];im.paste(layer.resize((W,H),Image.Resampling.LANCZOS),(0,maptop));d=ImageDraw.Draw(im)
 for item in bounds:
  if item['kind']!='map_label':d.text(tuple(item['position']),item['text'],font=font(item['font_px'],item['bold']),fill=item['color'],anchor='lt')
 # Essential current-year conditions are short and remain above the crowded bottom metadata zone.
 text('partial','2026 부분연도' if year==2026 else '연결 표본 기준',66,724,26,color=muted);text('legend_under','10억 이하',90,1817,25,color=muted);text('legend_no_trade','당해 미거래',320,1817,25,color=muted);text('legend_over','초과 숨김',610,1817,25,color=muted);d.ellipse([66,1824,80,1838],fill=orange);d.ellipse([296,1824,310,1838],fill=dim);text('exclusion','미연결 884단지 제외 · 최대 계약일 2026.10.10',66,1854,25,color=muted)
 file=O/f'year_{year}.png';im.save(file);(O/f'layout_bounds_{year}.json').write_text(json.dumps({'episode_override':True,'text_right_limit':920,'map_background_bleed':True,'elements':bounds},ensure_ascii=False,indent=2),encoding='utf8');allreceipts.append({'year':year,'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'drawn':counts,'map_observed':st['map_observed'],'map_under':st['map_under'],'ratio':ratio,'over_hidden':st['map_over']})
shapepr=[pr(p) for f,r in main for p in r];shape_w=max(x for x,y in shapepr)-min(x for x,y in shapepr);point_w=max(pr(p)[0] for p in xy.values())-min(pr(p)[0] for p in xy.values());v2=json.loads((E/'outputs/map-preview-v2/preview_receipt.json').read_text(encoding='utf8'));v2h=v2['fixed_viewport'][3]-v2['fixed_viewport'][1];v2scale=min((660-24)/(ext[2]-ext[0]),(v2h-16)/(ext[3]-ext[1]));v2shape=(max(p[0] for f,r in main for p in r)-min(p[0] for f,r in main for p in r))*v2scale;assert shape_w>=850 and shape_w/v2shape>=2.5
receipt={'preview_only':False,'full_video':True,'actual_data_frames':allreceipts,'coordinate_crs':'native EPSG5179 direct','coordinate_count':8288,'unlinked_count':884,'packet_sha256':hashlib.sha256(PACK.read_bytes()).hexdigest(),'fixed_extent_5179':ext,'map_viewport':[0,maptop,W,maptop+H],'actual_mainland_geometry_width_px':shape_w,'actual_point_cloud_width_px':point_w,'v2_mainland_geometry_width_px':v2shape,'map_scale_gain_vs_v2':shape_w/v2shape,'native_dot_radius_px':2.3,'dot_diameter_at_375px':4.6*375/1080,'heatmap':False,'blur_or_glow':False,'trend_statistic':'map_under/map_observed each contract year; explicit 70..100 percent axis','layout_override':{'reason':'User explicitly rejected tiny v2 map and requested reference-like edge-to-edge readability. Conservative rect is not used to shrink the map.','map_bleed':True,'episode_only':True,'not_all_device_safe_guarantee':True},'audio_generated':False,'reference_asset_copied':False,'reference_music_copied':False,'city_label_anchors':labels};(O/'render_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'shape_width_px':shape_w,'point_cloud_width_px':point_w,'gain_vs_v2':shape_w/v2shape},ensure_ascii=False))



