import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
e=Path(__file__).resolve().parent;root=e.parents[2];sys.path.insert(0,str(root))
from notify import telegram
o=e/'outputs/script-review-v1';ds=json.loads((o/'review_decisions.json').read_text(encoding='utf-8'));s=ds['script'];b=ds['budget']
for d in [s,b]:
 for path,digest in d['artifacts'].items():assert hashlib.sha256((e/path).read_bytes()).hexdigest()==digest
receipt=o/'telegram_delivery.json'
r=json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else {}
def save():receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if not r.get('file_sent'):
 assert telegram.send_file(o/'script_v1.md',caption='창릉 대본 v1 · 왕숙 지도/달력 포맷 · 사용자 검토용',quiet=True)
 r['file_sent']=True;r['file_sha256']=hashlib.sha256((o/'script_v1.md').read_bytes()).hexdigest();save()
if not r.get('message_sent'):
 message=f'''창릉 영상: 대본·숫자 검수까지 완료했습니다.

왕숙처럼 전체계획도→일자리·교통·분양가·생활·공급→삼송/원흥/지축 대안→S1/S4/S5 권역별 후보 순서입니다. 왕숙 편 연결, 다음 교산 예고, 기존 브랜드/BGM, 구독·감사와 말끝3초도 포함했습니다.
공식 RTMS 2026Q3 자료를 새로 조회해 비교 단지 중위값·n을 직접 계산했고, 공고 핵심 수치와 낭독 원문을 독립 검수했습니다. 예상14~16분이며 실제 음성·MP4는 아직 생성하지 않았습니다.

① 대본 v1 확정: /approve {s['id']}
수정: /revise {s['id']} 수정내용

② Jun 음성 예산 승인: /approve {b['id']}
최초6874자+부분수정여유1375자=포함크레딧 최대8249, 추가결제0원. 포함잔액31075 확인. 자동재시도/충전/초과결제/새유료이미지·음악 제외. 기존브랜드·음악과로컬편집을 재사용합니다.

현재는 위 대본/예산 검토 대기입니다. 두 승인이 들어오면 해당 버전만 음성 생성과 타임록 단계로 이어갑니다. 완료 검토와 공개 업로드는 각각 별도 결정입니다.
파일: {o / 'script_v1.md'}'''
 assert len(message)<=4096 and telegram.send(message,quiet=True)
 r.update(message_sent=True,sent_at=datetime.now(timezone.utc).isoformat(),script_decision=s['id'],budget_decision=b['id']);save()
print('Exact script file and scoped script/budget decisions delivered to Telegram')
