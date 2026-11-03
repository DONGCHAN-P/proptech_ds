from pathlib import Path
import json,re,sys,hashlib
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify.video_decisions import write
proposal=json.loads((EP/'editor/production-v6-preview/scene_proposal.json').read_text(encoding='utf8'))
old=json.loads((EP/'scenes.json').read_text(encoding='utf8'));write(EP/'editor/production-v6-preview/scenes_before_v6.json',old)
script=(EP/'outputs/script-review-v6/script_v6.md').read_text(encoding='utf8')
sections=re.findall(r'## (M\d+) · ([^\n]+)\n\n### 낭독\n\n([\s\S]*?)\n### 화면 지시\n\n([\s\S]*?)(?=\n## M|\Z)',script)
assert len(sections)==len(proposal['scenes'])==10
timing={x['scene_id']:x for x in proposal['scenes']}
rows=[]
for sid,message,text,direction in sections:
 t=timing[sid]
 rows.append({**t,'message':message,'narration_text':text.strip(),'screen_direction':direction.strip(),'claim_ids':[],'claim_basis':'existing v5 claim basis + research/commute-v6 for M002; no invented new claim IDs','asset_ids':[],'asset_types':['reuse_verified_map','local_explanatory_motion'],'script_revision':'script-v6','audio_revision':'audio-v6-preview-heami-rateminus1','start_s':t['start_frame']/30,'end_s':t['end_frame']/30,'status':'preview_timing_locked','asset_binding':'outputs/production-v6-preview/project.json'})
write(EP/'scenes.json',{'episode_id':EP.name,'revision':'script-v6-preview-timing-lock','status':'preview_production','timing_status':'measured local TTS; internal caption splits estimated','scenes':rows,'duration_frames':proposal['duration_frames'],'fps':30,'not_final_Jun_timing':True})
s=json.loads((EP/'state.json').read_text(encoding='utf8'));s.update(audio_revision='audio-v6-preview-heami-rateminus1',timing_revision='preview-timing-lock-v6',stage='preview_editing')
for t in s['active_tasks']:
 if t['task_id']=='free-narration-v6':t['status']='complete_measured_not_listened'
write(EP/'state.json',s)
print('10 preview scenes locked to measured local TTS; original scenes archived')
