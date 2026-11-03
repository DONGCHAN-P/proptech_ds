from pathlib import Path
import json
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-preview'); fs=json.loads((q/'findings.json').read_text(encoding='utf-8'))
for f in fs:f['status']='fixed_in_project_pending_mp4';f['evidence']['recheck']='input_check.py rerun: 166 cues, zero numeric boundary candidates'
fs.append({'issue_id':'QAV6-003','scene_id':'M005','timecode':'proof_detail representative still','severity':'recommended','문제':'상세지도 하단 고등학교(고2) 면이 부분 크롭됨; 현재 발화 대상 초6·유6은 온전함','evidence':'outputs/production-v6-preview/proof_detail.png actual view_image; central map lower-right edge','수정안':'발화 비대상 고2 라벨을 생략하거나 상세지도 범위/범례를 조절','owner':'editor_v6','status':'open','checked_revision':'proof_detail.png'})
(q/'findings.json').write_text(json.dumps(fs,ensure_ascii=False,indent=2),encoding='utf-8')
(q/'still_review.json').write_text(json.dumps({'file':'outputs/production-v6-preview/proof_detail.png','actual_visual_inspection':True,'type':'Remotion representative still; not final MP4','scene_id':'M005','checks':{'S4_locator_and_detail_match':True,'school6_kindergarten6_visible':True,'scheduled_vs_target_distinct':True,'subtitle_title_source_unclipped':True},'limitations':['one still only','unspoken high-school parcel partly cropped','continuous playback and audio not checked']},ensure_ascii=False,indent=2),encoding='utf-8')
print('Representative still evidence recorded')
