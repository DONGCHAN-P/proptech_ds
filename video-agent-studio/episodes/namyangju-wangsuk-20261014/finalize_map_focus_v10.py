from pathlib import Path
import hashlib,json,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
out=e/'outputs/map-focus-v10';video=out/'map-focus_v10_front.mp4';qp=e/'qa/map-focus-v10/front_review.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads(qp.read_text(encoding='utf-8'));h=sha(video)
assert q['sha256']==h and q['required_open_count']==0 and q['local_review_ready']
assert q['video_frames']==15750 and abs(q['duration_s']-525)<.1
artifacts={str(p.relative_to(e)):sha(p) for p in (video,qp,e/'outputs/story-review-v6/script_v6.md')}
for n in ('1','2','3'):
 p=out/f'map-focus_v10_{n}.mp4';artifacts[str(p.relative_to(e))]=sha(p)
 receipt=json.loads((out/f'telegram_receipt_{n}.json').read_text(encoding='utf-8'))
 assert receipt['message_sent'] and receipt['sha256']==sha(p)
target=out/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'v10 앞부분00:00~08:45 검토본. 변경02:45~08:45: 예정역·도로·위치전환·지도위요약·음성대상강조. 기존대본/음성유지. MP4 SHA256 {h}. 이 부분산출물검토만해당;08:45이후수정/업로드/공개승인아님.')
 d.update(version='map-focus-v10-front',artifacts=artifacts,publication_authorized=False,scope={'review_range_s':[0,525],'changed_range_s':[165,525],'partial_review_only':True},qa_scope='actual encoded representative frames and full caption-bar ROI; actual listening and continuous playback unverified')
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(target,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in c['decisions']):c['decisions'].append(d)
write(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='v10_front_completed_review_pending',pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='v10_front_rendered_and_sample_QA_passed',current_review_video_path=str(video.relative_to(e)),video_sha256=h,actual_video_duration_seconds=q['duration_s'],delivery_revision='map-focus-v10-front',delivery_status='local_partial_review_ready',publication_authorized=False,new_paid_generation_authorized=False,completed_gate_approved_for_v10=False,revision_v10_applied_through_s=525)
s['staged_deliveries_v10']={n:{'video':f'outputs/map-focus-v10/map-focus_v10_{n}.mp4',**json.loads((out/f'telegram_receipt_{n}.json').read_text(encoding='utf-8'))} for n in ('1','2','3')}
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'sha256':h,'review_range_s':[0,525]}))
