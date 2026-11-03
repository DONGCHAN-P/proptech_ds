from pathlib import Path
import json,subprocess,hashlib,concurrent.futures
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];R=EP.parents[2];O=EP/'outputs/production-v1'
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
p=json.loads((O/'project.json').read_text(encoding='utf8'));v=p['visual_intervals'];points={}
def add(f,label):points.setdefault(max(0,min(p['duration_frames']-1,int(f))),[]).append(label)
def key(x):return json.dumps({k:z for k,z in x['props'].items() if k!='caption'},sort_keys=True)
groups={};scenes={}
for i,x in enumerate(v):
 k=key(x);groups.setdefault(k,[]).append(x);scenes.setdefault(x['scene_id'],[]).append(x)
 if i==0 or key(v[i-1])!=k:
  add(x['start_frame']-1,'cut_before');add(x['start_frame'],'cut_start');add(x['start_frame']+min(44,x['duration_frames']-1),'motion_end')
for xs in groups.values():
 x=max(xs,key=lambda x:len(x['props'].get('caption','')));add((x['start_frame']+x['end_frame'])//2,'longest_caption')
overview=[]
for sid,xs in scenes.items():
 if sid.startswith('M'):
  body=[x for x in xs if x['kind']=='body'];x=body[len(body)//2];f=(x['start_frame']+x['end_frame'])//2;add(f,sid+'_overview');overview.append((sid,f))
add(p['outro_start']-1,'last_body');add(p['outro_start'],'outro');add(p['duration_frames']-1,'final')
src=O/'gyosan_full_v1_free_tts.mp4';dest=Q/'frames';dest.mkdir(exist_ok=True)
def extract(f):
 out=dest/f'{f:06d}.png';z=subprocess.run([str(F),'-v','error','-y','-ss',f'{f/30:.9f}','-i',str(src),'-frames:v','1',str(out)],capture_output=True);assert z.returncode==0,z.stderr
 return f
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(extract,sorted(points)))
def sheet(rows,out,cols=3,w=640):
 h=round(w*9/16);canvas=Image.new('RGB',(cols*w,((len(rows)+cols-1)//cols)*(h+25)),'#ffffff');d=ImageDraw.Draw(canvas)
 for n,(label,f) in enumerate(rows):
  im=Image.open(dest/f'{f:06d}.png');im.thumbnail((w,h));x=n%cols*w;y=n//cols*(h+25);canvas.paste(im,(x,y));d.text((x+5,y+h+3),f'{label} f{f} {f/30:.3f}s',fill='black')
 canvas.save(out)
sheet(overview,Q/'scene_overview_10.png',2,960)
rows=[('/'.join(points[f]),f) for f in sorted(points)]
for n in range(0,len(rows),12):sheet(rows[n:n+12],Q/f'sheet_{n//12:02d}.jpg')
(Q/'frame_manifest.json').write_text(json.dumps({'source':str(src),'sha256':hashlib.file_digest(src.open('rb'),'sha256').hexdigest(),'frames':points,'overview':overview},indent=2),encoding='utf8')
print(json.dumps({'frames':len(points),'sheets':(len(rows)+11)//12,'overview':str(Q/'scene_overview_10.png')}))
