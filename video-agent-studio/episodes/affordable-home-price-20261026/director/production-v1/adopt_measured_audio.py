"""Adopt measured voice evidence without granting a render or release approval."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EP = Path(__file__).resolve().parents[2]
ROOT = EP.parents[2]
HERE = Path(__file__).parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

lock = read(HERE / 'locked_script.json')
folder = EP / 'narration/production-injoon-v2'
timing = read(folder / 'final_timing.json')
qa = read(folder / 'technical_validation.json')
assert timing['script_sha256'] == qa['script_sha256'] == lock['script_sha256']
assert not qa['required_technical_errors'] and qa['clipped_samples'] == 0
assert sha(folder / 'final_timing.json') == qa['final_timing_sha256']
assert qa['new_paragraphs'] == 45 and qa['actual_meaning_cues'] == 150
for chapter in qa['chapters']:
    assert sha(ROOT / chapter['audio_file']) == chapter['sha256']
proposals = read(EP / 'narration/timing_proposals_v2.json')
scenes = read(EP / 'scenes.json')
by_id = {s['scene_id']: s for s in proposals['scenes']}
assert len(scenes['scenes']) == len(by_id) == 45
for scene in scenes['scenes']:
    measured = by_id[scene['scene_id']]
    assert measured['chapter'] == scene['chapter']
    scene.update(chapter_local_start_s=measured['start_s'], chapter_local_end_s=measured['end_s'],
                 body_start_s=measured['body_start_s'], body_end_s=measured['body_end_s'],
                 audio_revision=timing['audio_revision'],
                 timing_basis='actual_native_and_PCM_chapter_local; global_EDL_pending',
                 status='content_approved_measured_voice_source_integration')
save(EP / 'scenes.json', scenes)
now = datetime.now(timezone.utc).isoformat()
state = read(EP / 'state.json')
state.update(stage='measured_audio_source_integration', script_revision='v2',
             audio_revision=timing['audio_revision'], timing_revision='native-v2',
             timing_status='measured_chapter_local_global_EDL_pending',
             voice_stage='generated_technical_pass_independent_ASR_pending',
             editor_stage='actual_voice_source_integration', updated_at=now,
             audio_seconds=qa['total_seconds'], actual_listening=False)
save(EP / 'state.json', state)
queue = read(ROOT / 'config/video_production_queue_20261026.json')
item = next(i for i in queue['items'] if i['episode'] == EP.name)
item.update(status=state['stage'], current_script=lock['script_path'])
save(ROOT / 'config/video_production_queue_20261026.json', queue)
plan = read(HERE / 'plan.json')
plan['current_stage'] = state['stage']
updates = {'facts': 'current_primary_delta_pass', 'script': 'v2_locked',
           'dual_content_review': 'both_approved_exact_v2',
           'voice_timing': 'generated_technical_pass_independent_ASR_pending',
           'visual_templates': 'readability_v2_pass_measured_integration'}
for step in plan['steps']:
    if step['id'] in updates:
        step['status'] = updates[step['id']]
save(HERE / 'plan.json', plan)
save(HERE / 'measured_audio_adoption.json', {
    'status': 'adopted_measured_source_inputs', 'at_utc': now,
    'script_sha256': lock['script_sha256'], 'timing_sha256': sha(folder / 'final_timing.json'),
    'technical_receipt_sha256': sha(folder / 'technical_validation.json'),
    'chapters': 10, 'paragraphs': 45, 'cues': 150, 'body_seconds': qa['total_seconds'],
    'actual_listening': False, 'independent_ASR': 'pending', 'full_render_authorized': False,
    'claude_optional_recommendations': 'No required content issues. Preserve approved script; use sourced labels for LTV context. Do not add unverified guarantee availability or recalculate cases on screen.'
})
print(json.dumps({'stage': state['stage'], 'paragraphs': 45, 'cues': 150, 'seconds': qa['total_seconds']}))
