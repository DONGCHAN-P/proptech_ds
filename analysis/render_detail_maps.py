from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
root=Path('video/public/detail-maps');config=json.loads((root/'shots.json').read_text(encoding='utf8'))
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if bold else '')+'.ttf',size)
for shot in config['shots']:
 m=json.loads((root/(shot['id']+'.json')).read_text(encoding='utf8'))
 raw=Image.new('RGB',(m['cols']*256,m['rows']*256))
 for t in m['tiles']:raw.paste(Image.open(root/'tiles'/t['file']),(t['x']*256,t['y']*256))
 bg=raw.crop((m['cropX'],m['cropY'],m['cropX']+1380,m['cropY']+760));bg.save(root/(m['id']+'-base.png'))
 card=Image.new('RGB',(1920,1080),'#F6F4EF');d=ImageDraw.Draw(card)
 d.text((65,40),'데이터로 보는 부동산 · 광교·동탄',font=font(24),fill='#6E6E6E')
 d.text((65,90),m['title'],font=font(52,True),fill='#111')
 d.text((65,165),m['subtitle'],font=font(25),fill='#6E6E6E')
 card.paste(bg,(65,240));d=ImageDraw.Draw(card)
 for i,p in enumerate(m['pins']):
  x,y=65+p['x'],240+p['y'];c=p.get('color',m['color'])
  if not(22<p['x']<1358 and 22<p['y']<738):raise RuntimeError(f"Pin outside safe map area: {p['name']}")
  d.ellipse((x-21,y-21,x+21,y+21),fill=c,outline='white',width=4)
  d.text((x,y-1),str(i+1),font=font(25,True),fill='white',anchor='mm')
  ly=265+i*145
  d.ellipse((1472,ly,1515,ly+43),fill=c);d.text((1494,ly+21),str(i+1),font=font(25,True),fill='white',anchor='mm')
  d.text((1532,ly+2),p['name'],font=font(29,True),fill='#111')
  d.text((1472,ly+62),p['note'],font=font(22),fill='#6E6E6E')
  d.line((1472,ly+108,1860,ly+108),fill='#ddd8ce',width=2)
 meters=200 if m['zoom']>=16 else 1000;mpp=156543.03392*math.cos(math.radians(m['lat']))/(2**m['zoom']);w=meters/mpp
 d.rectangle((90,946,110+w,982),fill='white');d.line((100,955,100+w,955),fill='#111',width=4);d.text((100,962),str(meters)+' m',font=font(17),fill='#111')
 d.text((65,1028),m['credit']+' · 2026.10.13 · 시설 대표 위치',font=font(19),fill='#6E6E6E')
 card.save(root/(m['id']+'.png'))
 print(m['id']+' PNG ready')
