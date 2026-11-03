from pathlib import Path
import json,subprocess,wave,io,hashlib,sys,numpy as np
EP=Path(__file__).resolve().parents[1];R=EP.parents[2];O=EP/'outputs/production-v1';C=EP/'editor/cache';C.mkdir(parents=True,exist_ok=True)
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';P=F.with_name('ffprobe.exe');p=json.loads((O/(sys.argv[2]if len(sys.argv)>2 else 'rendered_project.json')).read_text(encoding='utf8'));fps=30;sr=48000
def run(argv):
 z=subprocess.run(list(map(str,argv)),capture_output=True)
 if z.returncode:raise RuntimeError(z.stderr.decode('utf8',errors='replace')[-3000:])
 return z.stdout
def ff(a):return run([F,'-v','error','-y']+a)
def pcm(f):
 raw=ff(['-i',f,'-f','wav','-c:a','pcm_s16le','-ac','2','-ar','48000','pipe:1'])
 with wave.open(io.BytesIO(raw),'rb') as w:return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32).reshape(-1,2)/32768
def encode(name,start,end):
 rows=[s for s in p['visual_intervals'] if start<=s['start_frame'] and s['end_frame']<=end];assert sum(x['duration_frames'] for x in rows)==end-start
 lines=['ffconcat version 1.0']
 for s in rows:lines += [f"file '{Path(s['source_file']).as_posix()}'",'option framerate 30',f"duration {s['duration_frames']/30:.12f}"]
 lines += [f"file '{Path(rows[-1]['source_file']).as_posix()}'",'option framerate 30'];lst=C/(name+'.ffconcat');lst.write_text('\n'.join(lines)+'\n',encoding='utf8');out=C/(name+'.mp4')
 ff(['-f','concat','-safe','0','-i',lst,'-an','-r','30','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);return out
def brand(src,name,n):
 out=C/(name+'.mp4');ff(['-i',src,'-an','-r','30','-frames:v',n,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);return out
branddir=R/'video-agent-studio/episodes/goyang-changneung-20261015/outputs/production-v7-preview'
length=round(p['duration_frames']/30*sr);mix=np.zeros((length,2),np.float32)
for u in p['audio_units']:
 chunk=pcm(u['audio_path']);dst=round(u['start_frame']/30*sr);mix[dst:dst+len(chunk)]+=chunk
music=pcm(R/'video/public/changneung-v3/data_city_ambient_v1.wav');bed=np.tile(music,(int(np.ceil(length/len(music))),1))[:length]*.06
for start,n,file in [(p['intro_at'],150,'brand_intro_clean_v7.mp4'),(p['outro_start'],300,'brand_outro_clean_v7.mp4')]:
 a=round(start/30*sr);b=round((start+n)/30*sr);bed[a:b]=0;chunk=pcm(branddir/file);mix[a:min(a+len(chunk),b)]+=chunk[:b-a]
mix+=bed;raw_peak=float(np.max(np.abs(mix)));gain=min(1,.96/max(raw_peak,.00001));mix*=gain
wav=O/'full_mix.wav'
with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
aac=O/'full_mix.m4a';ff(['-i',wav,'-c:a','aac','-b:a','192k','-f','mp4',aac])
parts=[encode('opening',0,p['intro_at']),brand(branddir/'brand_intro_clean_v7.mp4','intro',150),encode('body',p['intro_at']+150,p['outro_start']),brand(branddir/'brand_outro_clean_v7.mp4','outro',300)]
lst=C/'full.ffconcat';lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{x.as_posix()}'\n" for x in parts),encoding='utf8');tag=sys.argv[1]if len(sys.argv)>1 else 'v1';out=O/f'gyosan_full_{tag}_free_tts.mp4';ff(['-f','concat','-safe','0','-i',lst,'-i',aac,'-map','0:v:0','-map','1:a:0','-c','copy','-t',p['duration_frames']/30,'-movflags','+faststart',out])
z=subprocess.run([str(P),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)],capture_output=True);q=json.loads(z.stdout);v=next(x for x in q['streams']if x['codec_type']=='video');a=next(x for x in q['streams']if x['codec_type']=='audio');assert z.returncode==0 and not z.stderr;assert int(v['nb_read_frames'])==p['duration_frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert float(q['format']['duration'])>=600
record=dict(file=str(out),sha256=hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),bytes=out.stat().st_size,duration_s=float(q['format']['duration']),probe=q,full_count_frames_decode=True,decode_exit_code=z.returncode,decode_stderr=z.stderr.decode(),mixed_pcm_peak=float(np.max(np.abs(mix))),master_gain=gain,voice='Local free Microsoft Heami rate2',paid_api_calls=0,actual_listening=False,continuous_playback=False,outro_after_audio_end_gap_s=(p['outro_start']-p['audio_units'][-1]['end_frame'])/30)
(O/'technical.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');(O/f'technical_{tag}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:record[k] for k in ['sha256','duration_s','bytes','paid_api_calls']}))
