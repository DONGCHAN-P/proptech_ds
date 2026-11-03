from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
O=EP/'outputs/minimal-v12';v=O/'minimal_v12_front.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();decision=json.loads((O/'completed_decision.json').read_text(encoding='utf-8'));ident=decision['id'];receipt=O/'telegram_receipt_front.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:print('already notified');sys.exit(0)
text=('남양주 v10 기준 최소 수정 v12 · 00:00~08:45 검토본 완성\n'
'v10 구성·강조 효과는 유지하고 줌 인/아웃과 잘못된 예정역 위치 표시만 수정했습니다. 기존 음성·166개 자막은 보존했습니다.\n'
f'영상 경로: {v}\n안내: {O/"README.md"}\n'
'실제 파일 기술 검사·전체 디코드·독립 시각 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.\n'
f'/approve {ident}\n/revise {ident} 수정내용')
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'decision_id':ident},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False}))
