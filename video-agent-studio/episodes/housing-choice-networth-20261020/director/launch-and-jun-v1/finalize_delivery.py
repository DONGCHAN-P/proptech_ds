"""Record only verified Jun replacement, successful private upload and exact old deletion."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
RELEASE=EP/'outputs/jun-release-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rel(p):return p.relative_to(ROOT).as_posix()

job=read(RELEASE/'upload_job.json');record=read(RELEASE/'upload_receipt.json')
dual=read(RELEASE/'dual_media_review.json');deletion=read(HERE/'old_private_deletion_receipt.json')
qa_path=HERE/'codex_final_review.json';qa=read(qa_path)
auth=read(HERE/'authorization.json');ledger=read(EP/'narration/jun-production-v1/generation_ledger.json')
render=read(EP/'editor/jun-production-v1/render_receipt.json');edl=read(EP/'outputs/jun-production-v1/assembly_edl.json')
assert record['video_id']!=auth['old_private_video_id'] and record['sha256']==job['sha256']==render['final_sha256']
assert record['private_verified'] and record['caption_serving_verified'] and record['caption_status']=='serving'
assert record['verification']['status']['privacyStatus']=='private' and not record['verification']['status'].get('publishAt')
assert record['verification']['processingDetails']['processingStatus']=='succeeded'
assert deletion['phase']=='deleted_verified' and deletion['old_video_absent_verified']
assert deletion['old_video_id']=='exEGpjcqdF0' and deletion['new_video_id']==record['video_id']
assert deletion['local_files_deleted']==0 and dual['video_sha256']==job['sha256'] and not dual['required_open'] and not dual['critical_open']
assert qa['approved'] and not qa['required_issues'] and qa['video_sha256']==job['sha256']
assert sha(ROOT/job['video'])==job['sha256'] and sha(ROOT/job['subtitles'])==job['subtitles_sha256']
assert ledger['actual_credits']<=10739 and ledger['topup_calls']==ledger['overage_calls']==ledger['automatic_retries']==0
public_path=ROOT/'config/current_video.json';public=read(public_path)
assert 'XWAWnSrz7FE' in json.dumps(public),'Public baseline must remain the existing Gyosan film.'
baseline_hash=sha(public_path)
now=dt.datetime.now(dt.timezone.utc).isoformat()
completion={'status':'Jun_private_uploaded_verified_old_private_replaced','url':record['url'],'video_id':record['video_id'],
    'video':job['video'],'video_sha256':job['sha256'],'subtitles':job['subtitles'],'subtitles_sha256':job['subtitles_sha256'],
    'title':job['title'],'thumbnail':job['thumbnail'],'thumbnail_sha256':job['thumbnail_sha256'],
    'voice':'ElevenLabs Jun / eleven_v4','caption_cues':206,'body_seconds':1177.4333333333334,
    'film_seconds':edl['total_seconds'],'provider_header_actual_credits':ledger['actual_credits'],'included_credit_cap':10739,
    'additional_cash_usd':0,'automatic_paid_retries':0,'old_private_deleted_video_id':'exEGpjcqdF0',
    'old_private_deletion_receipt':rel(HERE/'old_private_deletion_receipt.json'),'local_files_deleted':0,
    'new_visibility':'private','scheduled':False,'processing':'succeeded','Korean_caption_status':'serving',
    'dual_review':rel(RELEASE/'dual_media_review.json'),'coverage':qa.get('coverage',{}),
    'actual_listening':False,'continuous_playback':False,'Studio_ContentID_review':False,
    'current_public_config_sha256_unchanged':baseline_hash,'protected_other_private_id':'szSvG_2IehY','verified_at_utc':now}
save(RELEASE/'completion.json',completion)
text=(f"# 매매 전세 월세 Jun 최종본 비공개 업로드\n\n{record['url']}\n\n"
      f"제목: {job['title']}\n\nElevenLabs Jun 음성·206개 의미 단위 자막. 실제 길이 {int(edl['total_seconds'])//60}분 {int(edl['total_seconds'])%60}초. "
      "선택한 매매·전세·월세 비교형 썸네일을 적용했습니다.\n\n"
      f"포함 크레딧 실제 사용은 공급자 응답 헤더 합계 {ledger['actual_credits']:,}입니다. 승인 상한10,739 이내, 추가 결제·충전0, 자동 유료 재시도0입니다.\n\n"
      "YouTube 비공개·예약없음·처리완료·한국어CC serving을 조회했습니다. 새 버전 확인 후 기존 비공개 exEGpjcqdF0의 삭제와 부재를 확인했습니다. 로컬 원본과 다른 영상은 보존했습니다.\n\n"
      "Codex·Claude 최종 미디어 검수의 필수 이슈는 없습니다. 검수는 인코딩 표본 화면·전체 자막과 타이밍·음성인식·전체 디코드·신호 측정 범위입니다. 직접 청취·연속 재생·Studio Content ID 확인은 수행하지 않았습니다. "
      "세부 범위와 권고사항은 Jun_검수.json 및 작업폴더의 qa/jun-production-v1에서 확인할 수 있습니다.\n")
(RELEASE/'private_upload_status.md').write_text(text,encoding='utf8')
state=read(EP/'state.json')
history=state.setdefault('private_upload_history',[])
old=state.get('private_upload',{})
if old.get('video_id') and old['video_id']!=record['video_id'] and not any(h.get('video_id')==old['video_id'] for h in history):history.append(old)
state.update(stage='private_uploaded_verified',production_authorization=rel(HERE/'authorization.json'))
state['jun_replacement_v1'].update(status=completion['status'],completion=rel(RELEASE/'completion.json'),
    actual_provider_header_credits=ledger['actual_credits'],deletion_executed=True,video_id=record['video_id'],
    final_video=job['video'],final_timing='narration/jun-production-v1/final_timing.json',updated_at_utc=now)
state['private_upload']=completion
save(EP/'state.json',state)
shelf_path=ROOT/'config/video_shelf.json';shelf=read(shelf_path)
for entry in shelf['entries']:
    if entry['name']=='매매전월세':
        entry['status']='Jun 최종본 / 양측 검수 통과 / 비공개 업로드·처리·자막 확인 / 이전 비공개본 교체 완료'
        entry['youtube_url']=record['url']
        entry['files'].update({'영상.mp4':job['video'],'자막.srt':job['subtitles'],
            '비공개_업로드.md':rel(RELEASE/'private_upload_status.md'),'썸네일.png':job['thumbnail'],
            'Jun_검수.json':rel(qa_path),
            '음성_사용량.json':rel(EP/'narration/jun-production-v1/generation_ledger.json'),
            '업로드_교체기록.json':rel(HERE/'old_private_deletion_receipt.json')})
    elif entry['name']=='housing-choice':
        entry['status']='Jun 최종본 / 비공개 업로드·자막 확인 / 기존 원본·중간본 보존'
        entry['youtube_url']=record['url'];entry['files']['Jun_최종본.mp4']=job['video']
save(shelf_path,shelf)
queue_path=ROOT/'config/video_production_queue_20261026.json'
queue=read(queue_path);queue['housing_choice_jun_replacement']=completion;save(queue_path,queue)
assert sha(public_path)==baseline_hash
print(json.dumps({'url':record['url'],'seconds':edl['total_seconds'],'credits':ledger['actual_credits'],
                  'old_private_deleted':'exEGpjcqdF0','public_baseline_unchanged':True,'other_private_untouched':'szSvG_2IehY'},ensure_ascii=False))
