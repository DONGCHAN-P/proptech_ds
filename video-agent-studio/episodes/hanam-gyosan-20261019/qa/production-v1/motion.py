from pathlib import Path
import subprocess,concurrent.futures
from PIL import Image,ImageDraw
q=Path(__file__).resolve().parent;o=q.parents[1]/'outputs/production-v1';f=Path('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe')
starts=[6953,10899,20047,17177,24157,24605];d=q/'motion_r2';d.mkdir(exist_ok=True)
jobs=[(i,s+n,n)for i,s in enumerate(starts)for n in [0,11,22,33,44]]
def run(j):
 i,fr,n=j
 z=subprocess.run([str(f),'-v','error','-y','-ss',str(fr/30),'-i',str(o/'gyosan_full_v1r2_free_tts.mp4'),'-frames:v','1',str(d/f'{i}_{n}.png')],capture_output=True)
 assert z.returncode==0,z.stderr
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:list(ex.map(run,jobs))
c=Image.new('RGB',(1600,1230),'white');dr=ImageDraw.Draw(c)
for i,s in enumerate(starts):
 for k,n in enumerate([0,11,22,33,44]):
  c.paste(Image.open(d/f'{i}_{n}.png').resize((320,180)),(k*320,i*205));dr.text((k*320,i*205+182),f'{s+n} +{n}',fill='black')
c.save(q/'motion_r2.png');print('30 motion samples extracted')
