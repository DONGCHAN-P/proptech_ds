"""Check actual input bytes, charged text and all current hash bindings offline."""
from pathlib import Path
import hashlib
import json

OWN=Path(__file__).resolve().parent
ROOT=OWN.parents[4]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda data:hashlib.sha256(data).hexdigest()
manifest=read(OWN/'narration_manifest.json')
generation=read(OWN/'generation_input.json')
raw=read(OWN/'generator_raw_manifest.json')
budget=read(OWN/'budget_proposal.json')
caption=read(OWN/'caption_plan.json')
assert len(manifest['chapters'])==len(generation['paragraphs'])==7
for chapter,request in zip(manifest['chapters'],generation['paragraphs']):
    payload=chapter['text'].encode('utf-8')
    assert (ROOT/chapter['path']).read_bytes()==payload,chapter['chapter_id']+' bytes differ from billed request text'
    assert sha(payload)==chapter['sha256']==request['proposed_spoken_text_sha256']
    assert len(payload.decode('utf-8'))==chapter['characters']==request['characters']
    assert request['proposed_spoken_text']==chapter['text']
assert sum(c['characters'] for c in manifest['chapters'])==5797==budget['input_characters_to_send']
manifest_sha=sha((OWN/'narration_manifest.json').read_bytes())
assert raw['source_manifest_sha256']==caption['source_manifest_sha256']==budget['manifest_sha256']==manifest_sha
assert sha((OWN/'generation_input.json').read_bytes()) in (OWN/'generate.mjs').read_text(encoding='utf-8')
assert budget['included_credit_cap_proposed']==7000 and budget['additional_cash_cap_krw']==0
assert budget['automatic_retries']==0
print('PASS: 7 byte-identical LF inputs, 5797 billed characters, all live hash bindings, cap7000, cash0. No authenticated calls.')
