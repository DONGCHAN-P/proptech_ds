"""Verify the exact delivered draft, shelf aliases, frozen inputs and archive."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/script-review-v3'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


checks = read(OUT / 'package_checks.json')
current = sha(OUT / 'script_v3.md')
qa = read(EP / 'qa/full-history-v1/final_recheck_v3.json')
assert current == checks['script_sha256'] == qa['checked_revision']['script_sha256']
assert qa['required_count'] == 0
for path, meta in checks['files'].items():
    assert sha(ROOT / path) == meta['sha256'], path
receipt = read(ROOT / 'output/telegram_deliveries/regional_script_v3.json')
archive = read(OUT / 'archive_manifest.json')
assert receipt['ok'] and receipt['private_recipient_verified']
assert receipt['script_sha256'] == current
assert receipt['sha256'] == archive['sha256'] == sha(ROOT / archive['archive'])
with zipfile.ZipFile(ROOT / archive['archive']) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == archive['member_count']
    assert z.read('대본_v3.md') == (OUT / 'script_v3.md').read_bytes()
shelf = read(ROOT / 'config/video_shelf.json')
entry = next(e for e in shelf['entries'] if e['name'] == '지역별가격회복')
for alias, source in entry['files'].items():
    assert os.path.samefile(ROOT / '영상/지역별가격회복' / alias, ROOT / source), alias
frozen = read(EP / 'qa/full-history-v1/recheck_v3.json')['input_receipts']
checked = {}
for source, old in frozen.items():
    if source.endswith('/outputs/script-review-v3/script_v3.md'):
        continue
    assert sha(ROOT / source) == old['sha256'], source
    checked[source] = old['sha256']
state = read(EP / 'state.json')
assert state['stage'] == 'script_v3_delivered_for_review' and state['script_sha256'] == current
assert not state['timing_locked'] and state['collection_not_yet_integrated']
result = {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'status': 'verified_review_draft_delivered', 'script_sha256': current,
          'qa_required_open': 0, 'all_package_hashes_match': True,
          'archive_integrity': True, 'archive_members': archive['member_count'],
          'all_shelf_aliases_same_ntfs_file': True, 'frozen_inputs_and_prior_receipts_unchanged': checked,
          'telegram_message_id': receipt['message_id'], 'telegram_receipt': 'output/telegram_deliveries/regional_script_v3.json',
          'actual_listening': False, 'continuous_video_playback': False,
          'new_collection_in_current_price_analysis': False}
(OUT / 'delivery_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
state['delivery_verification'] = (OUT / 'delivery_verification.json').relative_to(ROOT).as_posix()
(EP / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({k: v for k, v in result.items() if k != 'frozen_inputs_and_prior_receipts_unchanged'}, ensure_ascii=False))
