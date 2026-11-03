"""Update current pointers only after API verifies the new public upload and old deletion."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(HERE/'upload_receipt.json');deletion=read(HERE/'deletion_receipt.json');job=read(HERE/'upload_job.json')
assert r['phase']=='replacement_complete' and deletion['phase']=='deleted_verified'
assert deletion['deleted_video_id']=='0495J7FMmCk' and deletion['replacement_video_id']==r['video_id']
assert r['ready'] and r['definition']=='hd' and r['caption_status']=='serving'
assert r['final_verification']['status']['privacyStatus']=='public'
final_check=read(HERE/'final_readback.json');assert final_check['old_id_absent'] and final_check['new_public'] and final_check['thumbnail_served_matches']
assert sha(ROOT/job['video'])==job['video_sha256']==r['sha256']
stamp=datetime.now(timezone.utc).isoformat();kst=datetime.now(timezone(timedelta(hours=9))).isoformat()
completion={'status':'new_public_verified_old_deleted','publication_revision':'reupload-20261101','old_video_id':'0495J7FMmCk',
 'old_video_deleted':True,'new_video_id':r['video_id'],'youtube_url':r['url'],'public':True,'HD':True,'korean_caption_status':'serving',
 'thumbnail_sha256':job['thumbnail_sha256'],'video_sha256':job['video_sha256'],'subtitles_sha256':job['subtitles_sha256'],
 'title':job['body']['snippet']['title'],'description_preserved':True,'local_sources_preserved':True,'new_paid_generation_calls':0,
 'verified_at':stamp,'verified_at_kst':kst,'shorts_description_links':read(HERE/'link_updates.json'),
 'native_related_video_cards_endscreens':'not verified through Data API','same_media_reuploaded':True,'actual_listening_performed_this_task':False,'continuous_playback_performed_this_task':False}
save(HERE/'completion.json',completion)
cfgpath=ROOT/'config/current_video.json';cfg=read(cfgpath)
assert cfg['episode']==EP.name and cfg['youtube_url'] in ['https://youtu.be/0495J7FMmCk',r['url']]
cfg.update(youtube_url=r['url'],youtube_video_id=r['video_id'],previous_video_url='https://youtu.be/0495J7FMmCk',publication_status='public',
 publication_revision='reupload-20261101',report=(HERE/'completion.json').relative_to(ROOT).as_posix(),updated_at=stamp,
 replaced_video_deleted=True,replaced_video_id='0495J7FMmCk')
save(cfgpath,cfg)
statepath=EP/'state.json';state=read(statepath)
if not (HERE/'state.before.json').exists():save(HERE/'state.before.json',state)
state.update(stage='public_reuploaded_verified',public_upload_url=r['url'],youtube_url=r['url'],youtube_video_id=r['video_id'],
 publication_revision='reupload-20261101',current_authorization='director/reupload-20261101/authorization.json',
 current_release_record='director/reupload-20261101/completion.json',replaced_public_main_id='0495J7FMmCk',replaced_public_main_deleted=True,updated_at=stamp)
state['current_public_main']={'video_id':r['video_id'],'url':r['url'],'sha256':job['video_sha256'],'title':job['body']['snippet']['title'],'privacy':'public','processing':'succeeded','caption':'Korean serving'}
for container in [state,state.get('published_assets',{})]:
    if container.get('public_upload_url')=='https://youtu.be/0495J7FMmCk':container['public_upload_url']=r['url']
    for item in container.get('public_uploads',[]):
        if item.get('video_id')=='0495J7FMmCk':item.update(video_id=r['video_id'],url=r['url'],reuploaded_from='0495J7FMmCk')
save(statepath,state)
report=f'''# 본편 재업로드 · 2026-11-01

**새 공개 영상:** {r['url']}

제목: {job['body']['snippet']['title']}

사용자 요청 “효과 전혀 없어서 삭제하고 새로 업로드해줘”에 따라 동일 검수본을 새 영상 ID로 공개했다. 최신 아파트 야경·흰색/노란색 썸네일과 한국어 자막을 적용했다. 고화질 처리·자막 serving·공개 상태를 확인한 뒤 기존 본편 `0495J7FMmCk` 한 편을 삭제했고, API 재조회에서 기존 ID가 반환되지 않는 것을 확인했다.

연결 쇼츠 `nYl1XSdyFAQ`, `DnCBj7voUyY`의 설명문 본편 링크를 새 주소로 변경했다. 네이티브 관련영상·카드·최종화면은 Data API를 통한 확인 범위에 포함되지 않는다.

- 기존 영상·제목·설명·자막 목록·댓글·썸네일 기록: 이 폴더의 `old_*.before.*`
- 최종 영상: `{job['video']}` · SHA-256 `{job['video_sha256']}`
- 자막: `{job['subtitles']}`
- 썸네일: `{job['thumbnail']}`
- 작업 완료 확인: {kst}

기존 MP4·음성·자막·대본·썸네일 파일은 보존했다. 이번 작업에서 영상 재편집·음성 재생성·유료 API 생성은 수행하지 않았다. 기존 해시 검수 결과를 재사용하고 실제 업로드 결과를 새로 확인했다. 이번 작업의 연속 시청·실제 청취는 수행하지 않았다. 재업로드 이후 노출·CTR 변화는 아직 측정하지 않았다.
'''
(HERE/'공개_재업로드.md').write_text(report,encoding='utf8')
shelfpath=ROOT/'config/video_shelf.json';shelf=read(shelfpath);entry=next(e for e in shelf['entries'] if e['workspace'].replace('\\','/').endswith(EP.name))
entry.update(youtube_url=r['url'],youtube_visibility='public',publication_revision='reupload-20261101',status='본편 새 ID로 공개 재업로드 · 이전 본편 삭제 확인 · 최신 썸네일/한국어 자막/HD · 쇼츠 설명 본편 링크 갱신')
entry['files']['공개_업로드.md']=(HERE/'공개_재업로드.md').relative_to(ROOT).as_posix();entry['files']['재업로드_검증.json']=(HERE/'completion.json').relative_to(ROOT).as_posix()
save(shelfpath,shelf)
print(json.dumps({'status':completion['status'],'url':r['url'],'old_deleted':True,'HD':True,'captions':'serving','local_sources_preserved':True},ensure_ascii=False))
