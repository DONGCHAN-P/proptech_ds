from pathlib import Path
import json, subprocess, hashlib
from PIL import Image, ImageDraw
P=Path(__file__).parent; E=P.parents[1]; R=E.parents[2]
V=E/'outputs/production-v2/gyosan_review_v2_free_tts.mp4'
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
d=json.loads((E/'outputs/production-v2/project.json').read_text(encoding='utf8'))
points=[]
last=None
for x in d['visual_intervals']:
 if x['scene_id']!=last:
  t=x['start_frame']/30
  points.extend([max(0,t-1/30),t+1/30])
  last=x['scene_id']
points.extend([392,399,408,414,699,703,708,716,721,795,812,825,874,900,973,980.6,983.567])
points=sorted(set(round(t,3) for t in points))
for t in points:
 q=P/f'f_{t:08.3f}.png'
 subprocess.run([str(F),'-v','error','-ss',str(t),'-i',str(V),'-frames:v','1','-y',str(q)],check=True,capture_output=True)
for start in range(0,len(points),10):
 s=Image.new('RGB',(1280,1920),'#eeeeee'); draw=ImageDraw.Draw(s)
 for j,t in enumerate(points[start:start+10]):
  im=Image.open(P/f'f_{t:08.3f}.png');im.thumbnail((640,360));x=(j%2)*640;y=(j//2)*384
  s.paste(im,(x,y+24));draw.text((x+8,y+4),str(t),fill='black')
 s.save(P/f'boundary_{start//10+1}.jpg',quality=90)
result={'video_sha256':hashlib.sha256(V.read_bytes()).hexdigest(),'bytes':V.stat().st_size,'sample_times':points,'count':len(points),'source':'independently extracted final MP4'}
(P/'encoded_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result))
