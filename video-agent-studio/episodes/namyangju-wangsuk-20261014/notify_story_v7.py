from pathlib import Path
from datetime import datetime, timezone
import sys,json,hashlib
e=Path(__file__).resolve().parent;sys.path.insert(0,str(e.parents[2]))
from notify import telegram
f=e/'outputs/story-review-v7';d=json.loads((f/'approval_decisions.json').read_text(encoding='utf-8'))
assert hashlib.sha256((f/'script_v7.md').read_bytes()).hexdigest()==d['script_sha256']
receipt=f/'telegram_delivery.json'
assert not receipt.exists(), 'Already delivered; inspect receipt before resending'
message=f'''남양주 수정: 후반 대본 v7 검토 준비

12:02부터의 결론을 새로 썼습니다. 오늘의 입지·시설·가격·완성 시차를 정리한 뒤 왕숙1 북부 B1·B2 공동 후보, 남부 B17, 왕숙2 A3를 선정하고 이유를 설명합니다. A1은 예산·이른 입주·학교를 우선할 때의 경쟁 후보입니다.
신혼희망타운은 대장 후보에서 제외했습니다. 현재 자유매매 가능한 상품이라는 뜻은 아니며, 전매·거주 조건 충족 뒤의 일반 매매시장 후보로 구분했습니다.
앞선 9개 장의 낭독문과 기존 음성은 유지합니다.

검토 파일:
{f / 'script_v7.md'}

대본 확정: /approve {d['script']['id']}
대본 수정: /revise {d['script']['id']} 수정내용

새 후반 음성은 Jun으로 1541자+수정여유309자, 제출문자·실제크레딧 각각 최대1850. 포함잔액31715 확인, 추가결제0원. 자동재시도·충전·초과결제·새 유료이미지 제외.
음성 예산 승인: /approve {d['budget']['id']}
예산 수정: /revise {d['budget']['id']} 수정내용

두 승인은 이 버전에만 적용됩니다. 새 음성 생성은 아직 하지 않았습니다. 지도·타임라인 검토영상은 별도로 작업하고 있으며 준비되는 구간부터 경로를 알려드리겠습니다.'''
ok=telegram.send(message,quiet=True)
if not ok: raise RuntimeError('Telegram send failed')
receipt.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'delivered':True,'kind':'text_only','message_sha256':hashlib.sha256(message.encode()).hexdigest(),'script_sha256':d['script_sha256'],'decision_ids':{'script':d['script']['id'],'budget':d['budget']['id']}},ensure_ascii=False,indent=2),encoding='utf-8')
print('Telegram v7 scoped review text delivered; no file upload.')
