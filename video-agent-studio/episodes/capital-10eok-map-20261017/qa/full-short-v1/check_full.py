from pathlib import Path
import json,hashlib,subprocess,io,collections
import numpy as np
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'outputs/full-short-v1';BIN=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
video=O/'capital_10eok_2006-2026_v1.mp4';vsha=sha(video);assert vsha=='fbf5e3868f7a706261863719a8e348c3a7e5a0b1bdf5366a15da8a7605190ec6'
timeline=read(O/'timeline.json');receipt=read(O/'render_receipt.json');pkt=read(EP/'research/annual-map-v2/map_packet_v2.json');prior=read(EP/'qa/map-preview-v3/final_review.json');assert sha(EP/'research/annual-map-v2/map_packet_v2.json')==prior['packet_sha256']
assert timeline['frames']==1200 and timeline['duration_s']==40
expected=[];targets={0,1199};mids={};end=0
for s in timeline['segments']:
 assert s['start_frame']==end and s['end_frame_exclusive']-s['start_frame']==s['frames'];end=s['end_frame_exclusive'];expected.extend([s['year']]*s['frames'])
 for f in [s['start_frame']-1,s['start_frame'],s['start_frame']+1,s['end_frame_exclusive']-1]:
  if 0<=f<1200:targets.add(f)
 mids.setdefault(s['year'],(s['start_frame']+s['end_frame_exclusive'])//2)
targets.update(mids.values());assert end==len(expected)==1200;assert sorted(mids)==list(range(2006,2027))
stats=[];references={}
for fr in receipt['actual_data_frames']:
 y=fr['year'];st=next(x for x in pkt['coverage'] if x['year']==y);count=collections.Counter(c['years'][str(y)]['status'] for c in pkt['complexes']);assert fr['map_under']==count['under']==st['map_under'];assert fr['map_observed']==st['map_observed']==count['under']+count['over'];assert fr['drawn']['no_trade']==count['no_trade'];assert fr['over_hidden']==count['over'];assert abs(fr['ratio']-100*count['under']/st['map_observed'])<1e-9
 f=O/fr['file'];assert sha(f)==fr['sha256'];references[y]=np.array(Image.open(f).convert('RGB').resize((375,667),Image.Resampling.BILINEAR),dtype=np.float32);stats.append({'year':y,'under':count['under'],'observed':st['map_observed'],'ratio':fr['ratio'],'source_png_sha256':sha(f)})
for y in [2006,2025,2026]:assert (O/f'year_{y}.png').read_bytes()==(EP/f'outputs/map-preview-v3/year_{y}.png').read_bytes()
probe=json.loads(subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True).stdout);assert len(probe['streams'])==1;s=probe['streams'][0];assert s['codec_type']=='video' and s['width']==1080 and s['height']==1920 and s['r_frame_rate']=='30/1' and int(s['nb_frames'])==1200
d=subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(video),'-an','-vf','scale=375:667','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1'],capture_output=True,check=True)
buf=d.stdout;n=0;errors=[];frames=[];means=[]
while True:
 a=buf.find(b'\xff\xd8');b=buf.find(b'\xff\xd9',max(0,a))
 if a<0 or b<0:break
 jpg=buf[a:b+2];im=Image.open(io.BytesIO(jpg)).convert('RGB');arr=np.asarray(im,dtype=np.float32);ref=references[expected[n]];mae=float(np.abs(arr-ref).mean());errors.append(mae);means.append(float(arr.mean()))
 if n in targets:
  f=Q/f'actual_frame_{n:04}.jpg';f.write_bytes(jpg);frames.append({'frame':n,'year':expected[n],'file':str(f),'mae_to_expected_year_png':mae})
 n+=1;buf=buf[b+2:]
assert n==1200 and sha(video)==vsha;assert max(errors)<4,('wrong frame or flash',max(errors),int(np.argmax(errors)))
for start in range(0,21,7):
 ys=list(range(2006,2027))[start:start+7];canvas=Image.new('RGB',(1125,2061),'#ddd');draw=ImageDraw.Draw(canvas)
 for j,y in enumerate(ys):
  im=Image.open(Q/f'actual_frame_{mids[y]:04}.jpg');x=j%3*375;yy=j//3*687;canvas.paste(im,(x,yy+20));draw.text((x,yy),f'{y} frame{mids[y]}',fill='black')
 canvas.save(Q/f'years_contact_{start//7+1}.jpg')
header=Image.new('RGB',(1125,1540),'#ddd');draw=ImageDraw.Draw(header)
for j,y in enumerate(range(2006,2027)):
 im=Image.open(Q/f'actual_frame_{mids[y]:04}.jpg').crop((0,90,375,290));x=j%3*375;yy=j//3*220;header.paste(im,(x,yy+20));draw.text((x,yy),str(y),fill='black')
header.save(Q/'all_year_headers.jpg')
result={'scope':'40초 전체 무음쇼츠 독립기술·프레임대조','video_file':str(video),'sha256':vsha,'bytes':video.stat().st_size,'frame_count':n,'duration_s':40,'audio_streams':0,'probe':probe,'packet_sha256':prior['packet_sha256'],'all_21_counter_ratio_checks':stats,'actual_selected_frames':frames,'all_1200_frames_compared_to_expected_year_source_png':True,'max_mean_absolute_rgb_error':max(errors),'worst_frame':int(np.argmax(errors)),'min_frame_rgb_mean':min(means),'flash_detection_method':'모든375px디코드프레임을해당시점예상연도원본PNG와비교. 최대MAE<4. 별도시청대체아님.','decode_exit_code':0,'stderr':d.stderr.decode(errors='replace'),'actual_frames_viewed':False,'actual_listening':False,'continuous_playback':False,'actual_device_playback':False,'episode_override_preserved':True}
(Q/'independent_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'frames':n,'max_mae':max(errors),'selected':len(frames),'video_sha':vsha}))
