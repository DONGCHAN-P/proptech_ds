"""Bind the four free clarity requests to the reviewed immutable phonetic plan."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
N = EP / 'narration'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, d):
    assert not p.exists(), 'Preserve existing authorization: ' + str(p)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
manifest_path = N / 'prepare-v3/delta_manifest.json'
manifest = read(manifest_path)
diff = read(N / 'prepare-v3/spoken_diff.json')
lock = read(HERE / 'locked_script.json')
targets = ['S014','S019','S024','S030']
assert manifest['script_sha256'] == diff['script_sha256'] == lock['script_sha256']
assert manifest['prepared_sha256'] == sha(N / 'prepare-v3/prepared.json') == '0c371115cbd7dfe9de40de7e1ef6f03c738bd52e974c217117878a659554ed6a'
assert manifest['generator_sha256'] == sha(N / 'repair_v3.py') == 'ada0c8d185fe7c120c71fb8684b7911dc3dad593f9d22adefdb29f31573c11b8'
assert manifest['spoken_diff_sha256'] == sha(N / 'prepare-v3/spoken_diff.json') == '310807406e42db8bce3683eb70f8101fa864571dc4834251418ac90206300bac'
assert manifest['target_scenes'] == [s['scene_id'] for s in diff['scenes']] == targets
assert manifest['new_network_calls_max'] == 4 and manifest['unchanged_raw_paragraphs'] == 41
assert manifest['display_and_financial_values_unchanged'] and manifest['meaning_cues_frozen'] == 150
assert all(row['parsed_krw'] == row['expected_krw'] for row in diff['numeric_validation'])
assert [r['expected_krw'] for r in diff['numeric_validation']] == [501030000,49020000,1029020000]
authorization_path = HERE / 'audio_generation_authorization_v3.json'
auth = {'approved':True, 'network_tts_authorized':True, 'source':'main_direct_instruction',
    'episode_id':EP.name, 'script_sha256':lock['script_sha256'],
    'prepared_sha256':sha(N / 'prepare-v3/prepared.json'), 'generator_sha256':sha(N / 'repair_v3.py'),
    'delta_manifest_sha256':sha(manifest_path), 'target_scenes':targets, 'new_network_calls_max':4,
    'cash_cap_krw':0, 'paid_calls_authorized':False, 'automatic_retry':False,
    'instruction_reference':authorization_path.relative_to(ROOT).as_posix(),
    'instruction':'Generate exactly four clarified paragraphs with the frozen free InJoon plan. Preserve all approved display text and values, reuse41 exact raw paragraphs, stop first failure. Actual post-generation ASR and timing QA remain required.',
    'reviewed_spoken_diff_sha256':sha(N / 'prepare-v3/spoken_diff.json'),
    'reviewed_tests':'Producer executed test_repair_v3.py:5passed, no network calls',
    'at_utc':datetime.now(timezone.utc).isoformat()}
save(authorization_path, auth)
save(N / 'main_tts_authorization_v3.json', auth)
print(json.dumps({'status':'four_free_requests_authorized_exact_plan', 'targets':targets, 'cash_cap_krw':0}))
