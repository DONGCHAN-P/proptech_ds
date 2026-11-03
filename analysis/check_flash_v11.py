from pathlib import Path
from PIL import Image,ImageChops
import json
p=Path('video/out/qa-v11');base=Image.open(p/'frame-180.5.png').convert('RGB');checks=[]
for t in ['180.53333','180.56667','180.6']:
 diff=ImageChops.difference(base,Image.open(p/f'frame-{t}.png').convert('RGB'));h=diff.histogram();mad=sum(i%256*n for i,n in enumerate(h))/(base.width*base.height*3)
 checks.append(dict(time=t,mean_absolute_pixel_difference=mad,large_frame_change=mad>1))
(p/'flash-check.json').write_text(json.dumps(checks,indent=2),encoding='utf8');print(checks)
