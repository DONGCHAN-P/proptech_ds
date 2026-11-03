from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
O=EP/'outputs/locator-timeline-v14';v=O/'region_prices_v14_M007.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest()
report=EP/'qa/locator-timeline-v14/price_review.json'
q=json.loads(report.read_text(encoding='utf-8'));assert q.get('required_open_count')==0 and q.get('local_review_ready') is True
receipt=O/'telegram_receipt_price.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:sys.exit('already sent')
text=f'남양주 가격 지도 부분 검토본이 준비됐습니다.\n원본 08:45.267~10:21.600 구간입니다.\n다산·별내 두 생활권을 동시에 표시하고, 실제 3단지 위치와 같은 면적·층·기간 조건의 실거래 중위값을 연결했습니다. 기존 음성과 자막은 유지했습니다.\n영상 경로: {v}\n전체 디코드 및 독립 시각 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.\n왼쪽 전체 계획판과 시간표를 적용한 앞 구간은 별도로 제작 중입니다.'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'qa_report':str(report)},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False}))
