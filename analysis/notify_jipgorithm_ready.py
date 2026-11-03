"""Send the explicitly requested completion notice once; never log credentials."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from notify.telegram import send

receipt = ROOT / 'output/jipgorithm-review-v1/telegram_completion_receipt.json'
if receipt.exists() and json.loads(receipt.read_text(encoding='utf8')).get('sent'):
    print('already_sent')
    raise SystemExit(0)
message = ('집고리즘 로컬 검토본 준비가 완료되었습니다.\n'
           'PC에서 http://127.0.0.1:8010/ 로 확인할 수 있습니다.\n'
           '예산 계산·회원 추천·개인 저장함·공개 지도 구현 및 테스트 40개, PC/모바일 흐름 검증을 마쳤습니다.\n'
           'Supabase 실제 프로젝트 연결·최신 금융 규정 자동 판정·실제 결제는 아직 적용 전입니다.\n'
           '설정 안내: web/SERVICE_SETUP.md')
try:
    ok = bool(send(message, quiet=True))
except Exception:
    ok = False
receipt.write_text(json.dumps({'sent': ok, 'at': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf8')
print(json.dumps({'telegram_completion_sent': ok}))
