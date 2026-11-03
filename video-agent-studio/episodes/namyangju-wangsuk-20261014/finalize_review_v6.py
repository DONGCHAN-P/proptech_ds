"""Register the exact rendered review artifact; never approve completed/pre_upload."""
from pathlib import Path
import hashlib, json, sys

e=Path(__file__).resolve().parent
repo=e.parents[2]
sys.path.insert(0,str(repo))
from notify.video_decisions import create, write

out=e/'outputs/video-review-v6'
video=out/'namyangju-map-led_v6.mp4'
qa=json.loads((e/'qa/map-led-v6/final_review.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
video_hash=sha(video)
technical=json.loads((out/'technical_qa/encoded_check.json').read_text(encoding='utf-8'))
assert technical['sha256']==video_hash
assert technical['whole_decode_pass'] is True
duration=float(technical['probe']['format']['duration'])
assert abs(duration-876.4)<0.1
assert qa['local_review_ready'] is True and qa['required_open_count']==0
assert qa['sha256'].lower()==video_hash
script=e/'writer/map-led-v4/script_v4.md'
assert sha(script)=='d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'
artifacts={str(p.relative_to(e)):sha(p) for p in [video,out/'namyangju-map-led_v6.srt',script,e/'qa/map-led-v6/final_review.json']}
target=out/'completed_decision.json'
if target.exists():
    d=json.loads(target.read_text(encoding='utf-8'))
    assert d['artifacts']==artifacts, 'Changed review artifacts need a new decision version.'
else:
    d=create(e.name,'completed',
       f'검토본 v6: 14:36.4,1080p30; script-v4-hook-outside/audio-v2. '
       f'완성본 수정 의견·검토 승인만 해당. MP4 SHA256 {video_hash}. 업로드·공개 승인 아님.')
    d.update(version='video-review-v6',artifacts=artifacts,
             qa_scope='actual_encoded_frame_samples_and_audio_signal_checks; no_actual_listening_or_continuous_playback',
             publication_authorized=False)
    write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d)
    write(target,d)
common=json.loads((e/'decisions.json').read_text(encoding='utf-8'))
if not any(x.get('id',x.get('decision_id'))==d['id'] for x in common['decisions']):
    common['decisions'].append(d)
write(e/'decisions.json',common)
s=json.loads((e/'state.json').read_text(encoding='utf-8'))
s.update(stage='completed_review_pending', active_tasks=[], pending_gate='completed',
         pending_decision_ids={'completed':d['id']}, last_decision_id=d['id'],
         render_process_session=None, current_review_render_status='rendered_and_sample_qa_passed',
         current_review_video_path=str(video.relative_to(e)).replace('\\','/'),
         video_path=str(video.relative_to(e)).replace('\\','/'), actual_video_duration_seconds=duration,
         delivery_revision='video-review-v6', delivery_status='local_review_ready',
         video_sha256=video_hash, qa_scope=qa.get('scope',d['qa_scope']),
         completed_gate_approved_for_v6=False, pre_upload_gate_approved_for_v6=False,
         included_credit_balance_before=34560, actual_audio_duration_seconds=865.76,
         publication_authorized=False, new_paid_generation_authorized=False)
s['completed_tasks']=list(dict.fromkeys(s.get('completed_tasks',[])+[
    'narration_audio_v2', 'editor_map_led_v6', 'qa_map_led_v6_sample_and_signal_review']))
write(e/'state.json',s)
scenes=json.loads((e/'scenes.json').read_text(encoding='utf-8'))
scenes['status']='rendered_local_review_ready'
for scene in scenes['scenes']:
    scene['status']='rendered_sample_qa_review_ready'
write(e/'scenes.json',scenes)
print(json.dumps({'completed_decision_id':d['id'],'video_sha256':video_hash,'local_review_ready':True}))
