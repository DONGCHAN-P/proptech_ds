import hashlib,json,re,sys,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
from notify.telegram import send
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
user=ep/'outputs/script-review-v2/script_v2.md'
assert sha(user)=='7e77b50a09982e6eec35bcbeaa49b73bb814cab6d59c243a1dbd10c60d4dadd5','User source changed: re-read before authorization'
source=user.read_text(encoding='utf-8')
texts=re.findall(r'### 낭독\s*\n(.*?)\n### 화면 지시',source,re.S)
assert len(texts)==10
script=ep/'writer/script-v3/script_v3.md';mp=ep/'writer/script-v3/manifest.json';m=read(mp)
assert len(m['chapters'])==10
for approved,c in zip(texts,m['chapters']):
    p=ep/'writer/script-v3'/c['path'];actual=p.read_text(encoding='utf-8')
    assert actual.strip()==approved.strip(),'User narration changed'
    assert sha(p)==c['sha256']
count=sum(len((ep/'writer/script-v3'/c['path']).read_text(encoding='utf-8')) for c in m['chapters'])
assert count<=6384 and count+math.ceil(count*.2)<=7661
out=ep/'outputs/script-review-v3';out.mkdir(exist_ok=True)
budget={'revision':'budget-v3-user-approved','script_revision':'script-v3','source_script_sha256':sha(script),
 'narration_manifest_sha256':sha(mp),'voice':'Jun - Clear Korean Lecturer','voice_id':'4p6UA7mnodF5q7JFFrnW','model':'eleven_v4',
 'chapter_count':10,'input_characters':count,'correction_character_cap':math.ceil(count*.2),
 'total_submitted_character_cap':7661,'actual_credit_hard_cap':7661,'additional_cash_usd_cap':0,
 'automatic_retry':False,'overage_or_topup_authorized':False,'paid_image_or_music_generation_authorized':False,
 'generation_authorized':True,'approval_source':'direct user: 음성 승인이고 영상 제작까지 작업진행해줘; saved script confirmation',
 'approved_maximum_from_previous_proposal':7661,'new_user_narration_source':str(user.relative_to(ep)),'new_user_narration_source_sha256':sha(user)}
write(out/'budget_proposal_v3.json',budget)
paths=[script,mp,user,*[ep/'writer/script-v3'/c['path'] for c in m['chapters']]]
artifacts={str(p.relative_to(ep)):sha(p) for p in paths}
ds=create(ep.name,'script','사용자가 저장한 수정 낭독을 그대로 확정, 화면 지시만 채널 톤·전편/레퍼런스 복기 기준 추가. script-v3.')
ds.update(status='approved',artifact_hashes=artifacts,approval_source='direct_user_message_and_saved_file_confirmation_2026-10-16',approval_text='대본 바꿀거 조금씩 바꿔뒀고 … 음성 승인이고 영상 제작까지 작업진행해줘 / script_v2.md 저장해뒀어 아까 저장없이 말했다')
db=create(ep.name,'budget','수정 저장 낭독 Jun 포함크레딧 최대7661,추가결제0원,자동재시도/초과결제/충전/새유료이미지음악 제외. 기존 제안 상한 이내 명시 승인.')
db.update(status='approved',artifact_hashes={**artifacts,str((out/'budget_proposal_v3.json').relative_to(ep)):sha(out/'budget_proposal_v3.json')},budget=budget,approval_source='direct_user_message_2026-10-16',approval_text='음성 승인이고 영상 제작까지 작업진행해줘')
for d in [ds,db]:write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d)
dec=read(ep/'decisions.json');dec['decisions'].extend([ds,db]);write(ep/'decisions.json',dec)
s=read(ep/'state.json');s.update(stage='voice_generation_and_visual_production_v3',script_revision='script-v3',source_script_sha256=sha(script),narration_characters=count,budget_credit_cap=7661,full_script_authorized=True,paid_generation_authorized=True,voice_generation_hold=False,pending_gate=None,pending_decision_ids={},script_decision_id=ds['id'],budget_decision_id=db['id'],active_tasks=['narration_audio_v3','channel_style_audit','editor_production_v3'],publication_authorized=False)
write(ep/'state.json',s)
pre=read(ep/'preflight.json')
for gate,d in [('script',ds),('budget',db)]:pre['approvals'][gate].update(decision_id=d['id'],artifact_hashes=d['artifact_hashes'],status='approved')
pre['approvals']['budget'].update(credits_cap=7661,cash_cap=0,automatic_retry_allowed=False)
write(ep/'preflight.json',pre)
proposal=read(ep/'writer/script-v3/scene_proposals.json')
scenes=proposal if isinstance(proposal,list) else proposal['scenes']
write(ep/'scenes.json',{'episode_id':ep.name,'revision':'script-v3-user-approved','status':'approved_script_awaiting_actual_audio','timing_status':'estimated_not_locked','scenes':scenes})
receipt={'script_decision_id':ds['id'],'budget_decision_id':db['id'],'script_sha256':sha(script),'manifest_sha256':sha(mp),'narration_characters':count,'credit_cap':7661,'user_narration_exact':True,'paid_calls_at_authorization':0}
write(out/'approval_receipt.json',receipt)
sent=send(f"저장하신 대본 변경 확인·승인 반영: 낭독 {count}자, 원문 그대로 보존했습니다. 음성은 포함크레딧 최대7661·추가결제0원 안에서 제작합니다. 왕숙 최종본과 광교·동탄 실제 프레임 비교→대표 장면 수정→검수→본편 확장 루프를 적용합니다. 수정 전 visual-review-v2는 최종 스타일로 채택하지 않습니다. 공개 업로드는 별도 최종 게이트를 유지합니다.")
receipt['telegram_notice_sent']=sent;write(out/'approval_receipt.json',receipt);print(json.dumps(receipt))
