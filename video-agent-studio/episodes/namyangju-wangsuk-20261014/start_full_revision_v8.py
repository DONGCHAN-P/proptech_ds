from pathlib import Path
import datetime,json,shutil
e=Path(__file__).resolve().parent;repo=e.parents[2]
out=e/'outputs/video-review-v8';out.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
brief={'revision':'landuse-full-v8','source':'direct_user_revision_request','recorded_at':now,
 'scope':{'from_frame':0,'end_frame_exclusive':26292,'fps':30,'full_episode_visual_revision_authorized':True},
 'requirements':[
 'At50s navigate continuously from large regional map toward Wangsuk1/2; at70s continue toward Wangsuk1 south.',
 'At152s locate the right-side W1/W2 native land-use boards on the left operating railway map using verified district location areas and consistent identification.',
 'At260s add researched concise meanings/uses to relevant blocks rather than anonymous codes; no invented project brands or development status.',
 'Extend the front land-use and caption guide through supply, alternatives, outside comparisons, block candidates and outro.',
 'Preserve constant white caption box, all269meaning cues, all11approvedJun files, intro/outro music; vary meaningful map layers without repeated camera resets.'
 ],
 'preserve':{'script':'script-v4-hook-outside','audio':'audio-v2','v6_and_front_v7':True},
 'authorization':{'local_full_revision_render':True,'new_paid_generation':False,'external_file_send':False,'publication':False}}
write(out/'revision_brief.json',brief)
p=e/'state.json';backup=e/'state_before_full_v8.json'
if not backup.exists():shutil.copy2(p,backup)
s=read(p);s.update(stage='landuse_full_v8_revision',active_tasks=['research_v8','editor_full_v8','qa_full_v8'],
 pending_gate=None,pending_decision_ids={},requested_output='full_landuse_video_v8',
 current_review_render_status='v8_revision_in_progress',delivery_status='revision_in_progress',
 new_paid_generation_authorized=False,publication_authorized=False,
 full_episode_visual_revision_authorized=True,revision_brief='outputs/video-review-v8/revision_brief.json')
write(p,s)
p=repo/'output/video_decisions/decisions/47449797986f.json';d=read(p)
if d['status']=='pending':
 d.update(status='revision_requested',direct_feedback_at=now,direct_feedback_scope='v8 zoom navigation, geographic linking, block meanings and rear visual extension')
 write(p,d)
p=e/'decisions.json';common=read(p)
for item in common['decisions']:
 if item.get('id',item.get('decision_id'))=='47449797986f':item.update(d)
if not any(x.get('decision_id')=='NYJ-FULL-V8-REVISION' for x in common['decisions']):
 common['decisions'].append({'decision_id':'NYJ-FULL-V8-REVISION','source':'direct_user_revision_request',
 'scope':'full26292frames visualedit; unchangedapprovedscript/audio','recorded_at':now,
 'new_paid_generation':False,'publication_authorized':False,'brief':'outputs/video-review-v8/revision_brief.json'})
write(p,common)
print(json.dumps({'revision':'v8','scope_frames':26292,'previous_front_decision':'revision_requested'}))
