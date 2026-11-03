from pathlib import Path
import json,sys,hashlib
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify.video_decisions import write
p=json.loads((EP/'preflight.json').read_text(encoding='utf8'))
write(EP/'editor/production-v6-preview/preflight_before_v6.json',p)
p['status']='script_approved_preview_production_in_progress'
p['baseline'].update(current_video='outputs/production-v5/changneung_full_v5r2.mp4',sha256='7979a8071e4c07d4047a46b37b4abf6fa89c1a8aa9f4fb0c90dd0d99bec9f0b0',script_revision='script-v6',audio_revision='audio-v6-preview-heami-rateminus1',brand_intro='outputs/editor-preflight-v1/brand_intro_generic_v1.mp4',brand_outro='outputs/editor-preflight-v1/brand_outro_generic_v1.mp4',bgm='reuse existing licensed brand tracks; no new music purchase')
d=json.loads((EP/'outputs/script-review-v6/review_decision.json').read_text(encoding='utf8'))
p['approvals']['script']={'decision_id':d['id'],'status':'approved','revision':'script-v6','artifact_hashes':d['artifact_hashes']}
for gate in ['budget','completed','pre_upload']:
 old=p['approvals'][gate]
 p.setdefault('historical_approvals',{})[gate]=old
 p['approvals'][gate]={'decision_id':None,'status':'not_granted_for_v6','artifact_hashes':{}}
p['approvals']['budget'].update(credits_cap=0,cash_cap=0,automatic_retry_allowed=False,note='free local preview; prior v3 paid allowance not transferred')
p['story'].update(opening_question='창릉 새집을 기다릴까, 원흥·삼송 기존집을 고를까',previous_episode_reference='광교동탄 기준→왕숙 완성 시차→창릉 기존 생활권 접점',next_episode_promise='하남 교산 같은 기준')
p['v6_production']={'voice':'Microsoft Heami local free review voice','narration_duration_seconds':916.7660317460317,'new_paid_generation':False,'claude_motion_request':'writer/claude-motion-v6','representative_qa':'pending','continuous_playback':'not_performed','actual_listening':'not_performed'}
write(EP/'preflight.json',p);write(EP/'editor/production-v6-preview/preflight_v6.json',p)
print('v6 preflight refreshed; prior scoped gate evidence retained separately')
