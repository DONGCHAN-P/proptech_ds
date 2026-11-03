import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];o=root/'output/cleanup-20261015'
p=o/'protected.json';initial=p.read_bytes()
assert not (o/'protected_before_duplicate_resolution.json').exists()
d=json.loads(initial);b=json.loads((o/'delete_bundle_verified.json').read_text(encoding='utf-8'))
paths={x['absolutePath'].casefold() for x in b['files']}
for x in b['files']:
 assert x['sha256']==x['canonical_sha256'] and len(x['sha256'])==64
 assert '/public/' in x['relativePath'] and '/editor/' in x['relativePath']
 canonical=Path(x['finalrefs'][0]).resolve()
 canonical.relative_to((root/'video/public').resolve())
 assert canonical.is_file() and canonical.stat().st_size==x['bytes']
 assert str(canonical).casefold() not in paths
(o/'protected_before_duplicate_resolution.json').write_bytes(initial)
old=len(d['files']);d['files']=[x for x in d['files'] if x['absolutePath'].casefold() not in paths]
d['duplicate_resolution']={'removed_redundant_bundle_copy_entries':old-len(d['files']),'canonical_sources_still_preserved':True,'basis':'full SHA256 verified audit delete_bundle_verified.json; canonicals present and size rechecked before deletion'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(d['duplicate_resolution']))
