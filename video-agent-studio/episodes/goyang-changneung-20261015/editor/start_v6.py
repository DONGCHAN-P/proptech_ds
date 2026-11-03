from pathlib import Path
import json,sys,hashlib,datetime
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify.video_decisions import write
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
script=EP/'outputs/script-review-v6/script_v6.md'
assert hashlib.sha256(script.read_bytes()).hexdigest()=='0c94b0c1547b6abd2968c6de622fbf9793cd7cd0e4ab7415664e4701fe162fc1'
dp=ROOT/'output/video_decisions/decisions/aa6d1cf31eb6.json';d=json.loads(dp.read_text(encoding='utf8'))
d.update(status='approved',approved_at=at,approval_source='direct_conversation',approval_note='오케이 이대로 영상 제작 넘어가자. 기존 영상 참고, Claude 모션그래픽 요청, 필요한 소스 API 활용 요청.',approval_scope='script-v6 and local preview production; no unbounded paid budget or upload',paid_generation_authorized=False,upload_authorized=False)
write(dp,d);write(EP/'outputs/script-review-v6/review_decision.json',d)
s=json.loads((EP/'state.json').read_text(encoding='utf8'))
s.update(stage='preview_production',script_revision='script-v6',script_decision_id=d['id'],draft_script_status='approved',pending_gate=None,pending_decision_ids={},render_started=False,voice_generation_hold=True,paid_generation_authorized=False,publication_authorized=False)
s['active_tasks']=[{'task_id':'free-narration-v6','owner':'free_narration_v6','status':'running','output':'narration/preview-v6'},{'task_id':'claude-motion-v6','owner':'director/Claude CLI','status':'running','output':'writer/claude-motion-v6'},{'task_id':'editor-v6-preview','owner':'editor_v6','status':'running','output':'outputs/production-v6-preview'}]
s['production_v6']={'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'voice_plan':'free local Korean SAPI preview; final Jun replacement requires scoped budget','motion_request':'actual Claude CLI one bounded code generation','existing_sources':'production-v5 / Wangsuk v15 style / original 5s intro 10s outro','new_paid_api_calls':0,'new_source_api_plan':'only when scene requires; scoped provider estimate and cap before paid generation','upload_authorized':False,'started_at':at}
write(EP/'state.json',s)
lp=EP/'decisions.json';l=json.loads(lp.read_text(encoding='utf8'))
for row in l['decisions']:
 if row.get('id')==d['id']:row.update(d)
write(lp,l)
write(EP/'editor/production-v6-preview/production_contract.json',{'script':'outputs/script-review-v6/script_v6.md','script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'user_request':'existing sources + actual Claude motion + necessary API sources','minimum_duration_seconds':600,'format':'1920x1080 30fps','voice':'free local Korean preview','brand':'original intro5s/outro10s BGM, last voice+3sec hold','motion':'fixed camera, target/route/calendar/price emphasis; no blink or rapid zoom','reuse_before_generate':True,'new_paid_budget':None,'five_gates_preserved':True,'plan':['lock script-v6 approval','reuse source manifest','free chapter voice + measured timing','Claude motion components + representative QA','full preview render','independent output QA','deliver preview and scoped final voice budget if needed']})
print('script-v6 approval recorded; preview production active; paid generation/upload not authorized')
