import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
from notify.telegram import send,send_file
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015';out=ep/'outputs/production-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
qa_path=ep/'qa/production-v3/final_review.json';qa=read(qa_path)
assert qa['required_open_count']==0 and qa['critical_open_count']==0 and qa['local_review_ready'] is True
video=out/'changneung_full_v3r2.mp4';srt=out/'changneung_full_v3.srt';project=out/'project_v3.json'
assert video.is_file() and sha(video) in json.dumps(qa)
assert sha(srt) in json.dumps(qa) and sha(project) in json.dumps(qa)
assert sha(ep/'writer/script-v3/script_v3.md')=='9b5d93523e0d50154d976beee0cccc57a4cddf38245838f77741faa6444a5311'
lock=read(ep/'editor/production-v3/timing_lock_v3.json');assert lock['duration_frames']==24140
ledger=read(ep/'narration/audio-v3/generation_ledger_v3.json');assert ledger['actual_credit_total']==2548
pref=read(root/'config/video_telegram_bridge.json')['notification_preference']
assert pref['channel']=='telegram' and 'deliverables' in pref['scope']
manifest={'revision':'production-v3-r2-local-review','video':str(video.relative_to(ep)),'duration_frames':24140,'fps':30,'duration_s':lock['duration_s'],'actual_voice_credits':2548,'additional_cash_usd':0,'publication_authorized':False,'actual_listening':False,'continuous_playback':False,'artifacts':[{'file':str(p.relative_to(ep)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [video,srt,project,qa_path]],'guide':'../../guides/채널_톤앤매너와_복기루프.md','superseded_review_video':'outputs/production-v3/changneung_full_v3.mp4; failed QA009, not delivery'}
write(out/'delivery_manifest.json',manifest)
(out/'README.md').write_text('# 창릉 본편 검토본 v3r2\n\n최종 검토 영상은 **changneung_full_v3r2.mp4**다. 기존 changneung_full_v3.mp4는 인트로 직후 1프레임 재등장 수정 전이므로 검토·게시 대상으로 사용하지 않는다.\n\n- 1920×1080 / 30fps / 24,140프레임 / 13분24.67초\n- 사용자 저장 낭독 v3 그대로, Jun 10장 / 실제 2,548 포함크레딧 / 추가결제0원\n- 자막: changneung_full_v3.srt / 편집 장면표: project_v3.json\n- 실제 전편 프레임 복기와 채널 토큰, 대표3종 검수 후 본편 확장\n- 최종 QA: ../../qa/production-v3/final_review.json\n- 프레임·타이밍·파일·음성 신호/원문 정렬 검수. 실제 청취·연속 재생은 미실시.\n- S4 정밀 블록 경계는 임의 생성하지 않고 공식 전체도와 검증된 방위관계, 기존 시설의 실제 지리를 구분해 설명했다.\n- 현재는 로컬 검토본이며 공개 업로드 승인·게시가 아니다.\n\n재현 소스와 자산은 ../../editor/production-v3/placement_guide.md 및 source_manifest_v3.json을 참조한다. 사진·지도 원출처/이용조건을 유지한다. 중복 용량을 줄이기 위해 별도 ZIP을 만들지 않았다.\n',encoding='utf-8')
artifacts={str(p.relative_to(ep)):sha(p) for p in [video,srt,project,qa_path,out/'delivery_manifest.json']}
d=create(ep.name,'completed','창릉 본편 v3r2 13분24.67초 제작 완료 검토. 왕숙·광교동탄 채널 톤 계승, 사용자 수정 낭독, 지도·달력·사진·가격 비교. QA필수0; 실제청취/연속재생 미실시. 제작완료 확인이며 공개 업로드 승인은 별도.')
d.update(artifact_hashes=artifacts,scope='local_review_only_not_publication',render_revision='production-v3-r2');write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
dec=read(ep/'decisions.json');dec['decisions'].append(d);write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='completed_review_pending',render_revision='production-v3-r2',video_path=str(video.relative_to(ep)),rendered_video_sha256=sha(video),delivery_revision='production-v3-r2',qa_path='qa/production-v3/final_review.json',pending_gate='completed',pending_decision_ids={'completed':d['id']},completed_gate_decision_id=d['id'],active_tasks=[],publication_authorized=False,actual_voice_credits_used=2548)
write(ep/'state.json',s)
pre=read(ep/'preflight.json');pre['approvals']['completed'].update(decision_id=d['id'],artifact_hashes=artifacts,status='pending');pre['release']['longform']=str(video.relative_to(ep));pre['qa'].update(required_open_issues=0,continuous_playback_performed=False,actual_listening_performed=False,evidence_paths=['qa/production-v3/final_review.json']);write(ep/'preflight.json',pre)
file_sent=send_file(video,f"창릉 본편 검토본 v3r2 · 13분24.67초\n사용자 수정 낭독·채널 톤 복기 적용. 필수 QA0건. 실제청취/연속재생 미검수.\n제작완료 확인: /approve {d['id']}\n수정: /revise {d['id']} 수정내용\n공개 업로드 승인은 별도입니다.")
notice_sent=send(f"창릉 검토본 제작 완료: {video}\n자막: {srt.name}\nJun 실제2548 포함크레딧,추가결제0. 전편과대표화면비교→차이수정→독립검수루프를가이드/공통설정에남겼습니다. 인트로뒤1프레임재등장도수정확인했습니다.\n제작완료 확인 /approve {d['id']} · 수정 /revise {d['id']} 의견\n이결정은완성본검토이며공개승인은아닙니다.")
receipt={'completed_decision_id':d['id'],'video':str(video),'video_sha256':sha(video),'telegram_file_sent':file_sent,'telegram_notice_sent':notice_sent,'publication_performed':False}
write(out/'delivery_receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
