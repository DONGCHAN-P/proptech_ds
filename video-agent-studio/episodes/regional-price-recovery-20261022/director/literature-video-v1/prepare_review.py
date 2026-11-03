"""Publish a local, versioned literature-video draft without starting production."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[5]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/literature-video-v1'
HERE = Path(__file__).parent

def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

state_path = EP / 'state.json'
state = read(state_path)
if not (HERE / 'state_before.json').exists():
    write(HERE / 'state_before.json', state)

protected_path = HERE / 'protected_inputs.json'
if not protected_path.exists():
    protected = {
        'reports/서울 경기 집값 격차의 복합 원인.md': '8c8ba9faff955bcd7f6085f80f822d3267cc071dde0f03a18b6a8c1ee398d492',
        state['script_file']: state['script_sha256'],
        state['production_review_video']: state['production_render']['video_sha256'],
        'config/current_video.json': sha(ROOT / 'config/current_video.json'),
    }
    write(protected_path, protected)
protected = read(protected_path)
for name, expected in protected.items():
    assert sha(ROOT / name) == expected, f'Protected input changed: {name}'

script_path = OUT / '내레이션_초안.md'
script = script_path.read_text(encoding='utf8')
scenes_path = OUT / '장면표.json'
scenes = read(scenes_path)
claims = read(OUT / '인용근거.json')
claim_ids = {claim['id'] for claim in claims['claims']}
narration_chars = 0
for scene in scenes['scenes']:
    pattern = rf"## {scene['scene_id']} · [^\n]+\n\n### 낭독\n\n(.*?)\n\n### 화면·근거"
    match = re.search(pattern, script, re.S)
    assert match, scene['scene_id']
    scene['narration_text'] = match.group(1).strip()
    scene['script_revision'] = scenes['script_revision']
    scene['audio_revision'] = None
    scene['timing_basis'] = scenes['timing_basis']
    assert all(claim_id in claim_ids for claim_id in scene['claim_ids'])
    assert scene['start'] is None and scene['end'] is None
    narration_chars += len(scene['narration_text'])
assert len(scenes['scenes']) == 8
write(scenes_path, scenes)

data = ROOT / 'analysis/housing_growth_2006/full_history_v1'
with (data / 'summary.csv').open(encoding='utf-8-sig', newline='') as stream:
    rows = {r['region']: r for r in csv.DictReader(stream)}
assert rows['서울']['max_drawdown_first_return_quarter'] == '2024Q3'
assert rows['서울']['max_drawdown_peak_quarter'] == '2021Q4'
assert rows['경기']['all_time_high_last_quarter'] == '2021Q4'
assert round(float(rows['경기']['latest_vs_all_time_high_pct']), 1) == -4.1
with (data / 'chart_source.csv').open(encoding='utf-8-sig', newline='') as stream:
    price_rows = {(r['region'], r['quarter']): r for r in csv.DictReader(stream)}
assert float(price_rows['서울', '2024Q3']['source_index']) > float(price_rows['서울', '2021Q4']['source_index'])
for region in ('서울', '경기'):
    assert rows[region]['price_start_quarter'] == '2006Q1'
    assert rows[region]['price_end_quarter'] == '2026Q2'
example = next(c for c in claims['claims'] if c['id'] == 'E02')
assert example['inputs']['completed'] - example['inputs']['removed_a'] == example['results']['net_a']
assert example['inputs']['completed'] - example['inputs']['removed_b'] == example['results']['net_b']

now = datetime.now(timezone.utc).isoformat()
decision_id = 'regional-literature-script-v1-20261023'
request = {
    'task_id': decision_id,
    'user_request': '내용이 좀 많은데 좋은 내용들이 많네, 이 근거들을 인용해서 영상을 만들어보고싶어',
    'scope': 'Local literature-cited video treatment, narration draft, scene and citation ledger; version-specific script review before production',
    'prior_inputs': protected,
    'local_only_delivery_for_this_draft': True,
    'paid_generation': False,
    'voice_generation': 'user_hold_preserved',
    'created_at': now,
}
write(HERE / 'request.json', request)
artifact_names = ['영상구성안.md', '내레이션_초안.md', '인용근거.json', '장면표.json']
artifacts = {name: {'path': (OUT / name).relative_to(ROOT).as_posix(), 'sha256': sha(OUT / name), 'bytes': (OUT / name).stat().st_size} for name in artifact_names}
qa_path = EP / 'qa/literature-video-v1/recheck.json'
qa_verified = None
if qa_path.exists():
    qa = read(qa_path)
    assert all(qa['summary'][key] == 0 for key in ('critical_open', 'required_open', 'recommended_open'))
    for name, expected in qa['checked_revision'].items():
        assert sha(OUT / name) == expected, f'QA revision mismatch: {name}'
    qa_verified = {'path': qa_path.relative_to(ROOT).as_posix(), 'sha256': sha(qa_path), 'critical_open': 0, 'required_open': 0, 'recommended_open': 0, 'scope': 'Narration and treatment text review plus changed-paragraph recheck; media unreviewed'}

verification = {
    'at_utc': now,
    'protected_inputs_unchanged': True,
    'scene_count': 8,
    'citation_source_count': len(claims['sources']) - 1,
    'own_dataset_count': 1,
    'all_scene_claim_ids_resolve': True,
    'narration_characters_with_spaces': narration_chars,
    'target_runtime_minutes': [8, 10],
    'actual_runtime_measured': False,
    'own_numeric_claims_checked_against_csv': True,
    'example_arithmetic_checked': True,
    'local_mechanism_causal_analysis_executed': False,
    'voice_generated': False,
    'video_rendered': False,
    'telegram_sent_by_this_task': False,
    'continuous_playback_performed': False,
    'actual_listening_performed': False,
    'artifacts': artifacts,
    'independent_qa': qa_verified,
}
write(OUT / 'verification.json', verification)

preflight = read(ROOT / 'video-agent-studio/templates/episode_preflight.json')
preflight.update(status='literature_video_v1_draft_preflight_not_production_approval', episode_id=state['episode_id'])
preflight['baseline']['previous_video'] = read(ROOT / 'config/current_video.json')
preflight['baseline']['script_revision'] = 'literature-video-v1-draft'
preflight['approvals']['topic'].update(status='direct_user_authorized_literature_adaptation_scope', decision_id=decision_id)
preflight['approvals']['script'].update(status='pending_version_specific_review', decision_id=decision_id)
preflight['approvals']['script']['artifact_hashes'] = {'내레이션_초안.md': sha(script_path)}
preflight['approvals']['budget'].update(status='voice_generation_deferred_by_user', cash_cap=0, automatic_retry_allowed=False)
preflight['story'].update(opening_question='인구가 줄거나 새집이 늘어도 왜 지역별 집값은 다르게 움직일까?', order=[s['scene_id'] for s in scenes['scenes']], each_section_answers=['claim', 'evidence', 'scope', 'what_to_compare'], candidate_scope='literature_interpretation_not_local_causal_attribution')
preflight['representative_previews'] = ['household_split', 'relocation_timeline', 'commuting_concept']
preflight['facts_required'] = ['paper_population_period_outcome', 'observational_or_conditional_identification', 'example_labels', 'own_index_definition_and_period', 'synthesis_vs_own_results']
preflight['qa']['evidence_paths'] = [(OUT / 'verification.json').relative_to(ROOT).as_posix()]
if qa_verified:
    preflight['qa']['script_text_review'] = qa_verified
write(EP / 'episode_preflight_literature_video_v1.json', preflight)

state.update(
    stage='literature_video_draft_v1_script_review_pending',
    next_script_status='literature_video_v1_draft_not_approved',
    next_script_file=script_path.relative_to(ROOT).as_posix(),
    next_script_sha256=sha(script_path),
    next_script_decision_id=decision_id,
    literature_video_plan=(OUT / '영상구성안.md').relative_to(ROOT).as_posix(),
    literature_video_claims=(OUT / '인용근거.json').relative_to(ROOT).as_posix(),
    literature_video_scenes=scenes_path.relative_to(ROOT).as_posix(),
    current_direction='Literature-cited explanatory episode: household composition, redevelopment relocation gaps, commuting and job connections; observed price paths provide context, no local causal attribution',
    content_status='new_literature_based_draft_pending_review_prior_chart_recitation_superseded_as_direction',
    new_render_authorized_at_this_stage=False,
    updated_at=now,
)
if qa_verified:
    state['literature_video_text_qa'] = qa_verified
assert state['budget_status'] == 'voice_generation_deferred_by_user'
write(state_path, state)
decisions_path = EP / 'decisions.json'
decisions = read(decisions_path)
entries = decisions['decisions']
entry = {'id': decision_id, 'status': 'draft_ready_user_script_review_pending', 'basis': request['user_request'], 'scope': request['scope'], 'artifact_hashes': {name: value['sha256'] for name, value in artifacts.items()}, 'independent_text_qa': qa_verified, 'local_delivery': True, 'voice_hold_preserved': True, 'created_at': now}
old = next((i for i, d in enumerate(entries) if d.get('id') == decision_id), None)
if old is None:
    entries.append(entry)
else:
    entries[old] = entry
write(decisions_path, decisions)

shelf_path = ROOT / 'config/video_shelf.json'
shelf = read(shelf_path)
entry = next(e for e in shelf['entries'] if e['workspace'] == EP.relative_to(ROOT).as_posix())
entry['status'] = '논문 인용형 영상 구성·대본 초안 v1 · 새 대본 검토 대기 · 실거래 인과분석 미실행 · 음성 생성 보류 · 기존 영상 보존'
for alias, name in [('논문영상_구성안.md', '영상구성안.md'), ('논문영상_대본.md', '내레이션_초안.md'), ('논문영상_장면표.json', '장면표.json'), ('논문영상_인용근거.json', '인용근거.json')]:
    entry['files'][alias] = (OUT / name).relative_to(ROOT).as_posix()
if qa_verified:
    entry['files']['논문영상_검수.json'] = qa_verified['path']
write(shelf_path, shelf)
print(json.dumps({'status': state['stage'], 'artifacts': len(artifacts), 'scenes': 8, 'literature_sources': 6, 'narration_characters': narration_chars, 'protected_unchanged': True}, ensure_ascii=False))
