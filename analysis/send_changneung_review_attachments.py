import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from notify.telegram import send_file

event_path = root / 'output/telegram_conversation/inbox/718066300.json'
event = json.loads(event_path.read_text(encoding='utf-8-sig'))
if event.get('application_status') == 'applied':
    print('Already applied; no duplicate delivery.')
    raise SystemExit(0)
ep = root / 'video-agent-studio/episodes/goyang-changneung-20261015'
out = ep / 'outputs/editorial-review-delivery-v1'
out.mkdir(parents=True, exist_ok=True)
items = [
    ('대본_검토보고서.txt', (ep / 'writer/editorial-review-v1/viewer_message_review.md').read_text(encoding='utf-8-sig'), '대본 검토 보고서 · 장별 평가와 수정 문장 예시'),
    ('화면_검토보고서.txt', (ep / 'qa/editorial-review-v1/편집품질_독립검토.md').read_text(encoding='utf-8-sig'), '화면 검토 보고서 · 시간대별 개선 의견 8개'),
]
script = (ep / 'writer/script-v3/script_v3.md').read_text(encoding='utf-8-sig')
narration = '\n\n'.join(m.group(1).strip() + '\n\n' + m.group(2).strip() for m in re.finditer(r'## (M\d{3}[^\n]*)\n.*?### 낭독\n(.*?)\n### 화면 지시', script, re.S))
assert narration.count('M00') == 10
items.append(('현재_대본_낭독문.txt', '현재 v5r2 영상의 승인 낭독문\n검토 의견을 반영한 수정 대본이 아닙니다.\n\n' + narration, '현재 영상 대본 · 화면 제작 지시를 제외한 낭독문'))
receipt_path = out / 'telegram_attachment_receipt.json'
receipt = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else {'event_id': 718066300, 'files': {}}

def save():
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for name, content, caption in items:
    path = out / name
    path.write_text(content, encoding='utf-8-sig')
    prior = receipt['files'].get(name, {})
    if prior.get('status') == 'sent':
        continue
    if prior.get('status') == 'sending':
        raise RuntimeError('Previous delivery outcome unknown; inspect before retry: ' + name)
    receipt['files'][name] = {'status': 'sending', 'path': str(path)}
    save()
    sent = send_file(path, caption)
    receipt['files'][name]['status'] = 'sent' if sent else 'failed'
    save()
    if not sent:
        raise RuntimeError('File delivery failed: ' + name)
event.update(application_status='applied', applied_at=datetime.now(timezone.utc).isoformat(), application_result='Requested review attachments and current narration text delivered to existing private Telegram chat; no gates or budgets changed.', attachment_delivery_receipt=str(receipt_path))
event_path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False))
