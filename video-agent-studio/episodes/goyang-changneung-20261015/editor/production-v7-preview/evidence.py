from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v7-preview';D=O/'encoded_evidence';D.mkdir(exist_ok=True);F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';p=json.loads((O/'project_v7.json').read_text(encoding='utf-8'));video=O/'changneung_full_v7_preview.mp4'
def frame(f,name):
 out=D/(name+'.png');z=subprocess.run(list(map(str,[F,'-v','error','-y','-ss',f/30,'-i',video,'-frames:v','1',out])),capture_output=True);assert z.returncode==0,z.stderr;return out
rows=[]
for i,x in enumerate(p['visual_intervals']):
 f=x['start_frame']+min(45,max(0,x['duration_frames']//2));name=f's{i:03}_f{f:05}';file=frame(f,name);rows.append(dict(file=str(file),frame=f,time_s=f/30,kind=x['kind'],unit_id=x['unit_id'],props=x['props']))
def sheet(items,prefix,cols=4,n=16):
 paths=[]
 for k in range(0,len(items),n):
  page=items[k:k+n];im=Image.new('RGB',(cols*480,((len(page)+cols-1)//cols)*300),'#e2e2e2');dr=ImageDraw.Draw(im)
  for j,r in enumerate(page):
   x=j%cols*480;y=j//cols*300;im.paste(Image.open(r['file']).convert('RGB').resize((480,270)),(x,y));dr.text((x+5,y+274),f"{r.get('unit_id','')} f{r['frame']} {r['frame']/30:.3f}s",fill='#111')
  dest=D/f'{prefix}_{k//n+1:02}.jpg';im.save(dest,quality=92);paths.append(str(dest))
 return paths
sheets=sheet(rows,'cut_contactsheet');motions=[];seen=set()
for x in p['visual_intervals']:
 q=x['props'];key=(q.get('mode'),q.get('active'),q.get('stage'),q.get('phase'))
 if key in seen or q.get('mode')not in ['plan','decision','rail','transit','school','supply','restrictions','resale_map','price']:continue
 if x['duration_frames']<46:continue
 seen.add(key)
 for delta in [0,15,30,44,60]:
  f=x['start_frame']+min(delta,x['duration_frames']-1);file=frame(f,f'm{len(seen):02}_{delta:02}_f{f}');motions.append(dict(file=str(file),frame=f,time_s=f/30,unit_id=x['unit_id'],props=q,delta=delta))
msheets=sheet(motions,'motion_contactsheet');bound=[]
for x in p['visual_intervals']:
 if x['kind']in ['intro','outro','chapter']:
  for f in sorted(set([max(0,x['start_frame']-1),x['start_frame'],min(x['end_frame']-1,x['start_frame']+75),x['end_frame']-1,min(p['duration_frames']-1,x['end_frame'])])):
   file=frame(f,f'boundary_{f:05}');bound.append(dict(file=str(file),frame=f,time_s=f/30,unit_id=x['unit_id']))
bsheets=sheet(bound,'boundary_contactsheet');mobile=D/'mobile512';mobile.mkdir(exist_ok=True);selected={}
for row in rows:
 mode=row['props'].get('mode',row['kind']);old=selected.get(mode)
 if old is None or len(row['props'].get('caption',''))>len(old['props'].get('caption','')):selected[mode]=row
for mode,row in selected.items():Image.open(row['file']).resize((512,288)).save(mobile/(mode+'.png'))
record=dict(video=str(video),actual_encoded_samples=True,cuts=rows,motions=motions,boundaries=bound,cut_sheets=sheets,motion_sheets=msheets,boundary_sheets=bsheets,mobile_dir=str(mobile),scope='sampled decoded frames; no continuous playback or listening')
(O/'evidence_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(f'EVIDENCE_COMPLETE cuts={len(rows)} motion={len(motions)} boundary={len(bound)}',flush=True)
