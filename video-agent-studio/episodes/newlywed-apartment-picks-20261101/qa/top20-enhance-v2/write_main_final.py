"""실제로 검수한 인코딩 표본과 독립 실행 증거를 최종 파일 해시에 연결한다."""
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path

EP=Path('C:/projects/realestate_reco/video-agent-studio/episodes/newlywed-apartment-picks-20261101')
Q=EP/'qa/top20-enhance-v2';ED=EP/'editor/top20-enhance-v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,o):(Q/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
v=read(Q/'final_evidence_manifest.json');r=read(ED/'render_receipt_main_v1.json');d=read(Q/'independent_full_decode.json')
source=read(Q/'caption_source_qa.json');c=read(Q/'content_timing_qa.json');recheck=read(Q/'EV2-C01_recheck.json')
t=read(EP/'director/top20-enhance-v2/locked_timing.json');freeze=read(ED/'source_freeze.json')
video=Path(v['video']);digest=sha(video)
assert digest==v['video_sha256']==r['output_sha256']==d['video_sha256']=='12b2221c246c1a10fb6e2c92750fbb4ca4d40b2195b721bef0afa2ee56bf28f5'
assert v['project_sha256']==r['project_sha256']==source['project_sha256']==freeze['project_sha256']=='f622ee9e8e8bfef7a61c3083528ede56ea4ce6375718923ce0ef5e4be7cd7323'
assert d['passed'] and d['exit_code']==0 and d['stderr_bytes']==0
assert not c['failed_checks'] and not source['failed_checks'] and all(recheck['checks'].values())
assert sha(EP/'director/top20-enhance-v2/locked_timing.json')==recheck['checked_revision']
assert r['audio_input_sha256']==c['checked_revision']['audio_sha256']==sha(ED/'main/assets/narration.wav')
assert all(b['all_three_present'] for b in v['boundary_coverage'])
assert len(v['existing_frames'])==125 and len(v['extra_long_caption_frames'])==28
assert sha(ED/'main/caption_mapping.json')==source['mapping_sha256']
sv=read(EP/'outputs/top20-enhance-v2/subtitle_verification.json');assert sha(sv['file'])==source['srt_sha256']
duration=float(v['probe']['format']['duration']);assert duration>480 and abs(duration-t['duration_s'])<1/30+.002
all_frames=v['existing_frames']+v['extra_long_caption_frames']
v['visual_inspection_status']='completed_sampled_contact_sheets_28_native_caption_rails_and4_full_resolution_details'
v['inspected_core_frame_count']=len(all_frames)
save('final_evidence_manifest.json',v)
scene_coverage=[]
for s in t['scenes']:
 rows=[f for f in v['existing_frames'] if s['start_s']-1e-7<=f['time_s']<s['end_s']-1e-7]
 longs=[f for f in v['extra_long_caption_frames'] if f['scene_id']==s['scene_id']]
 assert rows
 scene_coverage.append(dict(scene_id=s['scene_id'],start_s=s['start_s'],end_s=s['end_s'],
  encoded_manifest_indices=[f['manifest_index'] for f in rows],long_caption_evidence=[f['file'] for f in longs],
  sampled_visual_result='pass_no_confirmed_defect'))
detail_indices=[107,111,59,118]
detail=[dict(scene=f['expected_scene_at_request'],time_s=f['time_s'],path=f['file'],sha256=f['sha256'],view='full1920x1080')
        for f in v['existing_frames'] if f['manifest_index'] in detail_indices]
rail_sheets=[Q/'final-evidence'/f'caption-rails-{n:02d}.jpg' for n in range(1,5)]
for path in v['sheets']+[str(p) for p in rail_sheets]:assert Path(path).exists()

