from pathlib import Path
from PIL import Image,ImageDraw
import json
OWN=Path(__file__).resolve().parent;EP=OWN.parents[2];ROOT=EP.parents[2]
d=json.loads((OWN/'encoded_evidence.json').read_text('utf-8'));sch=json.loads((EP/'editor/jun-user-script-v1/full-film-v1/schedule.json').read_text('utf-8-sig'));frames={r['frame_index']:r for r in d['frames']}
def sheet(rows,name,cols=3,size=(640,360)):
 height=size[1]+24;im=Image.new('RGB',(cols*size[0],((len(rows)+cols-1)//cols)*height),'#e5e5e5');draw=ImageDraw.Draw(im)
 for i,row in enumerate(rows):
  x,y=(i%cols)*size[0],(i//cols)*height
  if row:
   with Image.open(ROOT/row['path']) as src:im.paste(src.convert('RGB').resize(size,Image.Resampling.LANCZOS),(x,y+24))
   draw.text((x+5,y+4),row.get('label',str(row.get('frame_index'))+' '+f'{row.get("time_s",0):.3f}s'),fill='black')
 im.save(OWN/name,quality=94)
bodies=[];chapters=[]
for p in sch['placements']:
 if p['kind'] in ['scene','chapter']:
  row={**frames[p['frame']+p['frames']-1],'label':p['id']+' '+str(p['frame']+p['frames']-1)}
  (bodies if p['kind']=='scene' else chapters).append(row)
for i in range(3):sheet(bodies[i*11:(i+1)*11],f'encoded_scenes_{i+1}.jpg')
sheet(chapters,'encoded_chapters.jpg')
for part in range(4):
 rows=[]
 for p in sch['placements'][part*10:(part+1)*10]:
  for delta in [-1,0,1]:
   n=p['frame']+delta;rows.append({**frames[n],'label':p['id']+' '+str(n)} if n in frames else None)
 sheet(rows,f'encoded_boundaries_{part+1}.jpg',size=(480,270))
roi_paths=sorted((OWN/'encoded-v2-0d73a746eee4').glob('caption-*.png'))
for part in range(4):sheet([{'path':p.relative_to(ROOT).as_posix(),'label':p.stem} for p in roi_paths[part*39:(part+1)*39]],f'encoded_captions_{part+1}.jpg',cols=2,size=(864,62))
sheet([frames[n] for n in [21053,21054,21060,21062,21143,21144,21443]],'encoded_ending.jpg',cols=2,size=(960,540))
print('Actual encoded contact sheets:31scenes,7chapters,40cutstarts,156captions,criticalending7frames.')
