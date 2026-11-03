from pathlib import Path
import json,hashlib,sys,datetime
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify import video_decisions as gates
O=EP/'outputs/production-v6-preview'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tech=read(O/'technical_r4.json');qa=read(EP/'qa/production-v6-preview/final_review.json')
mp4=O/tech['file'];script=EP/'outputs/script-review-v6/script_v6.md'
assert sha(script)=='0c94b0c1547b6abd2968c6de622fbf9793cd7cd0e4ab7415664e4701fe162fc1'
assert mp4.exists() and mp4.stat().st_size==tech['bytes'] and sha(mp4)==tech['sha256']
assert qa.get('required_unresolved')==[],qa.get('required_unresolved')
assert qa.get('status') not in ['pending_final_media','failed',None]
srt=O/'changneung_v6_preview_r4.srt';assert srt.exists()
paths=[mp4,srt,O/'technical_r4.json',EP/'qa/production-v6-preview/final_review.json',O/'rendered_project_r4.json']
assert all(p.exists() for p in paths)
artifacts={p.relative_to(EP).as_posix():sha(p) for p in paths}
decision_path=O/'review_decision.json'
d=read(decision_path) if decision_path.exists() else gates.create(EP.name,'completed','창릉 대본 v6 무료 TTS 검토 영상 r4. 기존 지도·브랜드 및 실제 Claude 모션 코드 적용. 검토용이며 Jun 유료 음성·업로드 승인은 포함하지 않음.')
d.update(scope='free_TTS_preview_r4_only',script_revision='script-v6',audio_revision='audio-v6-preview-heami-rateminus1',artifact_hashes=artifacts,paid_generation_authorized=False,upload_authorized=False)
gates.write(decision_path,d);gates.write(ROOT/'output/video_decisions/decisions'/f"{d['id']}.json",d)
state=read(EP/'state.json')
state.update(stage='preview_completed_review_pending',script_revision='script-v6',source_script_sha256=sha(script),audio_revision='audio-v6-preview-heami-rateminus1',timing_revision='preview-timing-lock-v6-r4',narration_characters=len((EP/'outputs/script-review-v6/narration_v6.txt').read_text(encoding='utf8')),render_started=True,active_tasks=[],pending_gate='completed',pending_decision_ids={'completed':d['id']},voice_generation_hold=True,paid_generation_authorized=False,publication_authorized=False)
state['current_preview']={'path':mp4.relative_to(EP).as_posix(),'sha256':tech['sha256'],'duration_seconds':28018/30,'script_revision':'script-v6','audio_revision':'free local Heami review voice','not_final_Jun':True,'qa':'qa/production-v6-preview/final_review.json'}
state['production_v6'].update(status='preview_delivered_for_review',motion_code='writer/claude-motion-v6/MotionKit.tsx',actual_claude_code_received=True,new_paid_image_video_calls=0,new_paid_voice_calls=0,completed_decision_id=d['id'])
gates.write(EP/'state.json',state)
pre=read(EP/'preflight.json');pre['status']='preview_completed_review_pending';pre['approvals']['completed']={'decision_id':d['id'],'status':d['status'],'artifact_hashes':artifacts};pre['v6_production'].update(representative_qa='completed; see final review for sampled coverage',final_preview=mp4.relative_to(EP).as_posix(),audio_revision='free local Heami, final Jun not generated')
gates.write(EP/'preflight.json',pre)
log=read(EP/'decisions.json')
if not any(x.get('id')==d['id'] for x in log['decisions']):log['decisions'].append(d)
gates.write(EP/'decisions.json',log)
sc=read(EP/'scenes.json');sc.update(duration_frames=28018,status='preview_completed_review_pending',revision='script-v6-preview-timing-lock-r4',speech_signal_end_frame=27628,outro_start_frame=27718,signal_basis='PCM abs>0.006, not actual listening');gates.write(EP/'scenes.json',sc)
gates.write(O/'delivery_manifest.json',{'revision':'production-v6-preview-r4','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file':mp4.name,'sha256':tech['sha256'],'bytes':tech['bytes'],'duration_seconds':28018/30,'artifact_hashes':artifacts,'review_decision_id':d['id'],'voice':'Free Microsoft Heami review; final Jun replacement pending','actual_listening':False,'continuous_playback':False,'five_scoped_gates_preserved':True,'new_paid_voice_image_video_calls':0,'telegram_notice':'visible final reply automatically mirrored; no duplicate direct text send','current_published_video_unchanged':True})
(O/'README.md').write_text(f'# 창릉 v6 검토 영상\n\n현재 기준 파일: `{mp4.name}`\n\n15분 33.933초 · 1920×1080 · 30fps · 무료 로컬 Heami TTS 검토용입니다. 최종 Jun 음성은 생성하지 않았습니다.\n\n기존 지도·브랜드·권리 확인 소스를 재사용하고 실제 Claude 모션 코드 6종을 채널 스타일에 맞춰 적용했습니다. r2/r3는 검수 수정 전 보존본입니다. 자막은 `{srt.name}`을 사용합니다.\n\n실제 MP4 표본 프레임·경계 및 전 스트림 디코드를 확인했습니다. 청취·연속 재생은 수행하지 않았습니다. 세부 범위는 `../../qa/production-v6-preview/final_review.json`에 기록합니다.\n\n검토 결정ID: `{d["id"]}`. 이 파일의 완료 검토는 유료 생성·게시 승인을 포함하지 않습니다.\n',encoding='utf8')
print(json.dumps({'file':str(mp4),'sha256':tech['sha256'],'duration_s':28018/30,'decision_id':d['id'],'required_unresolved':qa['required_unresolved']},ensure_ascii=False))
