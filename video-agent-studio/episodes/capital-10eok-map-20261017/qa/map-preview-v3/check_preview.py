from pathlib import Path
import json,hashlib,subprocess,collections
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'outputs/map-preview-v3';BIN=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pkt=read(EP/'research/annual-map-v2/map_packet_v2.json');receipt=read(O/'preview_receipt.json');prior=read(EP/'qa/map-preview-v2/final_review.json');assert sha(EP/'research/annual-map-v2/map_packet_v2.json')==receipt['packet_sha256']==prior['packet_sha256'];checks=[]
for fr in receipt['actual_data_frames']:
 y=fr['year'];st=next(x for x in pkt['coverage'] if x['year']==y);counts=collections.Counter(c['years'][str(y)]['status'] for c in pkt['complexes'])
 assert fr['map_under']==fr['drawn']['under']==counts['under']==st['map_under'];assert fr['map_observed']==counts['under']+counts['over']==st['map_observed'];assert fr['drawn']['no_trade']==counts['no_trade'];assert fr['over_hidden']==counts['over'];assert abs(fr['ratio']-100*counts['under']/st['map_observed'])<1e-10
 assert sha(O/fr['file'])==fr['sha256'];bounds=read(O/f'layout_bounds_{y}.json')['elements'];outside_conservative=[];outside_canvas=[]
 for b in bounds:
  l,t,r,bb=b['bbox']
  if not (0<=l<r<=1080 and 0<=t<bb<=1920):outside_canvas.append(b['name'])
  if not(l>=156 and t>=448 and r<=816 and bb<=1160):outside_conservative.append(b['name'])
 assert not outside_canvas
 checks.append({'year':y,'under':counts['under'],'observed':st['map_observed'],'no_trade':counts['no_trade'],'over':counts['over'],'ratio':fr['ratio'],'outside_conservative':outside_conservative,'outside_canvas':outside_canvas})
video=O/'style_preview_9s.mp4';before=sha(video);pr=subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True);probe=json.loads(pr.stdout);assert len(probe['streams'])==1;vs=probe['streams'][0];assert vs['codec_type']=='video' and vs['width']==1080 and vs['height']==1920 and int(vs['nb_frames'])==270 and vs['r_frame_rate']=='30/1'
d=subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(video),'-an','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1'],capture_output=True,check=True)
buf=d.stdout;n=0;targets={0,89,90,179,180,269};frames=[]
while True:
 a=buf.find(b'\xff\xd8');b=buf.find(b'\xff\xd9',max(a,0))
 if a<0 or b<0:break
 if n in targets:
  f=Q/f'actual_frame_{n:03}.jpg';f.write_bytes(buf[a:b+2]);frames.append({'frame':n,'file':str(f),'sha256':sha(f)})
 n+=1;buf=buf[b+2:]
assert n==270 and sha(video)==before
for f in frames:
 im=Image.open(f['file']);im.resize((375,667),Image.Resampling.LANCZOS).save(Q/f"phone375_frame_{f['frame']:03}.png")
contact=Image.new('RGB',(1125,1374),'#eee');draw=ImageDraw.Draw(contact)
for i,f in enumerate(frames):
 im=Image.open(Q/f"phone375_frame_{f['frame']:03}.png");x=i%3*375;y=i//3*687;contact.paste(im,(x,y+20));draw.text((x,y),str(f['frame']),fill='black')
contact.save(Q/'encoded_phone375_contact.jpg')
# 앱 실제 측정이 아닌 기존 보수적 모형의 위험 표시. 사용자 episode override를 취소하지 않는다.
im=Image.open(Q/'phone375_frame_180.png').convert('RGBA');over=Image.new('RGBA',im.size,(0,0,0,0));draw=ImageDraw.Draw(over);draw.rectangle([0,0,375,667*.14],fill=(255,0,0,70));draw.rectangle([0,667*.65,375,667],fill=(255,0,0,70));draw.rectangle([311,0,375,667],fill=(255,0,0,40));Image.alpha_composite(im,over).convert('RGB').save(Q/'modeled_ui_risk_375.png')
out={'preview_only':True,'video_sha256':before,'packet_sha256':receipt['packet_sha256'],'decoded_frames':n,'decode_exit_code':0,'audio_streams':0,'probe':probe,'year_checks':checks,'actual_frames':frames,'map_shape_width_px':receipt['actual_mainland_geometry_width_px'],'map_scale_gain':receipt['map_scale_gain_vs_v2'],'point_cloud_width_px':receipt['actual_point_cloud_width_px'],'conservative_override_applied':True,'actual_listening':False,'continuous_playback':False,'actual_frames_viewed':False,'limitations':['전체 conservative bbox를 통과한 판이 아님. 사용자 episode override로 지도 bleed와 큰 배치를 검토.','일부조건·범례·지도남부는 앱 UI에 가릴 수 있음. 모형위험표시이며 실기기·실앱 재생 아님.','기존21년가격·좌표정합은 동일packet SHA로승계,새9초시안3연도만actual검수.']}
(Q/'independent_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'video_sha256':before,'frames':n,'checks':checks},ensure_ascii=True))
