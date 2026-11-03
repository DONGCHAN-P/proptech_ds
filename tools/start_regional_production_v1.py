"""Record the current direct production instruction and freeze v3 inputs."""
from pathlib import Path
import datetime as dt
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
now=dt.datetime.now(dt.timezone.utc).isoformat()
state=read(EP/'state.json')
current=sha(ROOT/state['script_file'])
assert current=='99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
assert sha(ROOT/'영상/지역별가격회복/대본.md')==current
if not (OUT/'state_before_production.json').exists(): write(OUT/'state_before_production.json',state)
decision=read(ROOT/'output/video_decisions/decisions/00054f140c83.json')
assert decision['artifact_hashes']['script_v3.md']==current
decision.update(status='approved',direct_chat_response={'at':now,'text':'이걸로 영상 제작 진행해줘','scope':'v3 script approved for production; budget and upload gates remain separate'})
write(ROOT/'output/video_decisions/decisions/00054f140c83.json',decision)
state.update(stage='production_v1_preparing',script_status='v3_approved_by_direct_production_request',
             production_revision='production-v1-jun',updated_at=now,
             budget_status='preparing_scoped_credit_quote_not_approved',audio_status='not_generated_for_v3')
write(EP/'state.json',state)
brief=read(EP/'brief.json')
if not (OUT/'brief_before_production.json').exists(): write(OUT/'brief_before_production.json',brief)
brief.update(scope='new_video_production_from_approved_script_v3',script_file=state['script_file'],script_sha256=current,
             user_authorization='2026-10-23 direct: 이걸로 영상 제작 진행해줘',
             canvas={'width':1920,'height':1080,'fps':30},voice='ElevenLabs Jun / eleven_v4',
             paid_generation=False,budget_gate='quote_then_explicit_credit_cap_approval',upload=False)
write(EP/'brief.json',brief)
decisions=read(EP/'decisions.json')
if not any(x['id']=='regional-production-v1-20261023' for x in decisions['decisions']):
    decisions['decisions'].append({'id':'regional-production-v1-20261023','status':'authorized_local_production',
      'basis':'Direct user request: 이걸로 영상 제작 진행해줘','script_sha256':current,
      'scope':'v3 script production, local assets/composition/previews/render preparation. Jun credit budget and upload remain separate.',
      'created_at':now})
write(EP/'decisions.json',decisions)
pre=read(EP/'episode_preflight_v3.json')
pre.update(status='production_v1_preparing_budget_not_approved',updated_at=now)
pre['approvals']['script'].update(status='approved_by_direct_chat',decision_id='00054f140c83')
write(EP/'episode_preflight_production_v1.json',pre)
for folder in ['editor/production-v1','visual/production-v1','narration/production-v1','outputs/production-v1-jun','outputs/production-v1-budget']:
    (EP/folder).mkdir(parents=True,exist_ok=True)
print(json.dumps({'script_approved':current,'production':'production-v1-jun','paid_generation_started':False},ensure_ascii=False))
