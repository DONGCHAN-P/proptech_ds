"""Publish the verified monthly revision into current episode state and user shelf."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((HERE/'upload_receipt.json').read_text(encoding='utf8'))
assert r['phase']=='scheduled_verified' and r['status']['publishAt']=='2026-10-29T12:00:00Z'
video=EP/'outputs/apartment_top20_monthly_v2.mp4';assert r['video_sha256']==sha(video)
qa=json.loads((EP/'qa/monthly-v2/independent/findings.json').read_text(encoding='utf8'))
assert qa['artifact']['sha256']==sha(video) and qa['verdict']['critical_open']==qa['verdict']['required_open']==0
out=EP/'outputs/monthly-v2';out.mkdir(exist_ok=True)
text=f'''# 월별 TOP20 예약 업로드

{r['youtube_url']}

공개 예약: **2026년 10월 29일 오후 9시(한국시간)**. API에서 `private` + `publishAt=2026-10-29T12:00:00Z`를 재조회해 확인했다. 공개 시각 전에는 채널 소유자 계정으로 확인할 수 있다.

제목: 20년, 아파트 중위가 TOP20의 변화｜84㎡ 실거래 월별 순위

최종 영상: `../apartment_top20_monthly_v2.mp4` · 56.8초 · 1080×1920 · 60fps  
SHA-256: `{r['video_sha256']}`

처리 상태: `{(r.get('processing_details') or {}).get('processingStatus','unknown')}`  
해상도: `{(r.get('content_details') or {}).get('definition','unknown')}`  
썸네일 API: `{r.get('thumbnail_status','unknown')}`

기존 분기 영상과 기존 게시 영상은 보존했다. 새 월별 버전을 한 번 업로드했다. 새 유료 생성은 없다.
실제 MP4 표본 화면과 독립 검수를 수행했으며, 연속 재생·실제 청취·실기기 시청은 수행하지 않았다.

예약 근거: [YouTube 공식 API 문서](https://developers.google.com/youtube/data/reference/rest/v3/videos#status.publishAt). 실제 요청/확인 기록은 `../../director/monthly-v2/upload_job.json`, `upload_receipt.json`에 있다.
'''
(out/'업로드정보.md').write_text(text,encoding='utf8')
for name in ['state.json','brief.json','BRIEF.md']:
    prior=HERE/('prior_v1_'+name)
    if not prior.exists():shutil.copyfile(EP/name,prior)
oldpreflight=EP/'director/episode_preflight.json'
if not (HERE/'prior_v1_episode_preflight.json').exists():shutil.copyfile(oldpreflight,HERE/'prior_v1_episode_preflight.json')
state=json.loads((EP/'state.json').read_text(encoding='utf8'))
state.update(phase='scheduled_publication',revision='monthly-v2',duration_s=56.8,fps=60,
  source_data='research/monthly-v2/data.json',source_validation='research/monthly-v2/validation.json',
  final_video=video.relative_to(ROOT).as_posix(),final_sha256=sha(video),
  youtube_url=r['youtube_url'],youtube_video_id=r['video_id'],youtube_privacy_current=r['status']['privacyStatus'],
  publish_at_kst='2026-10-29T21:00:00+09:00',publish_at_utc=r['status']['publishAt'],
  upload_receipt='director/monthly-v2/upload_receipt.json',independent_qa='qa/monthly-v2/independent/findings.json',
  Claude_direction='initial TOP20 text review preserved; monthly follow-up timed out240s, no new approval claimed',
  updated_at_kst=datetime.now(timezone(timedelta(hours=9))).isoformat())
save(EP/'state.json',state)
brief=json.loads((EP/'brief.json').read_text(encoding='utf8'))
brief.update(revision='monthly-v2',request='월별 TOP20, 새 실거래가 없으면 직전 가격 유지, 자연스러운 HyperFrames 전환, 완성 후 오늘21시 공개 예약',
   period_candidate='2006-12 through2026-06, monthly updates of trailing12-month transaction median',
   eligibility_candidate='new valid trade in month AND trailing12-month n>=5 updates quote; otherwise keep prior qualified quote',
   duration_candidate_seconds=56.8,upload_requested=True,upload_visibility='scheduled public',publish_at_kst='2026-10-29T21:00:00+09:00')
save(EP/'brief.json',brief)
newbrief='''---
workflow: general-video
flow: automation
storyboard: no
destination: YouTube Shorts
aspect: "9:16"
language: ko
length: 56.8s
message: "월별 단지 TOP20의 진입·추월을 연속해서 보여준다"
---

'''+(EP/'editor/monthly-v2/design.md').read_text(encoding='utf8')+'\n현재 제작결과/게시 상태는 state.json 및 outputs/monthly-v2/업로드정보.md를 따른다. 이전 분기 지침은 director/monthly-v2/prior_v1_BRIEF.md에 보존했다.\n'
(EP/'BRIEF.md').write_text(newbrief,encoding='utf8')
pre=json.loads((HERE/'episode_preflight.json').read_text(encoding='utf8'))
pre['status']='completed_and_scheduled_verified';pre['qa']['independent']='passed scoped review; qa/monthly-v2/independent/findings.json'
pre['approvals']['pre_upload']['status']='executed_from_direct_user_authorization_after_QA'
pre['publication']={'url':r['youtube_url'],'current_privacy':'private','publish_at_kst':'2026-10-29T21:00:00+09:00','verified':True}
save(HERE/'episode_preflight.json',pre);save(oldpreflight,pre)
cfgpath=ROOT/'config/video_shelf.json';cfg=json.loads(cfgpath.read_text(encoding='utf8'))
entry=next(e for e in cfg['entries'] if e['name']=='단지_TOP20_쇼츠')
base=EP.relative_to(ROOT).as_posix()
entry.update(status='월별 TOP20 v2 · 거래 없으면 유지 · 60fps · 10월29일21시 공개 예약 확인',local_revision='monthly-v2',
    local_video_sha256=sha(video),youtube_url=r['youtube_url'],youtube_visibility='scheduled public',publish_at_kst='2026-10-29T21:00:00+09:00')
entry['files']={
    '영상.mp4':base+'/outputs/apartment_top20_monthly_v2.mp4','표지.png':base+'/outputs/cover_monthly_v2.png',
    '화면구성.md':base+'/outputs/monthly-v2/화면구성.md','제작결과.md':base+'/outputs/monthly-v2/제작결과.md',
    '업로드정보.md':base+'/outputs/monthly-v2/업로드정보.md','TOP20_데이터.csv':base+'/research/monthly-v2/top20_monthly.csv',
    '집계방법.md':base+'/research/monthly-v2/methods.md','단지명_매핑.csv':base+'/research/monthly-v2/name_mapping.csv',
    '진입이벤트.csv':base+'/research/monthly-v2/entry_events.csv','독립검수.json':base+'/qa/monthly-v2/independent/findings.json',
    '초기_TOP20_Claude검토.md':base+'/collaboration/top20_direction_response.md','월별_Claude추가검토_상태.json':base+'/collaboration/monthly_v2_attempt.json',
    '이전_분기_영상.mp4':base+'/outputs/apartment_top20_race_v1.mp4','이전_분기_TOP20.csv':base+'/research/top20_quarterly.csv'}
save(cfgpath,cfg)
print(json.dumps({'state':state['phase'],'url':r['youtube_url'],'publish_at_kst':state['publish_at_kst'],'shelf_config_updated':True},ensure_ascii=False))
