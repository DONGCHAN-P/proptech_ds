from pathlib import Path
import json,hashlib,re,wave,subprocess
from PIL import Image,ImageDraw
import numpy as np
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v5';V=O/'gyosan_review_v5_free_tts.mp4';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
def read(f):return json.loads(f.read_text(encoding='utf8'))
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
norm=lambda x:re.sub(r'\s+','',x)
p=read(O/'rendered_project.json');units=read(E/'units_prepared.json');approved=read(EP/'narration/units_v5.json');reuse=read(E/'audio_reuse.json');changes=read(EP/'outputs/script-review-v5/changes.json');scene={x['scene_id']:x for x in read(EP/'writer/scenes_v5.json')}
old_approved=read(EP/'narration/units_v4.json');expected={u['unit_id']:u['text'] for u in old_approved}
for c in changes:
 for uid in c['unit_ids']:
  assert expected[uid].count(c['before'])==1
  expected[uid]=expected[uid].replace(c['before'],c['after'])
assert all(expected[u['unit_id']]==u['text'] for u in approved)
t=read(O/'technical.json');assert t['sha256']==sha(V)
t.update(voice='Local free Microsoft Heami rate2 / 261 phrase WAVs:240 byte-identical reused,21 newly generated',new_phrase_wavs=21,reused_phrase_wavs=240,phrase_wav_count=261)
save(O/'technical.json',t);save(O/'technical_v5.json',t)
source_lineage={str(f.relative_to(E)):sha(f) for f in (E/'source').glob('*') if f.is_file()}
assert all(sha(E/k)==sha(E.parent/'review-v4'/k) for k in source_lineage)
save(E/'visual_inheritance.json',dict(passed=True,baseline='production-v4/gyosan_review_v4r1_free_tts.mp4',all_visual_source_bytes_identical=True,source_sha256=source_lineage,public_assets='visual/review-v4/public unchanged',M008_parcel_geometry='same source bytes',M009_resale_recall='asserted in content_verification'))
assert norm(''.join(u['text'] for u in units))==norm(''.join(u['text'] for u in approved))
changed={uid for c in changes for uid in c['unit_ids']};assert changed=={u['unit_id'].rsplit('_p',1)[0] for u in reuse if not u['reused']}
am=read(E/'audio_input_manifest.json');am.update(prepared_phrase_count=len(units),newly_generated_phrase_count=21,reused_phrase_count=240,reuse_basis='Exact spoken_text match then byte-identical WAV SHA256')
save(E/'audio_input_manifest.json',am)
audio=[]
for u in p['audio_units']:
 f=Path(u['audio_path'])
 with wave.open(str(f),'rb') as w:a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');assert a.size and np.max(np.abs(a.astype(np.int32)))>0
 r=next(r for r in reuse if r['unit_id']==u['unit_id'])
 if r['reused']:assert sha(f)==r['sha256']==sha(Path(r['source']))
 audio.append(dict(unit_id=u['unit_id'],sha256=sha(f),reused=r['reused']))
assert all(x['props']['title']==scene[x['scene_id']]['title'] for x in p['visual_intervals'] if x['scene_id'] in scene)
recall=[x for x in p['visual_intervals'] if '실거래 중위값이었습니다' in x.get('props',{}).get('phrase_text','')];assert recall and all(x['props']['reviewKind']=='compare' for x in recall)
assert p['outro_start']-p['audio_units'][-1]['end_frame']==90
save(E/'content_verification.json',dict(passed=True,changed_parent_units=sorted(changed),new_phrase_wavs=sum(not r['reused'] for r in reuse),reused_wavs=sum(r['reused'] for r in reuse),approved_text_preserved=True,all_titles_match=True,M009_resale_chart_preserved=True,cta_hold_frames=90,audio=audio,actual_listening=False))
D=O/'changed_proofs';D.mkdir(exist_ok=True);rows=[]
def grab(n,label,kind):
 f=D/(label+'.png');z=subprocess.run([str(F),'-v','error','-y','-ss',str(n/30),'-i',str(V),'-frames:v','1',str(f)],capture_output=True);assert z.returncode==0,z.stderr
 rows.append(dict(frame_requested=n,time_s=n/30,file=str(f),kind=kind,label=label))
for uid in sorted(changed):
 us=[u for u in p['audio_units'] if u['parent_unit_id']==uid];a=us[0]['start_frame'];b=us[-1]['end_frame'];grab((a+b)//2,uid,'changed_parent_mid')
 for n,label in [(max(0,a-2),'before'),(a+2,'start'),(b-2,'end'),(b+2,'after')]:grab(n,uid+'_'+label,'changed_boundary_nearby')
for sid,s in scene.items():
 x=next(x for x in p['visual_intervals'] if x['scene_id']==sid and x['kind']=='body');grab(x['start_frame']+min(2,x['duration_frames']-1),sid+'_title','title')
for x in p['visual_intervals']:
 if x['kind']=='chapter':grab(x['start_frame']+45,x['scene_id']+'_chapter','chapter_title')
grab(recall[0]['start_frame']+20,'M009_resale_recall','v4r1_fix_preserved')
save(O/'changed_timestamps.json',dict(video=str(V),sha256=sha(V),scope='Requested times at changed parent midpoints, nearby boundaries and every title; seek correspondence is not guaranteed frame-exact',samples=rows))
files=[Path(r['file']) for r in rows if r['kind']!='changed_boundary_nearby'];sheet=Image.new('RGB',(1600,250*((len(files)+3)//4)),'#ddd');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(files):
 im=Image.open(f);im.thumbnail((400,225));x=i%4*400;y=i//4*250;sheet.paste(im,(x,y));draw.text((x+5,y+229),f.stem,fill='black')
sheet.save(D/'contactsheet.jpg',quality=90)
inputs=[EP/'outputs/script-review-v5/script_v5.md',EP/'outputs/script-review-v5/changes.json',EP/'writer/scenes_v5.json',EP/'narration/units_v5.json',*E.glob('*.py'),*E.glob('*.cjs'),*E.glob('*.ps1'),*list((E/'source').glob('*')),*[Path(x['audio_path']) for x in p['audio_units']],*[Path(x['source_file']) for x in p['visual_intervals'] if x.get('source_file')]]
save(O/'input_manifest.json',{str(f.relative_to(R)):sha(f) for f in inputs if f.is_file()})
save(E/'handoff.json',dict(status='render_complete_independent_qa_pending',video=str(V),sha256=sha(V),duration_s=p['duration_frames']/30,technical=str(O/'technical.json'),content_verification=str(E/'content_verification.json'),changed_timestamps=str(O/'changed_timestamps.json'),source_manifest=str(O/'input_manifest.json'),approved_script='v5',changed_parent_units=sorted(changed),new_wavs=21,reused_wavs=240,paid_api_calls=0,uploaded=False,actual_listening=False,continuous_playback=False,M009_resale_fix_preserved=True,all_titles_match=True,next_owner='independent QA / director'))
print(json.dumps(dict(video=str(V),sha256=sha(V),samples=len(rows),duration_s=p['duration_frames']/30)))
