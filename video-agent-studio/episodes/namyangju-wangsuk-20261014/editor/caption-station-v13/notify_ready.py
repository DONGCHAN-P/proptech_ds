from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram
stage=sys.argv[1];O=EP/'outputs/caption-station-v13';v=O/f'caption-station_v13_{stage}.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest();receipt=O/f'telegram_receipt_{stage}.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('sha256')==sha:print('already sent');sys.exit(0)
text=('남양주 v13 · '+('앞부분 00:00~08:45 먼저 준비됐습니다.' if stage=='front' else '전체 조립본이 준비됐습니다.')+'\n'
'브랜드의 빈 흰 박스를 없애고, 일패역을 원도 업무·철도시설과 함께 표시했습니다. 잠깐 튀던 지도/강조 중간화면도 제거했습니다.\n'
f'영상 경로: {v}\n안내: {O/"README.md"}\n'
'실제 파일 전체 디코드·독립 시각 검수 통과. 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.\n')
if stage=='front':text+='전체본은 기존 후반을 그대로 연결하고 박스 없는 아웃트로를 반영해 별도로 안내하겠습니다.'
else:
 d=json.loads((O/'completed_decision.json').read_text(encoding='utf-8'));text+=f'앞부분 별도 경로: {O/"caption-station_v13_front.mp4"}\n08:45 접합부 8프레임 유지 후 후반 내용·시간은 기존 v8을 재사용하며 비디오는 재인코딩했습니다. 원본 전체 AAC는 동일합니다.\n/approve {d["id"]}\n/revise {d["id"]} 수정내용'
sent=telegram.send(text,quiet=True);receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'stage':stage,'sha256':sha},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'message_sent':bool(sent),'file_sent':False,'stage':stage}))
