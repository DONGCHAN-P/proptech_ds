"""Apply the explicit user choice to defer speech generation, preserving video work."""
from pathlib import Path
import datetime as dt,json
ROOT=Path(__file__).resolve().parents[1];EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=dt.datetime.now(dt.timezone.utc).isoformat()
p=ROOT/'output/video_decisions/decisions/5fe307eed02c.json';decision=read(p)
assert decision['gate']=='budget' and decision['episode']==EP.name and decision['status']!='approved'
decision.update(status='revision_requested',direct_chat_response={'at':now,'answer':'음성 생성 보류','scope':'No paid speech generation; continue local visual video production'},resolution='deferred_by_user')
write(p,decision)
state=read(EP/'state.json');state.update(stage='full_visual_review_production_voice_deferred',updated_at=now,
 budget_status='voice_generation_deferred_by_user',audio_status='narration_not_generated_user_hold',
 full_review_scope='Full visuals/captions with provisional timing and reused local brand/music; not an actual Jun timing lock',timing_locked=False)
write(EP/'state.json',state)
brief=read(EP/'brief.json');brief.update(voice_generation='deferred_by_user_2026-10-23',paid_generation=False,
 review_output='Full visual/caption review with existing local music; provisional timing')
write(EP/'brief.json',brief)
pre=read(EP/'episode_preflight_production_v1.json');pre['approvals']['budget'].update(status='deferred_by_user',decision_id='5fe307eed02c')
write(EP/'episode_preflight_production_v1.json',pre)
d=read(EP/'decisions.json')
if not any(v['id']=='regional-voice-deferred-20261023'for v in d['decisions']):
    d['decisions'].append({'id':'regional-voice-deferred-20261023','status':'explicit_user_instruction','basis':'Async budget reply: 음성 생성 보류',
     'scope':'No voice synthesis or paid requests. Continue full visual/caption review using provisional timing and existing local brand/music; no upload.',
     'created_at':now})
write(EP/'decisions.json',d)
assert not (EP/'narration/production-v1/authorization.json').exists()
print(json.dumps({'voice_generation':'deferred_by_user','paid_calls':0,'full_visual_review':'authorized_continuation'},ensure_ascii=False))
