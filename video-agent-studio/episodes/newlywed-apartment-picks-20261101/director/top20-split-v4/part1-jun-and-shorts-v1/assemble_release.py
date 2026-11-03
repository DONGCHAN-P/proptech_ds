"""Bind four independently checked final files, without publishing anything."""
from pathlib import Path
import hashlib
import json

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]
H = E / 'editor/top20-split-v4/jun-and-shorts-v1'
Q = E / 'qa/top20-split-v4/jun-and-shorts-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def relative(path):
    return path.resolve().relative_to(R).as_posix()


def main():
    specs = [('main', H / 'main/jun-v3', D / 'locked_timing.json',
              Q / 'main_final_review.json', 'main-v3')]
    for sid in ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11']:
        specs.append((sid, H / 'shorts/native-v4' / sid,
                      D / 'shorts' / sid / 'locked_timing.json',
                      Q / f'{sid}_final_review.json', sid + '-v4'))
    assets = []
    for sid, editor, timing, qa_path, evidence_id in specs:
        receipt_path = editor / 'render_receipt.json'
        receipt = read(receipt_path)
        video = Path(receipt['video'])
        video.resolve().relative_to(E / 'outputs/top20-split-v4/jun-and-shorts-v1')
        digest = hashlib.sha256(video.read_bytes()).hexdigest()
        qa = read(qa_path)
        evidence_path = Q / 'encoded' / evidence_id / 'encoded_manifest.json'
        evidence = read(evidence_path)
        assert digest == receipt['video_sha256'] == qa['video_sha256'] == evidence['video_sha256'], sid
        assert qa['required_open_count'] == qa['critical_open_count'] == 0, sid
        assert qa['status'] == 'passed_for_local_review' and evidence['status'] == 'passed', sid
        lock = read(timing)
        project = editor / 'project' if sid == 'main' else editor
        assert (project / 'index.html').is_file(), sid
        assets.append(dict(id=sid, video=relative(video), video_sha256=digest,
                           duration_s=lock['total_s'], timing=relative(timing),
                           project=relative(project), editor_receipt=relative(receipt_path),
                           qa=relative(qa_path), encoded_manifest=relative(evidence_path)))
    result = dict(revision='jun-and-shorts-v1', render_revision='main-jun-v3_shorts-native-v4',
                  status='four_exact_artifacts_independently_checked', assets=assets)
    target = D / 'release_manifest.json'
    assert not target.exists(), 'Preserve an already assembled release'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], assets=len(assets))))


if __name__ == '__main__':
    main()
