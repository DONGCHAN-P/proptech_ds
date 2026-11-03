from pathlib import Path
import json, shutil

e=Path(__file__).resolve().parent
p=e/'state.json'
backup=e/'state_before_v6_normalization.json'
if not backup.exists():
    shutil.copy2(p, backup)
s=json.loads(p.read_text(encoding='utf-8'))
s['previous_delivery_v3']={k:s.get(k) for k in [
    'video_path','actual_video_duration_seconds','delivery_revision','qa_scope',
    'delivery_status','delivery_authorization_status','actual_credits_used']}
s.update(requested_output='full_map_led_video_v6', facts_revision='map-led-v5+alternatives-v5+outside-comparisons-v6',
         caption_revision='semantic-v4-provider-character-aligned', caption_count=269,
         target_shot_count=48, audio_status='audio-v2_generated_decoded_and_original_character_aligned',
         new_voice_generated=True, actual_credits_used=2751, additional_cash_usd=0,
         video_path=None, actual_video_duration_seconds=None, delivery_revision='video-review-v6_pending',
         delivery_status='editing_awaiting_internal_visual_gate',
         delivery_authorization_status='local_review_production_authorized; new_media_transmission_not_requested',
         current_render_target='outputs/video-review-v6/namyangju-map-led_v6.mp4', render_process_session=None,
         qa_scope='audio_source_alignment_and_intro_proof_verified; full_v6_render_pending',
         music_revision='owned_data_city_ambient_v1_intro_outro_ducked',
         builtin_gpt_images_generated_this_revision=0,
         image_gap_resolution='approved_fact_map_status_panel_fallback; no_new_generation',
         completed_gate_approved_for_v6=False, pre_upload_gate_approved_for_v6=False)
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'state':'v6_current_fields_normalized','previous_snapshot_preserved':True}))
