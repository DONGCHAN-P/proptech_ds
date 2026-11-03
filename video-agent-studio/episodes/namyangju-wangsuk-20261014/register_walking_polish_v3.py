import json
from pathlib import Path
e=Path(__file__).resolve().parent;repo=e.parents[2]
p=repo/'output/video_decisions/decisions/2581a0870436.json'
if p.exists():
 d=json.loads(p.read_text(encoding='utf-8'));d['previous_status']=d['status'];d['status']='revision_requested';d['revision_basis']='Direct user: walking figure too large, stickman poor aesthetic; improve person and walking motion';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='walking_motion_polish',active_tasks=['walking_polish_editor','walking_polish_qa'],pending_gate=None,target_proof_version='rail-route-proof-v3',full_video_patch_authorized=False);p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'decisions.json';d=json.loads(p.read_text(encoding='utf-8'))
for item in d['decisions']:
 if item.get('id',item.get('decision_id'))=='2581a0870436':item['status']='revision_requested'
d['decisions'].append({'decision_id':'NYJ-WALK-POLISH-20261015-03','status':'approved_direct_user_instruction','scope':'Refine oversized stick walking figure and motion in standalone proof; retain other maps, bus, voice and timings; preserve full master'})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('walking-only proof revision registered')
