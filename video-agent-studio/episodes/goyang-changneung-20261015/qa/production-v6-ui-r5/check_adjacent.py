from pathlib import Path
from PIL import Image,ImageDraw
from concurrent.futures import ThreadPoolExecutor
import json,subprocess
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');O=E/'outputs/production-v6-ui-r5';Q=E/'qa/production-v6-ui-r5';D=Q/'adjacent_r5';D.mkdir(exist_ok=True);changes=json.loads((O/'change_manifest.json').read_text(encoding='utf-8'))['changes'];frames=sorted(set(f for c in changes for f in [c['start_frame']-1,c['end_frame']-1] if f>=0));ff=Path('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe');mp=O/'changneung_full_v6_ui_r5.mp4'
def run(f):
 p=D/f'f{f:05}.png';subprocess.run([str(ff),'-v','error','-ss',f'{f/30:.9f}','-i',str(mp),'-frames:v','1','-y',str(p)],check=True,capture_output=True);return p
with ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(run,frames))
for k in range(0,len(frames),24):
 im=Image.new('RGB',(1920,1740),'#ddd');d=ImageDraw.Draw(im)
 for j,f in enumerate(frames[k:k+24]):
  src=Image.open(D/f'f{f:05}.png');src.thumbnail((480,270));x=j%4*480;y=j//4*290;im.paste(src,(x,y));d.text((x+4,y+272),f'f{f} @{f/30:.3f}s',fill='black')
 im.save(Q/f'adjacent_sheet_{k//24+1:02}.jpg',quality=92)
(Q/'adjacent_manifest.json').write_text(json.dumps({'frames':frames,'count':len(frames),'scope':'changed interval start-1 and end-1 actual final first-pass MP4'},indent=2),encoding='utf-8');print('adjacent samples',len(frames),'sheets',(len(frames)+23)//24)
