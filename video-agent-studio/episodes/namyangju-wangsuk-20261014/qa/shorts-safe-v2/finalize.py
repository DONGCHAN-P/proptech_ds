import json,hashlib
from pathlib import Path
Q=Path(__file__).resolve().parent;E=Q.parents[1];O=E/'outputs/shorts-safe-v2'
checks=json.loads((Q/'independent_checks.json').read_text(encoding='utf8'))
assert len(checks)==3
manifest=json.loads((O/'manifest.json').read_text(encoding='utf8'))
for r in checks:
 assert hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()==r['sha256']
 assert all(c['overlaps']==0 for c in r['device_matrix'])
 assert r['whole_decode_pass'] and r['audio_packets_identical'] and r['srt_bytes_identical']
 m=next(m for m in manifest if m['id']==r['id']);assert m['sha256']==r['sha256'];r['source_frame_range']=m['source_frame_range']
findings=json.loads((Q/'findings.json').read_text(encoding='utf-8-sig'))
assert all(f['status']=='closed_verified' for f in findings)
review=dict(revision='shorts-safe-v2 final',expected_mp4_count=3,actual_mp4_count=len(list(O.glob('*_safe_v2.mp4'))),files=checks,required_open_count=0,critical_open_count=0,local_review_ready=True,actual_device_playback=False,actual_listening=False,continuous_playback=False,device_matrix_coverage=dict(viewport_count=9,fit_modes=['contain','cover'],cases_per_file=18,total_cases=54,ui_model='header14%; footer35%; right actionrail64CSSpx',overlaps=0,scope='내부 보수 모형의 접힌 일반 UI 검사. 광고 safezone은 참고이며 일반 콘텐츠/모든 기기의 공식 보장이 아님.'),visual_coverage=dict(all_cue_start_contact_sheets_viewed=True,scene_boundaries='rail1149/1150; price825/826; choice755/756; actual PNG inspected',longest_cues='all3 actual encoded frames inspected',maximum_zoom='static plates; no animated zoom',extracted_boundary_frames=sum(len(r['sample_frames']) for r in checks),all_extracted_boundary_images_viewed=False),content_review=dict(price_median_samples_period_area=True,base_price_and_extra_cost=True,plan_vs_operation=True,copyright_credit=True,caption_no_clipping_in_viewed_samples=True,comparison_basis='approved v1 captions/source panels preserved; no new external factual research'),font_review=dict(title_px=44,caption_px=44,key_values_px='36..38',conditions_px=24,limitation='compact map embedded secondary labels are small; core target/values repeated separately. Small-screen legibility is sampled, not every-device guarantee.'),guide_reference=str(E/'editor/shorts-safe-v2/placement_guide.md'),zip=dict(expected=False,reason='MP4 3개 직접 납품; ZIP 요청 없음'))
assert review['actual_mp4_count']==3
(Q/'final_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf8')
handoff=dict(owner='video_qa',revision='shorts-safe-v2 final',input_versions=['published shorts-release-v1','cross-platform-safe-v1','editor shorts-safe-v2 final'],outputs=[str(Q/'final_review.json'),str(Q/'findings.json'),str(Q/'independent_checks.json')],verified=['실제 MP4 3개 SHA/크기/코덱/길이/프레임','독립 전체 decode','AAC packet hash 및 SRT bytes 동일','의미 큐 샘플/최장큐/중요 경계 실제 프레임','3편×18 UI모형 및 전체 source bbox'],unresolved=['실제 기기 앱 재생 미검수','실제 음성 청취/연속 재생 미검수'],affected_scenes=['M003','M007','M008'],next_owner='video_director',status='local_review_ready',publication_authorization_used=False)
(Q/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf8')
print('Final QA reports written; 3 files verified.')

