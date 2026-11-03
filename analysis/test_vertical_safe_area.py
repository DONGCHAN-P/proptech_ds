"""Check critical rectangle against explicitly modeled device/UI cases, not real-device certification."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=json.loads((root/'config/vertical_video_safe_area.json').read_text(encoding='utf-8'))
r=p['profiles'][p['default_profile']]['critical_rect'];out=[]
for w,h in p['validation']['phone_viewports_css']+p['validation']['tablet_viewports_css']:
 for mode in p['validation']['fit_modes']:
  scale=(min if mode=='contain' else max)(w/1080,h/1920);dx=(w-1080*scale)/2;dy=(h-1920*scale)/2
  b=[dx+r['left']*scale,dy+r['top']*scale,dx+r['right']*scale,dy+r['bottom']*scale]
  # Conservative modeled full-width header/footer and 64 CSS-pixel right action rail.
  ui=[0,.14*h,w-64,.65*h]
  passed=b[0]>=ui[0] and b[1]>=ui[1] and b[2]<=ui[2] and b[3]<=ui[3]
  out.append({'viewport':[w,h],'fit':mode,'critical_bbox':b,'modeled_ui_clear_rect':ui,'passed':passed})
d={'profile':p['revision'],'cases':out,'failed':sum(not x['passed'] for x in out),'coverage':'model only; no actual device playback; normal collapsed UI; no square preview guarantee'}
dest=root/'output/vertical-safe-area';dest.mkdir(exist_ok=True)
(dest/'geometry_model_latest.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
print(json.dumps({'cases':len(out),'failed':d['failed'],'failures':[x for x in out if not x['passed']]}))
raise SystemExit(bool(d['failed']))
