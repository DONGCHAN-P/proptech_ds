from pathlib import Path
import json, hashlib, subprocess
from PIL import Image,ImageOps,ImageDraw
EP=Path(__file__).resolve().parents[2]
O=EP/'outputs/production-v3'; Q=Path(__file__).resolve().parent
ROOT=EP.parents[2]; F=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
movie=O/'changneung_full_v3.mp4'; p=json.loads((O/'rendered_project_v3.json').read_text('utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
hash_before=sha(movie)
shots=p['shots']; N=p['duration_frames']; selected={0,612,613,762,763,23747,23748,23749,23750,23839,23840,23841,N-1}
for s in shots:
 selected.add((s['start_frame']+s['end_frame'])//2)
 for d in [-1,0,1]:selected.add(max(0,min(N-1,s['start_frame']+d)))
longs=sorted([v for v in p['visual_intervals'] if v.get('caption')],key=lambda v:len(v['caption']),reverse=True)[:8]
selected.update(v['start_frame'] for v in longs)
selected=sorted(selected); dest=Q/'encoded_frames';dest.mkdir(exist_ok=True)
for start in range(0,len(selected),25):
 batch=selected[start:start+25]
 for f in batch:
  result=subprocess.run([str(F),'-v','error','-y','-ss',f'{f/30:.12f}','-i',str(movie),'-frames:v','1',str(dest/f'frame_{f:06}.png')],capture_output=True)
  if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
 print(f'Extracted {min(start+25,len(selected))}/{len(selected)}',flush=True)
def sheet(name,frames,cols=3):
 w,h=640,380;canvas=Image.new('RGB',(cols*w,((len(frames)+cols-1)//cols)*h),'#dddddd');draw=ImageDraw.Draw(canvas)
 for i,n in enumerate(frames):
  x=(i%cols)*w;y=(i//cols)*h;im=Image.open(dest/f'frame_{n:06}.png').convert('RGB');im.thumbnail((w,360));canvas.paste(im,(x,y+20));draw.text((x+5,y+3),f'frame {n} | {n/30:.3f}s',fill='black')
 canvas.save(Q/name)
for i in range(0,len(selected),18):sheet(f'encoded_contact_{i//18+1:02}.jpg',selected[i:i+18])
record={'mp4_sha256_before':hash_before,'mp4_sha256_after':sha(movie),'project_sha256':sha(O/'rendered_project_v3.json'),'frames':selected,'count':len(selected),'continuous_playback':False,'actual_listening':False,'note':'independent extraction from final MP4; contact sheets require direct visual review'}
(Q/'encoded_frame_manifest.json').write_text(json.dumps(record,indent=2),'utf8')
print(json.dumps({'frames':len(selected),'hash_unchanged':record['mp4_sha256_before']==record['mp4_sha256_after']}),flush=True)
