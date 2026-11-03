"""Freeze the director's reviewed v3 draft and its aggregate evidence, offline."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from notify import video_decisions

EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/script-review-v3'
HISTORY = ROOT / 'analysis/housing_growth_2006/full_history_v1'
ALL = ROOT / 'analysis/housing_growth_2006/full_transactions_v1'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return p.relative_to(ROOT).as_posix()


script_hash = sha(OUT / 'script_v3.md')
qa_path = EP / 'qa/full-history-v1/final_recheck_v3.json'
qa = read(qa_path)
assert qa.get('current_script_sha256', qa.get('checked_revision', {}).get('script_sha256')) == script_hash
assert qa.get('required_open_issue_count', qa.get('required_fix_count', qa.get('required_count'))) == 0, 'Required draft issues remain'
claude = read(OUT / 'collaboration/claude_execution_receipt.json')
assert claude['exit_code'] == 0 and not claude['is_error']
assert claude['requested_effort'] == 'max'
assert any('claude-opus' in m for m in claude['actual_model_usage'])
assert claude['script_input_sha256'] == sha(OUT / 'script_v3_before_review.md')
structure = read(OUT / 'structure_checks.json')
assert structure['script_sha256'] == script_hash
assert structure['all_paragraphs_have_explicit_visual_source_status_alternative']

# Apply the QA-provided wording corrections to new record versions only.
metadata_issue = next(f for f in qa['findings'] if f['issue_id'] == 'FHQA-R01')
corrected = {}
for item in metadata_issue['evidence']['exact_repair_locations']:
    source = ROOT / item['path']
    if source not in corrected:
        corrected[source] = {'data': read(source), 'pointers': []}
    node = corrected[source]['data']
    parts = item['json_pointer'].strip('/').split('/')
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    node[parts[-1]] = item['replacement']
    corrected[source]['pointers'].append(item['json_pointer'])
correction_receipt = {'issue_id': 'FHQA-R01', 'at_utc': NOW, 'scope': 'wording_only_new_record_versions_old_records_unchanged', 'records': []}
for source, info in corrected.items():
    target = OUT / (source.stem + '_corrected_v2.json')
    write(target, info['data'])
    correction_receipt['records'].append({'original': rel(source), 'original_sha256': sha(source),
        'corrected': rel(target), 'corrected_sha256': sha(target), 'changed_json_pointers': info['pointers']})
write(OUT / 'metadata_correction_record.json', correction_receipt)

# A new decision refers only to this concrete script version; it grants no approval.
decision_file = OUT / 'script_decision.json'
if decision_file.exists():
    decision = read(decision_file)
    assert decision['artifact_hashes']['script_v3.md'] == script_hash
else:
    decision = video_decisions.create(
        EP.name, 'script',
        '지역별 가격 회복 대본 v3: 2006년 이후 보유 7지역 전체 유효거래와 전체 기간 회복 분석. '
        f'대본 SHA256 {script_hash}. 대본 검토만 해당하며 유료 생성·완성·게시 승인은 별도.')
    decision.update(artifact_hashes={'script_v3.md': script_hash}, script_revision='v3',
                    artifact_path=rel(OUT / 'script_v3.md'))
    video_decisions.write(video_decisions.STORE / 'decisions' / f'{decision["id"]}.json', decision)
    write(decision_file, decision)

# Preserve older state and verification records rather than rewriting their history.
state = read(EP / 'state.json')
if state.get('script_revision') != 'v3':
    write(OUT / 'episode_state_before_v3.json', state)
state.update(
    stage='script_v3_review_draft',
    script_revision='v3', script_file=rel(OUT / 'script_v3.md'), script_sha256=script_hash,
    script_status='codex_v3_with_claude_editorial_review_independent_qa_not_user_approved',
    updated_at=NOW,
    research_status='2006-2026Q2 full valid transaction statistics plus full supported matched-index history; official-index crosscheck and causal tests pending',
    collection_status_file='raw/rtms_trade_expansion/additional_20261023/batch_status.json',
    collection_snapshot_file='raw/rtms_trade_expansion/additional_20261023/snapshot.json',
    collection_not_yet_integrated=True,
    script_decision_id=decision['id'],
    claude_collaboration={
        'requested_model': 'opus', 'requested_effort': 'max',
        'cli_subscription_reported': 'pro', 'status': 'editorial_review_completed',
        'payload_authorized': True, 'actual_generated_text': True,
        'actual_model_usage': claude['actual_model_usage'],
        'reviewed_script_sha256': claude['script_input_sha256'],
        'receipt': rel(OUT / 'collaboration/claude_execution_receipt.json'),
        'integration_record': rel(OUT / '검토반영.md')},
    qa_file=rel(qa_path), audio_status='not_generated_for_v3', timing_locked=False,
    budget_status='no_paid_voice_image_video_generation_authorized',
    pre_upload_status='not_authorized', telegram_delivery_receipt=None,
    delivery_verification=None)
for item in ['qa/full-history-v1/findings.json', 'qa/full-history-v1/recheck_v3.json',
             'qa/full-history-v1/final_recheck_v3.json']:
    if item not in state.setdefault('qa_history', []):
        state['qa_history'].append(item)
write(EP / 'state.json', state)

decisions = read(EP / 'decisions.json')
new = [
    {'id': 'regional-full-history-v3-20261023', 'status': 'authorized_draft_scope_only',
     'basis': 'User requested full available transaction history since2006 and further collection',
     'scope': 'Preserve v1/v2/raw. Full valid-transaction statistics and full-history peaks/drawdowns/first-return episodes. No production approval.',
     'script_sha256': script_hash, 'script_decision_id': decision['id']},
    {'id': 'regional-claude-payload-v3-20261023', 'status': 'explicitly_authorized',
     'basis': 'User reply: 새 집계·대본의 Claude 전달 승인',
     'scope': '2006-2026Q2 seven-region aggregate packet and v3 draft to Claude Opus effort=max; no individual trades or credentials',
     'prompt_sha256': claude['prompt_sha256'], 'execution_status': 'completed'},
    {'id': 'additional-regions-20261023', 'status': 'authorized_running',
     'scope': 'Gwangju old-five-district geography, Ulsan, Chungbuk, Chungnam; 200601-202609; known-call cap8000 per day; no automated next-day restart',
     'boundary_review': 'Retired/parent district codes remain separate until dedup/geography checks',
     'implementation_fix': 'Atomic status write retries transient Windows reader-lock PermissionError; regression tests passed'}]
existing = {x['id'] for x in decisions['decisions']}
decisions['decisions'] += [dict(x, created_at=NOW) for x in new if x['id'] not in existing]
write(EP / 'decisions.json', decisions)

pre = read(EP / 'episode_preflight_v2.json')
pre.update(status='script_v3_preflight_filled_not_production_approval', updated_at=NOW)
pre['baseline']['script_revision'] = 'v3'
pre['approvals']['topic'].update(decision_id='regional-full-history-v3-20261023', status='authorized_research_and_draft_scope')
pre['approvals']['script'].update(decision_id=decision['id'], artifact_hashes={'script_v3.md': script_hash}, status='pending_version_specific_review')
pre['story']['opening_question'] = '집은 오래 들면 오른다, 그 오래는 몇 년일까?'
pre['story']['each_section_answers'] = ['all_valid_price_and_volume', 'matched_price_change', 'full_supported_history', 'peak_to_first_return', 'sample_and_boundary_scope']
pre['representative_previews'] = ['whole_transaction_price_vs_matched_index', 'full_2006_six_region_history', 'completed_vs_censored_recovery', 'CTA_outro_boundary']
pre['facts_required'] = ['all_valid_vs_matched_subset', '2006_to_2026Q2_price_endpoint', 'sejong_early_cache_vs2015_matching', 'running_peak_first_return_and_censoring', 'recent_window_sensitivity_not_alltime_ATH', 'factor_scope_and_fixed_boundaries', 'official_index_crosscheck_before_public_release']
pre['qa'].update(evidence_paths=['qa/full-history-v1/independent_recompute.json', 'qa/full-history-v1/recheck_v3.json', 'qa/full-history-v1/final_recheck_v3.json', 'outputs/script-review-v3/structure_checks.json'],
                 required_open_issues='Draft scoped required issues closed; public-release official-index crosscheck remains; no audio/video QA')
pre['release']['telegram_notice_receipt'] = None
write(EP / 'episode_preflight_v3.json', pre)

snapshot = read(ROOT / 'raw/rtms_trade_expansion/additional_20261023/snapshot.json')
write(OUT / 'collection_snapshot_at_delivery.json', snapshot)
paths = {
    '대본_v3.md': OUT / 'script_v3.md',
    '낭독대본_v3.txt': OUT / 'narration_v3.txt',
    '화면설계_v3.md': OUT / 'visual_storyboard.md',
    '분석기준과_변경점.md': OUT / '분석기준과_변경점.md',
    '클로드검토_원문.md': OUT / 'claude_review_v3.md',
    '검토반영.md': OUT / '검토반영.md',
    '수집현황_전달시점.json': OUT / 'collection_snapshot_at_delivery.json',
    '검수/최종대본검수.json': qa_path,
    '검수/구조확인.json': OUT / 'structure_checks.json',
    '검수/클로드실행영수증.json': OUT / 'collaboration/claude_execution_receipt.json',
    '검수/기록문구_정정내역.json': OUT / 'metadata_correction_record.json',
    '검수/작성자_검증기록_정정본.json': OUT / 'validation_corrected_v2.json',
    '검수/작성자_영수증_정정본.json': OUT / 'verification_receipt_corrected_v2.json',
}
for p in [HISTORY / 'report.md', HISTORY / 'summary.csv', HISTORY / 'episodes.csv',
          HISTORY / 'chart_source.csv', HISTORY / 'annual_valid_volume.csv',
          HISTORY / 'full_history_six_regions_2006.png', HISTORY / 'full_history_sejong_2015.png',
          HISTORY / 'running_peak_drawdown_full_history.png']:
    paths['전체기간_지수와회복/' + p.name] = p
for p in [ALL / 'report.md', ALL / 'quarterly_all_valid_transactions.csv',
          ALL / 'quarterly_median_price_per_m2_six_regions_2006.png',
          ALL / 'quarterly_median_price_per_m2_sejong_cache_history.png']:
    paths['전체거래_가격분포/' + p.name] = p
manifest = {
    'created_at': NOW, 'script_revision': 'v3', 'script_sha256': script_hash,
    'script_decision_id': decision['id'], 'status': 'review_draft_not_approved',
    'qa_required_open': 0, 'actual_listening': False, 'continuous_playback': False,
    'files': {rel(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in paths.values()},
    'frozen_inputs': read(EP / 'qa/full-history-v1/recheck_v3.json')['checked_revision'],
    'collection_snapshot_asof': snapshot['checked_at'], 'extra_raw_in_price_analysis': False}
write(OUT / 'package_checks.json', manifest)
archive = OUT / '지역별_영상대본_v3_2006이후.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for name, p in paths.items():
        z.write(p, name)
    z.write(OUT / 'package_checks.json', '검수/패키지목록.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name, p in paths.items():
        assert z.read(name) == p.read_bytes()
write(OUT / 'archive_manifest.json', {'archive': rel(archive), 'bytes': archive.stat().st_size,
                                    'sha256': sha(archive), 'member_count': len(paths) + 1})

cfg = read(ROOT / 'config/video_shelf.json')
entry = next(e for e in cfg['entries'] if e['name'] == '지역별가격회복')
entry['status'] = '대본 v3 · 2006년 이후 전체 유효거래·전체 기간 회복 분석 · Claude Opus max 검토·독립 수치 검수 · 사용자 검토 초안 · 음성·영상 미제작. 대본보기.html은 이전 v1.'
entry['files'].update({
    '대본.md': rel(OUT / 'script_v3.md'), '낭독대본.txt': rel(OUT / 'narration_v3.txt'),
    '화면설계.md': rel(OUT / 'visual_storyboard.md'), '분석기준.md': rel(OUT / '분석기준과_변경점.md'),
    '수치근거.md': rel(OUT / '분석기준과_변경점.md'), '클로드협업.md': rel(OUT / '검토반영.md'),
    '클로드검토.md': rel(OUT / 'claude_review_v3.md'),
    '이전대본_v2.md': rel(EP / 'outputs/script-review-v2/script_v2.md'),
    '전체거래_가격흐름.png': rel(ALL / 'quarterly_median_price_per_m2_six_regions_2006.png'),
    '전체거래_계산표.csv': rel(ALL / 'quarterly_all_valid_transactions.csv'),
    '전체거래_분석.md': rel(ALL / 'report.md'),
    '전체기간_지수흐름.png': rel(HISTORY / 'full_history_six_regions_2006.png'),
    '전체기간_낙폭.png': rel(HISTORY / 'running_peak_drawdown_full_history.png'),
    '전체기간_회복분석.md': rel(HISTORY / 'report.md'),
    '전체기간_회복구간.csv': rel(HISTORY / 'episodes.csv'),
    '검토자료_v3.zip': rel(archive)})
write(ROOT / 'config/video_shelf.json', cfg)
print(json.dumps({'script_sha256': script_hash, 'required_open': 0, 'script_decision_id': decision['id'],
                  'archive_bytes': archive.stat().st_size, 'archive_members': len(paths) + 1}, ensure_ascii=False))
