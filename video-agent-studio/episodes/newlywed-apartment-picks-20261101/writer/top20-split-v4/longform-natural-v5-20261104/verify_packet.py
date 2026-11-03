"""생성기를 재실행하지 않고 디스크 산출물과 원본 매핑을 대조한다."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
OUT = Path(__file__).resolve().parent

def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))

rows = read('sentence_mapping.json')['sentences']
patches = read('sentence_patches.json')['patches']
validation = read('validation.json')
handoff = read('handoff.json')
original_path = ROOT / validation['input_revisions'][0]['path']
original = [r for r in json.loads(original_path.read_text(encoding='utf-8-sig'))['sentences'] if r['kind'] == 'accepted_main']
md = (OUT / 'script_v5.md').read_text(encoding='utf-8')
emitted = re.findall(r'<!-- ([^>]+) -->\n([^\n]+)', md)
assert emitted == [(r['sentence_id'], r['text']) for r in rows]
assert len(rows) == 90 and len(patches) == 47
assert [r['sentence_id'] for r in rows] == [r['sentence_id'] for r in original]
assert all(validation['checks'].values())
assert all(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest() == r['sha256'] for r in validation['input_revisions'])
assert all(r['reading_text'] for r in rows)
assert sum(r['changed'] for r in rows) == len(patches)
source_index = {r['sentence_id']: r for r in original}
new_index = {r['sentence_id']: r for r in rows}
for patch in patches:
    sid = patch['oldID']
    assert patch['old_text'] == source_index[sid]['text']
    assert patch['old_reading_text'] == source_index[sid]['reading_text']
    assert patch['new_text'] == new_index[sid]['text']
    assert patch['new_reading_text'] == new_index[sid]['reading_text']
    assert all(text in (OUT / 'before_after.md').read_text(encoding='utf-8') for text in (patch['old_text'], patch['new_text']))
protected = new_index['P01-R11-V2-04']
expected = read('phonetics.json')['entries'][0]['reading_text']
assert expected == '상계 이차 중앙 하이츠'
assert protected['reading_text'].startswith(expected + ' ')
assert '2차' in protected['text']
assert all((OUT / name).is_file() for name in handoff['outputs'] if name not in ('verification.json', 'freeze_manifest.json'))
result = {
    'status': 'local_artifact_consistency_passed_not_independent_qa',
    'markdown_sentence_mapping': len(emitted), 'patch_records': len(patches),
    'local_validation_checks': len(validation['checks']),
    'input_hashes_verified': len(validation['input_revisions']),
    'all_declared_output_files_present_except_this_receipt_before_creation': True,
    'protected_reading': protected['reading_text'],
    'reading_characters': sum(len(r['reading_text']) for r in rows),
    'changed_reading_characters': sum(len(p['new_reading_text']) for p in patches),
    'actual_listening': False, 'new_audio_generated': False,
    'artifact_hashes': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in handoff['outputs'] if name not in ('verification.json', 'freeze_manifest.json')},
}
(OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
freeze = {
    'task_id': handoff['task_id'], 'status': 'writer_text_frozen_reference_only_not_approved_or_generated',
    'main_sentence_count': len(rows), 'changed_sentence_count': len(patches),
    'reading_characters': result['reading_characters'],
    'changed_reading_characters': result['changed_reading_characters'],
    'character_count_policy': '공백·문장부호 포함, 문장 사이 연결용 구분자 제외; API 전송량이나 청구 크레딧은 아님',
    'parent_review_delta': validation['parent_review_delta'],
    'artifact_hashes': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in handoff['outputs'] if name != 'freeze_manifest.json'},
}
(OUT / 'freeze_manifest.json').write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert all((OUT / name).is_file() for name in handoff['outputs'])
print(json.dumps({k: v for k, v in result.items() if k != 'artifact_hashes'}, ensure_ascii=False))
