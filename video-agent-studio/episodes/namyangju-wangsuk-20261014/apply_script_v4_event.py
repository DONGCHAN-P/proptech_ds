from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
e=Path(__file__).resolve().parent;repo=e.parents[2]
event_path=repo/'output/video_decisions/inbox/718066296.json';event=json.loads(event_path.read_text(encoding='utf-8'))
decision=json.loads((repo/'output/video_decisions/decisions/553d76e214f6.json').read_text(encoding='utf-8'))
script=e/'outputs/story-review-v4/script_v4.md';digest=hashlib.sha256(script.read_bytes()).hexdigest()
assert event['decision_id']==decision['id']=='553d76e214f6'
assert event['episode']==decision['episode']==e.name
assert event['gate']==decision['gate']=='script' and event['action']=='approve'
assert decision['status']=='approved' and decision['response']['update_id']==event['update_id']
assert digest=='d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da' and digest in decision['summary']
if event.get('application_status')=='applied':
 print('already applied; no duplicate stage transition')
 raise SystemExit(0)
p=e/'state.json';state=json.loads(p.read_text(encoding='utf-8'))
assert state['script_sha256']==digest and state['script_revision']=='script-v4-hook-outside'
state.update(stage='script_v4_approved_budget_v2_pending',script_approved=True,script_approval_decision=decision['id'],script_approval_event=str(event_path.relative_to(repo)).replace('\\','/'),budget_approved=False,new_paid_generation_authorized=False,pending_gate='budget',pending_decision_ids={'budget':'f86d1138e110'})
p.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'decisions.json';records=json.loads(p.read_text(encoding='utf-8'))
for d in records['decisions']:
 if d.get('id',d.get('decision_id'))==decision['id']:
  d['status']='approved';d['approval_event']=str(event_path.relative_to(repo)).replace('\\','/');d['approved_script_sha256']=digest
p.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(e/'outputs/story-review-v4/script_decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')
event.update(application_status='applied',applied_at=datetime.now(timezone.utc).isoformat(),application={'episode':e.name,'script_revision':'script-v4-hook-outside','script_sha256':digest,'scope':'script approval only; budget, completed, pre_upload not approved'})
event_path.write_text(json.dumps(event,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'applied':True,'decision_id':decision['id'],'gate':'script','script_approved':True,'budget_approved':False,'paid_generation_started':False}))
