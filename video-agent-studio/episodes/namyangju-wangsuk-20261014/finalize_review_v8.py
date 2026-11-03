from pathlib import Path
import hashlib,json,sys
e=Path(__file__).resolve().parent; repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
out=e/'outputs/video-review-v8';video=out/'namyangju-landuse_full_v8.mp4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
qpath=e/'qa/landuse-full-v8/final_review.json';q=json.loads(qpath.read_text(encoding='utf-8'))
h=sha(video)
assert h==q['sha256']=='94b6d04aa780c93509203b705ce02fa12085d57a0faef23a0629769db0549ba4'
assert q['local_review_ready'] and q['required_open_count']==0
script=e/'outputs/story-review-v6/script_v6.md'
assert sha(script)=='428d0e0325097d6d146e358a4f92f2fcfd3337ab12bff7b77e4e7e57ca40ca41'
srt=out/'namyangju-landuse_full_v8.srt'
artifacts={str(p.relative_to(e)):sha(p) for p in (video,srt,script,qpath)}
target=out/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'전체 검토본 v8:14분50.67초,1080p30,275자막. 대본v6·새벡터인트로·기존인트로/아웃트로복원·전체지도수정. MP4 SHA256 {h}. 이 산출물의 검토 승인만 해당. 업로드·공개 승인 아님.')
 d.update(version='video-review-v8',artifacts=artifacts,publication_authorized=False,qa_scope='77 actual frames and all26720 caption-bar ROI; actual listening/continuous playback unverified')
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(target,d)
p=e/'decisions.json';common=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in common['decisions']):common['decisions'].append(d)
write(p,common)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'))
s.update(stage='completed_review_pending',pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='rendered_and_sample_qa_passed',current_review_video_path=str(video.relative_to(e)),full_episode_video_path=str(video.relative_to(e)),video_path=str(video.relative_to(e)),video_sha256=h,actual_video_duration_seconds=q['duration_s'],delivery_revision='video-review-v8',delivery_status='local_review_ready',completed_gate_approved_for_v8=False,pre_upload_gate_approved_for_v8=False,publication_authorized=False,new_paid_generation_authorized=False,qa_scope=d['qa_scope'])
write(p,s)
p=e/'scenes.json';s=json.loads(p.read_text(encoding='utf-8'));s['status']='rendered_local_review_ready'
for x in s['scenes']:x['status']='rendered_sample_qa_review_ready'
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'video_sha256':h,'local_review_ready':True}))
