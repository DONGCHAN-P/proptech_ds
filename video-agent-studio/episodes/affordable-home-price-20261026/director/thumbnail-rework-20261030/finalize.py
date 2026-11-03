from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
import hashlib,json,numpy as np
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/thumbnail-rework-20261030'
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
final=OUT/'TH001_affordable_photo_v1.png'
receipt=json.loads((HERE/'replace_receipt.json').read_text(encoding='utf8'))
after=json.loads((HERE/'after_api.json').read_text(encoding='utf8'))
assert receipt['phase']=='thumbnail_set_accepted' and receipt['file_sha256']==sha(final)
def pix(p):return np.asarray(Image.open(p).convert('RGB').resize((128,72)),dtype=float)
served=pix(OUT/'thumbnail_served_after.jpg');new=pix(final);old=pix(OUT/'previous_thumbnail_live.jpg')
new_error=float(np.abs(served-new).mean());old_error=float(np.abs(served-old).mean())
match=new_error<8 and new_error<old_error/3
completion={'status':'thumbnail_replaced_verified' if match else 'thumbnail_set_accepted_cdn_refresh_pending',
 'video_id':'0495J7FMmCk','youtube_url':'https://youtu.be/0495J7FMmCk','thumbnail':final.relative_to(ROOT).as_posix(),
 'thumbnail_sha256':sha(final),'dimensions':Image.open(final).size,'bytes':final.stat().st_size,
 'changed_at_kst':receipt['changed_at_kst'],'youtube_thumbnail_set_accepted':True,
 'served_image_matches_new_thumbnail':match,'served_new_mean_absolute_error':new_error,'served_old_mean_absolute_error':old_error,
 'title_description_privacy_unchanged':after['title_description_privacy_unchanged'],
 'CTR_change':'unmeasured; baseline decline user reported','plan_saved':'docs/superpowers/specs/2026-10-30-jipgorithm-timemap-integration.md'}
save(HERE/'completion.json',completion)
record=f'''# 썸네일 교체 · 2026-10-30

대상: https://youtu.be/0495J7FMmCk

큰 흰색 **현금 1억~5억**, 큰 노란색 **얼마짜리 집?**, 아파트 야경 배경으로 기존 채널 표지의 표현을 계승했다. 기존 매매·전세·월세 선택본과 공통 ExtraBold 글꼴·노란색을 참고했다. 설명 카드·공식·중복 배지를 줄이고 현금 범위와 질문이 먼저 보이게 했다.

1280×720 PNG, 320/160픽셀 축소 확인, 글자 경계 잘림0건. 시각 담당 검토는 `../../visual/thumbnail-rework-20261030/review/review.json`에 기록했다. 생성 배경은 특정 실제 단지를 표시하지 않는 가상 아파트이며 출처·생성 이력은 내부 자산 목록에 보관했다.

변경 시각: {receipt['changed_at_kst']}  
SHA-256: `{sha(final)}`  
YouTube 썸네일 설정 API: 성공  
공개 썸네일 이미지 일치: {match}

제목·설명·공개 상태가 기존과 동일함을 재조회했다. 교체 전 실제 공개 썸네일은 `previous_thumbnail_live.jpg`, 원래 로컬 표지는 `previous_thumbnail_local.png`로 보존했다. 조회/게시 기록은 `../../director/thumbnail-rework-20261030/`에 있다.

CTR 저하는 사용자 보고다. 이번 작업에서 노출수·CTR을 별도 측정하지 않았으며 썸네일이 저하 원인이라고 확정하거나 교체 후 개선을 주장하지 않았다. 교체 시각 이후 같은 유입경로·유사 기간의 노출수와 클릭률을 기준으로 효과를 확인할 수 있다.

집고리즘 통합 기획은 `docs/superpowers/specs/2026-10-30-jipgorithm-timemap-integration.md`에 보관했다.
'''
(OUT/'변경기록.md').write_text(record,encoding='utf8')
statepath=EP/'state.json';state=json.loads(statepath.read_text(encoding='utf8'))
if not (HERE/'prior_episode_state.json').exists():save(HERE/'prior_episode_state.json',state)
state.update(thumbnail_revision='photo-v1-20261030',thumbnail_asset=completion['thumbnail'],thumbnail_sha256=sha(final),thumbnail_youtube_applied_at=receipt['changed_at_kst'],thumbnail_replacement_record='director/thumbnail-rework-20261030/completion.json')
save(statepath,state)
curpath=ROOT/'config/current_video.json';current=json.loads(curpath.read_text(encoding='utf8'))
assert current['episode']==EP.name and current['youtube_url']=='https://youtu.be/0495J7FMmCk'
current.update(thumbnail=completion['thumbnail'],thumbnail_sha256=sha(final),thumbnail_revision='photo-v1-20261030',thumbnail_updated_at=receipt['changed_at_kst']);save(curpath,current)
shelfpath=ROOT/'config/video_shelf.json';cfg=json.loads(shelfpath.read_text(encoding='utf8'))
entry=next(e for e in cfg['entries'] if e['workspace'].replace('\\','/').endswith(EP.name))
oldsource=entry['files'].get('썸네일.png')
if oldsource and not oldsource.endswith('TH001_affordable_photo_v1.png'):entry['files']['이전_썸네일.png']=oldsource
entry['files']['썸네일.png']=completion['thumbnail'];entry['files']['썸네일_변경기록.md']=(OUT/'변경기록.md').relative_to(ROOT).as_posix()
entry['thumbnail_revision']='photo-v1-20261030';entry['thumbnail_sha256']=sha(final);save(shelfpath,cfg)
print(json.dumps(completion,ensure_ascii=False))