report=dict(task_id='top20-enhance-QA-v2',revision='enhanced-main-v1',status='passed_scoped_local_review',
 checked_at=datetime.now(timezone.utc).isoformat(),video=str(video),video_sha256=digest,
 duration_s=duration,bytes=video.stat().st_size,duration_over_480=True,
 critical_open=0,required_open=0,recommended_open=0,
 full_decode=True,full_decode_evidence=dict(path=str(Q/'independent_full_decode.json'),sha256=sha(Q/'independent_full_decode.json'),
  exit_code=0,stderr_bytes=0,video_frames=15850,audio='전체 AAC 오디오 스트림 디코드',
  limitation='디코드 성공은 실제 청취·연속 시청을 뜻하지 않음'),
 media=v['probe'],source_project_sha256=r['project_sha256'],render_receipt=str(ED/'render_receipt_main_v1.json'),
 scope=dict(delivery='로컬 검토본 본편만',all_29_scenes_sampled=True,scene_count=29,brand_segments=2,
  boundary_groups_including_opening=31,actual_transition_boundaries=30,all_boundary_before_first_next_samples=True,
  supplied_encoded_frames_inspected=125,independently_extracted_long_caption_frames_inspected=28,
  total_unique_encoded_frames_inspected=153,inspection_method='125장 및 추가28장의 전체프레임을640px폭 컨택트시트로 직접 확인;긴 자막28개는원본해상도 하단크롭으로확인;중요4장은전체1920x1080으로확인',
  caption_source_cues=157,caption_source_sentences=113,
  max_zoom='사진·지도 카메라 줌 없음.소스 scale는막대/연결선의0→1 scaleX이며컷직전최종상태를표본검수.',
  actual_listening=False,continuous_playback=False,pronunciation='unchecked',final_mix_loudness='unchecked',
  motion_smoothness='unchecked;컷직전/첫/다음표본의단절·플래시만검수',
  exact_browser_all_glyph_bbox='unchecked;실행권한과Brotli부재.최종인코딩장면별긴자막의실제잘림검수로보완',
  uploads='범위밖;업로드부재는차단아님',packaging='최종배포정리는총괄담당;ZIP은이번본편검수계약범위밖'),
 visual_results=dict(
  scene_and_cut='모든장면·브랜드 경계 표본에서잘못된이전장면복귀·빈플래시·자막잘림 미발견',
  caption_rail='본문 큐 사이흰레일유지,브랜드/마지막무음CTA레일숨김.추가28개긴자막 전체가박스내에읽힘.',
  N001='같은53개구/2024.11.1/전체·초혼 기준 명시.첫4위동일,동안22→16·6510쌍,마포21→17·6487쌍 일치.',
  N002='남동16→27·5588쌍,원미20→24·5982쌍,미추홀10→20·6162쌍 일치.',
  I002='전체차이59·초혼7634/6746/차이888·재혼733/1563/차이830의최종상태확인',
  layout='사진중심·인접비교·상위권목록세구도를실제인코딩에서확인.미공개상위행마스킹유지.',
  end_hold=dict(last_spoken_end_provider_s=t['last_spoken_end_s'],planned_outro_start_s=t['brand_outro']['start_s'],
   encoded_outro_first_frame_s=math.ceil(t['brand_outro']['start_s']*30)/30,
   measured_gap_from_provider_word_s=math.ceil(t['brand_outro']['start_s']*30)/30-t['last_spoken_end_s'],
   silent_hold_frame_s=517.1160204081633,white_caption_rail_visible=False,
   note='발화종료기준은제공자단어시각;실제청취로종료를확정하지않음')),
 audio_evidence=dict(input_audio_sha256=r['audio_input_sha256'],
  unchanged_original_PCM_frames=c['timing']['original_frames'],splice_prefix_equal=c['timing']['prefix_equal'],
  splice_suffix_equal=c['timing']['suffix_equal'],added_PCM_frames=c['timing']['added_frames'],
  added_provider_word_counts=c['timing']['new_word_mapping'],
  evidence=str(Q/'content_timing_qa.json'),metadata_fix_evidence=str(Q/'EV2-C01_recheck.json'),
  parent_ASR=str(EP/'director/top20-enhance-v2/evidence/audio-asr/summary.json'),
  ASR_scope='추가N001/N002 숫자대조.초혼/재혼 철자차이만으로 발음오류/자연스러움 확정안함.',
  dry_level_evidence=str(EP/'director/top20-enhance-v2/evidence/audio_levels.json'),
  dry_level_scope='총괄이제공한S022/N001/N002/C001 dry PCM peak/RMS기록을읽음;QA가재측정하거나최종믹스를청취한것아님',
  actual_listening=False),
 evidence=dict(manifest=str(Q/'final_evidence_manifest.json'),manifest_sha256=sha(Q/'final_evidence_manifest.json'),
  decoded_contact_sheets=v['sheets'],caption_rail_sheets=[str(p) for p in rail_sheets],full_resolution_details=detail,
  content_timing=str(Q/'content_timing_qa.json'),caption_source=str(Q/'caption_source_qa.json'),
  representatives=str(Q/'representatives_review.json'),source_freeze=str(ED/'source_freeze.json')),
 scene_coverage=scene_coverage,boundary_coverage=v['boundary_coverage'],findings=[],
 limitations=['실제청취·전구간연속재생미실시','153개표본프레임검수는전체15850프레임시각검사를뜻하지않음','기술·표본·내용검수범위의로컬검토본통과'])
