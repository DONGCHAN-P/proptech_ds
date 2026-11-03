"""Reject critical text outside the active shared safe-area policy."""
import argparse,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('bounds');p.add_argument('--report',required=True);p.add_argument('--profile');a=p.parse_args()
c=root/'config/vertical_video_safe_area.json';config=json.loads(c.read_text(encoding='utf-8'));profile=a.profile or config['default_profile'];r=config['profiles'][profile]['critical_rect'];rect=[r['left'],r['top'],r['right'],r['bottom']]
b=json.loads(Path(a.bounds).read_text(encoding='utf-8'));issues=[]
if b.get('safe_rect')!=rect:issues.append({'reason':'stale_profile','recorded':b.get('safe_rect'),'expected':rect})
for i,x in enumerate(b.get('elements',[])):
 bb=x.get('bbox')
 if bb is None:continue
 if len(bb)!=4 or bb[0]<rect[0] or bb[1]<rect[1] or bb[2]>rect[2] or bb[3]>rect[3]:issues.append({'element':i,'kind':x.get('kind'),'bbox':bb,'reason':'outside_critical_rect'})
 minimum=config['profiles'][profile]['minimum_font_px']
 key={'title':'title','caption':'caption','key_value':'key_value','condition_source':'conditions'}.get(x.get('kind'))
 if key and x.get('font_px',0)<minimum[key]:issues.append({'element':i,'kind':x.get('kind'),'font_px':x.get('font_px'),'minimum':minimum[key],'reason':'font_below_policy'})
if not b.get('elements'):issues.append({'reason':'no_measured_elements'})
d={'profile':profile,'profile_revision':config['revision'],'profile_sha256':hashlib.sha256(c.read_bytes()).hexdigest(),'safe_rect':rect,'element_count':len(b.get('elements',[])),'failures':issues,'passed':not issues,'scope':'Measured source bounds only; inspect encoded frames and device/UI simulations separately.'}
out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'elements':d['element_count'],'failures':len(issues),'passed':d['passed']}))
raise SystemExit(bool(issues))
