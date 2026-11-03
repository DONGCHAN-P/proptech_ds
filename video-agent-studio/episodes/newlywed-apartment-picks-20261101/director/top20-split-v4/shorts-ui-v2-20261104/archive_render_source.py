"""Preserve exact render bytes after Studio adds nonvisual selection IDs."""
from pathlib import Path
import hashlib
import json
import re
import shutil

D = Path(__file__).resolve().parent
E = D.parents[2]
H = E / 'editor/top20-split-v4/shorts-ui-v2-20261104'


def main():
    project = H / 'SHORT03-R15-R11'
    manifest = json.loads((project / 'input_manifest.json').read_text(encoding='utf-8'))
    snapshot = H / 'render_source_snapshot/SHORT03-R15-R11'
    assert not snapshot.exists(), 'Preserve existing snapshot'
    changed = []
    for item in manifest['project_files']:
        src = project / item['path']
        data = src.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            assert src.suffix == '.html', item['path']
            normalized = re.sub(rb' data-hf-id="[^"]*"', b'', data)
            assert hashlib.sha256(normalized).hexdigest() == item['sha256'], item['path']
            changed.append(dict(path=item['path'], studio_sha256=hashlib.sha256(data).hexdigest(),
                                render_sha256=item['sha256'], difference='Studio data-hf-id selection attributes only'))
            data = normalized
        dest = snapshot / item['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == item['sha256']
    shutil.copyfile(project / 'input_manifest.json', snapshot / 'input_manifest.json')
    record = dict(status='exact_render_source_preserved', editable_studio_project=str(project),
                  immutable_render_source_snapshot=str(snapshot), selection_metadata_changes=changed,
                  source_geometry_text_timing_audio_changed=False, original_studio_files_overwritten=False)
    (D / 'render_source_snapshot.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('exact_render_source_snapshot_verified', len(manifest['project_files']), 'files')


if __name__ == '__main__':
    main()
