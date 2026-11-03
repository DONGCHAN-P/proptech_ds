from pathlib import Path
import json

e = Path(__file__).resolve().parent
lock = json.loads((e/'editor/map-led-production-v6/timing_lock.json').read_text(encoding='utf-8'))
p = e/'scenes.json'
data = json.loads(p.read_text(encoding='utf-8'))
by_id = {item['scene_id']: item for item in lock['narration']}
assert len(by_id) == len(data['scenes']) == 11
assert lock['source_script_sha256'] == 'd816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'
for scene in data['scenes']:
    item = by_id[scene['scene_id']]
    assert scene['audio_sha256'] == item['sha256']
    start, end = item['from_frame'], item['from_frame'] + item['duration_frames']
    scene.update(start_frame=start, end_frame=end, start=start/30, end=end/30,
                 start_s=start/30, end_s=end/30, fps=30,
                 timing_basis='provider_original_character_alignment; decoded_PCM_ceil_to_30fps; editor_timing_lock',
                 status='timing_locked_visual_edit')
data.update(revision='scenes-map-led-v6-frame-locked', status='timing_locked_visual_edit',
            duration_frames=lock['duration_frames'], fps=30,
            actual_video_timing='editor/map-led-production-v6/timing_lock.json',
            planned_video_duration_s=lock['duration_frames']/30,
            lead_in_frames=45, outro_tail_frames=270)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
p = e/'state.json'
state = json.loads(p.read_text(encoding='utf-8'))
state.update(stage='timing_locked_map_led_edit', timing_revision='timing-lock-v6-original-character-alignment',
             editor_revision='map-led-production-v6', visual_revision='map-led-v6',
             planned_video_duration_seconds=lock['duration_frames']/30,
             planned_video_duration_frames=lock['duration_frames'],
             actual_credits_used_v2=2751, approval_event='output/video_decisions/inbox/718066296.json',
             current_review_render_status='not_rendered_awaiting_internal_visual_gate',
             current_review_video_path=None)
p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'scenes': 11, 'video_frames': lock['duration_frames'], 'video_seconds': lock['duration_frames']/30}))
