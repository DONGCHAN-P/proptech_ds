from pathlib import Path
from PIL import Image,ImageDraw
p=Path('video/out/qa-v11');files=sorted(p.glob('frame-*.png'),key=lambda f:float(f.stem.split('-')[-1]))
for part in range((len(files)+11)//12):
 page=Image.new('RGB',(1440,960),'#333333');d=ImageDraw.Draw(page)
 for j,f in enumerate(files[part*12:(part+1)*12]):
  im=Image.open(f);im.thumbnail((440,210));x=j%3*480;y=j//3*240;page.paste(im,(x,y+25));d.text((x+10,y+5),f.stem,fill='white')
 page.save(p/f'contact-{part}.jpg')
