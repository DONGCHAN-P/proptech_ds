from pathlib import Path
import json,subprocess,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v2';C=E/'cache/assembly';C.mkdir(parents=True,exist_ok=True)
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';P=F.with_name('ffprobe.exe')
def run(a):
 z=subprocess.run(list(map(str,a)),capture_output=True)
 if z.returncode:raise RuntimeError(z.stderr.decode('utf8',errors='replace')[-3000:])
 return z.stdout
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
p=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));fps=30
def encode(name,start,end):
 rows=[x for x in p['visual_intervals'] if start<=x['start_frame'] and x['end_frame']<=end];assert sum(x['duration_frames'] for x in rows)==end-start
 lines=['ffconcat version 1.0']
 for x in rows:lines.extend([f"file '{Path(x['source_file']).as_posix()}'",'option framerate 30',f"duration {x['duration_frames']/30:.12f}"])
 lines.extend([f"file '{Path(rows[-1]['source_file']).as_posix()}'",'option framerate 30']);lst=C/(name+'.ffconcat');lst.write_text('\n'.join(lines)+'\n',encoding='utf8');out=C/(name+'.mp4')
 run([F,'-v','error','-y','-f','concat','-safe','0','-i',lst,'-an','-r','30','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','20','-threads','8','-pix_fmt','yuv420p','-video_track_timescale','90000',out]);return out
old=EP/'editor/cache';parts=[old/'opening.mp4',old/'intro.mp4',encode('body',p['intro_at']+150,p['outro_start']),old/'outro.mp4'];assert all(x.exists() for x in parts)
lst=C/'full.ffconcat';lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{x.as_posix()}'\n" for x in parts),encoding='utf8')
audio=EP/'outputs/production-v1/full_mix.m4a';out=O/'gyosan_review_v2_free_tts.mp4'
run([F,'-v','error','-y','-f','concat','-safe','0','-i',lst,'-i',audio,'-map','0:v:0','-map','1:a:0','-c','copy','-t',p['duration_frames']/30,'-movflags','+faststart',out])
q=json.loads(run([P,'-v','error','-count_frames','-show_streams','-show_format','-of','json',out]));v=next(x for x in q['streams'] if x['codec_type']=='video');a=next(x for x in q['streams'] if x['codec_type']=='audio');assert int(v['nb_read_frames'])==29808;assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert abs(float(q['format']['duration'])-993.6)<.05
extracted=C/'demuxed_audio.m4a';run([F,'-v','error','-y','-i',out,'-map','0:a:0','-c','copy','-f','mp4',extracted])
def audio_hash(f):return hashlib.sha256(run([F,'-v','error','-i',f,'-map','0:a:0','-c','copy','-f','adts','pipe:1'])).hexdigest()
assert audio_hash(audio)==audio_hash(extracted)
record=dict(file=str(out),sha256=sha(out),bytes=out.stat().st_size,duration_s=float(q['format']['duration']),probe=q,decoded_video_frames=int(v['nb_read_frames']),decoded_audio_frames=int(a['nb_read_frames']),full_decode=True,decode_exit_code=0,original_audio_file=str(audio),original_audio_sha256=sha(audio),aac_packets_sha256=audio_hash(audio),audio_packets_identical=True,paid_api_calls=0,actual_listening=False,continuous_playback=False,changed_scene_ids=[f'M{i:03}' for i in range(10)],preserved_opening_frames=524,preserved_brand_intro_frames=150,preserved_brand_outro_frames=300,cta_hold_frames=p['outro_start']-p['audio_units'][-1]['end_frame'])
(O/'technical.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:record[k] for k in ['file','sha256','duration_s','bytes','audio_packets_identical']}))
