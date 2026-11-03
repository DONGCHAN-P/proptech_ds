from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
stage=sys.argv[1];out=EP/'outputs/stable-maps-v11';v=out/f'stable-maps_v11_{stage}.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();receipt=out/f'telegram_receipt_{stage}.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:print('already notified');sys.exit(0)
text=('남양주 정적 지도 v11 · '+('철도 부분 검토본' if stage=='rail' else '앞부분 통합 검토본')+' 준비됐습니다.\n'+('원본 02:45~04:33 / 108초 동안 같은 철도 지도 고정\n' if stage=='rail' else '원본 00:00~08:45 / 설명 지도 모션 제거\n')+'운영 노선과 주변 역을 처음부터 표시하고 예정역은 실제 운영역 사이의 계획 구간으로 구분했습니다.\n영상 경로: '+str(v)+'\n안내: '+str(out/'README.md')+'\n실제 파일 기술 검사·전체 디코드·독립 시각 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.')
if stage=='front':text+='\n이번 00:00~08:45 부분 검토 결정입니다.\n/approve 1ad71ef3e8a0\n/revise 1ad71ef3e8a0 수정내용'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'stage':stage},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False,'stage':stage}))
