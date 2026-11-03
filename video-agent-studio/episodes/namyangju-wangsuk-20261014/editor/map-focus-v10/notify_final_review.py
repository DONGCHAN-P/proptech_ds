from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from notify import telegram
o=EP/'outputs/map-focus-v10';d=json.loads((o/'completed_decision.json').read_text(encoding='utf-8'));q=json.loads((o/'qa_front_review.json').read_text(encoding='utf-8'))
p=o/'map-focus_v10_front.mp4';sha=hashlib.sha256(p.read_bytes()).hexdigest()
assert d['id']=='91a40cf0a547' and q['sha256']==sha and q['required_open_count']==0
assert any(str(k).replace('\\','/').endswith(p.name) and v==sha for k,v in d['artifacts'].items())
receipt=o/'telegram_final_review_receipt.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('message_sent'):
 print(json.dumps({'duplicate_skipped':True}));sys.exit(0)
text=('남양주 지도 집중 수정 v10 · 최종 검수 확정 안내\n'
 '학교 라벨 가림 수정본으로 갱신했습니다. 기존 1·2단계는 동일하며 3단계·통합본만 갱신됐습니다.\n'
 '검토 범위: 원본 00:00~08:45 통합본. 실제 수정은 02:45~08:45이며 이후 구간은 이번 파일에 포함하지 않았습니다.\n'
 '독립 검수 필수 미해결 0개. 15,750프레임 흰 자막바·접합·수정 장면을 확인했고, 원본 AAC의 구간 추출 24,610개 패킷 SHA가 일치했습니다. 실제 청취·연속 재생은 미확인입니다.\n'
 f'영상: {p}\n납품 ZIP: {o / "map-focus_v10_front_delivery.zip"}\n'
 '영상 파일은 전송하지 않았으며 업로드 승인 요청이 아닙니다.\n'
 f'검토 승인: /approve {d["id"]}\n수정 의견: /revise {d["id"]} 수정내용')
sent=telegram.send(text,quiet=True)
receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'decision_id':d['id'],'sha256':sha,'scope_s':[0,525]},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'message_sent':bool(sent),'file_sent':False,'decision_id':d['id']}))
