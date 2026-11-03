from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
e=Path(__file__).resolve().parent;sys.path.insert(0,str(e.parents[2]))
from notify import telegram
o=e/'outputs/locator-timeline-v14';d=json.loads((o/'completed_decision.json').read_text(encoding='utf-8'))
assert d['gate']=='completed' and d['version']=='locator-timeline-v14'
for path,digest in d['artifacts'].items():assert hashlib.sha256((e/path).read_bytes()).hexdigest()==digest
receipt=o/'telegram_receipt_completed_gate.json'
assert not receipt.exists(),'Already delivered; inspect existing receipt'
message=f'''남양주 v14 전체 검토본과 자막·검수 묶음을 준비했습니다.

전체 영상15분21.77초:
{o / 'namyangju_locator_timeline_full_v14.mp4'}

전체 자막:
{o / 'namyangju_locator_timeline_full_v14.srt'}

대본·가이드·근거·검수 포함 ZIP:
{o / 'namyangju_locator_timeline_v14_delivery.zip'}

반영: 좌측 전체계획도 위치 안내, 가로 시간축, 다산/별내83~85㎡급 가격 지도, 일반형 권역별 대장 후보 새 후반. 확대·축소/짧은 전체지도 삽입은 없습니다. 신혼희망타운은 대장 후보에서 제외했습니다.
후반 Jun 음성616크레딧 사용/추가결제0원. 앞9장 낭독·시간은 유지했습니다. 전체 컷/자막·정렬·기술검수를 했으며 실제 청취와 연속재생은 미검증입니다.

이 전체본 제작완료 검토 결정ID: {d['id']}
수정 없음: /approve {d['id']}
수정 요청: /revise {d['id']} 시간대와 수정내용

이 회신은 이 영상의 완료 검토에만 적용됩니다. 업로드·공개는 별도 pre_upload 승인 전까지 진행하지 않습니다.'''
assert telegram.send(message,quiet=True),'Telegram send failed'
receipt.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'message_sent':True,'file_sent':False,'message_sha256':hashlib.sha256(message.encode()).hexdigest(),'completed_decision_id':d['id']},ensure_ascii=False,indent=2),encoding='utf-8')
print('v14 completed review gate and exact artifact paths sent as Telegram text.')
