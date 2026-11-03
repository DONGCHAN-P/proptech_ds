"""Apply the verified measured brand EDL to the common scene timeline."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
source = EP / 'outputs/private-production-v1'
edl = read(source / 'assembly_edl.json')
qa = read(HERE / 'edl_review.json')
assert qa['edl_sha256'] == sha(source / 'assembly_edl.json')
assert qa['subtitles_sha256'] == sha(source / 'captions_measured.srt')
assert qa['checked_cues'] == 150 and qa['tail_after_last_speech_s'] >= 3
scenes = read(EP / 'scenes.json')
for scene in scenes['scenes']:
    start, end = scene['chapter_local_start_s'], scene['chapter_local_end_s']
    offsets = [o for o in edl['offset_map'] if o['chapter'] == scene['chapter'] and start >= o['local_start_s'] - 1e-6 and end <= o['local_end_s'] + 1e-6]
    assert len(offsets) == 1, scene['scene_id']
    offset = offsets[0]['global_offset_s']
    scene.update(start_s=start + offset, end_s=end + offset,
                 global_offset_s=offset, timing_basis='actual_native_PCM_and_verified_brand_EDL',
                 status='content_approved_global_measured_source_integration')
save(EP / 'scenes.json', scenes)
state = read(EP / 'state.json')
state.update(timing_status='global_measured_EDL_verified', film_seconds=edl['total_seconds'], updated_at=datetime.now(timezone.utc).isoformat())
save(EP / 'state.json', state)
preflight = read(EP / 'director/episode_preflight.json')
preflight.update(status='measured_audio_source_integration')
preflight['baseline']['audio_revision'] = 'production-injoon-v2'
preflight['change_control']['single_timing_lock'] = 'narration/production-injoon-v2/final_timing.json'
preflight['qa'].update(semantic_caption_original_text_match='passed_all150_source_and_SRT',
    last_speech_plus_three_seconds='passed_3.020208s', caption_display_mapping_and_numeric_value_match='passed_source_mapping',
    evidence_paths=['director/production-v1/edl_review.json'])
save(EP / 'director/episode_preflight.json', preflight)
print(json.dumps({'scenes':len(scenes['scenes']), 'film_seconds':edl['total_seconds'], 'timing':'global_measured_EDL_verified'}))
