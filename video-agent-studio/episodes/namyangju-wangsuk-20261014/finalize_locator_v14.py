"""Package the actual reviewed v14 media and create its completed gate only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,shutil,zipfile
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
o=e/'outputs/locator-timeline-v14';qroot=e/'qa/locator-timeline-v14'
full=o/'namyangju_locator_timeline_full_v14.mp4';srt=full.with_suffix('.srt')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
existing=o/'completed_decision.json'
if existing.exists():
 d=json.loads(existing.read_text(encoding='utf-8'))
 assert all(sha(e/path)==digest for path,digest in d['artifacts'].items())
 print(json.dumps({'completed_decision_id':d['id'],'status':'already_packaged_artifacts_verified'}));sys.exit(0)
q=json.loads((qroot/'final_review.json').read_text(encoding='utf-8'))
lock=json.loads((e/'timing_lock_v14.json').read_text(encoding='utf-8'))
assert q['sha256']==sha(full) and q['required_open_count']==0 and q['local_review_ready']
assert q['restriction_table_checked'] is True
assert q['video_frames']==lock['duration_frames']==27653
assert abs(q['duration_s']-lock['duration_s'])<.1
assert full.stat().st_size>1_000_000 and srt.stat().st_size>1000
h=json.loads((e/'narration/region-leaders-v7/handoff.json').read_text(encoding='utf-8'))
assert h['actual_credit_total']==616 and h['additional_cash_usd']==0
files=[(full,'video/'+full.name),(srt,'captions/'+srt.name),(e/'outputs/story-review-v7/script_v7.md','script/script_v7.md'),(e/'timing_lock_v14.json','timing_lock_v14.json'),(e/'narration/region-leaders-v7/handoff.json','checks/new_voice_handoff.json'),(e/'research/region-leaders-v14/price_map.json','sources/price_map.json'),(e/'research/region-leaders-v14/candidates.json','sources/candidates.json'),(e.parents[1]/'guides/지역_상세지도와_의미단위_자막.md','guides/지역_상세지도와_의미단위_자막.md')]
for name in ['final_review.json','detail_review.json','price_review.json','prefix_review.json','script_findings.json','new_alignment_review.json','caption_array_review.json']:
 files.append((qroot/name,'checks/'+name))
for name in ['audio_mix_manifest_v14.json','technical_full_v14.json','closing_shot_manifest.json','timed_captions_v14.json']:
 files.append((o/name,'checks/'+name))
for name in ['README.md','source_manifest_v14.json']:
 files.append((o/name,name))
for p in sorted((o/'sources').glob('*.json')):
 files.append((p,'sources/'+p.name))
delivery=o/'delivery_v14';delivery.mkdir(exist_ok=True)
manifest={}
for source,name in files:
 assert source.exists(),str(source)
 target=delivery/name;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(source,target);assert sha(source)==sha(target)
 manifest[name]={'sha256':sha(target),'bytes':target.stat().st_size}
write(delivery/'delivery_manifest.json',{'version':'locator-timeline-v14','duration_frames':27653,'fps':30,'duration_s':lock['duration_s'],'files':manifest,'new_voice_credits':616,'additional_cash_usd':0,'actual_listening':False,'continuous_playback':False,'caption_mode':'burned-in MP4; optional matching SRT supplied','publication_authorized':False})
archive=o/'namyangju_locator_timeline_v14_delivery.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for p in sorted(delivery.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(delivery).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;entries=len(z.namelist())
write(o/'zip_receipt.json',{'sha256':sha(archive),'bytes':archive.stat().st_size,'entries':entries,'crc_check_passed':True})
artifacts={str(p.relative_to(e)):sha(p) for p in [full,srt,e/'outputs/story-review-v7/script_v7.md',qroot/'final_review.json',archive]}
target=o/'completed_decision.json'
if target.exists():
 d=json.loads(target.read_text(encoding='utf-8'));assert d['artifacts']==artifacts
else:
 d=create(e.name,'completed',f'남양주 v14 전체 검토본15분21.77초: 4:33부터 좌측 단일 전체 토지계획도+상세영역, 교통/학교/입주/일자리 가로 시간축, 다산/별내 실제83~85㎡급 3단지 가격 지도, 승인 대본v7의 일반형 권역별 후보 새 후반. MP4 SHA256 {sha(full)}. 실제 전체 프레임/컷/정렬 기술검수, 실제 청취·연속재생 미검증. 사용616크레딧/추가결제0. 이 버전 제작완료 검토만이며 업로드·공개 승인 아님.')
 d.update(version='locator-timeline-v14',artifacts=artifacts,publication_authorized=False,qa_scope='actual encoded frames, boundaries, captions, provider alignment and decoded PCM; listening/continuous playback unverified')
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(target,d)
p=e/'decisions.json';c=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')==d['id'] for x in c['decisions']):c['decisions'].append(d)
write(p,c)
p=e/'state.json';s=json.loads(p.read_text(encoding='utf-8'))
s.update(stage='v14_completed_review_pending',active_tasks=[],pending_gate='completed',pending_decision_ids={'completed':d['id']},current_review_render_status='v14_rendered_independent_QA_passed',current_review_video_path=str(full.relative_to(e)),front_review_video_path='outputs/locator-timeline-v14/namyangju_v14_review_00-12m01s.mp4',video_sha256=sha(full),actual_video_duration_seconds=lock['duration_s'],delivery_revision='locator-timeline-v14',delivery_status='local_review_ready',delivery_zip_path=str(archive.relative_to(e)),new_paid_generation_authorized=False,publication_authorized=False)
s['visual_revision_status']={key:'rendered_full_independent_QA_passed' for key in ['M007','detail_273_to_525_2667','common_timelines','new_closing_visuals','full_assembly']}
s['visual_revision_status']['new_closing_voice']='generated_alignment_PCM_verified_616_credits'
write(p,s)
p=e/'scenes.json';s=json.loads(p.read_text(encoding='utf-8'));s['status']='rendered_local_review_ready'
s.update(front_review_revision='locator-timeline-v14',front_review_frames=21636,visual_override_range_frames=[0,27653])
for x in s['scenes']:
 x['status']='rendered_independent_QA_review_ready'
 x['visual_override']={'revision':'locator-timeline-v14','source':str(full.relative_to(e)),'range_frames':[x['start_frame'],x['end_frame']],'status':'actual_rendered_independent_QA_passed'}
write(p,s)
p=o/'request_coverage.json';c=json.loads(p.read_text(encoding='utf-8'))
for x in c['requested_changes']:x['status']='rendered_full_independently_checked';x['final_review']='qa/locator-timeline-v14/final_review.json'
c.update(full_episode_completed=True,completed_decision_id=d['id'],publication_authorized=False)
write(p,c)
print(json.dumps({'completed_decision_id':d['id'],'full_sha256':sha(full),'zip_sha256':sha(archive),'zip_entries':entries,'duration_s':lock['duration_s']}))
