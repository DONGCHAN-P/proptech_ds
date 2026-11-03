"""Bounded offline QA: compare frozen small tables; never recompute raw trades."""
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/production-v1-jun'
QA = Path(__file__).resolve().parent

def read(p):
    return json.loads(Path(p).read_text('utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def relative(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()

checks = Counter()
failures = []
inputs = {}

def check(group, ok, detail):
    checks[group] += 1
    if not ok:
        failures.append({'check': group, 'detail': detail})

def track(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    key = relative(p)
    if key not in inputs:
        inputs[key] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    if expected is not None:
        check('input_sha', inputs[key]['sha256'] == expected, key)
    return inputs[key]

def typed(v, kind):
    if v == '':
        return None
    if kind == 'bool':
        assert v in ('True', 'False')
        return v == 'True'
    if kind == 'int':
        n = float(v)
        assert n.is_integer()
        return int(n)
    if kind == 'float':
        return float(v)
    return v

data_path = EP / 'visual/production-v1/chart_data.json'
d = read(data_path)
track(data_path)
track(OUT / 'project/assets/chart_data.json', sha(data_path))
prior = read(EP / 'qa/full-history-v1/independent_recompute.json')
final = read(EP / 'qa/full-history-v1/final_recheck_v3.json')
prior_hashes = final['reuse']['prior_raw_input_hashes']
tables = {}
for name, source in d['metadata']['sources'].items():
    p = ROOT / source['relative_path']
    track(p, source['sha256'])
    if source['relative_path'] in prior_hashes and name != 'approved_script':
        check('prior_immutable_sha', source['sha256'] == prior_hashes[source['relative_path']]['sha256'], name)
    if name not in d['metadata']['table_schemas']:
        continue
    schema = d['metadata']['table_schemas'][name]
    with p.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        check('csv_headers', reader.fieldnames == list(schema), name)
        rows = [{k: typed(v, schema[k]) for k, v in row.items()} for row in reader]
    tables[name] = len(rows)
    if name == 'series':
        expected = {r: [] for r in d['regions']}
        for row in rows:
            expected[row['region']].append({'quarter': row['quarter'], 'index': row['normalized_start_100'],
                                          'drawdown': row['running_drawdown_pct'], 'matched_complexes': row['matched_complexes']})
    elif name == 'all_transactions':
        expected = {r: [row for row in rows if row['region'] == r] for r in d['regions']}
    elif name == 'summary':
        expected = {row['region']: row for row in rows}
    else:
        expected = rows
    check('csv_exact_values_order_nulls', d[name] == expected, name)

for kind, old, current in [('summary', prior['recomputed_summaries'], list(d['summary'].values())),
                           ('episodes', prior['recomputed_episodes'], d['episodes'])]:
    check('prior_math_reuse', len(old) == len(current), kind + ' row count')
    for a, b in zip(old, current):
        for k, v in a.items():
            value = b.get(k)
            equal = (math.isclose(v, value, abs_tol=1e-9, rel_tol=1e-12)
                     if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(value, (int, float))
                     else k in b and v == value)
            check('prior_math_reuse', equal, f'{kind}:{a.get("region")}:{a.get("episode_id", "")}:{k}')
check('final_script_sha', d['metadata']['script_sha256'] == final['checked_revision']['script_sha256'], 'approved v3')
for p, expected in read(OUT / 'checks/input_versions.json')['inputs'].items():
    track(Path(p.replace('\\', '/')), expected)
for r, rows in d['series'].items():
    check('supported_start_end', rows[0]['quarter'] == ('2015Q1' if r == d['regions'][-1] else '2006Q1') and rows[-1]['quarter'] == '2026Q2', r)
for e in d['episodes']:
    if e['right_censored']:
        check('censored_no_return', e['first_return_quarter'] is None and e['first_return_index'] is None, e['episode_id'])

scenes = read(EP / 'scenes.json')['scenes']
approved = read(EP / 'outputs/script-review-v3/scenes_v3.json')['scenes']
beat_manifest = read(OUT / 'project/beat_manifest.json')
timing = read(OUT / 'project/timing_resolved.json')
beats = [b for s in scenes for b in s['beats']]
ids = [b['beat_id'] for b in beats]
check('scene_beat_coverage', len(scenes) == 12 and len(beats) == 39 and len(set(ids)) == 39, '12 scenes / 39 distinct beats')
check('scene_beat_coverage', scenes == approved, 'shared scenes versus approved scenes snapshot')
check('scene_beat_coverage', ids == [b['beat_id'] for b in beat_manifest['beats']] == [b['beat_id'] for b in timing['beats']], 'ordered authored beat IDs')
coverage = []
for scene in scenes:
    p = OUT / f"project/compositions/{scene['scene_id']}.html"
    text = p.read_text('utf-8-sig')
    track(p)
    jobs = json.JSONDecoder().raw_decode(text.split('const jobs=', 1)[1])[0]
    for b in scene['beats']:
        plan = next(x for x in beat_manifest['beats'] if x['beat_id'] == b['beat_id'])
        check('authored_visual_source_preserved', plan['visual'] == b['visual'] and plan['source'] == b['source'], b['beat_id'])
        check('authored_beat_present', f'id="{b["beat_id"]}"' in text, b['beat_id'])
        actual = [x for x in jobs if x['id'] in plan['chart_ids']]
        check('authored_chart_ids', len(actual) == len(plan['chart_ids']), b['beat_id'])
        coverage.append({'scene_id': scene['scene_id'], 'beat_id': b['beat_id'], 'body_start': plan['start'],
                         'body_end': plan['end'], 'chart_ids': plan['chart_ids'],
                         'chart_units': [j['unit'] for j in actual], 'authored': True, 'encoded_full_scene': False})

tech = read(OUT / 'checks/preview_technical.json')
for item in tech['clips'] + tech['frames'] + [tech['combined_preview']]:
    track(item['path'], item['sha256'])
track(ROOT / tech['contact_sheet'])
for p in (OUT / 'project/preview').glob('*.html'):
    track(p)
for p in (OUT / 'reusable_assets').glob('baseline_gyosan_*s.png'):
    track(p)
offline = read(EP / 'narration/production-v1/offline_verification.json')
for name, expected in offline['source_sha256'].items():
    track(EP / 'narration/production-v1' / name, expected)
check('offline_22_receipt', len(offline['checks']) == 22 and all(c['result'] == 'passed' for c in offline['checks']), 'receipt only, no rerun or synthesis')
manifest_path = EP / 'narration/production-v1/manifest.json'
manifest = read(manifest_path)
decision = read(EP / 'outputs/production-v1-budget/budget_decision.json')
track(manifest_path, decision['artifact_hashes']['narration_manifest'])
check('offline_manifest_script', manifest['script_sha256'] == d['metadata']['script_sha256'], 'approved v3')
check('offline_manifest_beat_coverage', ids == [b['beat_id'] for b in manifest['paragraphs']], '39 narration paragraphs')
for b in manifest['paragraphs']:
    track(EP / 'narration/production-v1' / b['path'], b['sha256'])
check('budget_pending', decision['id'] == '5fe307eed02c' and decision['status'] == 'pending', 'no authorization applied')
for p in [EP / 'brief.json', EP / 'state.json', EP / 'scenes.json', OUT / 'qa_request.json',
          OUT / 'checks/preview_technical.json', OUT / 'checks/timeline_validation.json',
          OUT / 'checks/hyperframes_check.json', OUT / 'checks/input_versions.json',
          OUT / 'project/beat_manifest.json', OUT / 'project/timing_resolved.json',
          OUT / 'project/index.html', OUT / 'project/frame.md', OUT / 'project/assembly_plan.json',
          EP / 'narration/production-v1/offline_verification.json',
          EP / 'narration/production-v1/offline_preflight.json',
          EP / 'outputs/production-v1-budget/budget_decision.json', Path(__file__)]:
    track(p)
receipt = {'task_id': 'RPR-PROD1-PREVIEW-QA', 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
           'status': 'pass' if not failures else 'fail', 'scope': '동결 소규모 CSV→JSON/기존 수치 QA의 SHA 재사용·제작 구성·오프라인 영수증 검증. 원거래 재계산/음성 생성/새 렌더 없음.',
           'counts': dict(checks), 'failures': failures, 'tables': tables, 'authored_coverage': coverage,
           'prior_math_verifier_sha256': prior['verifier_sha256'], 'inputs': inputs,
           'reuse_limits': '이전 검산 영수증의 필드만 비교. 수치 허용오차 abs=1e-9, rel=1e-12 유지. 정확한 거래일은 이전 검산 범위 밖이므로 현재 CSV 보존만 확인.',
           'new_api_calls': 0, 'paid_calls': 0, 'new_research': False, 'raw_trade_recompute': False,
           'new_png_or_video': 0, 'continuous_playback': 'unchecked', 'actual_listening': 'unchecked'}
(QA / 'input_verification.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': receipt['status'], 'checks': sum(checks.values()), 'inputs': len(inputs), 'tables': tables, 'failures': failures}, ensure_ascii=False))
