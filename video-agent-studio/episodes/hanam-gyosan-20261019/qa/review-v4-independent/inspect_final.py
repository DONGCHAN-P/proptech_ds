from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw
P=Path(__file__).parent; E=P.parents[1]; R=E.parents[2]; O=E/'outputs/production-v4'
V=O/'gyosan_review_v4_free_tts.mp4'; F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
sha=hashlib.sha256(V.read_bytes()).hexdigest();tech=json.loads((O/'technical.json').read_text(encoding='utf8'));assert sha==tech['sha256']
d=json.loads((O/'project.json').read_text(encoding='utf8')); reps=json.loads((O/'representative_timestamps.json').read_text(encoding='utf8'))
points=[(x['frame'],x.get('scene_id','')+' '+x.get('kind','')) for x in reps]
for x in d['visual_intervals']:
 if x['kind']=='chapter':
  for f in [x['start_frame']-1,x['end_frame']]:points.append((f,'chapter boundary'))
for f in [d['intro_at']-1,d['intro_at'],d['intro_at']+149,d['intro_at']+150,d['outro_start']-91,d['outro_start']-90,d['outro_start']-1,d['outro_start'],d['duration_frames']-1]:points.append((f,'brand/CTA boundary'))
unique={f:label for f,label in points};points=sorted(unique.items())
for f,label in points:
 q=P/f'frame_{f:06}.png';subprocess.run([str(F),'-v','error','-ss',str(f/30),'-i',str(V),'-frames:v','1','-y',str(q)],check=True,capture_output=True)
for start in range(0,len(points),8):
 s=Image.new('RGB',(1280,1536),'#eee');draw=ImageDraw.Draw(s)
 for j,(f,label) in enumerate(points[start:start+8]):
  im=Image.open(P/f'frame_{f:06}.png');im.thumbnail((640,360));x=(j%2)*640;y=(j//2)*384;s.paste(im,(x,y+24));draw.text((x+4,y+4),f'{f/30:.3f}s {label}',fill='black')
 s.save(P/f'sheet_{start//8+1:02}.jpg',quality=90)
assert hashlib.sha256(V.read_bytes()).hexdigest()==sha
(P/'encoded_manifest.json').write_text(json.dumps({'sha256':sha,'bytes':V.stat().st_size,'frames':[{'frame':f,'time_s':f/30,'label':l} for f,l in points],'count':len(points),'stable_before_after':True,'source':'independently extracted final v4 MP4; seek timestamps, not frame-select decoded boundary proof'},ensure_ascii=False,indent=2),encoding='utf8')
print('stable sha',sha,'samples',len(points),'sheets',(len(points)+7)//8)
