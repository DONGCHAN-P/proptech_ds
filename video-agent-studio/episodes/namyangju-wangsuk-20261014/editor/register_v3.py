from pathlib import Path
import json
e=Path(__file__).resolve().parent.parent
project=json.loads((e.parents[2]/'video/src/namyangju-v2/project.json').read_text(encoding='utf-8'))
p=e/'scenes.json';scenes=json.loads(p.read_text(encoding='utf-8'))
scenes['revision']='scenes-motion-v3';scenes['shot_plan']='writer/shot_plan_video_v2.json';scenes['shot_bindings']='visual/shot_asset_binding_v2.json'
for s in scenes['scenes']:
 shots=[x for x in project['shots'] if x['chapter_id']==s['scene_id']]
 s['shot_ids']=[x['shot_id'] for x in shots]
 s['asset_ids']=sorted({a for x in shots for a in x['binding']['asset_ids']})
 s['visual_revision']='visual-v5';s['editor_revision']='motion-v3';s['status']='rendering_v3';s['timing_basis']='approved_audio_v1_decoded_pcm_frame_timeline'
p.write_text(json.dumps(scenes,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(render_revision='video-v3-in-progress',editor_revision='motion-v3',render_process_session=81880,current_render_target='editor/render_v3/namyangju-wangsuk_v3.mp4',previous_review_video='outputs/video-review-v1/namyangju-wangsuk_v1.mp4',v2_qa='qa/quality_full_v2_review.json',delivery_status='v3_rendering_before_full_qa',telegram_progress_v3_sent=True);p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print('registered 62 bound shots and v3 render state')
