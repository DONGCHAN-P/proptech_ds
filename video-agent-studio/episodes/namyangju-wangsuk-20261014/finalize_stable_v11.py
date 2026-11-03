from pathlib import Path
import hashlib,json,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
out=e/'outputs/stable-maps-v11';video=out/'stable-maps_v11_front.mp4';qp=e/'qa/stable-maps-v11/finalfront_review.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads(qp.read_text(encoding='utf-8'));h=sha(video)
assert q['sha256']==h and q['required_open_count']==0 and q['local_review_ready']
assert q['video_frames']==15750 and abs(q['duration_s']-525)<.1
paths=[video,qp,out/'stable-maps_v11_rail.mp4',e/'outputs/story-review-v6/script_v6.md']
artifacts={str(p.relative_to(e)):sha(p) for p in paths}
target=out/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'v11 정적지도 앞부분00:00~08:45 검토본.1:04맥락수정,설명지도줌/팬/펄스/선그리기/짧은삽입컷제거,운영철도고대비,추정역핀폐기및공식계획구간재검증. MP4 SHA256 {h}. 이부분검토만해당;업로드/공개승인아님.')
 d.update(version='stable-maps-v11-front',artifacts=artifacts,publication_authorized=False,scope={'review_range_s':[0,525],'partial_review_only':True},qa_scope='actual encoded dense frames, full map ROI and cut inventory; actual listening and continuous playback unverified')
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(target,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in c['decisions']):c['decisions'].append(d)
write(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='v11_front_completed_review_pending',pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='v11_front_rendered_and_dense_QA_passed',current_review_video_path=str(video.relative_to(e)),video_sha256=h,actual_video_duration_seconds=q['duration_s'],delivery_revision='stable-maps-v11-front',delivery_status='local_partial_review_ready',publication_authorized=False,new_paid_generation_authorized=False,completed_gate_approved_for_v11=False,revision_v11_applied_through_s=525)
write(p,s)
p=e/'scenes.json';s=json.loads(p.read_text(encoding='utf-8'));s['visual_revision_target']='stable-maps-v11-front';s['visual_revision_scope']='static explanatory maps through525s; approved channel branding preserved'
for x in s['scenes']:
 if 1750<=x.get('end_frame',0) and x.get('start_frame',0)<15750:x['visual_override']={'revision':'stable-maps-v11-front','source':str(video.relative_to(e)),'status':'actual_rendered_dense_QA_passed','motion':'none_for_explanatory_maps'}
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'sha256':h}))
