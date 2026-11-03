from pathlib import Path
import argparse,json,hashlib,subprocess
E=Path(__file__).resolve().parent;EP=E.parent.parent;O=EP/'outputs/production-v3'
ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg-bin',required=True);ap.add_argument('--input-name',default='changneung_full_v3r2.mp4');a=ap.parse_args();B=Path(a.ffmpeg_bin);F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
def run(cmd):
 x=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if x.returncode:raise RuntimeError(x.stderr.decode('utf-8',errors='replace')[-2500:])
 return x.stdout
project=json.loads((O/'rendered_project_v3.json').read_text(encoding='utf-8'));lock=json.loads((E/'timing_lock_v3.json').read_text(encoding='utf-8'));full=O/a.input_name;q=json.loads(run([P,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(full)]));v=next(x for x in q['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==int(v['nb_read_frames'])==24140;assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert any(x['codec_type']=='audio' for x in q['streams'])
frames=sorted({0,612,613,762,763,764,765,23747,23748,23749,lock['last_provider_spoken_frame'],lock['outro_start_frame']-1,lock['outro_start_frame'],lock['duration_frames']-1,*[(s['start_frame']+s['end_frame'])//2 for s in project['shots']]})
actual=O/('actual_frames_'+full.stem);actual.mkdir(exist_ok=True)
for batch in range(0,len(frames),80):
 group=[f for f in frames[batch:batch+80] if not (actual/f'frame_{f:06}.png').exists()]
 if not group:continue
 expr='+'.join(f'eq(round(t*30),{f})' for f in group)
 run([F,'-v','error','-y','-i',str(full),'-vf',"select='"+expr+"'",'-fps_mode','passthrough',str(actual/f'batch_{batch}_%04d.png')])
 for i,f in enumerate(group,1):(actual/f'batch_{batch}_{i:04d}.png').replace(actual/f'frame_{f:06}.png')
 print(f'Extracted {min(batch+80,len(frames))}/{len(frames)} encoded frames',flush=True)
h=hashlib.sha256(full.read_bytes()).hexdigest();result={'file':str(full),'sha256':h,'probe':q,'duration_frames':24140,'fps':30,'whole_decode_passed':True,'actual_sampled_frames':frames,'actual_frame_directory':actual.name,'extraction_basis':'continuous PTS round(t*30); passthrough image output; not resettable filter n','caption_count':len(project['captions']),'shots':len(project['shots']),'timing_lock_sha256':project['timing_lock_sha256'],'actual_listening':False,'continuous_playback':False,'QA_pending':True,'cache_only_paths':['editor/production-v3/cache/assembly','editor/production-v3/cache/public','editor/production-v3/cache/bundle']};(O/'technical_full_v3.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'sha256':h,'frames':24140,'duration_s':24140/30,'samples':len(frames)}),flush=True)
