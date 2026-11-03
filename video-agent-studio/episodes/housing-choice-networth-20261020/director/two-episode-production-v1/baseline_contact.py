import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent/'baseline_frames'
OUT.mkdir(exist_ok=True)
ff=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
video=EP/'outputs/integrated-review-v1/housing_choice_review_v1.mp4'
times=[12,187,360,600,780,1000]
canvas=Image.new('RGB',(1440,860),'#eeeae4')
for index,t in enumerate(times):
    target=OUT/f'{t:04d}s.png'
    subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(target)],check=True)
    pic=Image.open(target).convert('RGB').resize((720,405))
    x=(index%2)*720; y=(index//2)*285
    pic=pic.resize((480,270))
    canvas.paste(pic,(x,y))
    ImageDraw.Draw(canvas).text((x+490,y+10),f'baseline {t}s',fill='#173348')
canvas.save(OUT/'contact.png')
print(json.dumps({'frames':len(times),'contact':str((OUT/'contact.png').relative_to(ROOT))}))
