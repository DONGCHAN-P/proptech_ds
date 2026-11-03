from pathlib import Path
from PIL import Image,ImageDraw
import json
O=Path(__file__).resolve().parent.parent.parent/'outputs/production-v6-ui-r5';D=O/'encoded_evidence';p=O/'encoded_evidence_manifest.json';e=json.loads(p.read_text(encoding='utf-8'))
for c in e['motion_clips']:
 sheet=Image.new('RGB',(2048,318),'#f6f4ef');draw=ImageDraw.Draw(sheet)
 for i,d in enumerate([0,15,30,44]):
  sheet.paste(Image.open(D/f'motion_{c["mode"]}_{d:02d}.png').convert('RGB').resize((512,288)),(i*512,0));draw.text((i*512+8,294),f'{c["mode"]} / {d}f / actual encoded MP4',fill='black')
 name=f'motion_strip_{c["mode"]}.jpg';sheet.save(D/name,quality=94);c['strip']=name
for j in range(3):
 modes=e['motion_clips'][j*3:(j+1)*3];sheet=Image.new('RGB',(1536,len(modes)*240),'#f6f4ef');draw=ImageDraw.Draw(sheet)
 for k,c in enumerate(modes):
  for i,d in enumerate([0,15,30,44]):
   sheet.paste(Image.open(D/f'motion_{c["mode"]}_{d:02d}.png').resize((384,216)),(i*384,k*240));draw.text((i*384+5,k*240+220),f'{c["mode"]} / {d}f',fill='black')
 sheet.save(D/f'motion_contactsheet_{j+1:02d}.jpg',quality=94)
p.write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
print('9 actual encoded motion strips / 3 summary sheets created',flush=True)
