from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
e=Path(__file__).resolve().parent;sys.path.insert(0,str(e.parents[2]))
from notify import telegram
o=e/'outputs/readability-cta-v15';d=json.loads((o/'completed_decision.json').read_text(encoding='utf-8'))
assert d['gate']=='completed' and d['version']=='readability-cta-v15'
for path,digest in d['artifacts'].items():assert hashlib.sha256((e/path).read_bytes()).hexdigest()==digest
receipt=o/'telegram_receipt_completed_gate.json';assert not receipt.exists(),'Already delivered'
message=f'''남양주 v15 수정 검토본을 준비했습니다(15분31.97초).

전체 영상:
{o / 'namyangju_readability_cta_full_v15.mp4'}
전체 자막:
{o / 'namyangju_readability_cta_full_v15.srt'}
영상·자막·대본·검수 묶음:
{o / 'namyangju_readability_cta_v15_delivery.zip'}

반영: 시간축 상단 글자 잘림 공통 수정,1:28 일자리 왼쪽 전체지도,2:45왕숙역→3:08일패역 설명 지도 구분,13:21학교·공원 인출선 정리. 요청하신 감사 멘트와🔔구독·👍좋아요 모션을 넣고 마지막 발화 문자 종료부터3초를 유지한 뒤 기존10초아웃트로를 연결했습니다.
새 음성은59자/24포함크레딧·추가결제0원입니다. 기존음성/301자막에새4자막만더했습니다. 실제 프레임/전환/자막·정렬 검수 완료, 실제청취·연속재생은 미검증입니다.

완료 검토 결정ID: {d['id']}
수정 없음: /approve {d['id']}
수정 요청: /revise {d['id']} 시간대와 수정내용
이번 영상 완료 검토에만 적용되며 업로드·공개는 별도 pre_upload 승인 전까지 진행하지 않습니다.'''
assert telegram.send(message,quiet=True),'Telegram send failed'
receipt.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'message_sent':True,'file_sent':False,'message_sha256':hashlib.sha256(message.encode()).hexdigest(),'completed_decision_id':d['id']},ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s['telegram_v15_completion_notice_sent']=True;p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print('v15 exact artifact paths and scoped completed review sent as Telegram text.')
