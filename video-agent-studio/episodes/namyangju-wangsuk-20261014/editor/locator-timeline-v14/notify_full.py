from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
O=EP/'outputs/locator-timeline-v14';v=O/'namyangju_locator_timeline_full_v14.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();report=EP/'qa/locator-timeline-v14/final_review.json';q=json.loads(report.read_text(encoding='utf-8'));assert q['required_open_count']==0 and q['local_review_ready'];assert q['sha256']==sha
d=json.loads((O/'completed_decision.json').read_text(encoding='utf-8'));receipt=O/'telegram_receipt_full.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:sys.exit('already sent')
text=f'남양주 v14 전체 수정본이 준비됐습니다. 15분21.767초입니다.\n전체 계획판의 현재 위치 표시·가로 시간표·다산/별내 동시 가격 지도와 새 후반 후보 결론을 반영했습니다. 북부 B1·B2 공동 후보, 남부 B17, 왕숙2 A3와 A1의 선택 조건 및 공고 제한을 정리했습니다.\n영상 경로: {v}\n자막: {O/"namyangju_locator_timeline_full_v14.srt"}\n안내: {O/"README.md"}\n전체 디코드·지도 단발 화면/접합부·자막·브랜드 구간 독립 검수 통과. 실제 청취·연속 재생은 미확인입니다. 기존 앞부분 PCM 내용은 유지하고 새 후반 결합을 위해 전체 AAC를 재인코딩했습니다. 파일은 전송하지 않았습니다.\n/approve {d["id"]}\n/revise {d["id"]} 수정내용'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'qa_report':str(report),'decision_id':d['id']},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False,'decision_id':d['id']}))
