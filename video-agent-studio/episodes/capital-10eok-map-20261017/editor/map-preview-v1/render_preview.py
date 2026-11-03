from pathlib import Path
import json,hashlib,time,sys,argparse
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent));from geometry import forward,rings
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];V=E/'visual/map-preview-v1';O=E/'outputs/map-preview-v1';O.mkdir(parents=True,exist_ok=True)
C=json.loads((R/'config/vertical_video_safe_area.json').read_text(encoding='utf-8'));rect=C['profiles'][C['default_profile']]['critical_rect'];safe=[rect[k] for k in ['left','top','right','bottom']]
ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);a=ap.parse_args();packet_path=Path(a.packet);packet=json.loads(packet_path.read_text(encoding='utf-8'));assert packet['prototype_only'] is True;assert packet['threshold_manwon']==100000
boundary=json.loads((R/'assets/geo/sudogwon_sgg.geojson').read_text(encoding='utf-8'));cream='#f6f4ef';blue='#286cda';ink='#173348';muted='#637580';fonts={}
def font(size,bold=False):
 key=(size,bold)
 if key not in fonts:fonts[key]=ImageFont.truetype(str(V/('Pretendard-Bold.ttf' if bold else 'Pretendard-Regular.ttf')),size)
 return fonts[key]
xy={c['complex_id']:forward(c['lon'],c['lat']) for c in packet['complexes']};allrings=[(f,r) for f in boundary['features'] for r in rings(f['geometry'])];main=[(f,r) for f,r in allrings if sum(p[0] for p in r)/len(r)>=900000];remote=[(f,r) for f,r in allrings if sum(p[0] for p in r)/len(r)<900000]
pts=[p for f,r in main for p in r]+list(xy.values());bb=[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)];pad=3500;bb=[bb[0]-pad,bb[1]-pad,bb[2]+pad,bb[3]+pad];viewport=[156,586,816,956];w,h=660,370;k=min((w-20)/(bb[2]-bb[0]),(h-20)/(bb[3]-bb[1]));pr=lambda p:(round(w/2+(p[0]-(bb[0]+bb[2])/2)*k,2),round(h/2-(p[1]-(bb[1]+bb[3])/2)*k,2))
basemap=Image.new('RGB',(w,h),cream);bd=ImageDraw.Draw(basemap)
for f,r in main:bd.polygon([pr(p) for p in r],fill={'서울':'#e2e8e7','인천':'#ece7da','경기':'#edece5'}[f['properties']['region']],outline='#bbc5c5',width=1)
# Remote islands are context in a fixed inset; all actual points stay in main extent.
if remote:
 rp=[p for f,r in remote for p in r];rb=[min(p[0] for p in rp),min(p[1] for p in rp),max(p[0] for p in rp),max(p[1] for p in rp)];rk=min(108/(rb[2]-rb[0]),78/(rb[3]-rb[1]));bd.rounded_rectangle([6,276,132,366],radius=8,fill='#eeece5',outline='#cbd1cf');rpr=lambda p:(69+(p[0]-(rb[0]+rb[2])/2)*rk,321-(p[1]-(rb[1]+rb[3])/2)*rk)
 for f,r in remote:bd.polygon([rpr(p) for p in r],fill='#dedfd6',outline='#aebbb9')
