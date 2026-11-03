from pathlib import Path
import json

e=Path(__file__).resolve().parent
lock=json.loads((e/'editor/map-led-production-v6/timing_lock.json').read_text(encoding='utf-8'))
p=e/'scenes.json'; data=json.loads(p.read_text(encoding='utf-8'))
narration={n['scene_id']:n for n in lock['narration']}
assert len(lock['shots'])==48
for scene in data['scenes']:
    n=narration[scene['scene_id']]
    shots=[x for x in lock['shots'] if x['scene_id']==scene['scene_id']]
    start=min(x['from_frame'] for x in shots)
    end=max(x['from_frame']+x['duration_frames'] for x in shots)
    scene.update(start_frame=start,end_frame=end,start=start/30,end=end/30,start_s=start/30,end_s=end/30,
                 narration_start_frame=n['from_frame'], narration_end_frame=n['from_frame']+n['duration_frames'],
                 shot_ids=[x['shot_id'] for x in shots],
                 asset_ids=sorted({a for x in shots for a in x.get('asset_ids',[])}),
                 status='rendering_v6')
data.update(revision='scenes-map-led-v6-visual-and-audio-locked',status='rendering_v6',shot_count=48)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'))
s.update(stage='rendering_map_led_v6',current_review_render_status='rendering',
         render_revision='video-v6-map-led', render_process_session=8361,
         internal_full_render_gate='qa/map-led-v6/proof_gate.json',
         delivery_status='rendering_v6')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'scene_visual_ranges_locked':11,'shots':48,'full_render_started':True}))
