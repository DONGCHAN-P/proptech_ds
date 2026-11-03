from pathlib import Path
import subprocess,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v6-ui-r5';OLD=EP/'outputs/production-v6-preview';B=R/'video/node_modules/@remotion/compositor-win32-x64-msvc';F=B/'ffmpeg.exe';P=B/'ffprobe.exe'
def run(a):
 z=subprocess.run(list(map(str,a)),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if z.returncode:raise RuntimeError(z.stderr.decode('utf-8',errors='replace')[-5000:])
 return z.stdout
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def ff(a):return run([F,'-v','error','-y']+a)
def still(file,frame,out):ff(['-ss',f'{frame/30:.9f}','-i',file,'-frames:v','1',out])
p=json.loads((O/'rendered_project_r5.json').read_text(encoding='utf-8'));video=O/'changneung_full_v6_ui_r5.mp4';tech=json.loads((O/'technical_r5.json').read_text(encoding='utf-8'))
z=subprocess.run([str(P),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);q=json.loads(z.stdout);v=next(s for s in q['streams'] if s['codec_type']=='video');a=next(s for s in q['streams'] if s['codec_type']=='audio');assert z.returncode==0 and z.stderr==b'' and int(v['nb_read_frames'])==28018;assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert (a['sample_rate'],a['channels'])==('48000',2)
tech.update(decode_exit_code=z.returncode,full_frame_decode_probe=q,decode_stderr='',decode_method='ffprobe -count_frames decodes video/audio streams; not packet count; no null encoder claim',sha256=sha(video));(O/'technical_r5.json').write_text(json.dumps(tech,ensure_ascii=False,indent=2),encoding='utf-8');print('full decode 28018 frames passed',flush=True)
D=O/'encoded_evidence';D.mkdir(exist_ok=True);m=[];seen=set();font=ImageFont.truetype(str(R/'video/public/changneung-v3/Pretendard-Regular.woff2'),18) if False else ImageFont.load_default()
segments=[]
for i,x in enumerate(p['intervals']):
 if x['r5_props']['mode']=='baseline':continue
 if i==0 or p['intervals'][i-1]['semantic_key']!=x['semantic_key']:segments.append(x)
for i,x in enumerate(segments):
 f=x['start_frame'];files=[]
 for d in [0,15,30,44]:
  frame=min(f+d,x['end_frame']-1);name=f's{i:03d}_f{frame:05d}.png';still(video,frame,D/name);files.append(name)
 m.append({'scene_id':x['scene_id'],'unit':x.get('unit'),'start_frame':f,'semantic_key':x['semantic_key'],'caption':x['props']['caption'],'samples':files})
for j in range(0,len(m),12):
 rows=m[j:j+12];sheet=Image.new('RGB',(1536,12//3*312),'#eee');draw=ImageDraw.Draw(sheet)
 for k,x in enumerate(rows):
  im=Image.open(D/x['samples'][-1]).convert('RGB').resize((512,288));xx=k%3*512;yy=k//3*312;sheet.paste(im,(xx,yy));draw.text((xx+4,yy+290),f"{x['scene_id']} {x['start_frame']/30:.2f}s {json.loads(x['semantic_key'])[0:3]}",fill='black',font=font)
 sheet.save(D/f'changed_contactsheet_{j//12+1:02d}.jpg',quality=92)
 print(f'actual changed sheet {j//12+1}',flush=True)
clips=[]
for mode,phase in [('plan',''),('commute',''),('transit',''),('rail',''),('price','delta'),('school','education'),('supply',''),('family',''),('decision','')]:
 candidates=[x for x in segments if x['r5_props']['mode']==mode and (not phase or x['r5_props']['phase']==phase) and x['r5_props']['focus'] not in ['all','overview']]
 if not candidates:continue
 x=candidates[0];f=x['start_frame'];name=f'motion_{mode}.mp4';ff(['-ss',f'{f/30:.9f}','-i',video,'-an','-t','3','-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',D/name]);samples=[];arrays=[]
 for d in [0,1,15,30,44,60]:
  out=D/f'motion_{mode}_{d:02d}.png';still(D/name,d,out);samples.append(out.name);arrays.append(np.asarray(Image.open(out).convert('RGB'),dtype=np.int16))
 changes=[int((np.max(np.abs(arrays[i]-arrays[0]),axis=2)>20).sum()) for i in range(1,len(arrays))];assert max(changes[:4])>20,(mode,changes)
 clips.append({'mode':mode,'file':name,'start_frame_in_full':f,'duration_frames':90,'fps':30,'silent':True,'source':'actual final encoded full MP4','samples':samples,'pixels_changed_vs_first_over20':changes,'human_continuous_playback':False})
 print('encoded continuous sample '+mode,flush=True)
for mode,t in [('price',395),('supply',610),('family',804)]:
 still(video,round(t*30),D/f'mobile_{mode}_after.png');im=Image.open(D/f'mobile_{mode}_after.png');im.resize((512,288)).save(D/f'mobile_{mode}_512.png')
 before=EP/'qa/viewer-review-v1/frames'/f'{t:04d}s.jpg'
 if before.exists():
  board=Image.new('RGB',(1024,320),'#f6f4ef');board.paste(Image.open(before).convert('RGB').resize((512,288)),(0,0));board.paste(im.resize((512,288)),(512,0));draw=ImageDraw.Draw(board);draw.text((10,294),f'R4 before / {t}s',fill='black',font=font);draw.text((522,294),f'R5 actual encoded / {t}s',fill='black',font=font);board.save(D/f'mobile_compare_{mode}.png')
boundaries=[]
for frame in [254,255,404,405,15184,15185,15200,15316,15317,27627,27628,27717,27718,28017]:
 name=f'boundary_f{frame:05d}.png';still(video,frame,D/name);boundaries.append({'frame':frame,'file':name})
record={'full_mp4':str(video),'sha256':sha(video),'scope':'Actual final encoded samples; no human continuous playback or listening claimed','changed_segments':m,'motion_clips':clips,'boundaries':boundaries,'timing':'measured unit endpoints; proportional internal clause estimate; not forced alignment','input_invariants':{'script':sha(EP/'outputs/script-review-v6/script_v6.md'),'audio_mix':sha(OLD/'full_mix_r2.m4a'),'r4':sha(OLD/'changneung_full_v6_preview_r4.mp4')},'total_frames':28018,'intro_start':255,'intro_end':405,'outro_start':27718,'signal_end':27628}
(O/'encoded_evidence_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('evidence complete',flush=True)
