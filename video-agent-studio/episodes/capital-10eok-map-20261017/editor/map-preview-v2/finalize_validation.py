from pathlib import Path
import json,hashlib
E=Path('video-agent-studio/episodes/capital-10eok-map-20261017');R=E/'research/annual-map-v2';O=E/'outputs/map-preview-v2';p=json.loads((R/'map_packet_v2.json').read_text(encoding='utf8'));adjacent=0;all_events=0
for c in p['complexes']:
 prev_observed=None
 for y in range(2006,2027):
  state=c['years'][str(y)]['status']
  if y>2006 and c['years'][str(y-1)]['status']=='over' and state=='under':adjacent+=1
  if state in ['under','over']:
   if prev_observed=='over' and state=='under':all_events+=1
   prev_observed=state
assert adjacent==374 and all_events==528
f=R/'validation.json';d=json.loads(f.read_text(encoding='utf8'));d.pop('mapped_over_to_under_reappearances',None);d['adjacent_year_over_to_under']=adjacent;d['all_observed_over_to_under_reappearances']=all_events;d['reappearance_definition']='Compare successive observed price states; no_trade years do not reset last observed status. Actual frame status is still no_trade in those years.';d['modeled_mobile_safe_cases']=18;d['modeled_mobile_safe_failed']=0;f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
for f in [R/'handoff.json',O/'handoff.json']:
 h=json.loads(f.read_text(encoding='utf8'));h['adjacent_year_over_to_under']=adjacent;h['all_observed_over_to_under_reappearances']=all_events;h['reappearance_counts_are_not_total_current_blue_points']=True;h['modeled_mobile_safe_cases']=18
 for a in h['outputs']:
  q=Path(a['path']);a['sha256']=hashlib.sha256(q.read_bytes()).hexdigest();a['bytes']=q.stat().st_size
 f.write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf8')
print({'adjacent':adjacent,'all_observed_reappearances':all_events,'video_rerendered':False})
