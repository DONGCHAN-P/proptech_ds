"""Retain the v5 release draft and reuse unchanged packaging for v6."""
import hashlib
import json
import shutil
from pathlib import Path
EP=Path(__file__).resolve().parents[2]
source=EP/'outputs/private-release-v1'
target=EP/'outputs/private-release-v2'
target.mkdir(exist_ok=True)
files=[source/name for name in ['description_draft.md','metadata_draft.json','thumbnail.png','thumbnail.html','thumbnail_checks.json']]
files += [p for p in (source/'assets').rglob('*') if p.is_file()]
manifest=[]
for file in files:
    destination=target/file.relative_to(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        shutil.copy2(file,destination)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(file)==digest(destination)
    manifest.append({'source':file.relative_to(EP).as_posix(),'target':destination.relative_to(EP).as_posix(),'sha256':digest(file)})
(target/'packaging_reuse.json').write_text(json.dumps({'status':'unchanged_packaging_copied_for_new_timing','files':manifest,'metadata_and_thumbnail_final_QA':'pending_with_final_MP4'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reused_packaging_files':len(files),'release_folder':target.relative_to(EP).as_posix(),'uploaded':False}))
