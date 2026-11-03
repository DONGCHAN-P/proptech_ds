from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');Q=E/'qa/production-v6-ui-r5';O=E/'outputs/production-v6-ui-r5/partial';F=Path('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe');P=F.with_name('ffprobe.exe');out=Q/'partial_frames';out.mkdir(exist_ok=True);records=[]
for mode in ('plan','transit','price'):
 file=O/(mode+'_90f.mp4');probe=subprocess.run([str(P),'-v','error','-count_frames','-show_entries','stream=codec_type,nb_read_frames,width,height,avg_frame_rate,duration','-of','json',str(file)],capture_output=True,text=True);records.append({'mode':mode,'exit':probe.returncode,'probe':json.loads(probe.stdout),'stderr':probe.stderr})
 sheet=Image.new('RGB',(1920,1160),'#ddd');draw=ImageDraw.Draw(sheet)
 for j,f in enumerate((0,15,30,44,60,89)):
  dest=out/f'{mode}_{f:03}.png';subprocess.run([str(F),'-v','error','-ss',f'{f/30:.9f}','-i',str(file),'-frames:v','1','-y',str(dest)],check=True,capture_output=True)
  im=Image.open(dest);im.thumbnail((960,540));x=j%2*960;y=j//2*380;im.thumbnail((640,360));sheet.paste(im,(x,y));draw.text((x+5,y+362),f'{mode} partial frame{f} @{f/30:.3f}s',fill='black')
 sheet.save(Q/f'partial_{mode}.jpg',quality=93)
(Q/'partial_technical.json').write_text(json.dumps(records,indent=2),encoding='utf-8');print('18 actual partial encoded frames extracted; three full partial decodes complete')
