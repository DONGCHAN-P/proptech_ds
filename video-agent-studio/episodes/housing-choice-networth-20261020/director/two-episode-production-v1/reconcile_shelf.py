"""Reconcile only our recorded v3 newline normalization before linking the approved v5."""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
old_checks=json.loads((EP/'outputs/cost-wording-v3/checks.json').read_text(encoding='utf-8'))
old_source=ROOT/old_checks['target']
expected=old_checks['target_sha256']
assert hashlib.sha256(old_source.read_bytes()).hexdigest()==expected
manifest_path=ROOT/'영상/경로목록.json'
original=manifest_path.read_bytes()
manifest=json.loads(original.decode('utf-8'))
changes=[]
for row in manifest['files']:
    if row['source'].replace('\\','/') != old_checks['target']:
        continue
    alias=ROOT/row['alias']
    assert os.path.samefile(alias,old_source)
    assert hashlib.sha256(alias.read_bytes()).hexdigest()==expected
    if row['sha256']!=expected:
        changes.append({'alias':row['alias'],'previous_manifest_sha256':row['sha256'],
                        'verified_generated_v3_sha256':expected,'reason':'recorded v3 CRCRLF normalization after shelf refresh'})
        row.update(sha256=expected,bytes=old_source.stat().st_size)
assert len(changes)==2, 'Only the two previously generated v3 links may be reconciled.'
backup=HERE/'shelf_manifest_before_v5_reconcile.json'
assert not backup.exists()
backup.write_bytes(original)
(HERE/'shelf_reconcile_receipt.json').write_text(json.dumps({'source_checks':'outputs/cost-wording-v3/checks.json',
    'changes':changes,'old_source_preserved':True,'unrecorded_edits_overwritten':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'own_generated_links_reconciled':len(changes),'old_source_preserved':True}))
