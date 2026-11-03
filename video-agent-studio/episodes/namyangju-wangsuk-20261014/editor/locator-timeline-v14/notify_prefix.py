from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
O=EP/'outputs/locator-timeline-v14';v=O/'namyangju_v14_review_00-12m01s.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();report=EP/'qa/locator-timeline-v14/prefix_review.json';q=json.loads(report.read_text(encoding='utf-8'));assert q['required_open_count']==0 and q['local_review_ready']
receipt=O/'telegram_receipt_prefix.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:sys.exit('already sent')
text=f'남양주 수정 검토본을 처음부터 12분01.2초까지 연결했습니다.\n상세 지도의 왼쪽 전체 위치판·범위 표시, 일자리·철도·학교·입주 가로 시간표, 다산·별내 동시 가격 지도를 반영했습니다.\n영상 경로: {v}\n전체 디코드·21636프레임 지도/자막바·접합부 독립 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.\n승인된 새 후반 대본의 음성도 준비돼, 후보 결론과 기존 아웃트로를 붙인 전체본을 계속 제작 중입니다.'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'qa_report':str(report)},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False}))
