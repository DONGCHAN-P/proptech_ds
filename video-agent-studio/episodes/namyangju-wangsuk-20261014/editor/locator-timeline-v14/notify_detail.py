from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
O=EP/'outputs/locator-timeline-v14';v=O/'landuse_locator_timeline_v14.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest()
report=EP/'qa/locator-timeline-v14/detail_review.json';q=json.loads(report.read_text(encoding='utf-8'));assert q.get('required_open_count')==0 and q.get('local_review_ready') is True
receipt=O/'telegram_receipt_detail.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:sys.exit('already sent')
text=f'남양주 상세지도·시간표 부분 검토본이 준비됐습니다.\n원본 04:33~08:45.267 구간입니다.\n왼쪽에는 현재 권역의 전체 토지계획판 하나와 상세 범위 테두리, 오른쪽에는 기존 상세 지도를 배치했습니다. 입주예정·학교목표·개장미정을 가로 시간표로 구분했습니다. 기존 음성·자막을 유지했습니다.\n영상 경로: {v}\n전체 디코드 및 독립 시각 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.\n일자리·교통·외부 비교 시간표와 새 후반 대본을 반영한 전체본은 계속 제작 중입니다.'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'qa_report':str(report)},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False}))
