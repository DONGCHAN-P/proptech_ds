from pathlib import Path
import json,subprocess,hashlib,wave,numpy as np
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v6-preview';C=E/'cache/assembly_r3';C.mkdir(parents=True,exist_ok=True)
B=R/'video/node_modules/@remotion/compositor-win32-x64-msvc';F=B/'ffmpeg.exe';P=B/'ffprobe.exe'
p=json.loads((O/'rendered_project_r3.json').read_text(encoding='utf-8'));fps=30
def run(cmd):
 z=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if z.returncode:raise RuntimeError(z.stderr.decode('utf-8',errors='replace')[-5000:])
 return z.stdout
def ff(a):return run([F,'-v','error','-y']+a)
def probe(f):return json.loads(run([P,'-v','error','-show_streams','-show_format','-of','json',f]))
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as g:
  for x in iter(lambda:g.read(8*1024*1024),b''):h.update(x)
 return h.hexdigest()
def encode(name,start,end):
 rows=[s for s in p['visual_intervals'] if start<=s['start_frame'] and s['end_frame']<=end];assert sum(s['duration_frames'] for s in rows)==end-start
 listing=C/(name+'.ffconcat');lines=['ffconcat version 1.0']
 for s in rows:lines.extend([f"file '{(O/s['frame_file']).as_posix()}'",'option framerate 30',f"duration {s['duration_frames']/fps:.12f}"])
 lines.extend([f"file '{(O/rows[-1]['frame_file']).as_posix()}'",'option framerate 30']);listing.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 out=C/(name+'.mp4');ff(['-f','concat','-safe','0','-i',listing,'-an','-r','30','-pix_fmt','yuv420p','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-video_track_timescale','90000',out]);print(name+' encoded',flush=True);return out
def normal(src,name,n):
 out=C/(name+'.mp4');ff(['-i',src,'-an','-r','30','-frames:v',n,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);return out
def pcm(src):
 import io
 data=ff(['-i',src,'-f','wav','-c:a','pcm_s16le','-ac','2','-ar','48000','pipe:1'])
 with wave.open(io.BytesIO(data),'rb') as w:
  assert w.getnchannels()==2 and w.getframerate()==48000
  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32).reshape(-1,2)/32768
print('Unchanged r2 AAC mix reused',flush=True)
parts=[encode('opening',0,p['intro_at']),normal(EP/'outputs/editor-preflight-v1/brand_intro_generic_v1.mp4','intro',150),encode('body',p['intro_at']+150,p['outro_start']),normal(EP/'outputs/editor-preflight-v1/brand_outro_generic_v1.mp4','outro',300)]
listing=C/'full.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{x.as_posix()}'\n" for x in parts),encoding='utf-8')
out=O/'changneung_full_v6_preview_r3.mp4';ff(['-f','concat','-safe','0','-i',listing,'-i',O/'full_mix_r2.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-t',p['duration_frames']/fps,'-movflags','+faststart',out]);q=probe(out);v=next(s for s in q['streams'] if s['codec_type']=='video');assert int(v['nb_frames'])==p['duration_frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert any(s['codec_type']=='audio' for s in q['streams']);pass # full stream decode is performed by verify_r2.py with ffprobe -count_frames
proofs=O/'final_proofs_r3';proofs.mkdir(exist_ok=True)
for name,t in [('intro_before',(p['intro_at']-1)/30),('intro_after',(p['intro_at']+150)/30),('commute',180),('price',380),('school',480),('outro_before',(p['outro_start']-1)/30),('outro_start',p['outro_start']/30)]:ff(['-ss',t,'-i',out,'-frames:v','1',proofs/(name+'.png')])
record={'file':out.name,'sha256':sha(out),'bytes':out.stat().st_size,'probe':q,'decode_exit_code':None,'decode_deferred_to':'verify_r2.py','actual_listening':False,'continuous_playback':False,'voice':'Free Windows Heami preview; final Jun timing not represented','bgm':'existing owned data_city_ambient_v1, gain0.075 under voice; approved brand audio preserved','duration_frames':p['duration_frames'],'speech_end_frame':p['speech_end_frame'],'outro_start_frame':p['outro_start'],'hold_frames':65,'signal_end_frame':p['signal_end_frame'],'signal_basis':'PCM abs>0.006; see cta_signal_r2.json'}
(O/'technical_r3.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print('MP4 complete '+str(out),flush=True)
