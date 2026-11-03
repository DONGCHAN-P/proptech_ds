from pathlib import Path
import hashlib,json,sys,zipfile,shutil
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
o=e/'outputs/readability-cta-v15';qr=e/'qa/readability-cta-v15'
full=o/'namyangju_readability_cta_full_v15.mp4';srt=full.with_suffix('.srt')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
if (o/'completed_decision.json').exists():
 d=read(o/'completed_decision.json');assert all(sha(e/p)==h for p,h in d['artifacts'].items())
 print(json.dumps({'completed_decision_id':d['id'],'status':'already_packaged_verified'}));sys.exit(0)
q=read(qr/'final_review.json');lock=read(e/'timing_lock_v15.json');voice=read(e/'narration/cta-v8/handoff.json')
assert q['sha256']==sha(full) and q['required_open_count']==0 and q['local_review_ready']
assert q['video_frames']==lock['duration_frames']==27959 and abs(q['duration_s']-lock['duration_s'])<.1
for key in ['timeline_clipping_checked','jobs_locator_checked','station_inset_switch_checked','south_leaders_checked','cta_motion_checked']:assert q[key] is True,key
assert q['post_speech_hold_frames']==90 and q['total_caption_count']==305
assert voice['actual_credits']==24 and voice['submitted_characters']==59 and voice['post_requests']==1 and voice['retries']==0
subtitle_blocks=[b for b in srt.read_text(encoding='utf-8').strip().split('\n\n') if '-->' in b]
assert len(subtitle_blocks)==305
assert ' '.join(' '.join(b.splitlines()[2:]) for b in subtitle_blocks[-4:])==(e/'outputs/story-review-v8/M010_cta.txt').read_text(encoding='utf-8')
files=[(full,'video/'+full.name),(srt,'captions/'+srt.name),(e/'outputs/story-review-v8/script_v8.md','script/script_v8.md'),(e/'outputs/story-review-v8/manifest.json','script/manifest.json'),(e/'timing_lock_v15.json','timing_lock_v15.json'),(e/'narration/cta-v8/handoff.json','checks/cta_voice_handoff.json'),(qr/'final_review.json','checks/final_review.json'),(e.parents[1]/'guides/지역_상세지도와_의미단위_자막.md','guides/지역_상세지도와_의미단위_자막.md')]
for p in sorted(qr.glob('*.json')):
 if p.name!='final_review.json':files.append((p,'checks/'+p.name))
for name in ['README.md','source_manifest_v15.json','technical_full_v15.json','timeline_bbox_audit.json','audio_mix_manifest_v15.json','timed_captions_v15.json','audio_region_measurements.json']:
 if (o/name).exists():files.append((o/name,name))
for p in sorted((o/'sources').glob('*.json')):files.append((p,'sources/'+p.name))
delivery=o/'delivery_v15';delivery.mkdir(exist_ok=True);manifest={}
for source,name in files:
 assert source.exists(),str(source)
 target=delivery/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 assert sha(source)==sha(target)
 manifest[name]={'sha256':sha(target),'bytes':target.stat().st_size}
write(delivery/'delivery_manifest.json',{'version':'readability-cta-v15','duration_frames':27959,'fps':30,'duration_s':lock['duration_s'],'files':manifest,'current_revision_voice_credits':24,'additional_cash_usd':0,'actual_listening':False,'continuous_playback':False,'caption_mode':'burned-in MP4 with optional matching SRT','post_speech_hold_frames':90,'publication_authorized':False})
archive=o/'namyangju_readability_cta_v15_delivery.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for p in sorted(delivery.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(delivery).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;entries=len(z.namelist())
write(o/'zip_receipt.json',{'sha256':sha(archive),'bytes':archive.stat().st_size,'entries':entries,'crc_check_passed':True})
artifacts={str(p.relative_to(e)):sha(p) for p in [full,srt,e/'outputs/story-review-v8/script_v8.md',qr/'final_review.json',archive]}
d=create(e.name,'completed',f'남양주 v15 수정 전체 검토본15분31.97초: 모든 시간축 글자 잘림 수정,일자리 좌측 전체지도,왕숙역→일패역 설명 시점에 맞는 작은 지도,13:21 교차 인출선 정리,사용자 지정 CTA와🔔👍모션/말끝3초후기존10초outro. 기존301자막+새4=305,추가음성24포함크레딧·현금0. MP4 SHA256 {sha(full)}. 실제 청취·연속재생은 미검증. 완료 검토만이며 업로드·공개 승인이 아님.')
d.update(version='readability-cta-v15',artifacts=artifacts,publication_authorized=False,qa_scope='actual encoded frame and boundary review, all-frame metrics and caption/alignment audit; actual listening and continuous playback unverified')
write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d);write(o/'completed_decision.json',d)
p=e/'decisions.json';c=read(p);c['decisions'].append(d);write(p,c)
p=e/'state.json';s=read(p)
s.update(stage='v15_completed_review_pending',active_tasks=[],pending_gate='completed',pending_decision_ids={'completed':d['id']},render_revision='readability-cta-v15',editor_revision='readability-cta-v15',caption_revision='v14-301-preserved+cta-v8-4-provider-aligned',caption_count=305,current_review_render_status='v15_rendered_independent_QA_passed',current_review_video_path=str(full.relative_to(e)),video_path=str(full.relative_to(e)),video_sha256=sha(full),actual_video_duration_seconds=lock['duration_s'],delivery_revision='readability-cta-v15',delivery_status='local_review_ready',delivery_zip_path=str(archive.relative_to(e)),new_paid_generation_authorized=False,publication_authorized=False,new_voice_credits=24,new_voice_submitted_characters=59,qa_scope='all-frame metrics and targeted actual-frame review; actual listening/continuous playback unverified',telegram_v15_completion_notice_sent=False)
write(p,s)
p=e/'scenes.json';s=read(p)
s.update(status='rendered_local_review_ready',visual_override_range_frames=[0,27959],visual_revision_target='readability-cta-v15')
for x in s['scenes']:
 x['status']='rendered_independent_QA_review_ready'
 x['visual_override']={'revision':'readability-cta-v15','source':str(full.relative_to(e)),'range_frames':[x['start_frame'],x['end_frame']],'status':'actual_rendered_independent_QA_passed'}
write(p,s)
print(json.dumps({'completed_decision_id':d['id'],'full_sha256':sha(full),'zip_sha256':sha(archive),'zip_entries':entries,'duration_s':lock['duration_s']}))
