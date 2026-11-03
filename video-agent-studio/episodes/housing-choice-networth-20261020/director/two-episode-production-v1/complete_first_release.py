"""Record completion only after the actual private upload and caption processing pass."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
OUT=EP/'outputs/private-release-v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

record=read(OUT/'upload_receipt.json');job=read(OUT/'upload_job.json')
assert record['private_verified'] and record['verification']['status']['privacyStatus']=='private'
assert record['verification']['processingDetails']['processingStatus']=='succeeded'
assert record['caption_serving_verified'] and record['caption_status']=='serving'
assert not record['verification']['status'].get('publishAt')
assert sha(ROOT/job['video'])==job['sha256']
dual=read(OUT/'dual_media_review.json')
assert dual['video_sha256']==job['sha256'] and dual['required_open']==dual['critical_open']==[]
assert all(dual[r]['approved'] for r in ['codex','claude'])
url='https://www.youtube.com/watch?v='+record['video_id']
now=datetime.now(timezone.utc).isoformat()
summary={'status':'private_uploaded_processed_with_Korean_captions','url':url,'video_id':record['video_id'],
         'video_sha256':job['sha256'],'subtitles_sha256':job['subtitles_sha256'],
         'visibility':'private','scheduled':False,'reviewers':['Codex','Claude Opus effort=max'],
         'known_required_open':[],'free_TTS':'ko-KR-InJoonNeural','paid_TTS_calls':0,
         'caption_cues':206,'body_seconds':1510.2666666666664,'film_seconds':1525.2666666666664,
         'actual_listening':False,'continuous_playback':False,'Studio_ContentID_review':False,
         'review_scope':'Actual sampled encoded frames, complete source/SRT/timing checks, full decode, ASR and signal evidence.',
         'verified_at_utc':now}
save(OUT/'completion.json',summary)
(OUT/'private_upload_status.md').write_text(
    '# 매매·전세·월세와 자산\n\n'
    f'YouTube 비공개: {url}\n\n'
    '25분 25초 · 1920×1080 · 무료 한국어 TTS · 의미 단위 자막 206개\n\n'
    'Codex와 Claude가 해당 버전의 검수 증거를 확인했습니다. 알려진 필수 수정 사항은 없습니다. '
    '실제 비공개 상태와 영상 처리 완료, 한국어 자막 트랙 제공 상태를 조회했습니다.\n\n'
    '검수 범위: 실제 인코딩 표본 프레임, 전체 자막·원문·타이밍, 전체 디코드, 로컬 음성 인식과 음량 신호 분석. '
    '직접 청취·연속 재생·Studio Content ID 확인은 수행하지 않았습니다.\n',encoding='utf-8')
state=read(EP/'state.json')
state.update(stage='private_uploaded_verified',updated_at=now,completed_status='exact_version_dual_review_passed',
             pre_upload_status='private_upload_completed_by_direct_user_authorization',private_upload=summary,
             limitations=['Actual listening, continuous playback and Studio Content ID review not performed.'])
state['free_tts_production'].update(status='private_uploaded_verified',
    final_timing='narration/free-tts-v1/caption-v7/final_timing.json',caption_cues=206,
    final_video=job['video'],subtitles=job['subtitles'],final_dual_review=rel(OUT/'dual_media_review.json'))
state['claude_collaboration']='actual_script_and_exact_final_media_reviews_passed'
state['growth_supplement'].update(integrated_into_video=True,narration='free_InJoon_completed',user_script_approval='current_direct_user_production_instruction')
state['cost_wording']['integrated_into_video']=True
save(EP/'state.json',state)
preflight=read(HERE/'episode_preflight.json')
preflight['status']='private_upload_complete_with_declared_review_coverage'
for gate in ['completed','pre_upload']:
    decision=read(OUT/('completed_decision.json' if gate=='completed' else 'pre_upload_decision.json'))
    preflight['approvals'][gate].update(status='current_version_condition_satisfied',decision_id=decision['id'],
        artifact_hashes={'video_sha256':job['sha256'],'subtitles_sha256':job['subtitles_sha256']})
preflight['qa'].update(timeline_font_bbox_and_stroke_all_cases='passed_current_source_and_encoded_samples',
    actual_encoded_frames='passed_declared_samples',all_cut_boundaries_no_flash='passed_declared_EDL_boundary_samples',
    semantic_caption_original_text_match='passed_all206',protected_numbers_units_names='passed_all206',
    caption_box_exceptions='passed_brand_and_CTA_samples',last_speech_plus_three_seconds='passed_3.019251s',
    full_decode='passed_video_and_audio',caption_display_mapping_and_numeric_value_match='passed',
    required_open_issues=0,evidence_paths=[job['dual_review'],rel(OUT/'release_validation.json'),
        rel(EP/'qa/private-production-v1/source_v7_pass_receipt.json'),rel(HERE/'edl_review_v7.json')])
for key in ['inset_matches_spoken_region','station_locations','leaders_do_not_cross','actual_block_plan_and_locator','district_area_vs_planned_station_distinguished']:
    preflight['qa'][key]='not_applicable_to_new_financial_comparison_content; existing_reference_assets_preserved'
preflight['release'].update(longform=job['video'],title_description_sources_chapters='dual_review_passed',
    thumbnail='dual_review_passed',actual_platform_privacy='private_verified',processing='succeeded',
    Korean_caption_track='serving_verified',studio_copyright='unchecked',telegram_notice_receipt=None)
preflight['change_control'].update(single_timing_lock='narration/free-tts-v1/caption-v7/final_timing.json',
    package_frozen_before_hash=True,unchanged_audio_reused=True)
save(HERE/'episode_preflight.json',preflight)
decisions=read(EP/'decisions.json')
for name in ['completed_decision.json','pre_upload_decision.json']:
    d=read(OUT/name)
    if not any(x['id']==d['id'] for x in decisions['decisions']):decisions['decisions'].append(d)
save(EP/'decisions.json',decisions)
queue=read(ROOT/'config/video_production_queue_20261026.json')
queue['items'][0].update(status='private_uploaded_verified',private_upload=summary)
queue['items'][1]['status']='ready_after_first_private_upload'
save(ROOT/'config/video_production_queue_20261026.json',queue)
shelf=read(ROOT/'config/video_shelf.json')
for entry in shelf['entries']:
    if entry['workspace']==rel(EP):
        entry['status']='양측 검수 통과 / 무료 음성·자막 완성 / YouTube 비공개 업로드·처리 확인'
        entry['files'].update({'영상.mp4':job['video'],'자막.srt':job['subtitles'],
            '현재대본.md':state['script_path'],'비공개_업로드.md':rel(OUT/'private_upload_status.md'),
            '썸네일.png':job['thumbnail']})
save(ROOT/'config/video_shelf.json',shelf)
issue=read(HERE/'caption_revision_v7.json')
issue.update(status='closed_after_exact_final_dual_review',final_video_sha256=job['sha256'],
             final_subtitles_sha256=job['subtitles_sha256'],dual_review=rel(OUT/'dual_media_review.json'))
save(HERE/'caption_revision_v7.json',issue)
closed={'id':'CAPTION-MEANING-001-closed-caption-v7','gate':'qa','status':'closed',
        'issue_id':'CAPTION-MEANING-001','video_sha256':job['sha256'],
        'subtitles_sha256':job['subtitles_sha256'],'dual_review':rel(OUT/'dual_media_review.json'),
        'at_utc':now}
if not any(x['id']==closed['id'] for x in decisions['decisions']):
    decisions['decisions'].append(closed)
    save(EP/'decisions.json',decisions)
print(json.dumps({'first_episode':'completed_private_only','url':url,'next_episode':'ready'},ensure_ascii=False))
