from pathlib import Path
import hashlib,json,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
o=e/'outputs/minimal-v12';v=o/'minimal_v12_front.mp4';qp=e/'qa/minimal-v12/front_review.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads(qp.read_text(encoding='utf-8'));h=sha(v)
assert q['sha256']==h and q['required_open_count']==0 and q['local_review_ready']
assert q['video_frames']==15750 and abs(q['duration_s']-525)<.1
artifacts={str(p.relative_to(e)):sha(p) for p in [v,qp,e/'outputs/story-review-v6/script_v6.md']}
p=o/'completed_decision.json'
if p.exists():
 d=json.loads(p.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'v12 부분검토본00:00~08:45. 최종v10원본을기준으로줌인/줌아웃및중간위치지도제거·예정역표기만수정. 나머지v10구성/모션/음성/자막유지. MP4 SHA256 {h}. 이부분검토만해당;업로드/공개승인아님.')
 d.update(version='minimal-v12-front',artifacts=artifacts,publication_authorized=False,scope={'review_range_s':[0,525],'base_revision':'map-focus-v10-final','changes_only':['camera zoom removal','station location correction'],'partial_review_only':True})
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(p,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in c['decisions']):c['decisions'].append(d)
write(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='v12_front_completed_review_pending',pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='v12_minimal_v10_revision_QA_passed',current_review_video_path=str(v.relative_to(e)),video_sha256=h,actual_video_duration_seconds=q['duration_s'],delivery_revision='minimal-v12-front',delivery_status='local_partial_review_ready',new_paid_generation_authorized=False,publication_authorized=False);write(p,s)
p=e/'scenes.json';s=json.loads(p.read_text(encoding='utf-8'));s['visual_revision_target']='minimal-v12-front';s['visual_revision_scope']='Final v10 with only zoom removal and planned station corrections through525s'
for x in s['scenes']:
 if x.get('end_frame',0)>1898 and x.get('start_frame',0)<15750:x['visual_override']={'revision':'minimal-v12-front','source':str(v.relative_to(e)),'status':'actual_rendered_QA_passed','changes':'zoom removal and planned station corrections only'}
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'sha256':h}))
