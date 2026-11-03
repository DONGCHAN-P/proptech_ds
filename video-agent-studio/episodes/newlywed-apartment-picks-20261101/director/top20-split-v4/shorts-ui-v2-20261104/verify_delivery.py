"""Verify the exact local release, approvals, preserved main and short aliases."""
from pathlib import Path
import hashlib
import json
import os

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    delivery = read(D / 'delivery.json')
    gate = read(D / 'completed_decision.json')
    state = read(E / 'state.json')
    release = read(D / 'release_manifest.json')
    assert delivery['status'] == 'local_review_ready' and len(delivery['assets']) == 3
    assert delivery['new_paid_calls'] == delivery['additional_credits'] == delivery['additional_cash_krw'] == delivery['uploads'] == 0
    assert gate['gate'] == 'completed' and gate['status'] == 'pending'
    assert gate['upload_authorized'] is gate['part2_production_authorized'] is False
    assert read(R / 'output/video_decisions/decisions/5fa686c7d1e9.json')['status'] == 'revision_requested'
    for record in gate['artifacts']:
        assert sha(R / record['path']) == record['sha256'], record['path']
    for record in read(D / 'preserved_state_fingerprint.json')['files']:
        assert sha(R / record['path']) == record['sha256'], record['path']
    main_asset = release['unchanged_main']
    assert sha(R / main_asset['video']) == main_asset['video_sha256'] == state['active_video_sha256']
    for item in delivery['assets']:
        digest = sha(R / item['video'])
        qa = read(R / item['qa'])
        evidence = read(R / item['encoded_manifest'])
        assert digest == item['video_sha256'] == qa['video_sha256'] == evidence['video_sha256']
        assert qa['status'] == 'passed_for_local_review' and qa['required_open_count'] == qa['critical_open_count'] == 0
        assert evidence['status'] == 'passed' and evidence['minimum_audio_correlation'] > .97
        lock = read(R / item['timing'])
        assert sha(Path(lock['master_audio'])) == lock['master_audio_sha256']
        assert lock['voice_regeneration_calls'] == lock['additional_credits'] == 0
        project = R / item['project']
        manifest = read(project / 'input_manifest.json')
        for source in manifest['inputs']:
            assert sha(Path(source['path'])) == source['sha256'], source['path']
        frozen_project = project
        if item['id'] == 'SHORT03-R15-R11':
            snapshot = read(D / 'render_source_snapshot.json')
            assert snapshot['status'] == 'exact_render_source_preserved'
            assert snapshot['source_geometry_text_timing_audio_changed'] is False
            frozen_project = Path(snapshot['immutable_render_source_snapshot'])
        for source in manifest['project_files']:
            assert sha(frozen_project / source['path']) == source['sha256'], source['path']
    assert state['active_upload_authorized'] is False and state['pending_decision_id'] == gate['id']
    cfg = read(R / 'config/video_shelf.json')
    entry = next(x for x in cfg['entries'] if x['name'] == '신혼부부_TOP20_1편')
    folder = R / cfg['shelf'] / entry['name']
    for alias, source in entry['files'].items():
        assert os.path.samefile(folder / alias, R / source), alias
    comparison = read(D / 'comparison_manifest.json')
    assert comparison['status'] == 'actual_encoded_comparison_ready' and len(comparison['frames']) == 6
    for frame in comparison['frames']:
        assert sha(Path(frame['file'])) == frame['sha256']
    report = dict(status='passed', shorts=3, main_unchanged=True,
                  checked_shelf_links=len(entry['files']), completed_decision_id=gate['id'],
                  additional_credits=0, additional_cash_krw=0, uploads=0,
                  five_gates_preserved=True, existing_budgets_unchanged=True,
                  actual_listening=False, continuous_playback=False)
    (D / 'delivery_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
