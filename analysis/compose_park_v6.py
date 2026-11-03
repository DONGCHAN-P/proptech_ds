from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,math
base=Path('video/public/maps-v6');m=json.loads((base/'map.json').read_text());canvas=Image.new('RGB',(1024,768))
for y in range(3):
 for x in range(4):canvas.paste(Image.open(base/f'{x}-{y}.png'),(x*256,y*256))
canvas=canvas.crop((0,64,1024,704));draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',24)
for name,lon,lat in [('원천호수',127.0624,37.2817),('신대호수',127.0757,37.2795)]:
 x=(lon+180)/360*2**m['z']*256-m['x0']*256;y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**m['z']*256-m['y0']*256-64
 if name=='신대호수':x,y=950,285
 draw.ellipse((x-7,y-7,x+7,y+7),fill='#2F6FED',outline='white',width=2)
 box=draw.textbbox((0,0),name,font=font);w=box[2]+24
 bx=min(x+14,1024-w-8);by=y-22
 draw.rounded_rectangle((bx,by,bx+w,by+43),radius=7,fill='#182c40');draw.text((bx+12,by+5),name,font=font,fill='white')
canvas.save('video/public/maps-v6/park.png')
p=Path('video/src/ContinuationV6.tsx');s=p.read_text(encoding='utf8')
if '<svg width="1020" height="640"' in s:
 start=s.index('<svg width="1020" height="640"');end=s.index('</svg>',start)+len('</svg>');s=s[:start]+"<Img src={staticFile('maps-v6/park.png')} style={{width:1020,height:640,objectFit:'contain',borderRadius:22}}/>"+s[end:]
s=s.replace('호수공원 실제 지형 데이터','호수공원 실제 상세 지도').replace('2026.10.12 수집 · 호수·공원 지형 재구성','2026.10.13 지도 타일 · 지역 위치 표시');p.write_text(s,encoding='utf8')
