from pathlib import Path
import hashlib,json,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
o=e/'outputs/caption-station-v13';front=o/'caption-station_v13_front.mp4';full=o/'caption-station_v13_full.mp4'
qroot=e/'qa/caption-station-v13';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fq=json.loads((qroot/'front_review.json').read_text(encoding='utf-8'))
q=json.loads((qroot/'full_review.json').read_text(encoding='utf-8'))
for p,r,frames in ((front,fq,15750),(full,q,26720)):
 assert r['sha256']==sha(p) and r['required_open_count']==0 and r['local_review_ready']
 assert r['video_frames']==frames
assert abs(fq['duration_s']-525)<.1 and abs(q['duration_s']-26720/30)<.1
paths=[front,full,o/'brand_intro_v13_no_caption.mp4',o/'brand_outro_v13_no_caption.mp4',qroot/'front_review.json',qroot/'full_review.json',e/'outputs/story-review-v6/script_v6.md']
artifacts={str(p.relative_to(e)):sha(p) for p in paths};h=sha(full);target=o/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'v13수정검토:앞부분0..8:45 및 전체연결본14:50.67. 무음인트로/아웃트로빈흰자막박스제거,일패역철도/업무시설동일원도도해보강,8f구화면·1/4f강조복귀·짧은임시지도삽입제거. 8:45이후본문은기존v8보존,마지막브랜드박스만제거. Full MP4 SHA256 {h}. 업로드/공개승인아님.')
 d.update(version='caption-station-v13',artifacts=artifacts,publication_authorized=False,scope={'front_revision_range_s':[0,525],'unchanged_rear_source':'video-review-v8','outro_box_removed_frames':[26420,26720]},qa_scope='actual encoded frame boundaries and flash audit; actual listening and continuous playback unverified')
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(target,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in c['decisions']):c['decisions'].append(d)
write(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(stage='v13_completed_review_pending',active_tasks=[],pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='v13_rendered_flash_QA_passed',current_review_video_path=str(full.relative_to(e)),front_review_video_path=str(front.relative_to(e)),video_sha256=h,actual_video_duration_seconds=q['duration_s'],delivery_revision='caption-station-v13',delivery_status='local_review_ready',new_paid_generation_authorized=False,publication_authorized=False);write(p,s)
p=e/'scenes.json';s=json.loads(p.read_text(encoding='utf-8'));s['visual_revision_target']='caption-station-v13';s['visual_revision_scope']='front flash/cuegap/station geometry corrections and brand caption exclusions; rear content reused fromv8';s['caption_panel_excluded_frames']=[[0,45],[917,1067],[26420,26720]]
for x in s['scenes']:
 if x.get('start_frame',0)<15750:x['visual_override']={'revision':'caption-station-v13','source':str(front.relative_to(e)),'status':'actual_rendered_boundary_QA_passed'}
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'full_sha256':h,'front_sha256':sha(front)}))
