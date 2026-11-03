from pathlib import Path
import json,hashlib,subprocess,io,math
import numpy as np
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];O=EP/'outputs/monthly-5eok-v1';R=EP/'research/monthly-5eok-v1';BIN=EP.parents[2]/'video/node_modules/@remotion/compositor-win32-x64-msvc'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=read(Q/'monthly_data_independent_review.json')
for f in data['file_hashes']:assert sha(Path(f['file']))==f['sha256']
summ=read(R/'monthly_summary.json');logs=read(O/'motion_frame_log.json');tl=read(O/'timeline.json');tech=read(O/'technical_receipt.json');cache=read(O/'cache_receipt.json');assert len(logs)==1710 and tl['total_frames']==1710 and tl['month_frames']==6 and len(tl['months'])==250
for f,r in enumerate(logs):
 if f<90:mi,prev,a,pos,phase=0,0,1.,0.,'opening_hold'
 elif f>=1590:mi,prev,a,pos,phase=249,249,1.,249.,'ending_hold'
 else:
  k=f-90;mi=k//6;u=(k%6+1)/6;prev=max(0,mi-1);a=u*u*(3-2*u);pos=max(0.,mi-1+u);phase='monthly_motion'
 assert r['frame']==f and r['month_index']==mi and r['previous_month_index']==prev and r['month']==summ[mi]['month'] and abs(r['alpha_smoothstep']-a)<1e-12 and abs(r['chart_time_position']-pos)<1e-12 and r['phase']==phase
 assert r['actual_map_under']==summ[mi]['map_under'] and r['actual_map_observed']==summ[mi]['map_observed'] and not r['numbers_interpolated']
for i,m in enumerate(tl['months']):assert m['month']==summ[i]['month'] and m['start_frame']==90+6*i and m['end_frame_exclusive']==96+6*i
for i,rr in enumerate(cache['source_draw_counts']):assert rr['under_drawn']==summ[i]['map_under'] and rr['no_trade_drawn']==summ[i]['map_no_trade'] and rr['over_hidden']==summ[i]['map_over'] and rr['first_observation_hidden']==summ[i]['map_not_yet_observed']
v=O/'capital_5eok_monthly_2006-2026_v1.mp4';before=sha(v);assert before==tech['sha256']=='18e73426dea8ceba5f2819d205f4941e2136fb89a2af22654456d080ce0b965a'
probe=json.loads(subprocess.run([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(v)],capture_output=True,check=True).stdout);assert len(probe['streams'])==1;s=probe['streams'][0];assert s['codec_type']=='video' and s['width']==1080 and s['height']==1920 and int(s['nb_frames'])==1710 and s['r_frame_rate']=='30/1' and s['sample_aspect_ratio']=='1:1'
# 월 패널 숫자/날짜 영역만 비교. 지도·chart의모션을정적PNG와비교하지않는다.
static=Image.open(O/'cache/static.png').convert('RGB');refs={}
for mi in range(250):
 im=static.copy();panel=Image.open(O/f'cache/panel_{mi:03}.png').convert('RGBA');im.paste(panel,(0,380),panel);refs[mi]=np.asarray(im.resize((375,667),Image.Resampling.BILINEAR),dtype=np.float32)[210:247]
targets={0,89,90,95,96,97,98,99,100,101,1589,1590,1709}
for start in [966,1254,1584]:targets.update(range(start-1,start+6))
for i in [0,49,99,149,199,249]:targets.add(90+6*i+5)
targets=sorted(targets);d=subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(v),'-an','-vf','scale=375:667','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1'],capture_output=True,check=True)
buf=d.stdout;n=0;maes=[];bright=[];diffs=[];last=None;frames=[]
while True:
 a=buf.find(b'\xff\xd8');b=buf.find(b'\xff\xd9',max(a,0))
 if a<0 or b<0:break
 jpg=buf[a:b+2];im=Image.open(io.BytesIO(jpg)).convert('RGB');arr=np.asarray(im,dtype=np.float32);mi=logs[n]['month_index'];maes.append(float(np.abs(arr[210:247]-refs[mi]).mean()));bright.append(int((arr[90:247].max(axis=2)>150).sum()))
 if last is not None:diffs.append({'frame':n,'map_mae':float(np.abs(arr[270:622]-last[270:622]).mean()),'chart_mae':float(np.abs(arr[150:197]-last[150:197]).mean())})
 if n in targets:
  f=Q/f'actual_frame_{n:04}.jpg';f.write_bytes(jpg);frames.append({'frame':n,'month':logs[n]['month'],'alpha':logs[n]['alpha_smoothstep'],'file':str(f)})
 last=arr;n+=1;buf=buf[b+2:]
assert n==1710 and sha(v)==before and max(maes)<8 and min(bright)>300
for start in range(0,len(frames),12):
 batch=frames[start:start+12];canvas=Image.new('RGB',(1500,2061),'#ddd');draw=ImageDraw.Draw(canvas)
 for i,f in enumerate(batch):
  x=i%4*375;y=i//4*687;canvas.paste(Image.open(f['file']),(x,y+20));draw.text((x,y),f"{f['frame']} {f['month']} a{f['alpha']:.3f}",fill='black')
 canvas.save(Q/f'motion_contact_{start//12+1}.jpg')
active=[x for x in diffs if 96<=x['frame']<1590];result={'video_file':str(v),'sha256':before,'bytes':v.stat().st_size,'frame_count':1710,'duration_s':57,'fps':30,'probe':probe,'audio_streams':0,'decode_exit_code':0,'all_1710_frame_log_formula_checks':True,'all_250_month_endpoint_draw_counts_match':True,'all_1710_actual_date_counter_roi_compared':True,'max_date_counter_roi_mae':max(maes),'min_header_bright_pixels':min(bright),'active_map_nonidentical_adjacent_frames':sum(x['map_mae']>0.005 for x in active),'active_chart_nonidentical_adjacent_frames':sum(x['chart_mae']>0.005 for x in active),'active_adjacent_frames':len(active),'selected_frames':frames,'motion_differences':diffs,'actual_samples_viewed':False,'actual_listening':False,'continuous_playback':False,'actual_device_playback':False,'limits':['점RGB는월간endpoint사이smoothstep전환이며가격중위값·거래건수·위치를보간하지않음.','chart커서는실측월간값을시각적으로연결하며중간월값을만들지않음.','v3큰지도episodeoverride와앱UI가림위험승계.']}
(Q/'motion_independent_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:result[k] for k in ['frame_count','sha256','max_date_counter_roi_mae','min_header_bright_pixels','active_map_nonidentical_adjacent_frames','active_chart_nonidentical_adjacent_frames','active_adjacent_frames']}))
