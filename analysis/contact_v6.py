from PIL import Image,ImageDraw
from pathlib import Path
times=[2,10,17,24,29,39,45,55,65,78,93,100,118,135,154,172,192,212,230,251,273]
base=Path('video/out/qa-v6')
for k in range(0,len(times),4):
    group=times[k:k+4]
    canvas=Image.new('RGB',(1920,1120),'#16171a')
    draw=ImageDraw.Draw(canvas)
    for j,t in enumerate(group):
        im=Image.open(base/f'frame-{t}.png').convert('RGB').resize((960,540))
        x=(j%2)*960;y=(j//2)*560
        canvas.paste(im,(x,y+20));draw.text((x+12,y+3),f'{t}s',fill='white')
    canvas.save(base/f'contact-{k//4}.png')
