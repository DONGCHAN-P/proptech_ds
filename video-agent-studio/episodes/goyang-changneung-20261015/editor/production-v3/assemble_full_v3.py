from pathlib import Path
import argparse,json,subprocess,hashlib,shutil,time
import numpy as np
E=Path(__file__).resolve().parent;EP=E.parent.parent;ROOT=EP.parents[2];O=EP/'outputs/production-v3';CACHE=E/'cache/assembly';CACHE.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg-bin',required=True);ap.add_argument('--output-name',default='changneung_full_v3r2.mp4');args=ap.parse_args();B=Path(args.ffmpeg_bin);F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
project=json.loads((O/'rendered_project_v3.json').read_text(encoding='utf-8'));lock=json.loads((E/'timing_lock_v3.json').read_text(encoding='utf-8'));assert project['timing_lock_sha256']==hashlib.sha256((E/'timing_lock_v3.json').read_bytes()).hexdigest()
def run(cmd):
 result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-4000:])
 return result.stdout
def ff(a):return run([F,'-v','error','-y']+list(map(str,a)))
def probe(p):return json.loads(run([P,'-v','error','-show_streams','-show_format','-of','json',str(p)]))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(4*1024*1024),b''):h.update(c)
 return h.hexdigest()
def decode(src,name):
 p=CACHE/(name+'.f32')
 if not p.exists():ff(['-i',src,'-vn','-ar','48000','-ac','2','-c:a','pcm_f32le','-f','f32le',p])
 return np.memmap(p,dtype=np.float32,mode='r').reshape(-1,2)
voices={};source_audit=[]
for ch in lock['chapters']:
 sid=ch['scene_id'];src=EP/f'narration/audio-v3/{sid}.mp3';assert sha(src)==next(s['audio_sha256'] for s in lock['segments'] if s.get('scene_id')==sid and s['kind']=='narration');voices[sid]=decode(src,sid)
 source_audit.append({'scene_id':sid,'source_sha256':sha(src),'resampled_stereo_samples':len(voices[sid]),'original_mp3_preserved':True})
brand_intro=decode(EP/'outputs/editor-preflight-v1/brand_intro_generic_v1.mp4','brand_intro');brand_outro=decode(EP/'outputs/editor-preflight-v1/brand_outro_generic_v1.mp4','brand_outro');music=decode(ROOT/'video/public/changneung-v3/data_city_ambient_v1.wav','owned_music')
raw=CACHE/'full_mix.f32';total=lock['duration_frames']*1600;maxpeak=0;voice_ranges={sid:[] for sid in voices};mix_gain=.16
with raw.open('wb') as dest:
 for s in lock['segments']:
  count=s['duration_frames']*1600;kind=s['kind'];offset=s['start_frame']*1600
  if kind=='narration':
   sid=s['scene_id'];a=round(s['audio_start_s']*48000);b=min(round(s['audio_end_s']*48000),len(voices[sid]));voice_ranges[sid].append([a,b]);arr=np.zeros((count,2),np.float32);v=voices[sid][a:b];assert len(v)<=count;arr[:len(v)]=v*.9
  elif kind.startswith('brand'):arr=np.array((brand_intro if kind=='brand_intro' else brand_outro)[:count]);assert len(arr)==count
  else:arr=np.zeros((count,2),np.float32)
  if not kind.startswith('brand'):
   for k in range(0,count,4800):
    n=min(4800,count-k);global_sample=offset+k;voice=arr[k:k+n];rms=float(np.sqrt(np.mean(voice*voice)));target=.16 if rms>.008 else .27;mix_gain+=.35*(target-mix_gain)
    idx=(np.arange(n)+global_sample)%len(music);fadein=min(1,(global_sample+1)/24000);fadeout=min(1,max(0,(lock['outro_start_frame']*1600-global_sample)/72000));voice+=music[idx]*(mix_gain*fadein*fadeout)
  peak=float(np.abs(arr).max());maxpeak=max(maxpeak,peak);assert peak<1,peak;arr.astype(np.float32).tofile(dest)
assert raw.stat().st_size==total*8
for sid,ranges in voice_ranges.items():
 ranges.sort();assert ranges[0][0]==0 and ranges[-1][1]==len(voices[sid]);assert all(a[1]==b[0] for a,b in zip(ranges,ranges[1:])),sid
ff(['-f','f32le','-ar','48000','-ac','2','-i',raw,'-c:a','aac','-b:a','192k',O/'full_mix_v3.m4a'])
(O/'audio_mix_v3.json').write_text(json.dumps({'source_audio':source_audit,'all_source_resampled_PCM_samples_used_exactly_once':True,'source_ranges':voice_ranges,'sample_rate':48000,'channels':2,'samples_per_channel':total,'voice_gain':.9,'music':'existing Data City Ambient v1','music_signal_duck_gain_range':[.16,.27],'music_no_overlap_with_brand':True,'peak':maxpeak,'last_provider_to_outro_frames':90,'actual_listening':False,'source_PCM_not_regenerated':True},indent=2),encoding='utf-8')
print('Audio mixed; original resampled source ranges all preserved',flush=True)
def encode_images(name,start,end):
 states=[x for x in project['visual_intervals'] if x['kind']=='frame' and x['start_frame']>=start and x['end_frame']<=end];assert sum(x['duration_frames'] for x in states)==end-start
 listing=CACHE/(name+'.ffconcat');rows=['ffconcat version 1.0']
 for s in states:rows.extend([f"file '{(O/s['frame_file']).as_posix()}'",'option framerate 30',f"duration {s['duration_frames']/30:.12f}"])
 rows.extend([f"file '{(O/states[-1]['frame_file']).as_posix()}'",'option framerate 30']);listing.write_text('\n'.join(rows)+'\n',encoding='utf-8')
 dst=CACHE/(name+'.mp4');ff(['-f','concat','-safe','0','-i',listing,'-an','-vf','fps=30,format=yuv420p','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','18','-threads','4','-video_track_timescale','90000',dst]);v=next(x for x in probe(dst)['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==end-start
 print(f'{name} encoded {end-start} frames',flush=True);return dst
def normalize(src,name,n):
 dst=CACHE/(name+'.mp4');ff(['-i',src,'-an','-r','30','-frames:v',n,'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','90000',dst]);assert int(next(x for x in probe(dst)['streams'] if x['codec_type']=='video')['nb_frames'])==n;return dst
cta=project['cta_render'];prefix=encode_images('opening',0,613);intro=normalize(EP/'outputs/editor-preflight-v1/brand_intro_generic_v1.mp4','intro',150);body=encode_images('body',763,cta['start_frame']);cta_file=normalize(O/cta['file'],'cta',cta['duration_frames']);outro=normalize(EP/'outputs/editor-preflight-v1/brand_outro_generic_v1.mp4','outro',300)
parts=[(prefix,613),(intro,150),(body,cta['start_frame']-763),(cta_file,cta['duration_frames']),(outro,300)];assert sum(n for _,n in parts)==lock['duration_frames'];listing=CACHE/'full.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {n/30:.12f}\n" for p,n in parts),encoding='utf-8')
full=O/args.output_name;ff(['-f','concat','-safe','0','-i',listing,'-i',O/'full_mix_v3.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-t',lock['duration_s'],'-movflags','+faststart',full]);q=probe(full);v=next(x for x in q['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==lock['duration_frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert any(x['codec_type']=='audio' for x in q['streams']);ff(['-i',full,'-f','null','-'])
import sys
subprocess.run([sys.executable,str(E/'verify_final_v3.py'),'--ffmpeg-bin',args.ffmpeg_bin,'--input-name',args.output_name],check=True)
