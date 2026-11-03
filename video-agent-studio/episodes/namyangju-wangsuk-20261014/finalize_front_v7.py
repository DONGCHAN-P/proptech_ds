"""Register only the exact first-part review, never the full episode or upload."""
from pathlib import Path
import hashlib, json, sys

e=Path(__file__).resolve().parent
repo=e.parents[2]
sys.path.insert(0,str(repo))
from notify.video_decisions import create, write

out=e/'outputs/front-review-v7'
video=out/'namyangju-landuse_front_v7.mp4'
qa_path=e/'qa/landuse-front-v7/final_review.json'
qa=json.loads(qa_path.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=sha(video)
assert qa['local_review_ready'] is True and qa['required_open_count']==0
assert qa['sha256'].lower()==h
assert abs(float(qa['duration_s'])-13087/30)<0.1
script=e/'writer/map-led-v4/script_v4.md'
assert sha(script)=='d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'
srt=out/'namyangju-landuse_front_v7.srt'
artifacts={str(p.relative_to(e)):sha(p) for p in [video,srt,script,qa_path]}
target=out/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'))
 assert d['artifacts']==artifacts, 'Changed artifacts require a new versioned review decision.'
else:
 d=create(e.name,'completed',f'앞부분 수정 검토본 v7: 00:00~07:16.233,13087frames,1080p30. 기존 대본v4/음성v2 재사용. 흰 자막바·권역/토지이용지도·기업CI·철도맥락 수정. MP4 SHA256 {h}. 이 앞부분 산출물 검토만 해당하며 후반/전체본 적용·업로드 승인은 포함하지 않음.')
 d.update(version='front-review-v7',artifacts=artifacts,
          scope={'from_frame':0,'to_frame_exclusive':13087,'fps':30,'partial_review_only':True},
          publication_authorized=False,full_episode_application_approved=False)
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d)
 write(target,d)
common=json.loads((e/'decisions.json').read_text(encoding='utf-8'))
if not any(x.get('id',x.get('decision_id'))==d['id'] for x in common['decisions']):common['decisions'].append(d)
write(e/'decisions.json',common)
s=json.loads((e/'state.json').read_text(encoding='utf-8'))
s.update(stage='front_review_v7_pending',active_tasks=[],pending_gate='completed',
 pending_decision_ids={'completed':d['id']},last_decision_id=d['id'],
 current_review_render_status='front_rendered_and_sample_qa_passed',
 current_review_video_path=str(video.relative_to(e)).replace('\\','/'),
 video_path=str(video.relative_to(e)).replace('\\','/'),
 actual_video_duration_seconds=qa.get('duration_s',13087/30),
 full_episode_video_path='outputs/video-review-v6/namyangju-map-led_v6.mp4',
 full_episode_application_approved=False,delivery_revision='front-review-v7',
 delivery_status='front_local_review_ready',render_process_session=None,
 video_sha256=h,new_paid_generation_authorized=False,revision_v7_additional_cash_usd=0,
 revision_v7_new_voice_requests=0,revision_v7_new_image_requests=0,
 completed_gate_approved_for_v7=False,pre_upload_gate_approved_for_v7=False,publication_authorized=False)
s['completed_tasks']=list(dict.fromkeys(s.get('completed_tasks',[])+[
 'landuse_research_v7','landuse_visual_v7','editor_front_v7','qa_front_v7']))
write(e/'state.json',s)
p=e/'scenes.json';scenes=json.loads(p.read_text(encoding='utf-8'))
backup=e/'scenes_full_v6_before_front_v7.json'
if not backup.exists():backup.write_text(p.read_text(encoding='utf-8'),encoding='utf-8')
for scene in scenes['scenes']:
 if scene['scene_id'] in ['M000','M001','M002','M003','M004','M005']:
  scene.update(front_visual_revision='landuse-front-v7',front_review_video=str(video.relative_to(e)).replace('\\','/'),
               front_status='partial_review_ready',audio_revision='audio-v2',script_revision='script-v4-hook-outside')
scenes.update(front_review_revision='front-review-v7',front_review_frames=13087,full_episode_application_approved=False)
scenes['front_camera_manifest']='outputs/front-review-v7/scene_camera_manifest.json'
scenes['front_asset_manifest']='outputs/front-review-v7/source_manifest.json'
write(p,scenes)
print(json.dumps({'completed_decision_id':d['id'],'video_sha256':h,'front_local_review_ready':True}))
