from pathlib import Path
import argparse,json,subprocess,hashlib,shutil,time
import numpy as np
E=Path(__file__).resolve().parent;EP=E.parent.parent;ROOT=EP.parents[2];O=EP/'outputs/production-v4';CACHE=E/'cache/assembly';CACHE.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg-bin',required=True);ap.add_argument('--output-name',default='changneung_full_v4.mp4');args=ap.parse_args();B=Path(args.ffmpeg_bin);F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
project=json.loads((O/'rendered_project_v4.json').read_text(encoding='utf-8'));lock=json.loads((E.parent/'production-v3/timing_lock_v3.json').read_text(encoding='utf-8'));assert project['timing_lock_sha256']==hashlib.sha256((E.parent/'production-v3/timing_lock_v3.json').read_bytes()).hexdigest()
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
full=O/args.output_name;ff(['-f','concat','-safe','0','-i',listing,'-i',EP/'outputs/production-v3/full_mix_v3.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-t',lock['duration_s'],'-movflags','+faststart',full]);q=probe(full);v=next(x for x in q['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==lock['duration_frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert any(x['codec_type']=='audio' for x in q['streams']);ff(['-i',full,'-f','null','-'])

(O/'technical_v4.json').write_text(json.dumps({'file':full.name,'sha256':sha(full),'bytes':full.stat().st_size,'probe':q,'decode_exit_code':0,'aac_source':'outputs/production-v3/full_mix_v3.m4a','audio_reencoded':False,'actual_listening':False},indent=2),encoding='utf-8')
print('검증된 조립 경로로 v4 출력 완료',flush=True)
