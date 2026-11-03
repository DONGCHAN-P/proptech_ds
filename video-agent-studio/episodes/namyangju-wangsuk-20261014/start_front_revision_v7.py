from pathlib import Path
import datetime, json, shutil

e=Path(__file__).resolve().parent
repo=e.parents[2]
out=e/'outputs/front-review-v7'
out.mkdir(parents=True,exist_ok=True)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
feedback={
 'revision':'landuse-front-v7','source':'direct_user_feedback_after_video_review_v6','recorded_at':now,
 'scope':{'from_frame':0,'to_frame_exclusive':13087,'fps':30,'chapters':'M000 through M005','full_episode_application':False},
 'requirements':[
  'Keep white caption panel continuously visible; semantic text may change without panel blinking.',
  'Macro frames identify Wangsuk regions, not a crowd of anonymous block points.',
  'One coherent spatial land-use board with housing, school, park, commerce, roads and clear regional anchors.',
  'Use closer framing of the actual blocks being discussed; no overlapping point-label pairs.',
  'Jobs and commerce need verified locations and relevant enterprise CI, with planned versus operating status.',
  'Keep intuitive operating rail visual and connect it to land-use context.',
  'Replace 05:40 cardinal-direction cards with one land-use plate and focused closeups.',
  'Change informative layers and framing for each topic; avoid repeated identical zoom-in/out loops.'
 ],
 'preserve':{'script_revision':'script-v4-hook-outside','audio_revision':'audio-v2','v6_original':True},
 'authorization':{'local_edit_and_review_render':True,'new_paid_generation':False,'publication':False},
 'reference_images':'Three images attached in the user message: composition/legibility references; old rail status must not be copied.',
 'roles':{'research':'landuse_research_v7','visual':'landuse_visual_v7','editor':'rail_route_editor','director':'root'}
}
write(out/'revision_brief.json',feedback)
p=e/'state.json'
backup=e/'state_before_front_v7.json'
if not backup.exists():shutil.copy2(p,backup)
s=read(p)
s.update(stage='landuse_front_v7_revision',active_tasks=['landuse_research_v7','landuse_visual_v7','editor_front_v7'],
         pending_gate=None,pending_decision_ids={},requested_output='front_00m00s_to_07m16s_review_v7',
         delivery_status='revision_in_progress',current_review_render_status='front_revision_in_progress',
         previous_review_video='outputs/video-review-v6/namyangju-map-led_v6.mp4',
         new_paid_generation_authorized=False,publication_authorized=False,
         revision_brief='outputs/front-review-v7/revision_brief.json')
write(p,s)
global_d=repo/'output/video_decisions/decisions/a0ef44f61f35.json'
d=read(global_d)
if d['status']=='pending':
 d.update(status='revision_requested',direct_feedback_at=now,direct_feedback_scope='front land-use map and caption panel revision; see episode outputs/front-review-v7/revision_brief.json')
 write(global_d,d)
common=read(e/'decisions.json')
for item in common['decisions']:
 if item.get('id',item.get('decision_id'))=='a0ef44f61f35':item.update(d)
common['decisions'].append({'decision_id':'NYJ-FRONT-V7-REVISION','kind':'internal_edit_application',
 'source':'direct_user_revision_request','recorded_at':now,'scope':'front0..13087frames; existing script/audio unchanged',
 'revision_brief':'outputs/front-review-v7/revision_brief.json','no_new_paid_generation':True,'publication_authorized':False})
write(e/'decisions.json',common)
print(json.dumps({'revision':'landuse-front-v7','previous_review_gate':'revision_requested','scope_frames':13087,'paid_generation':False}))
