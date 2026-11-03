from pathlib import Path
from PIL import Image,ImageDraw
import json
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');o=E/'outputs/production-v6-preview';q=E/'qa/production-v6-preview';m=json.loads((o/'cut_evidence_manifest_r2.json').read_text(encoding='utf-8'));print(m.keys())
rows=m['frames']
for k in range(0,len(rows),24):
 board=Image.new('RGB',(1920,1800),'#ddd');d=ImageDraw.Draw(board)
 for j,r in enumerate(rows[k:k+24]):
  im=Image.open(o/r['file']).convert('RGB');im.thumbnail((480,270));x=(j%4)*480;y=(j//4)*300;board.paste(im,(x,y));d.text((x+4,y+272),f"f{r['frame']} {r['time_s']:.3f}s {Path(r['file']).name}",fill='black')
 board.save(q/f'boundary_sheet_{k//24+1:02}.jpg',quality=92)
print('made sheets', (len(rows)+23)//24)
