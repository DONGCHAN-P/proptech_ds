from pathlib import Path
import json,hashlib
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];R=EP/'research/annual-map-v2';O=EP/'outputs/map-preview-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(Q/'independent_checks.json');v=read(R/'validation.json');p=read(R/'map_packet_v2.json');h=read(R/'handoff.json');all_rep=0
for c in p['complexes']:
 over=None
 for y in p['years']:
  st=c['years'][str(y)]['status']
  if st=='over':over=y
  elif st=='under' and over is not None:all_rep+=1;over=None
assert v['adjacent_year_over_to_under']==374 and v['all_observed_over_to_under_reappearances']==all_rep==528
assert 'mapped_over_to_under_reappearances' not in v
assert h['adjacent_year_over_to_under']==374 and h['all_observed_over_to_under_reappearances']==528
for f in h['outputs']:assert sha(ROOT/f['path'])==f['sha256']
assert sha(R/'map_packet_v2.json')==r['packet_sha256'] and sha(O/'style_preview_6s.mp4')==r['video_sha256']
r.update(actual_frames_viewed=True,all_observed_over_to_under_reappearances=all_rep,validation_sha256=sha(R/'validation.json'),modeled_ui_samples_viewed=['393x852_cover','768x1024_cover','375x812_contain'])
(Q/'independent_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
finding={'issue_id':'MPV2-001','scene_id':'validation_metadata','timecode':'시안 전체','severity':'required','문제':'374건은 연속연도 전환인데 전체 재등장처럼 부르는 필드명','evidence':['validation.json의 수정된 두 지표','handoff.json','통합검토결과.md'],'수정안':'인접연도374와 미거래경유포함528로 구별','owner':'data','status':'closed_metadata_verified','checked_revision':sha(R/'validation.json')}
(Q/'findings.json').write_text(json.dumps({'required_open_count':0,'critical_open_count':0,'findings':[finding]},ensure_ascii=False,indent=2),encoding='utf8')
final={'revision':'map-preview-v2','scope':'6초 로컬 통합 시안 독립검수. 전체 본편·승인 게이트 아님.','preview_review_ready':True,'local_review_ready':True,'required_open_count':0,'critical_open_count':0,'full_video_review_ready':False,'full_video_rendered':False,'video_file':str(O/'style_preview_6s.mp4'),'sha256':r['video_sha256'],'packet_file':str(R/'map_packet_v2.json'),'packet_sha256':r['packet_sha256'],'validation_sha256':sha(R/'validation.json'),'frame_count':180,'duration_s':6,'width':1080,'height':1920,'fps':30,'audio_streams':0,'exact_10eok_group_count':174,'adjacent_year_over_to_under':374,'all_observed_reappearances':528,'native_5179_used_directly':True,'independent_proj_checked':False,'draw_candidates':8288,'unlinked':884,'actual_encoded_frames_viewed':[0,59,60,119,120,179],'bbox_checked_count':48,'label_anchor_pip_count':5,'safe_config_sha256':r['safe_config_sha256'],'actual_listening':False,'continuous_playback':False,'actual_device_playback':False,'source_limits':['2025공간자료와미연결884개·행정코드시차 유지','전체수도권최신거래전수완결 보증 아님','실제시안3개연도만표본열람,21년데이터검증과구별'],'evidence':['independent_checks.json','encoded_contact.jpg','통합검토결과.md','findings.json'],'new_api_requests':0,'paid_generation':False,'external_transmission':False,'media_modified':False}
(Q/'final_review.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf8')
handoff={'status':'v2 통합 시안 독립검수 완료','next_owner':'director','outputs':[str(Q/'final_review.json'),str(Q/'통합검토결과.md'),str(Q/'independent_checks.json'),str(Q/'findings.json')],'required_open_count':0,'critical_open_count':0,'preview_review_ready':True,'full_video_review_ready':False,'video_sha256':r['video_sha256'],'packet_sha256':r['packet_sha256'],'pending':'전체 숏폼은 대본·제작·완료·게시 단계 및 새 최종검수 별도','actual_listening':False,'continuous_playback':False}
(Q/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'preview_ready':True,'video_sha256':r['video_sha256'],'packet_sha256':r['packet_sha256'],'required_open_count':0}))
