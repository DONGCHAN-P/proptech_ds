from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent;OUT.mkdir(exist_ok=True)
FF=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
videos={'G':EP/'outputs/production-v1/gyosan_full_v1r3_free_tts.mp4','C':ROOT/'video-agent-studio/episodes/goyang-changneung-20261015/outputs/production-v8-jun/changneung_full_v8_jun.mp4'}
times={'G':[8,28,64,95,137,155,191,238,270,313,370,408,447,478,514,551,580,617,654,678,713,751,786,826,871,916,946,975],
       'C':[8,30,72,110,151,195,245,291,338,385,430,478,524,570,620,674,728,790,830]}
manifest=[]
for key,points in times.items():
 for t in points:
  path=OUT/f'{key}_{t:04d}.png'
  if not path.exists():
   result=subprocess.run([str(FF),'-v','error','-ss',str(t),'-i',str(videos[key]),'-frames:v','1','-y',str(path)],capture_output=True)
   assert result.returncode==0,result.stderr[-300:]
  manifest.append({'video':key,'seconds':t,'file':str(path)})
 for start in range(0,len(points),8):
  sheet=Image.new('RGB',(1280,4*390),'#eeeeee');draw=ImageDraw.Draw(sheet)
  for j,t in enumerate(points[start:start+8]):
   im=Image.open(OUT/f'{key}_{t:04d}.png');im.thumbnail((640,360));x=(j%2)*640;y=(j//2)*390
   sheet.paste(im,(x,y+25));draw.text((x+10,y+5),f'{key} {t//60:02d}:{t%60:02d}',fill='black')
  sheet.save(OUT/f'{key}_sheet_{start//8+1}.jpg',quality=88)
(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps({'frames':len(manifest),'output':str(OUT)}))
