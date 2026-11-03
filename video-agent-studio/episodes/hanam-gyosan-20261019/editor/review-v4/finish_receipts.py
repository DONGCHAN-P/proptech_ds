from pathlib import Path
import json,hashlib,subprocess,re,bisect
import numpy as np
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v4';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';video=O/'gyosan_review_v4r1_free_tts.mp4';p=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));technical=json.loads((O/'technical.json').read_text(encoding='utf8'))
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def run(args):
 z=subprocess.run([str(F),'-v','error','-y',*map(str,args)],capture_output=True)
 if z.returncode or z.stderr:raise RuntimeError(z.stderr.decode(errors='replace')[-2000:])
 return z
assert sha(video)==technical['sha256'];assert len(p['audio_units'])==263;assert p['outro_start']-p['audio_units'][-1]['end_frame']==90
norm=lambda x:re.sub(r'\s+','',x);approved=json.loads((EP/'narration/units_v4.json').read_text(encoding='utf8'));assert norm(''.join(x['text'] for x in approved))==norm(''.join(x['text'] for x in p['audio_units']))
cues=json.loads((O/'caption_cues.json').read_text(encoding='utf8'));assert norm(''.join(x['text'] for x in cues))==norm(''.join(x['text'] for x in approved));assert all(x['start_frame']<x['end_frame'] for x in cues)
motion=[];seen=set()
for x in p['visual_intervals']:
 q=x.get('props',{});k=q.get('reviewKind');stage=q.get('stage');key=(x['scene_id'],q.get('visual_key'))
 if q.get('motionFrame')!=0 or key in seen:continue
 if k=='v4_ai' and stage=='industry':continue
 seen.add(key);count=q.get('motionEnd',44)+1;folder=O/'motion_proofs_v4r1'/f'{x["scene_id"]}_{len(motion):02}_{k}';folder.mkdir(parents=True,exist_ok=True)
 run(['-ss',max(0,(x['start_frame']-.001)/30),'-i',video,'-frames:v',str(count),'-vf','scale=480:270',folder/'%03d.png']);frames=[np.array(Image.open(f).convert('RGB')).astype(np.int16) for f in sorted(folder.glob('*.png'))];assert len(frames)==count
 diff=[float(np.abs(b-a).mean()) for a,b in zip(frames,frames[1:])];unique=len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames});assert unique>2,(key,unique)
 motion.append(dict(scene_id=x['scene_id'],visual_key=q.get('visual_key'),start_frame=x['start_frame'],end_frame=x['start_frame']+count-1,actual_encoded_frames=count,unique_decoded_frames=unique,adjacent_changed_frames=sum(d>0 for d in diff),maximum_adjacent_mean_difference=max(diff),evidence=str(folder)))
(O/'motion_verification.json').write_text(json.dumps(dict(passed=True,sequences=motion),ensure_ascii=False,indent=2),encoding='utf8')
inputs=[E/'prepare_audio.py',E/'generate.ps1',E/'timeline.py',E/'prepare_visual.py',E/'render.cjs',E/'assemble.py',E/'patch_assemble.py',E/'patch_plan.json',E/'V4Q02_changes.json',E/'finish.py',EP/'outputs/script-review-v4/script_v4.md',EP/'outputs/script-review-v4/visual_storyboard.md',EP/'writer/scenes_v4.json',EP/'narration/units_v4.json',EP/'research/facilities_coordinates_v4.json',E/'osm_roads_raw.json',*list((E/'source').glob('*')),*[Path(x['audio_path']) for x in p['audio_units']],*[Path(x['source_file']) for x in p['visual_intervals'] if 'source_file' in x],*list((EP/'visual/review-v4/public').rglob('*'))];manifest={str(f.relative_to(R)):sha(f) for f in inputs if f.is_file()};(O/'input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
