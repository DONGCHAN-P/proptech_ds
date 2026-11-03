"""Track a narrow pronunciation revision without expanding the paid budget."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
review_path = EP / 'qa/audio-v1/review.json'
review = read(review_path)
lock = read(HERE / 'locked_script.json')
assert review['script_sha256'] == lock['script_sha256'] and not review['approved']
assert {i['id'] for i in review['required_issues']} == {'ASR-A2-NUM-001', 'ASR-A2-TERM-001'}
issue = {
    'id': 'affordable-price-audio-clarity-v3', 'gate':'internal_QA', 'status':'targeted_revision_preparation',
    'script_sha256':lock['script_sha256'], 'affected_scene_ids':['S014','S019','S024','S030'],
    'issue_ids':['ASR-A2-NUM-001','ASR-A2-TERM-001'],
    'basis':'Two-model local ASR leaves three amounts and two DSR uses ambiguous. No actual hearing error is asserted. Preserve approved display text, financial meaning and values; clarify reading only.',
    'prior_audio':'narration/production-injoon-v2', 'planned_audio':'narration/production-injoon-v3',
    'reuse_unchanged_paragraphs':41, 'new_free_TTS_calls_cap':4, 'paid_TTS_authorized':False,
    'cash_cap_krw':0, 'automatic_retry':False, 'generation_status':'requires_main_exact_prepared_plan_instruction',
    'review_path':review_path.relative_to(EP).as_posix(),
    'review_sha256':hashlib.sha256(review_path.read_bytes()).hexdigest(),
    'at_utc':datetime.now(timezone.utc).isoformat()}
path = HERE / 'audio_clarity_revision_v3.json'
assert not path.exists()
save(path, issue)
state = read(EP / 'state.json')
state.update(stage='targeted_audio_clarity_revision', voice_stage='four_paragraph_phonetic_plan_pending',
    timing_status='v2_measured_preserved_new_revision_pending', updated_at=issue['at_utc'])
save(EP / 'state.json', state)
decisions = read(EP / 'decisions.json')
assert not any(d['id'] == issue['id'] for d in decisions['decisions'])
decisions['decisions'].append(issue)
save(EP / 'decisions.json', decisions)
plan = read(HERE / 'plan.json')
plan['current_stage'] = state['stage']
for step in plan['steps']:
    if step['id'] == 'voice_timing': step['status'] = 'targeted_phonetic_revision_required_four_paragraphs'
    if step['id'] == 'source_audio_QA': step['status'] = '150_caption_text_glyph_pass_audio2_required_open'
save(HERE / 'plan.json', plan)
queue = read(ROOT / 'config/video_production_queue_20261026.json')
next(i for i in queue['items'] if i['episode'] == EP.name)['status'] = state['stage']
save(ROOT / 'config/video_production_queue_20261026.json', queue)
print(json.dumps({'revision':issue['id'], 'affected_paragraphs':4, 'unchanged':41, 'cash_cap_krw':0}))
