import json
import subprocess
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[4]
EP=Path(__file__).resolve().parents[1]
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PLAN={'UguOzeTENco':[0,1,4,8,12,18.5],'rMKZ1AYdS78':[0,.8,4.5], 'Kmfn_lWwfUQ':[0,2,6,10,14,20,25], 'xrPYY7tQvG8':[0,1,4.5]}
for vid,times in PLAN.items():
 folder=EP/'research/references'/vid;src=next(p for p in folder.glob('source.*') if p.suffix in ['.mp4','.webm','.mkv']);frames=[]
 for i,t in enumerate(times):
  out=folder/f'frame_{i:02d}_{t:g}.png';subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(src),'-frames:v','1','-vf','scale=360:-2',str(out)],check=True);frames.append(out)
 thumb=Image.open(frames[0]);tilew=360;tileh=thumb.height+36;cols=3;sheet=Image.new('RGB',(tilew*cols,tileh*((len(frames)+cols-1)//cols)),(237,240,244));draw=ImageDraw.Draw(sheet)
 for i,(frame,t) in enumerate(zip(frames,times)):
  x=i%cols*tilew;y=i//cols*tileh;im=Image.open(frame);sheet.paste(im,(x,y+36));draw.text((x+12,y+10),f'{vid}   {t:g}s',fill=(0,0,0))
 sheet.save(folder/'contact.png');print(json.dumps({'id':vid,'frames':len(frames),'contact':str(folder/'contact.png')}))
