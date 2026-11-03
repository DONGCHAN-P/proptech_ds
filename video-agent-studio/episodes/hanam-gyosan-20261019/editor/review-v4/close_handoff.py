from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v4'
def read(f):return json.loads(f.read_text(encoding='utf8'))
def save(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
v=O/'gyosan_review_v4r1_free_tts.mp4';q=EP/'qa/review-v4-independent/report.json';qa=read(q);t=read(O/'technical.json');m=read(O/'motion_verification.json')
assert sha(v)==qa['sha256']==t['sha256'];assert qa['required_unresolved']==0;assert len(m['sequences'])==14
m.update(video=str(v),sha256=sha(v),scope='14 short consecutive decoded MP4 sequences at approximate seek times; pixel variation measured, not uninterrupted human playback or a smoothness assessment',exact_absolute_frame_index_guaranteed=False)
save(O/'motion_verification.json',m)
save(O/'boundary_verification.json',dict(status='not_claimed',passed=False,reason='Automated source-to-frame comparison stopped because seek/frame-index correspondence was ambiguous. This is an extraction limitation, not a diagnosed video fault.',independent_qa=str(q),independent_scope=qa['coverage']['boundaries']))
manifest=read(O/'input_manifest.json')
for f in [E/'finish_receipts.py',E/'close_handoff.py']:manifest[str(f.relative_to(EP.parents[2]))]=sha(f)
save(O/'input_manifest.json',manifest)
save(E/'handoff.json',dict(status='complete_local_free_review',video=str(v),sha256=sha(v),bytes=v.stat().st_size,duration_s=qa['duration_s'],frames=33731,resolution='1920x1080',fps=30,source_script_revision='v4 approved unchanged',original_text_preserved=True,voice='263 new local Microsoft Heami rate2 phrase WAVs',caption_count=263,timing_basis='Actual PCM phrase lengths; semantic phrase captions, not word ASR',cta_hold_frames=90,paid_api_calls=0,uploads=0,technical=str(O/'technical_v4r1.json'),source_manifest=str(O/'input_manifest.json'),representatives=str(O/'representative_timestamps_v4r1.json'),motion_verification=str(O/'motion_verification.json'),motion_sequences=14,boundary_verification=str(O/'boundary_verification.json'),storyboard_coverage=str(E/'storyboard_coverage.json'),placement_guide=str(E/'placement_guide.md'),independent_qa=str(q),independent_qa_sha256=sha(q),required_unresolved=0,changed_visual_frames_r1=[32057,32192],audio_packets_identical_to_initial_v4=True,actual_listening=False,continuous_playback=False,limitations=['실제 청취·발음·자연스러움 및 전편 연속 재생은 미검수','자동 전경계 프레임 대조는 추출 기준 불확실로 통과를 주장하지 않음','자족5/7 개별 정확 필지 대신 실제 자족용지 전체와 계획 그래픽 사용','14개 짧은 연속 프레임 변화 측정은 전편 모션의 시청 검수가 아님'],next_owner='director: shelf/state update and user delivery; no upload authorization'))
print(json.dumps(dict(status='complete',sha256=sha(v),motion_sequences=14,required_unresolved=0)))
