"""Fresh local delivery verification; no generation, sending, or publication."""
from pathlib import Path
import hashlib
import json
import os

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    release = read(D / 'release_manifest.json')
    delivery = read(D / 'delivery.json')
    state = read(E / 'state.json')
    assert delivery['status'] == 'local_review_ready' and delivery['uploads'] == 0
    assert state['active_video_sha256'] == release['assets'][0]['video_sha256']
    assert state['active_upload_authorized'] is False
    gate = read(D / 'completed_decision.json')
    assert gate['status'] == 'pending' and gate['gate'] == 'completed'
    assert gate['upload_authorized'] is False and gate['part2_production_authorized'] is False
    for item in gate['artifacts']:
        assert digest(R / item['path']) == item['sha256'], item['path']
    for item in read(D / 'unaffected_state_fingerprint.json')['files']:
        assert digest(R / item['path']) == item['sha256'], item['path']
    for item in release['assets']:
        video = R / item['video']
        assert digest(video) == item['video_sha256']
        q = read(R / item['qa'])
        assert q['video_sha256'] == item['video_sha256']
        assert q['critical_open_count'] == q['required_open_count'] == 0
        proof = read(R / item['encoded_manifest'])
        assert proof['video_sha256'] == item['video_sha256'] and proof['status'] == 'passed'
        assert proof['minimum_audio_correlation'] > .97
    config = read(R / 'config/video_shelf.json')
    entry = next(x for x in config['entries'] if x['name'] == '신혼부부_TOP20_1편')
    folder = R / config['shelf'] / entry['name']
    for alias, source in entry['files'].items():
        assert os.path.samefile(folder / alias, R / source), alias
    old = read(D / 'baseline_state.json')
    assert digest(E / old['active_video']) == old['active_video_sha256']
    report = dict(status='passed', assets=4, checked_shelf_links=len(entry['files']),
                  credits_used=delivery['actual_credits'], credit_cap=delivery['credit_cap'],
                  cash_cost_krw=delivery['cash_cost_krw'], completed_gate=gate['id'],
                  completed_status=gate['status'], uploads=0, unrelated_state_unchanged=True,
                  previous_video_preserved=True, actual_listening=False, continuous_playback=False)
    (D / 'delivery_verification.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
