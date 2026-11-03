from pathlib import Path
import json,subprocess,argparse,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;O=EP/'outputs/production-v3';C=E/'cache/assembly'
ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg-bin',required=True);a=ap.parse_args();B=Path(a.ffmpeg_bin);F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
def run(cmd):
 x=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if x.returncode:raise RuntimeError(x.stderr.decode('utf-8',errors='replace')[-2000:])
 return x.stdout
def ff(x):return run([F,'-v','error','-y']+list(map(str,x)))
def probe(p):return json.loads(run([P,'-v','error','-show_streams','-show_format','-of','json',str(p)]))
def nv(p):return int(next(s for s in probe(p)['streams'] if s['codec_type']=='video')['nb_frames'])
p=json.loads((O/'rendered_project_v3.json').read_text(encoding='utf-8'));body=C/'body.mp4';n=nv(body);v=next(x for x in p['visual_intervals'] if x['start_frame']==763);assert v['shot']['kind']=='previous'
packets=json.loads(run([P,'-v','error','-select_streams','v:0','-read_intervals','0%+20','-show_packets','-show_entries','packet=pts_time,flags','-of','json',str(body)]))['packets'];keyframes=sorted(round(float(x['pts_time'])*30) for x in packets if 'K' in x['flags'] and float(x['pts_time'])>0);assert keyframes;cut=keyframes[0]
prefix=C/'body_r2_prefix.mp4';tail=C/'body_r2_tail.mp4';image=O/v['frame_file']
ff(['-i',body,'-loop','1','-i',image,'-filter_complex',"[0:v][1:v]overlay=0:0:enable='eq(n,0)',format=yuv420p[v]",'-map','[v]','-an','-frames:v',cut,'-c:v','libx264','-crf','18','-preset','fast','-video_track_timescale','90000',prefix]);assert nv(prefix)==cut
ff(['-ss',cut/30,'-i',body,'-map','0:v:0','-an','-c:v','copy','-video_track_timescale','90000',tail]);assert nv(tail)==n-cut,(nv(tail),n-cut)
cta=p['cta_render'];parts=[(C/'opening.mp4',613),(C/'intro.mp4',150),(prefix,cut),(tail,n-cut),(C/'cta.mp4',cta['duration_frames']),(C/'outro.mp4',300)];assert sum(n for _,n in parts)==24140;listing=C/'full_r2.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{f.as_posix()}'\nduration {n/30:.12f}\n" for f,n in parts),encoding='utf-8')
full=O/'changneung_full_v3r2.mp4';ff(['-f','concat','-safe','0','-i',listing,'-i',O/'full_mix_v3.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-t',24140/30,'-movflags','+faststart',full]);assert nv(full)==24140
result={'file':str(full),'sha256':hashlib.sha256(full.read_bytes()).hexdigest(),'base_file':'changneung_full_v3.mp4','base_sha256':hashlib.sha256((O/'changneung_full_v3.mp4').read_bytes()).hexdigest(),'changed_global_frames':[763],'short_reencoded_body_prefix_frames':cut,'body_tail_stream_copied_frames':n-cut,'all_other_segments_stream_copied':True,'audio_source_unchanged':'full_mix_v3.m4a','duration_frames':24140,'actual_listening':False}
(O/'boundary_patch_r2.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