motion_dir=EP/'director/top20-enhance-v2/evidence/motion'
motion=read(motion_dir/'manifest.json');assert motion['video_sha256']==digest
report['supplemental_motion']=dict(scene_id='S013',times_s=motion['times_s'],sample_count=9,
 strip_path=str(motion_dir/'count_reveal_strip.jpg'),strip_sha256=sha(motion_dir/'count_reveal_strip.jpg'),
 manifest_path=str(motion_dir/'manifest.json'),manifest_sha256=sha(motion_dir/'manifest.json'),
 independently_viewed=True,result='파란막대가단계적으로자라8483/16000수준에서242.4초이후유지.비교8473막대고정.9개표본에서overshoot/도약미발견.',
 limitation='9장정지표본의모션상태비교이며연속재생·실제청취아님')
report['scope']['core_encoded_frames_inspected']=153
report['scope']['supplemental_motion_frames_inspected']=9
report['scope']['total_unique_encoded_frames_inspected']=162
save('main_final.json',report)
f=read(Q/'findings.json')
for x in f['findings']:
 x['reported_revision']=x.get('reported_revision',x['checked_revision']);x['checked_revision']=digest
 x['status']='closed_verified' if x['issue_id']!='EV2-B05' else 'closed_accepted_design'
 x['resolution_evidence']=str(Q/'main_final.json')
 if x['issue_id']=='EV2-B05':x['resolution']='훅은10쌍차이의구체적발견,결말은사진+세비교질문의일관된구도로해결.아이콘배치는권장사항으로대체수용.'
f['final_video_sha256']=digest;f['critical_open']=0;f['required_open']=0
save('findings.json',f)
save('issue_FINAL_QA_HANDOFF.json',dict(issue_id='EV2-FINAL-QA-HANDOFF',recipients=['director','editor'],
 scene_id='all29_and30cuts',문제='범위명시최종독립검수통과',evidence=str(Q/'main_final.json'),
 제안='동일SHA의로컬검토본으로납품통합가능',영향='critical0/required0;청취·연속재생false를납품문구에도유지',
 video_sha256=digest,main_final_sha256=sha(Q/'main_final.json'),direct_message_sent=False))
save('handoff.json',dict(task_id='top20-enhance-QA-v2',status='final_scoped_QA_passed',
 artifacts=[str(Q/n) for n in ['main_final.json','findings.json','final_evidence_manifest.json','independent_full_decode.json','issue_FINAL_QA_HANDOFF.json']],
 input_revision=dict(video_sha256=digest,project_sha256=r['project_sha256'],timing_sha256=recheck['checked_revision']),
 final_QA_sha256=sha(Q/'main_final.json'),final_QA_frozen=True,
 verified=['전체비디오·오디오독립decode','125장컷/장면/브랜드표본+추가28장긴자막','N001/N002/I002최종값·마지막무음레일','불변수치/PCM/provider매핑검수연결'],
 unresolved=[],limitations=report['limitations'],affected_scenes=v['scene_ids'],next_owner='director:로컬검토본납품통합'))
out=read(Q/'main_final.json');assert out['video_sha256']==sha(video) and out['critical_open']==out['required_open']==0 and out['full_decode']
print(json.dumps(dict(status=out['status'],video_sha256=digest,duration_s=duration,critical_open=0,required_open=0,
 inspected_core_frames=153,supplemental_motion_frames=9,main_final_sha256=sha(Q/'main_final.json'),scene_count=29,actual_listening=False,continuous_playback=False,path=str(Q/'main_final.json')),ensure_ascii=False))
