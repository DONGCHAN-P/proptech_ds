from pathlib import Path
import json,hashlib,subprocess,struct
import numpy as np
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'outputs/production-v3';C=EP/'editor/production-v3/cache/assembly';F=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
lock=json.loads((EP/'editor/production-v3/timing_lock_v3.json').read_text('utf8'))
def execute(args):
 r=subprocess.run([str(F),'-v','error']+list(map(str,args)),capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout
def decode(p):
 w=execute(['-i',p,'-vn','-ar','48000','-ac','2','-c:a','pcm_s16le','-f','wav','pipe:1']);i=12
 while i+8<len(w):
  name=w[i:i+4];size=struct.unpack_from('<I',w,i+4)[0]
  if name==b'data':return np.frombuffer(w[i+8:i+8+min(size,len(w)-i-8)],np.int16).reshape(-1,2).astype(np.float32)/32768
  i+=8+size+(size%2)
 raise RuntimeError('no PCM data chunk')
voice_checks=[]
for c in lock['chapters']:
 sid=c['scene_id'];a=decode(EP/f'narration/audio-v3/{sid}.mp3');b=np.memmap(C/(sid+'.f32'),dtype=np.float32,mode='r').reshape(-1,2)
 voice_checks.append({'scene_id':sid,'samples':len(a),'cache_samples':len(b),'max_abs_error':float(np.max(np.abs(a-b))) if a.shape==b.shape else None})
stream_hashes=[]
for f in ['changneung_full_v3.mp4','full_mix_v3.m4a']:
 data=execute(['-i',O/f,'-vn','-c:a','copy','-f','adts','pipe:1']);stream_hashes.append({'file':f,'aac_adts_sha256':hashlib.sha256(data).hexdigest(),'aac_bytes':len(data)})
raw=np.memmap(C/'full_mix.f32',dtype=np.float32,mode='r').reshape(-1,2);music=np.memmap(C/'owned_music.f32',dtype=np.float32,mode='r').reshape(-1,2)
gain=.16;errors=[]
for s in lock['segments']:
 count=s['duration_frames']*1600;offset=s['start_frame']*1600;kind=s['kind']
 if kind=='narration':
  v=np.memmap(C/(s['scene_id']+'.f32'),dtype=np.float32,mode='r').reshape(-1,2);a=round(s['audio_start_s']*48000);b=min(round(s['audio_end_s']*48000),len(v));arr=np.zeros((count,2),np.float32);arr[:b-a]=v[a:b]*.9
 elif kind.startswith('brand'):arr=np.array(np.memmap(C/('brand_intro.f32' if kind=='brand_intro' else 'brand_outro.f32'),dtype=np.float32,mode='r').reshape(-1,2)[:count])
 else:arr=np.zeros((count,2),np.float32)
 if not kind.startswith('brand'):
  for k in range(0,count,4800):
   n=min(4800,count-k);g=offset+k;target=.16 if float(np.sqrt(np.mean(arr[k:k+n]*arr[k:k+n])))>.008 else .27;gain+=.35*(target-gain);fadein=min(1,(g+1)/24000);fadeout=min(1,max(0,(lock['outro_start_frame']*1600-g)/72000));arr[k:k+n]+=music[(np.arange(n)+g)%len(music)]*(gain*fadein*fadeout)
 errors.append({'kind':kind,'start_frame':s['start_frame'],'samples':count,'max_abs_error':float(np.max(np.abs(arr-raw[offset:offset+count])))})
report={'original_decode_vs_cache':voice_checks,'final_aac_stream_vs_mix':stream_hashes,'aac_streams_identical':stream_hashes[0]['aac_adts_sha256']==stream_hashes[1]['aac_adts_sha256'],'reconstructed_declared_mix_vs_raw':errors,'peak_raw':float(np.max(np.abs(raw))),'actual_listening':False,'limits':'Signal/cache/mix identity does not verify speech pronunciation or subjective loudness.'}
(Q/'audio_signal_audit.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2),flush=True)
