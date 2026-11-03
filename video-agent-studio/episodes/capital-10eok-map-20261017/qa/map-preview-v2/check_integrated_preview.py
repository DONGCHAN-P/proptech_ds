from pathlib import Path
import json,hashlib,subprocess,collections
import pandas as pd
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'outputs/map-preview-v2';R=EP/'research/annual-map-v2';BIN=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pkt=read(R/'map_packet_v2.json');v=read(R/'validation.json');receipt=read(O/'preview_receipt.json');assert sha(R/'map_packet_v2.json')==v['packet_sha256']==receipt['packet_sha256']
for f in v['inputs']:assert sha(Path(f['path']))==f['sha256']
old=read(EP/'qa/data-and-map-v1/official_coordinate_independent_review.json')
for f in old['file_hashes']:assert sha(Path(f['file']))==f['sha256']
links=pd.read_parquet(EP/'research/coordinate-link-v2/coordinate_links_reviewed.parquet');geo=pd.read_parquet(EP/'research/coordinate-link-v2/capital_official_geometry.parquet').set_index('HSMP_INNB');states=pd.read_parquet(EP/'research/source-completion-v1/annual_status_complete.parquet').set_index(['complex_id','year']);eligible=set(links[links.map_eligible].complex_id)
assert set(c['complex_id'] for c in pkt['complexes'])==eligible and len(eligible)==8288
assert len(set(c['HSMP_INNB'] for c in pkt['complexes']))==8288
exact=0;reappear=0;annual=[]
for c in pkt['complexes']:
 g=geo.loc[c['HSMP_INNB']];assert c['PNU']==g.PNU and c['x_5179']==g.x_5179 and c['y_5179']==g.y_5179
 for y in pkt['years']:
  r=states.loc[(c['complex_id'],y)];a=c['years'][str(y)]
  assert a['status']==r.status and a['n']==r.n and c['first_valid_trade_year']==r.first_valid_trade_year
  assert (a['median_manwon'] is None and pd.isna(r.median_manwon)) or a['median_manwon']==r.median_manwon
  if a['median_manwon']==100000:exact+=1;assert a['status']=='under'
  if y>2006 and c['years'][str(y-1)]['status']=='over' and a['status']=='under':reappear+=1
for y in pkt['years']:
 count=collections.Counter(c['years'][str(y)]['status'] for c in pkt['complexes']);s=next(x for x in pkt['coverage'] if x['year']==y)
 for state,key in [('under','map_under'),('over','map_over'),('no_trade','map_no_trade'),('not_yet_observed','map_not_yet_observed')]:assert count[state]==s[key]
 assert s['map_observed']==count['under']+count['over'];assert sum(count.values())==8288;annual.append(s)
assert exact==v['exactly_10eok_shown']==174
assert reappear==v['adjacent_year_over_to_under']==374
boundary=read(ROOT/'assets/geo/sudogwon_sgg.geojson')
def inside(p,g):
 rings=g['coordinates'] if g['type']=='Polygon' else [r for poly in g['coordinates'] for r in poly];x,y=p;yes=False
 for ring in rings:
  for a,b in zip(ring,ring[1:]+ring[:1]):
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
anchors=[]
for lab in receipt['city_label_anchors']:
 f=next(x for x in boundary['features'] if x['properties']['name']==lab['anchor_feature']);assert inside(lab['anchor_5179'],f['geometry']);anchors.append(lab)
cfg=read(ROOT/'config/vertical_video_safe_area.json');rect=cfg['profiles'][cfg['default_profile']]['critical_rect'];bounds_count=0
for y in [2006,2025,2026]:
 doc=read(O/f'layout_bounds_{y}.json')
 for e in doc['elements']:
  l,t,r,b=e['bbox'];assert l>=rect['left'] and t>=rect['top'] and r<=rect['right'] and b<=rect['bottom'];assert e['font_px']>=24;bounds_count+=1
 fr=next(x for x in receipt['actual_data_frames'] if x['year']==y);s=next(x for x in annual if x['year']==y);assert fr['drawn']['under']==s['map_under'] and fr['drawn']['no_trade']==s['map_no_trade'];assert fr['above_threshold_drawn']==0
video=O/'style_preview_6s.mp4';before=sha(video)
p=subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True);probe=json.loads(p.stdout);vs=[s for s in probe['streams'] if s['codec_type']=='video'];assert len(probe['streams'])==len(vs)==1 and vs[0]['width']==1080 and vs[0]['height']==1920 and int(vs[0]['nb_frames'])==180 and vs[0]['r_frame_rate']=='30/1'
r=subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(video),'-an','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1'],capture_output=True,check=True)
buf=r.stdout;n=0;targets={0,59,60,119,120,179};frames=[]
while True:
 a=buf.find(b'\xff\xd8');b=buf.find(b'\xff\xd9',max(0,a))
 if a<0 or b<0:break
 if n in targets:
  path=Q/f'actual_frame_{n:03}.jpg';path.write_bytes(buf[a:b+2]);frames.append({'frame':n,'file':str(path),'sha256':sha(path)})
 n+=1;buf=buf[b+2:]
assert n==180 and sha(video)==before
contact=Image.new('RGB',(1080,1980),'#ddd');draw=ImageDraw.Draw(contact)
for i,f in enumerate(frames):
 im=Image.open(f['file']);im.thumbnail((360,640));x=i%3*360;y=i//3*660;contact.paste(im,(x,y+20));draw.text((x,y),str(f['frame']),fill='black')
contact=contact.crop((0,0,1080,1320));contact.save(Q/'encoded_contact.jpg')
result={'stage':'integrated_preview_v2','packet_sha256':sha(R/'map_packet_v2.json'),'video_sha256':before,'full_video_rendered':False,'preview_only':True,'draw_candidates':8288,'excluded':884,'all_21_year_packet_states_match_price_source':True,'exactly_10eok_under':exact,'adjacent_over_to_under_reappearances':reappear,'native_5179_coordinates_exact':True,'native_polygon_inside_review_inherited_from':str(EP/'qa/data-and-map-v1/official_coordinate_independent_review.json'),'independent_proj_checked':False,'lonlat_transform_used':False,'anchor_pip_count':len(anchors),'bbox_count':bounds_count,'safe_config_sha256':sha(ROOT/'config/vertical_video_safe_area.json'),'decoded_frames':n,'decode_exit_code':0,'audio_streams':0,'probe':probe,'actual_frames':frames,'annual_scope':annual,'actual_listening':False,'continuous_playback':False,'actual_frames_viewed':False}
(Q/'independent_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['probe','annual_scope','actual_frames']},ensure_ascii=True))
