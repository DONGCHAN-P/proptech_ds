import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write,now
from notify.telegram import send_file
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015';out=ep/'outputs/production-v5'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (out/'delivery_started.json').exists(),'Do not duplicate delivery; inspect durable receipt first'
qpath=ep/'qa/production-v5/final_review.json';q=read(qpath)
assert q['required_open_count']==0 and q['critical_open_count']==0 and q['local_review_ready'] is True
v=out/'changneung_full_v5r2.mp4';srt=out/'changneung_full_v5.srt';project=out/'project_v5.json'
for p in [v,srt,project]:assert p.exists() and sha(p) in json.dumps(q),str(p)
assert sha(ep/'writer/script-v3/script_v3.md')=='9b5d93523e0d50154d976beee0cccc57a4cddf38245838f77741faa6444a5311'
assert sha(srt)==sha(ep/'outputs/production-v4/changneung_full_v4.srt')
manifest={'revision':'production-v5','created_at':now().isoformat(),'duration_frames':24140,'duration_s':24140/30,'fps':30,'audio_revision':'audio-v3','script_revision':'script-v3','additional_voice_generation':False,'external_paid_api_calls':0,'built_in_image_generation_count':1,'actual_listening':False,'continuous_playback':False,'upload_authorized_for_this_revision':False,
 'changes':['일자리 장 주제 전환 및 공통 지도 덮어쓰기 제거','실제 좌표의 외부5업무지·창릉지구 위치와 발화에 맞는 강조','183큐 의미대상 연결 및 지도·가격·일정·통근 단계의 자료 종류 교차','집-전철-직장 AI 개념 이미지와 한정 모션그래픽'],
 'artifacts':[{'file':str(p.relative_to(ep)),'sha256':sha(p),'bytes':p.stat().st_size} for p in [v,srt,project,qpath]],'previous_private_video_url':'https://youtu.be/0yvjR4NMw_Q','image_prompt':'visual/semantic-v5/assets/M002_commute_journey_concept_AI_v1.prompt.txt'}
write(out/'delivery_manifest.json',manifest)
artifacts={str(p.relative_to(ep)):sha(p) for p in [v,srt,project,qpath,out/'delivery_manifest.json']}
d=create(ep.name,'completed','창릉 v5 수정 완료 검토: 발화에 맞는 실제 지도 강조, 1:38 일자리 전환, 외부5업무지 위치, AI 통근 개념 이미지·도표·시간차 모션. 기존 음성·자막·길이 보존. 새 파일의 공개/업로드 승인은 별도.')
d.update(render_revision='production-v5',artifact_hashes=artifacts,scope='completed_review_only');write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
dec=read(ep/'decisions.json');dec['decisions'].append(d);write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='completed_review_pending',render_revision='production-v5',video_path=str(v.relative_to(ep)),rendered_video_sha256=sha(v),delivery_revision='production-v5',qa_path='qa/production-v5/final_review.json',pending_gate='completed',pending_decision_ids={'completed':d['id']},completed_gate_decision_id=d['id'],active_tasks=[],upload_authorized=False,publication_authorized=False,previous_private_release={'video_id':'0yvjR4NMw_Q','render_revision':'production-v4-r2','privacy':'private'});write(ep/'state.json',s)
pre=read(ep/'preflight.json');pre['approvals']['completed'].update(status='pending',decision_id=d['id'],artifact_hashes=artifacts);pre['release']['longform']=str(v.relative_to(ep));pre['qa'].update(required_open_issues=0,actual_listening_performed=False,continuous_playback_performed=False,evidence_paths=['qa/production-v5/final_review.json']);write(ep/'preflight.json',pre)
write(out/'delivery_started.json',{'at':now().isoformat(),'decision_id':d['id'],'video_sha256':sha(v)})
sent=send_file(v,f"창릉 v5 수정 검토본 · 13분 25초\n1:38 일자리 전환 / 외부5업무지 위치 / 발화대상 지도 강조 / AI 통근 개념 이미지·자료종류 교차·모션 반영. 기존 음성·자막 유지.\n실제 청취·전체 연속재생 미실시.\n완료 확인 /approve {d['id']}\n수정 /revise {d['id']} 수정내용\n기존 비공개 v4 영상은 유지됩니다.")
r={'completed_decision_id':d['id'],'video':str(v),'sha256':sha(v),'telegram_file_sent':sent,'youtube_upload_performed':False};write(out/'delivery_receipt.json',r);print(json.dumps(r,ensure_ascii=False))
