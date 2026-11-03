import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write,now
from notify.telegram import send,send_file
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015';out=ep/'outputs/production-v4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt_path=out/'delivery_receipt.json'
assert not receipt_path.exists(),'Delivery receipt already exists; inspect instead of resending'
qa_path=ep/'qa/production-v4/final_review.json';qa=read(qa_path)
assert qa['required_open_count']==0 and qa['critical_open_count']==0 and qa['local_review_ready'] is True
video=out/'changneung_full_v4r2.mp4';srt=out/'changneung_full_v4.srt';project=out/'project_v4.json'
for p in [video,srt,project]:assert p.is_file() and sha(p) in json.dumps(qa),str(p)
assert sha(ep/'writer/script-v3/script_v3.md')=='9b5d93523e0d50154d976beee0cccc57a4cddf38245838f77741faa6444a5311'
pref=read(root/'config/video_telegram_bridge.json')['notification_preference'];assert 'deliverables' in pref['scope']
manifest={'revision':'production-v4','created_at':now().isoformat(),'duration_frames':24140,'fps':30,'duration_s':24140/30,'spoken_script_revision':'script-v3','audio_revision':'audio-v3','new_paid_generation':False,'publication_authorized':False,'actual_listening':False,'continuous_playback':False,'artifacts':[{'file':str(p.relative_to(ep)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [video,srt,project,qa_path]],'changes':['낭독 표기와 표시 자막 분리 및 숫자·영문 표기 전수 교정','LH 실제 공간 도형 기반 창릉지구 경계와 창릉역 예정 권역 구분','S1·S4·S5 실제 계획 상세도와 동일 전체지도 locator'],'source':'research/map-location-v4/source_manifest.json'}
write(out/'delivery_manifest.json',manifest)
artifacts={str(p.relative_to(ep)):sha(p) for p in [video,srt,project,qa_path,out/'delivery_manifest.json']}
d=create(ep.name,'completed','창릉 본편 v4 수정 완료 검토. 숫자·영문 자막, 지구경계와 창릉역 예정권역, S1·S4·S5 실제 계획 상세도와 위치 locator 반영. 기존 음성·길이 보존, 새 유료 호출 없음. 이 결정은 해당 파일의 제작 완료 검토이며 공개 업로드 승인은 별도.')
d.update(artifact_hashes=artifacts,scope='local_review_only_not_publication',render_revision='production-v4-r2');write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
dec=read(ep/'decisions.json');dec['decisions'].append(d);write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='completed_review_pending',render_revision='production-v4-r2',video_path=str(video.relative_to(ep)),rendered_video_sha256=sha(video),delivery_revision='production-v4-r2',qa_path='qa/production-v4/final_review.json',pending_gate='completed',pending_decision_ids={'completed':d['id']},completed_gate_decision_id=d['id'],active_tasks=[],publication_authorized=False)
write(ep/'state.json',s)
pre=read(ep/'preflight.json');pre['approvals']['completed'].update(decision_id=d['id'],artifact_hashes=artifacts,status='pending');pre['release']['longform']=str(video.relative_to(ep));pre['qa'].update(required_open_issues=0,continuous_playback_performed=False,actual_listening_performed=False,evidence_paths=['qa/production-v4/final_review.json']);write(ep/'preflight.json',pre)
write(out/'delivery_started.json',{'decision_id':d['id'],'at':now().isoformat(),'video_sha256':sha(video)})
sent=send_file(video,f"창릉 수정 검토본 v4 · 13분 25초\n숫자·영문 자막 / 창릉지구와 예정역 구분 / S1·S4·S5 실제 계획 상세지도+위치 안내 반영. 기존 음성 유지·추가 비용 0원.\n프레임·타이밍 검수, 실제 청취·연속 재생 미실시.\n완료 확인 /approve {d['id']}\n수정 /revise {d['id']} 수정내용\n공개 업로드 승인은 별도입니다.")
notice=send(f"창릉 v4 수정본: {video}\n자막 표기 변경 목록: {out/'subtitle_change_list_v4.md'}\nLH 실제 공간자료로 단지·학교·공원·도로를 표시하고 전체지도에 상세 위치를 안내했습니다. 역은 예정 권역이며 확정 출입구 표시가 아닙니다.\n완료 확인 /approve {d['id']} · 수정 /revise {d['id']} 수정내용")
receipt={'completed_decision_id':d['id'],'video':str(video),'video_sha256':sha(video),'telegram_file_sent':sent,'telegram_notice_sent':notice,'publication_performed':False};write(receipt_path,receipt);print(json.dumps(receipt,ensure_ascii=False))
