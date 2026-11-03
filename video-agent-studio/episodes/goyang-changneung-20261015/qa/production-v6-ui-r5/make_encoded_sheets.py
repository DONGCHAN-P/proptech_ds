from pathlib import Path
from PIL import Image,ImageDraw
import json
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');O=E/'outputs/production-v6-ui-r5';Q=E/'qa/production-v6-ui-r5';m=json.loads((O/'encoded_evidence_manifest.json').read_text(encoding='utf-8'));root=O/'encoded_evidence';rows=[]
for s in m['changed_segments']:
 for n in s['samples']:rows.append((n,f"{s['scene_id']} {s['start_frame']} {n}"))
for n in m['boundaries']:rows.append((n['file'],f"boundary {n['frame']}"))
for clip in m['motion_clips']:
 for n in clip['samples']:rows.append((n,clip['mode']+' '+n))
for k in range(0,len(rows),24):
 sheet=Image.new('RGB',(1920,1740),'#ddd');d=ImageDraw.Draw(sheet)
 for j,(n,label) in enumerate(rows[k:k+24]):
  im=Image.open(root/n).convert('RGB');im.thumbnail((480,270));x=j%4*480;y=j//4*290;sheet.paste(im,(x,y));d.text((x+4,y+272),label,fill='black')
 sheet.save(Q/f'encoded_all_{k//24+1:02}.jpg',quality=92)
print('frames',len(rows),'sheets',(len(rows)+23)//24)
