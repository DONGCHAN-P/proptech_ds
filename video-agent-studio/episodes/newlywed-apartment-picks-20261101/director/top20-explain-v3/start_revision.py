from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2];sys.path.insert(0,str(R))
from notify.video_decisions import write
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
event=R/'output/telegram_conversation/inbox/718066312.json';feedback=read(event)
assert feedback['source']=='authenticated_telegram_user'
state=read(E/'state.json')
if not(D/'previous_state.json').exists():write(D/'previous_state.json',state)
write(D/'requirements.json',{'revision':'top20-explain-v3','source_event':str(event.relative_to(R)).replace('\\','/'),'request':feedback['text'],
 'requirements':[{'id':f'TG312-{i}','text':text}for i,text in enumerate(['지역별 부동산 특징과 랜드마크 설명 보강','합니다/입니다 문체','통계청 출처는 도입부에서 설명하고 반복 표기 제거','2024년 자료의 한계 설명','지역 지도·최근 가격·중위값·대표 단지'],1)],
 'voice':'free InJoon; latest free-TTS preference retained','cash_cap_krw':0,'old_private_video_id':state['youtube_video_id'],
 'old_video_sha256':state['video_sha256'],'new_upload_approval':'not inherited from previous version','source_event_sha256_before_application':sha(event)})
pre=read(R/'video-agent-studio/templates/episode_preflight.json');pre.update(episode_id=E.name,revision='top20-explain-v3',status='research_in_progress',
 baseline={'video':state['video'],'sha256':state['video_sha256'],'script':state['script'],'audio_revision':state['audio_revision']},
 input_contract={'narration_mode':'free TTS','original_user_feedback':str(event.relative_to(R)).replace('\\','/'),'proposed_script_changes':'all narration to 합니다/입니다; add verified regional/property/current-price context','timing_basis':'actual new audio required','episode_specific_choices':['census source intro only','2024 limitation explicit','current price period separately dated']})
write(D/'episode_preflight.json',pre)
state.update(active_revision='top20-explain-v3',phase='regional_features_and_current_price_research',active_preflight=str(D/'episode_preflight.json'),
 current_revision_plan=str(D/'제작계획.md'),updated_at=datetime.now(timezone(timedelta(hours=9))).isoformat())
write(E/'state.json',state)
decisions=read(E/'decisions.json')
if not any(x.get('id')=='D023'for x in decisions['decisions']):decisions['decisions'].append({'id':'D023','revision':'top20-explain-v3','source':'Telegram718066312','choice':'apply five user revision requirements; preserve current private release; verify current trade evidence before using price claims','status':'research_and_script_work_authorized','owner':'director'})
write(E/'decisions.json',decisions)
feedback.update(application_status='applied',applied_at=datetime.now(timezone.utc).isoformat(),application_task='top20-explain-v3',application_phase='in_progress',
 application_note='다섯 수정 사항을 새 제작 기준으로 적용. 자료·대본·화면 수정 진행 중이며 완료·업로드 승인으로 표시하지 않음.')
write(event,feedback)
print(json.dumps({'revision':'top20-explain-v3','feedback_applied':True,'phase':'research','previous_release_preserved':True,'paid_budget':0}))
