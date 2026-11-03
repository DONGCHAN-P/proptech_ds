from pathlib import Path
import json,shutil
e=Path(__file__).resolve().parent
plan=json.loads((e/'writer/map-led-v4/scene_plan.json').read_text(encoding='utf-8'))
audio=json.loads((e/'narration/alignment_manifest_v2.json').read_text(encoding='utf-8'));byid={c['scene_id']:c for c in audio['chapters']}
p=e/'scenes.json';backup=e/'scenes_previous_script_v2_preserved.json'
if not backup.exists():shutil.copy2(p,backup)
cursor=0
for scene in plan['scenes']:
 a=byid[scene['scene_id']];scene.update(script_revision='script-v4-hook-outside',audio_revision='audio-v2',audio_file=a['file'],audio_sha256=a['sha256'],alignment_file=a['alignment_file'],pcm_duration_s=a['pcm_duration_s'],narration_relative_start_s=cursor,narration_relative_end_s=cursor+a['pcm_duration_s'],start=None,end=None,start_s=None,end_s=None,timing_basis='provider_original_character_alignment_and_decoded_pcm; absolute_video_frames_pending_editor_lock',status='voice_locked_visual_edit')
 cursor+=a['pcm_duration_s']
plan.update(episode_id=e.name,revision='scenes-map-led-v6-audio-locked',status='voice_locked_visual_edit',audio_revision='audio-v2',new_tts_generated=True,new_images_generated=False,actual_narration_duration_s=cursor,actual_video_timing='pending_intro_leadin_and_outro_tail_frame_lock')
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'scenes':len(plan['scenes']),'narration_duration_s':cursor,'previous_scenes_preserved':True}))
