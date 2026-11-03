from pathlib import Path
import json, shutil
e=Path(__file__).resolve().parent
lock=json.loads((e/'editor/landuse-full-v8/timing_lock_final.json').read_text(encoding='utf-8'))
assert lock['total_frames']==26720 and lock['body_offset_frames']==398
path=e/'scenes.json'
backup=e/'outputs/video-review-v8/scenes_before_final_timing.json'
if not backup.exists(): shutil.copy2(path,backup)
data=json.loads(backup.read_text(encoding='utf-8'))
audio={x['scene_id']:x for x in lock['narration']}
for scene in data['scenes']:
    sid=scene['scene_id']
    if sid not in audio: continue
    item=audio[sid]
    scene['previous_content_anchor']={k:scene[k] for k in ('start_frame','end_frame','start_s','end_s') if k in scene}
    start=0 if sid=='M000' else scene['start_frame']+398
    end=917 if sid=='M000' else scene['end_frame']+398
    scene.update(start_frame=start,end_frame=end,start_s=start/30,end_s=end/30,
        narration_start_frame=item['from_frame'],narration_end_frame=item['from_frame']+item['duration_frames'],
        script_revision='script-v6-series-cta',audio_revision=item['audio_revision'],
        timing_basis='decoded_PCM_ceil_30fps; final_v8_lock; original_character_alignment',status='timing_locked_pending_final_render')
    if sid=='M000':
        scene.update(narration_text=(e/'outputs/story-review-v6/M000_series_hook.txt').read_text(encoding='utf-8'),
            title='전편에서 왕숙으로, 다음 창릉과 교산',
            message='전편 실제 화면과 후속편 구독 안내를 거쳐 왕숙 지도·입주 달력 질문으로 연결한다.',
            material_types=['vector_motion','previous_episode_video','landuse_diagram'],
            visual_instruction='outputs/intro-review-v9/README.md; actual rendered reference-matched vector intro',
            narration_relative_start_s=0,narration_relative_end_s=29.04)
data.update(revision='scenes-landuse-v8-series-hook-v6-timing-locked',status='timing_locked_pending_final_render',source_script='outputs/story-review-v6/script_v6.md',audio_revision='series-hook-v6+audio-v2-body',timing_lock='editor/landuse-full-v8/timing_lock_final.json',brand_intro=lock['brand_intro'],brand_outro=lock['brand_outro'],duration_frames=26720)
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
p=e/'state.json'; s=json.loads(p.read_text(encoding='utf-8'))
s.update(planned_video_duration_seconds=lock['duration_s'],planned_video_duration_frames=26720,caption_count=275,caption_revision='semantic-v6-hook-and-v4-body-character-aligned',opening_review_video='outputs/intro-review-v9/namyangju-intro_v9.mp4',opening_video_sha256='e6b9de272d1ea53e39e43d6d51ccaf10afebe32e95fef37259aa2f893602ca03',timing_lock='editor/landuse-full-v8/timing_lock_final.json',stage='v8_final_source_gate_pending',full_render_waiting_for='final_source_and_brand_boundary_gate')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print('Final 26720-frame timeline recorded; source gate and actual final MP4 remain pending.')
