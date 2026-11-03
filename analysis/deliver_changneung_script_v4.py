import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from notify.video_decisions import create, now, write
from notify.telegram import send_file

ep = root / 'video-agent-studio/episodes/goyang-changneung-20261015'
out = ep / 'outputs/script-review-v4'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

event_path = root / 'output/telegram_conversation/inbox/718066301.json'
event = read(event_path)
receipt_path = out / 'telegram_delivery_receipt.json'
if receipt_path.exists():
    raise RuntimeError('Delivery already initiated; inspect receipt before retry.')
qpath = ep / 'qa/script-review-v4/final_review.json'
q = read(qpath)
assert q['required_open_count'] == 0 and q['critical_open_count'] == 0 and q['review_ready'] is True
script = out / 'script_v4.md'
narration = out / 'narration_v4.txt'
changes = out / 'changes_v4.txt'
assert sha(script) in json.dumps(q), 'Independent review must bind final script hash'
assert script.read_bytes() == (ep / 'writer/script-v4/script_v4.md').read_bytes()
assert sha(ep / 'outputs/production-v5/changneung_full_v5r2.mp4') == '7979a8071e4c07d4047a46b37b4abf6fa89c1a8aa9f4fb0c90dd0d99bec9f0b0'
artifacts = {str(p.relative_to(ep)): sha(p) for p in [script, narration, changes, qpath, ep / 'writer/script-v4/claim_mapping.json', ep / 'writer/script-v4/scene_proposals.json']}
d = create(ep.name, 'script', '창릉 수정 대본 v4 검토: 본청약 사례의 취득 전제, 가격 대가, 기존 통근 구조, 3후보 입주 부분합, 가족 달력 및 조건부 최종 비교를 반영. 대본·화면 지시 검토만이며 새 음성·이미지·렌더·업로드 승인과 예산은 포함하지 않음.')
d.update(script_revision='script-v4', scope='script_and_scene_direction_only', artifact_hashes=artifacts, source_event='718066301', paid_generation_authorized=False, upload_authorized=False)
write(root / 'output/video_decisions/decisions' / f"{d['id']}.json", d)
decisions = read(ep / 'decisions.json')
old_id = '74bf28467ae1'
old_path = root / 'output/video_decisions/decisions' / f'{old_id}.json'
old = read(old_path)
if old.get('status') == 'pending':
    old.update(status='revision_requested', response={'source': 'authenticated_telegram_conversation', 'event_id': '718066301', 'note': event['text'], 'at': now().isoformat()}, next_script_decision_id=d['id'])
    write(old_path, old)
    for i, prior in enumerate(decisions['decisions']):
        if prior.get('id') == old_id:
            decisions['decisions'][i] = old
decisions['decisions'].append(d)
write(ep / 'decisions.json', decisions)
state = read(ep / 'state.json')
state.update(stage='script_review_pending', draft_script_revision='script-v4', draft_script_status='review_pending', draft_script_path='outputs/script-review-v4/script_v4.md', draft_script_sha256=sha(script), pending_gate='script', pending_decision_ids={'script': d['id']}, active_tasks=[], new_paid_generation=False, paid_generation_authorized=False, voice_generation_hold=True, upload_authorized=False, publication_authorized=False)
write(ep / 'state.json', state)
pre = read(ep / 'preflight.json')
pre['approvals']['script'] = {'decision_id': d['id'], 'status': 'pending', 'revision': 'script-v4', 'artifact_hashes': artifacts}
pre['approvals']['budget'].update(applies_to_script_revision='script-v3', applies_to_script_v4=False)
if pre['approvals']['completed'].get('decision_id') == old_id and old.get('status') == 'revision_requested':
    pre['approvals']['completed']['status'] = 'revision_requested'
write(ep / 'preflight.json', pre)

attachments = [
    (narration, out / '창릉_수정대본_v4.txt', f"창릉 수정 대본 v4 · 전체 낭독문\n대본 확정 /approve {d['id']}\n수정 /revise {d['id']} 수정내용\n대본 검토만이며 새 음성·영상 제작 예산은 포함하지 않습니다."),
    (changes, out / '창릉_v4_변경요약.txt', '창릉 v4 변경 요약 · 확인된 사실과 남은 조사 범위'),
]
receipt = {'source_event': '718066301', 'decision_id': d['id'], 'script_sha256': sha(script), 'files': {}}
write(receipt_path, receipt)
for source, target, caption in attachments:
    target.write_text(source.read_text(encoding='utf-8-sig'), encoding='utf-8-sig')
    receipt['files'][target.name] = {'status': 'sending', 'file': str(target), 'sha256': sha(target)}
    write(receipt_path, receipt)
    sent = send_file(target, caption)
    receipt['files'][target.name]['status'] = 'sent' if sent else 'failed'
    write(receipt_path, receipt)
    if not sent:
        raise RuntimeError('Attachment delivery failed: ' + target.name)
event.update(application_status='applied', application_result='Script v4 draft rewritten, independently reviewed, and narration/change-summary attachments delivered. New scoped script gate pending; no paid generation, render or upload.', completed_at=now().isoformat(), script_decision_id=d['id'], result_script=str(script), delivery_receipt=str(receipt_path))
write(event_path, event)
print(json.dumps(receipt, ensure_ascii=False))
