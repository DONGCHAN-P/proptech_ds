"""Record a finished private episode only after processing and captions verify."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--release-dir', default='outputs/private-release-v1')
parser.add_argument('--source-dir', default='outputs/private-production-v1')
parser.add_argument('--timing', default='narration/production-injoon-v2/final_timing.json')
args = parser.parse_args()
out = (EP / args.release_dir).resolve()
source = (EP / args.source_dir).resolve()
assert out.is_relative_to(EP) and source.is_relative_to(EP)
assert not (out / 'completion.json').exists(), 'Completion already recorded; preserve it.'
record = read(out / 'upload_receipt.json')
job = read(out / 'upload_job.json')
dual = read(out / 'dual_media_review.json')
timing_path = (EP / args.timing).resolve()
assert timing_path.is_relative_to(EP)
timing = read(timing_path)
edl = read(source / 'assembly_edl.json')
lock = read(HERE / 'locked_script.json')
assert record['private_verified'] and record['verification']['status']['privacyStatus'] == 'private'
assert record['verification']['processingDetails']['processingStatus'] == 'succeeded'
assert record['caption_serving_verified'] and record['caption_status'] == 'serving'
assert not record['verification']['status'].get('publishAt')
assert sha(ROOT / job['video']) == job['sha256'] == dual['video_sha256']
assert sha(ROOT / job['subtitles']) == job['subtitles_sha256'] == dual['subtitles_sha256']
assert timing['script_sha256'] == lock['script_sha256'] == dual['script_sha256']
assert dual['required_open'] == dual['critical_open'] == []
assert all(dual[r]['approved'] and sha(ROOT / dual[r]['receipt']) == dual[r]['receipt_sha256'] for r in ['codex', 'claude'])
now = datetime.now(timezone.utc).isoformat()
url = 'https://www.youtube.com/watch?v=' + record['video_id']
cues = sum(len(ch['cues']) for ch in timing['chapters'])
summary = {
    'status': 'private_uploaded_processed_with_Korean_captions',
    'url': url, 'video_id': record['video_id'], 'video_sha256': job['sha256'],
    'subtitles_sha256': job['subtitles_sha256'], 'visibility': 'private', 'scheduled': False,
    'reviewers': ['Codex', 'Claude Opus effort=max'], 'known_required_open': [],
    'free_TTS': timing['voice']['name'], 'paid_TTS_calls': 0, 'cash_TTS_krw': 0,
    'caption_cues': cues, 'body_seconds': sum(ch['total_seconds'] for ch in timing['chapters']), 'film_seconds': edl['total_seconds'],
    'actual_listening': False, 'continuous_playback': False, 'Studio_ContentID_review': False,
    'review_scope': dual['coverage'], 'policy_as_of': '2026-10-26', 'verified_at_utc': now}
save(out / 'completion.json', summary)
duration = round(edl['total_seconds'])
(out / 'private_upload_status.md').write_text(
    '# 감당 가능한 매매 가격 계산\n\n'
    f'YouTube 비공개: {url}\n\n'
    f'{duration // 60}분 {duration % 60}초 · 1920×1080 · 무료 한국어 TTS · 의미 단위 자막 {cues}개\n\n'
    'Codex와 Claude의 해당 버전 검수에서 필수 수정 사항을 모두 해소했습니다. '
    '실제 비공개 상태, 영상 처리 완료, 한국어 자막 제공 상태를 조회했습니다.\n\n'
    '검수 범위: 실제 인코딩 표본 프레임, 전체 자막·원문·타이밍, 전체 디코드, 로컬 음성 인식과 음량 신호 분석. '
    '직접 청취·연속 재생·Studio Content ID 확인은 수행하지 않았습니다.\n', encoding='utf-8')
state = read(EP / 'state.json')
state.update(stage='private_uploaded_verified', updated_at=now, completed_status='exact_version_dual_review_passed',
             pre_upload_status='private_upload_completed_by_direct_user_authorization', private_upload=summary,
             voice_stage='free_TTS_captioned_private_uploaded', editor_stage='final_encoded_dual_review_passed',
             final_video=job['video'], subtitles=job['subtitles'],
             limitations=['Actual listening, continuous playback and Studio Content ID review not performed.'])
state['last_decision_id'] = read(out / 'pre_upload_decision.json')['id']
save(EP / 'state.json', state)
scenes = read(EP / 'scenes.json')
for scene in scenes['scenes']:
    scene.update(status='reviewed_final_private_upload_complete', final_video_sha256=job['sha256'])
save(EP / 'scenes.json', scenes)
preflight = read(EP / 'director/episode_preflight.json')
preflight['status'] = 'private_upload_complete_with_declared_review_coverage'
preflight['baseline']['audio_revision'] = timing['audio_revision']
for gate in ['completed', 'pre_upload']:
    decision = read(out / (gate + '_decision.json'))
    preflight['approvals'][gate].update(status='current_version_condition_satisfied', decision_id=decision['id'],
        artifact_hashes={'video_sha256': job['sha256'], 'subtitles_sha256': job['subtitles_sha256']})
preflight['qa'].update(required_open_issues=0, full_decode='passed_audio_and_video',
    semantic_caption_original_text_match=f'passed_all{cues}', protected_numbers_units_names=f'passed_all{cues}',
    actual_encoded_frames='passed_declared_samples', continuous_playback_performed=False,
    actual_listening_performed=False,
    timeline_font_bbox_and_stroke_all_cases='passed_exact_source_and_declared_encoded_samples',
    all_cut_boundaries_no_flash='passed_declared_boundary_samples',
    caption_box_exceptions='passed_brand_and_CTA_samples',
    last_speech_plus_three_seconds='passed_verified_EDL_3.020208s',
    caption_display_mapping_and_numeric_value_match='passed_all_source_SRT_and_declared_encoded_samples',
    evidence_paths=[job['dual_review'], rel(out / 'release_validation.json')])
for key in ['inset_matches_spoken_region','station_locations','leaders_do_not_cross',
            'actual_block_plan_and_locator','district_area_vs_planned_station_distinguished']:
    preflight['qa'][key] = 'not_applicable_financial_case_episode'
preflight['release'].update(longform=job['video'], title_description_sources_chapters='dual_review_passed',
    thumbnail='dual_review_passed', actual_platform_privacy='private_verified', processing='succeeded',
    Korean_caption_track='serving_verified', studio_copyright='unchecked')
preflight['change_control'].update(single_timing_lock=timing_path.relative_to(EP).as_posix(),
    package_frozen_before_hash=True, unchanged_audio_reused=False)
save(EP / 'director/episode_preflight.json', preflight)
decisions = read(EP / 'decisions.json')
for name in ['completed_decision.json', 'pre_upload_decision.json']:
    decision = read(out / name)
    if not any(d['id'] == decision['id'] for d in decisions['decisions']):
        decisions['decisions'].append(decision)
clarity = read(HERE / 'audio_clarity_revision_v3.json')
assert clarity['status'] == 'closed_by_independent_current_voice_evidence'
closure_id = 'affordable-price-audio-clarity-v3-closed'
if not any(d['id'] == closure_id for d in decisions['decisions']):
    decisions['decisions'].append({'id':closure_id, 'gate':'internal_QA', 'status':'closed',
        'issue_ids':['ASR-A2-NUM-001','ASR-A2-TERM-001'],
        'evidence':clarity['evidence'], 'evidence_sha256':clarity['evidence_sha256'],
        'final_dual_review':rel(out / 'dual_media_review.json'), 'at_utc':now})
save(EP / 'decisions.json', decisions)
plan = read(HERE / 'plan.json')
plan['current_stage'] = 'private_uploaded_verified'
for step in plan['steps']:
    step['status'] = 'completed_with_exact_version_evidence'
plan['completion'] = rel(out / 'completion.json')
save(HERE / 'plan.json', plan)
queue = read(ROOT / 'config/video_production_queue_20261026.json')
next(i for i in queue['items'] if i['episode'] == EP.name).update(status='private_uploaded_verified', private_upload=summary)
queue['status'] = 'both_private_uploads_verified'
save(ROOT / 'config/video_production_queue_20261026.json', queue)
shelf = read(ROOT / 'config/video_shelf.json')
for entry in shelf['entries']:
    if entry['workspace'] == rel(EP):
        entry['status'] = '양측 검수 통과 / 무료 음성·자막 완성 / YouTube 비공개 업로드·처리 확인'
        entry['files'].update({'영상.mp4': job['video'], '자막.srt': job['subtitles'],
            '현재대본.md': lock['script_path'], '비공개_업로드.md': rel(out / 'private_upload_status.md'),
            '썸네일.png': job['thumbnail']})
save(ROOT / 'config/video_shelf.json', shelf)
print(json.dumps({'status': 'completed_private_only', 'url': url, 'cues': cues}, ensure_ascii=False))