basemap.save(V/'basemap_cache.png');bounds=[];receipts=[];t0=time.perf_counter();stats={s['year']:s for s in packet['coverage']};peak=max([y for y in packet['years'] if y<2026],key=lambda y:stats[y]['map_over']);years=[2006,peak,2026]
for year in years:
 im=Image.new('RGB',(1080,1920),cream);d=ImageDraw.Draw(im);elements=[]
 def text(name,txt,x,y,size,kind='condition_source',bold=False,color=ink):
  f=font(size,bold);bbx=d.textbbox((x,y),txt,font=f,anchor='lt');assert bbx[0]>=safe[0] and bbx[1]>=safe[1] and bbx[2]<=safe[2] and bbx[3]<=safe[3],(name,bbx);d.text((x,y),txt,font=f,fill=color,anchor='lt');elements.append({'name':name,'kind':kind,'text':txt,'bbox':list(bbx),'font_px':size})
 text('title','10억 이하, 수도권 84㎡',156,448,44,'title',True)
 text('year',str(year)+(' · 부분연도' if year==2026 else '년'),156,503,52,'key_value',True,color=blue)
 s=stats[year];eligible=[c for c in packet['complexes'] if year>=int(c['first_valid_trade_year'])];map_obs=sum(c['years'][str(year)]['status'] in ['under','over'] for c in eligible);map_under=sum(c['years'][str(year)]['status']=='under' for c in eligible);text('map_denominator',f"지도 표시: 관측 {map_obs:,} / 이하 {map_under:,}",156,558,24)
 layer=basemap.copy();ld=ImageDraw.Draw(layer);counts={'under':0,'over':0,'no_trade':0,'not_yet_observed':0};prior_build=0
 for wanted,color,radius in [('no_trade','#b3bbb9',1.7),('under',blue,2.4)]:
  for c in packet['complexes']:
   v=c['years'][str(year)];status=v['status']
   if status!=wanted:continue
   if year<int(c['first_valid_trade_year']):prior_build+=1;continue
   x,y=pr(xy[c['complex_id']]);assert 0<=x<w and 0<=y<h;ld.ellipse([x-radius,y-radius,x+radius,y+radius],fill=color);counts[wanted]+=1
 counts['over']=sum(c['years'][str(year)]['status']=='over' for c in packet['complexes']);counts['not_yet_observed']=sum(c['years'][str(year)]['status']=='not_yet_observed' for c in packet['complexes']);im.paste(layer,(156,586))
 text('preview_watermark','데이터 검증 중 · 시안',156,600,24,bold=True,color=muted)
 text('all_observed',f"보유자료 관측 {s['observed_complexes']:,}단지",156,965,36,'key_value',True)
 text('all_under',f"10억 이하 {s['under']:,}단지",156,1006,36,'key_value',True,color=blue)
 text('legend_under','10억 이하',180,1050,24,color=muted)
 text('legend_missing','미거래',360,1050,24,color=muted)
 text('excluded',f"좌표제외 {s['observed_complexes']-s['map_observed']:,}",580,1050,24,color=muted)
 d.ellipse([158,1055,170,1067],fill=blue);d.ellipse([338,1055,350,1067],fill='#b3bbb9')
 text('source','국토부 보유자료 · 연중위값(일부누락)',156,1081,24,color=muted)
 text('condition','83≤전용<85㎡ · 첫관측전 미표시',156,1108,24,color=muted)
 text('boundary_source','경계: SGIS·statgarten(MIT)',156,1135,24,color=muted)
 file=O/f'year_{year}.png';im.save(file);bbdoc={'safe_rect':safe,'elements':elements};(O/f'layout_bounds_{year}.json').write_text(json.dumps(bbdoc,ensure_ascii=False,indent=2),encoding='utf-8');bounds.extend(elements);receipts.append({'year':year,'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'drawn':counts,'source_statistics':s,'skipped_before_first_observation':prior_build,'map_eligible_observed':map_obs,'map_eligible_under':map_under})
receipt={'preview_only':True,'packet':str(packet_path),'packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),'years':years,'projection':'GRS80 UTM-K EPSG5179, SGIS provenance-linked inference, local file metadata absent','fixed_extent_projected':bb,'fixed_viewport':viewport,'all_candidate_points_inside_main_extent':True,'remote_boundary_inset':bool(remote),'point_radius':{'under':2.4,'no_trade':1.7},'above_threshold_points_drawn':0,'font':'Pretendard existing WOFF2 locally decoded with Node Brotli','render_seconds':time.perf_counter()-t0,'actual_data_frames':receipts,'price_carry_forward':False,'coordinate_precision_verified':False,'audio_generated':False,'full_video_rendered':False}
(O/'preview_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');(O/'layout_bounds.json').write_text(json.dumps({'safe_rect':safe,'elements':bounds},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'years':years,'render_seconds':receipt['render_seconds'],'files':[x['file'] for x in receipts]},ensure_ascii=False))
