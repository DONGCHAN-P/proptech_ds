from PIL import Image,ImageDraw
from pathlib import Path
times=[2,7,16,24,29,39,45,55,65,78,88,96,54,54.1,54.2]
sheet=Image.new('RGB',(1920,1200),'white')
d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 im=Image.open(f'video/out/qa-v2/frame-{t}.png').resize((480,270))
 x=(i%4)*480;y=(i//4)*300
 sheet.paste(im,(x,y));d.text((x+8,y+276),f'{t}s',fill='black')
sheet.save('video/out/qa-v2/contact.png')

