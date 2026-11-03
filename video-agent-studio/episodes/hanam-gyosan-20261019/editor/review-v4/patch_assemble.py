from pathlib import Path
import json,subprocess,hashlib,shutil
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v4';C=E/'cache/patch-r1';C.mkdir(exist_ok=True)
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';P=F.with_name('ffprobe.exe');p=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));plan=json.loads((E/'patch_plan.json').read_text(encoding='utf8'))
def run(args):
 z=subprocess.run(list(map(str,args)),capture_output=True)
 if z.returncode or z.stderr:raise RuntimeError(z.stderr.decode(errors='replace')[-2000:])
 return z.stdout
def ff(args):return run([F,'-v','error','-y',*args])
def probe(file):return json.loads(run([P,'-v','error','-count_frames','-show_streams','-show_format','-of','json',file]))
old=E/'cache/assembly';prefix=C/'body_prefix.mp4';ff(['-i',old/'body.mp4','-an','-frames:v',plan['prefix_keyframe'],'-c:v','copy',prefix]);q=probe(prefix);v=next(x for x in q['streams'] if x['codec_type']=='video');assert int(v['nb_read_frames'])==plan['prefix_keyframe'];assert abs(float(q['format']['duration'])-plan['prefix_duration_s'])<.001
start=plan['tail_start_global_frame'];end=p['outro_start'];lines=['ffconcat version 1.0']
for x in p['visual_intervals']:
 a=max(start,x['start_frame']);b=min(end,x['end_frame'])
 if b<=a:continue
 lines.extend([f"file '{Path(x['source_file']).as_posix()}'",'option framerate 30',f'duration {(b-a)/30:.12f}']);last=x['source_file']
lines.extend([f"file '{Path(last).as_posix()}'",'option framerate 30']);lst=C/'tail.ffconcat';lst.write_text('\n'.join(lines)+'\n',encoding='utf8');tail=C/'body_tail.mp4';ff(['-f','concat','-safe','0','-i',lst,'-an','-r','30','-frames:v',end-start,'-c:v','libx264','-preset','fast','-crf','20','-threads','8','-pix_fmt','yuv420p','-video_track_timescale','90000',tail])
parts=[old/'opening.mp4',old/'intro.mp4',prefix,tail,old/'outro.mp4'];lst=C/'full.ffconcat';lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{x.as_posix()}'\n" for x in parts),encoding='utf8');out=O/'gyosan_review_v4r1_free_tts.mp4';ff(['-f','concat','-safe','0','-i',lst,'-i',O/'full_mix.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-t',p['duration_frames']/30,'-movflags','+faststart',out]);q=probe(out);v=next(x for x in q['streams'] if x['codec_type']=='video');a=next(x for x in q['streams'] if x['codec_type']=='audio');assert int(v['nb_read_frames'])==p['duration_frames'];assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1')
def aac_sha(f):return hashlib.sha256(ff(['-i',f,'-map','0:a:0','-c','copy','-f','adts','pipe:1'])).hexdigest()
assert aac_sha(out)==aac_sha(O/'full_mix.m4a')
prior=json.loads((O/'technical.json').read_text(encoding='utf8'));shutil.copy2(O/'technical.json',O/'technical_initial_v4.json') if not (O/'technical_initial_v4.json').exists() else None;record=dict(prior,file=str(out),sha256=hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),bytes=out.stat().st_size,duration_s=float(q['format']['duration']),probe=q,audio_packets_identical_to_v4_mix=True,audio_packets_sha256=aac_sha(out),decoded_video_frames=int(v['nb_read_frames']),decoded_audio_frames=int(a['nb_read_frames']),decode_exit_code=0,decode_stderr='',revision='v4r1',revision_reason='V4Q02: existing-resale narration now recalls the existing-resale chart; original narration/audio/caption/timing preserved',reused_prefix_frames=plan['prefix_keyframe'],reencoded_tail_frames=end-start,changed_visual_frames=[32057,32192])
for name in ['technical.json','technical_v4r1.json']:(O/name).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:record[k] for k in ['file','sha256','bytes','duration_s','audio_packets_identical_to_v4_mix']}))
