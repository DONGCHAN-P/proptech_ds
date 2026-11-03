from pathlib import Path
import json,numpy as np
from PIL import Image
Q=Path(__file__).resolve().parent;EP=Q.parents[1];P=json.loads((EP/'outputs/production-v3/rendered_project_v3.json').read_text('utf8'));M=json.loads((Q/'encoded_frame_manifest.json').read_text('utf8'))
rows=[]
for n in M['frames']:
 v=next((v for v in P['visual_intervals'] if v['start_frame']<=n<v['end_frame']),None)
 if not v or v['kind']!='frame' or v.get('hideCaption') or not v.get('caption'):continue
 a=np.array(Image.open(Q/'encoded_frames'/f'frame_{n:06}.png').convert('RGB'))[928:1048]
 ys,xs=np.where((a.max(axis=2)<165)&(a.min(axis=2)<120))
 bbox=[int(xs.min()),int(ys.min()+928),int(xs.max()+1),int(ys.max()+929)] if len(xs) else None
 rows.append({'frame':n,'bbox':bbox,'inside_caption_safe':bbox is None or (bbox[0]>=131 and bbox[2]<=1789 and bbox[1]>=934 and bbox[3]<=1040)})
report={'basis':'actual encoded pixel dark-ink bounds in caption strip y928..1048; not DOM getBBox or OCR','checked':len(rows),'outside_safe':[r for r in rows if not r['inside_caption_safe']],'rows':rows}
(Q/'caption_pixel_bounds.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({'checked':len(rows),'outside_safe':report['outside_safe']}))
