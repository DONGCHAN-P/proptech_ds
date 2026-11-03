"""Send the verified v3 aggregate package to the configured own private chat."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from notify import telegram as tg

EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/script-review-v3'
RECEIPT = ROOT / 'output/telegram_deliveries/regional_script_v3.json'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


checks = read(OUT / 'package_checks.json')
if RECEIPT.exists() and read(RECEIPT).get('ok'):
    assert read(RECEIPT)['script_sha256'] == checks['script_sha256']
    print(json.dumps({'ok': True, 'already_delivered': True, 'receipt': str(RECEIPT)}))
    raise SystemExit(0)
for path, meta in checks['files'].items():
    assert sha(ROOT / path) == meta['sha256'], path
manifest = read(OUT / 'archive_manifest.json')
archive = ROOT / manifest['archive']
assert sha(archive) == manifest['sha256']
decision = read(OUT / 'script_decision.json')
assert decision['artifact_hashes']['script_v3.md'] == checks['script_sha256']
cfg = read(ROOT / 'config/video_telegram_bridge.json')
assert cfg['private_chat_only'] and 'deliverables' in cfg['notification_preference']['scope']
token, cid = tg.creds()
expected = os.environ.get('TELEGRAM_USER_ID', '').strip() or (cid if cid.isdigit() else '')
assert token and cid and cid.isdigit() and cid == expected, 'Private recipient not configured'
chat = tg._post('getChat', token, data={'chat_id': cid})
assert chat.get('ok') and chat['result'].get('type') == 'private' and str(chat['result']['id']) == cid, 'Private recipient verification failed'
caption = (
    '지역별 영상 대본 v3 · 2006년 이후 전체 이력\n'
    '집값은 결국 오른다? 지역별 회복의 시간\n'
    '보유 7개 지역 유효거래 6,640,041건의 가격·거래량과 전체 기간 고점·낙폭·복귀 분석을 담았습니다. '
    '세종은 초기 조회 이력과 2015년 이후 연속 비교 지수를 구분했습니다.\n'
    '대본·낭독본·12장면 화면설계·차트 5장·계산표·Claude Opus(max) 검토 반영 및 독립 검수 기록을 첨부합니다.\n'
    '광주·울산 추가 원자료 수집 완료, 충북→충남 진행 중. 새 원자료는 이번 가격 분석에 아직 합치지 않았습니다.\n'
    f'검토 대본 v3 결정 ID: {decision["id"]}\n'
    f'의견: /note {decision["id"]} 내용\n'
    f'수정: /revise {decision["id"]} 내용\n'
    f'대본 승인: /approve {decision["id"]}\n'
    '대본 검토 단계이며 유료 제작·업로드 승인은 별도입니다.')
with archive.open('rb') as f:
    response = tg._post('sendDocument', token, data={'chat_id': cid, 'caption': caption},
                        files={'document': (archive.name, f, 'application/zip')}, timeout=45)
message = response.get('result') or {}
record = {'at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'ok': bool(response.get('ok')), 'private_recipient_verified': True,
          'filename': archive.name, 'bytes': archive.stat().st_size,
          'sha256': sha(archive), 'script_sha256': checks['script_sha256'],
          'script_decision_id': decision['id'], 'message_id': message.get('message_id'),
          'document_file_name': (message.get('document') or {}).get('file_name'),
          'status': 'review_draft_not_approved', 'claude_review': 'opus_effort_max_completed'}
if not record['ok']:
    record['error'] = tg.mask(response.get('error', 'Unknown error'), token)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
if record['ok']:
    state = read(EP / 'state.json')
    assert state['script_sha256'] == record['script_sha256']
    state.update(stage='script_v3_delivered_for_review', telegram_delivery_receipt=RECEIPT.relative_to(ROOT).as_posix(), updated_at=record['at_utc'])
    (EP / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    pre = read(EP / 'episode_preflight_v3.json')
    pre['release']['telegram_notice_receipt'] = RECEIPT.relative_to(ROOT).as_posix()
    (EP / 'episode_preflight_v3.json').write_text(json.dumps(pre, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(0 if record['ok'] else 1)
