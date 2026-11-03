from pathlib import Path
import json
e=Path(__file__).resolve().parent;repo=e.parents[2]
p=repo/'output/video_decisions/decisions/7c87283e1216.json'
if p.exists():
 d=json.loads(p.read_text(encoding='utf-8'));d['previous_status']=d['status'];d['status']='revision_requested';d['revision_basis']='Direct user: at41sec replace lone Dasan station with land-use plan and surrounding residential/commercial context';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='dasan_context_proof_revision',active_tasks=['dasan_context_research','dasan_context_editor'],pending_gate=None,full_video_patch_authorized=False,changed_proof_interval_seconds=[40.3,61],target_proof_version='rail-route-proof-v2');p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'decisions.json';d=json.loads(p.read_text(encoding='utf-8'))
for item in d['decisions']:
 if item.get('id',item.get('decision_id'))=='7c87283e1216':item['status']='revision_requested'
d['decisions'].append({'decision_id':'NYJ-DASAN-PROOF-20261015-02','status':'approved_direct_user_instruction','changed_interval':[40.3,61],'scope':'Improve standalone proof Dasan station surroundings with verified land-use/urban context; preserve voice and other shots; main merge remains unapproved'})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('v2 proof revision recorded; previous approval request superseded by revision')
