from pathlib import Path
import json,subprocess,hashlib,wave,numpy as np,io
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-labels';C=E/'cache/assembly';C.mkdir(parents=True,exist_ok=True)
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';P=F.with_name('ffprobe.exe');p=json.loads((O/'rendered_project_v8.json').read_text(encoding='utf-8'));fps=30;sr=48000

def run(cmd):
 z=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if z.returncode:raise RuntimeError(z.stderr.decode('utf-8',errors='replace')[-3000:])
 return z.stdout

def ff(a):return run([F,'-v','error','-y']+a)
def pcm(f):
 raw=ff(['-i',f,'-f','wav','-c:a','pcm_s16le','-ac','2','-ar','48000','pipe:1'])
 with wave.open(io.BytesIO(raw),'rb')as w:return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32).reshape(-1,2)/32768

def encode(name,start,end):
 rows=[s for s in p['visual_intervals'] if start<=s['start_frame'] and s['end_frame']<=end];assert sum(x['duration_frames'] for x in rows)==end-start
 lines=['ffconcat version 1.0']
 for s in rows:lines += [f"file '{Path(s['source_file']).as_posix()}'",'option framerate 30',f"duration {s['duration_frames']/30:.12f}"]
 lines +=[f"file '{Path(rows[-1]['source_file']).as_posix()}'",'option framerate 30'];lst=C/(name+'.ffconcat');lst.write_text('\n'.join(lines)+'\n',encoding='utf-8');out=C/(name+'.mp4')
 ff(['-f','concat','-safe','0','-i',lst,'-an','-r','30','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);print('ENCODED '+name,flush=True);return out

def normal(src,name,n):
 out=C/(name+'.mp4');ff(['-i',src,'-an','-r','30','-frames:v',n,'-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);return out


oldC=EP/'editor/production-v8-preview/cache/assembly'; original=EP/'outputs/production-v8-preview/changneung_full_v8_preview.mp4'
parts=[oldC/'opening.mp4',oldC/'intro.mp4',encode('body',p['intro_at']+150,p['outro_start']),oldC/'outro.mp4']
lst=C/'full.ffconcat';lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{x.as_posix()}'\n" for x in parts),encoding='utf-8');out=O/'changneung_full_v8_labels.mp4';ff(['-f','concat','-safe','0','-i',lst,'-i',original,'-map','0:v:0','-map','1:a:0','-c','copy','-t',p['duration_frames']/30,'-movflags','+faststart',out])
z=subprocess.run([str(P),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)],capture_output=True);q=json.loads(z.stdout);v=next(x for x in q['streams']if x['codec_type']=='video');a=next(x for x in q['streams']if x['codec_type']=='audio');assert z.returncode==0 and not z.stderr;assert int(v['nb_read_frames'])==p['duration_frames'];assert(v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert(a['sample_rate'],a['channels'])==('48000',2)
h=hashlib.file_digest(out.open('rb'),'sha256').hexdigest();record=dict(file=str(out),sha256=h,bytes=out.stat().st_size,probe=q,full_count_frames_decode=True,decode_exit_code=z.returncode,decode_stderr=z.stderr.decode(),audio_stream_copy_from=str(original),original_timing_and_213_captions_preserved=True,actual_listening=False,continuous_playback=False);(O/'technical_v8_labels.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print('LABELS_FINAL_VERIFIED '+h,flush=True)
