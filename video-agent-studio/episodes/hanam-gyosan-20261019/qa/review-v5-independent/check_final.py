from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw
P=Path(__file__).parent;E=P.parents[1];R=E.parents[2];O=E/'outputs/production-v5';V=O/'gyosan_review_v5_free_tts.mp4';FF=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
sha=hashlib.sha256(V.read_bytes()).hexdigest();assert sha=='a13779a6b9dd5da21100d1c5f7db4c3199d8f3eacccb13cdd29f2d36536dbc3a'
d=json.loads((O/'changed_timestamps.json').read_text(encoding='utf8'));samples=[x for x in d['samples'] if x['kind'] in ['new_spoken_phrase_mid','title','chapter_title','v4r1_fix_preserved']]
proj=json.loads((O/'project.json').read_text(encoding='utf8'))
for target in ['C2','B2']:
 a=[x for x in proj['visual_intervals'] if x['scene_id']=='M008' and x['props'].get('reviewKind',x['props'].get('mode'))=='candidate' and x['props'].get('active')==target]
 if a:
  x=a[len(a)//2];f=(x['start_frame']+x['end_frame'])//2;samples.append({'frame_requested':f,'time_s':f/30,'kind':'candidate_preserved','label':target})
for j,x in enumerate(samples):
 q=P/f'v5_{j:02}.png';subprocess.run([str(FF),'-v','error','-ss',str(x['time_s']),'-i',str(V),'-frames:v','1','-y',str(q)],check=True,capture_output=True);x['independent_file']=str(q)
for start in range(0,len(samples),8):
 s=Image.new('RGB',(1280,1536),'#eee');draw=ImageDraw.Draw(s)
 for j,x in enumerate(samples[start:start+8]):
  im=Image.open(x['independent_file']);im.thumbnail((640,360));xx=(j%2)*640;y=(j//2)*384;s.paste(im,(xx,y+24));draw.text((xx+4,y+4),f"{start+j} {x['time_s']:.3f}s {x.get('label',x['kind'])}",fill='black')
 s.save(P/f'v5_sheet_{start//8+1}.jpg',quality=92)
assert hashlib.sha256(V.read_bytes()).hexdigest()==sha
(P/'encoded_manifest.json').write_text(json.dumps({'sha256':sha,'bytes':V.stat().st_size,'samples':samples,'count':len(samples),'stable_before_after':True},ensure_ascii=False,indent=2),encoding='utf8')
print('independent samples',len(samples))
