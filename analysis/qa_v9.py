from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json
p=Path('video/out/qa-v9');files=sorted(p.glob('frame-*.png'),key=lambda f:float(f.stem.split('-')[-1]))
for part in range((len(files)+11)//12):
 page=Image.new('RGB',(1440,960),'#333333');d=ImageDraw.Draw(page)
 for j,f in enumerate(files[part*12:(part+1)*12]):
  im=Image.open(f);im.thumbnail((440,210));x=j%3*480;y=j//3*240;page.paste(im,(x,y+25));d.text((x+10,y+5),f.stem,fill='white')
 page.save(p/f'contact-{part}.jpg')
checks=[]
for a,b in [(183,184),(200,202),(219,221),(246,248),(299,301),(482,484),(541,543),(571,573)]:
 im1=Image.open(p/f'frame-{a}.png').convert('RGB').crop((180,300,1730,805));im2=Image.open(p/f'frame-{b}.png').convert('RGB').crop((180,300,1730,805));hist=ImageChops.difference(im1,im2).histogram();mad=sum((i%256)*n for i,n in enumerate(hist))/(im1.width*im1.height*3);checks.append(dict(times=[a,b],mean_absolute_pixel_difference=mad))
(p/'static-image-check.json').write_text(json.dumps(checks,indent=2),encoding='utf8');print(json.dumps(checks))
