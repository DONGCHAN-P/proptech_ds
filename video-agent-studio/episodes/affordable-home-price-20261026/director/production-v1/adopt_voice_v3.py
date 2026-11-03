"""Adopt the exact v3 voice only after its independent evidence gate passes."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
compact = lambda s: ''.join(s.split())
def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
parser = argparse.ArgumentParser()
parser.add_argument('--audio-review', required=True)
args = parser.parse_args()
audio_path = (ROOT / args.audio_review).resolve()
assert audio_path.is_relative_to(EP) and audio_path.is_file()
audio = read(audio_path)
assert audio.get('approved') is True or audio.get('audio_approved') is True
assert not audio.get('required_issues') and not audio.get('critical_issues')
timing_path = EP / 'narration/production-injoon-v3/final_timing.json'
timing = read(timing_path)
lock = read(HERE / 'locked_script.json')
assert timing['script_sha256'] == audio['script_sha256'] == lock['script_sha256']
assert (audio.get('final_timing_sha256') or audio.get('final_timing', {}).get('sha256')) == sha(timing_path)
source = read(EP / 'qa/source-media-v1/source_approval_v4.json')
assert source['source_approved'] and source['required'] == source['critical'] == []
edl = read(EP / 'outputs/private-production-v1/assembly_edl.json')
edl_qa = read(HERE / 'edl_review_v3.json')
assert edl['timing_sha256'] == sha(timing_path) == source['checked_revision']['timing_sha256']
assert edl_qa['edl_sha256'] == sha(EP / 'outputs/private-production-v1/assembly_edl.json')
scenes = read(EP / 'scenes.json')
assert len(scenes['scenes']) == 45
archive = HERE / 'common-before-voice-v3'
assert not archive.exists()
archive.mkdir()
for name in ['scenes.json','state.json']:
    (archive / name).write_bytes((EP / name).read_bytes())
body_offset = 0
for chapter in timing['chapters']:
    for scene in [s for s in scenes['scenes'] if s['chapter'] == chapter['chapter']]:
        cues = [c for c in chapter['cues'] if c['scene_id'] == scene['scene_id']]
        assert cues and compact(''.join(c['text'] for c in cues)) == compact(scene['narration_text'])
        start, end = min(c['start_s'] for c in cues), max(c['end_s'] for c in cues)
        matches = [o for o in edl['offset_map'] if o['chapter'] == chapter['chapter'] and start >= o['local_start_s'] - 1e-6 and end <= o['local_end_s'] + 1e-6]
        assert len(matches) == 1
        offset = matches[0]['global_offset_s']
        scene.update(chapter_local_start_s=start, chapter_local_end_s=end,
            body_start_s=body_offset+start, body_end_s=body_offset+end,
            start_s=start+offset, end_s=end+offset, global_offset_s=offset,
            spoken_text_actual=' '.join(c['spoken_text'] for c in cues),
            audio_revision='production-injoon-v3', timing_basis='actual_v3_native_PCM_verified_EDL',
            status='source_and_voice_evidence_passed_render_pending')
    body_offset += chapter['total_seconds']
save(EP / 'scenes.json', scenes)
now = datetime.now(timezone.utc).isoformat()
state = read(EP / 'state.json')
state.update(stage='exact_source_and_voice_passed_render_ready', audio_revision='production-injoon-v3',
    timing_revision='native-v3', timing_status='global_measured_EDL_v3_verified',
    voice_stage='independent_ASR_evidence_passed_unlistened', editor_stage='exact_visual_v4_source_passed',
    audio_seconds=body_offset, film_seconds=edl['total_seconds'], updated_at=now,
    current_audio_review=args.audio_review, actual_listening=False)
save(EP / 'state.json', state)
issue = read(HERE / 'audio_clarity_revision_v3.json')
issue.update(status='closed_by_independent_current_voice_evidence', evidence=args.audio_review,
    evidence_sha256=sha(audio_path), final_timing_sha256=sha(timing_path), actual_listening=False)
save(HERE / 'audio_clarity_revision_v3.json', issue)
queue = read(ROOT / 'config/video_production_queue_20261026.json')
next(i for i in queue['items'] if i['episode'] == EP.name)['status'] = state['stage']
save(ROOT / 'config/video_production_queue_20261026.json', queue)
preflight = read(EP / 'director/episode_preflight.json')
preflight['status'] = state['stage']
preflight['baseline']['audio_revision'] = 'production-injoon-v3'
preflight['change_control']['single_timing_lock'] = 'narration/production-injoon-v3/final_timing.json'
preflight['qa'].update(timeline_font_bbox_and_stroke_all_cases='passed_source_visual_v4',
    semantic_caption_original_text_match='passed_all150', protected_numbers_units_names='passed_declared_source_and_ASR_evidence',
    actual_listening_performed=False, continuous_playback_performed=False,
    evidence_paths=['qa/source-media-v1/source_approval_v4.json',args.audio_review,'director/production-v1/edl_review_v3.json'])
save(EP / 'director/episode_preflight.json', preflight)
save(HERE / 'voice_v3_adoption.json', {'status':state['stage'],'at_utc':now,
    'script_sha256':lock['script_sha256'],'timing_sha256':sha(timing_path),
    'audio_review_sha256':sha(audio_path),'source_review_sha256':sha(EP / 'qa/source-media-v1/source_approval_v4.json'),
    'body_seconds':body_offset,'film_seconds':edl['total_seconds'],'actual_listening':False,'media_approved':False})
print(json.dumps({'status':state['stage'],'scenes':45,'film_seconds':edl['total_seconds']}))
