"""Freeze concrete upload metadata and the user's direct authorization for this revision."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
video=EP/'outputs/apartment_top20_monthly_v2.mp4';cover=EP/'outputs/cover_monthly_v2.png'
assert video.exists() and cover.exists()
description='''2006년부터 2026년까지, 어떤 아파트 단지가 가격 순위에 올라왔을까요?
수집한 서울·경기·인천·부산·대구·대전·세종의 단지 가운데 전용 84㎡대 아파트 TOP20을 월별로 비교했습니다.

■ 비교 기준
· 전용면적 84㎡ 이상~85㎡ 미만, 취소 거래 제외
· 가격: 산출월을 포함한 최근 12개월의 개별 매매금액 중위값
· 최초 산출 및 가격 갱신: 해당 12개월 거래 5건 이상
· 2006년 전체를 첫 집계로 사용하고, 2006년 12월~2026년 6월의 235개월 표시
· 대상: 식별 가능한 수집 단지 12,470개, 유효 거래 2,153,830건

■ 거래 없는 달의 표시
새 거래가 없으면 직전 가격을 유지합니다. 새 거래가 있어도 최근 12개월 표본이 5건 미만이면 직전 적격 가격을 유지합니다. 첫 적격 가격 전에는 순위에 들어가지 않습니다.
화면의 ‘산출월’은 마지막으로 가격을 갱신한 기준월(YY.MM), ‘건’은 그 산출월의 12개월 표본 수입니다. 거래가 오래 없던 단지의 과거 가격도 순위에 남을 수 있으므로 산출월을 함께 확인해 주세요.

수집 지역 전체에서 매월 다시 순위를 계산하고, 월별 수치 사이의 움직임을 부드럽게 연결했습니다. 마지막 8초에는 2026년 6월 순위를 유지합니다.

자료: 국토교통부 아파트 매매 실거래가 공개자료, 로컬 수집본
자료 종점: 2026년 6월 30일
단지별 면적·층·거래 구성 변화가 중위값에 함께 반영됩니다. 과거 취소·정정의 수집 시점은 파일마다 차이가 있습니다.

다음 데이터 비교도 궁금하다면 구독과 좋아요로 함께해 주세요.
#아파트 #실거래가 #부동산 #아파트순위 #shorts'''
job={'revision':'monthly-v2','video':video.relative_to(ROOT).as_posix(),'video_sha256':sha(video),'cover':cover.relative_to(ROOT).as_posix(),
     'publish_at_kst':'2026-10-29T21:00:00+09:00','publish_at_utc':'2026-10-29T12:00:00Z',
     'body':{'snippet':{'title':'20년, 아파트 중위가 TOP20의 변화｜84㎡ 실거래 월별 순위',
          'description':description,'categoryId':'27','defaultLanguage':'ko',
          'tags':['아파트','실거래가','아파트순위','부동산데이터','84제곱미터','월별순위','TOP20','shorts']},
       'status':{'privacyStatus':'private','publishAt':'2026-10-29T12:00:00Z','selfDeclaredMadeForKids':False,'containsSyntheticMedia':False}},
     'synthetic_media_decision':'실제 사람·장소의 사실적인 생성/변조 장면 없이 코드 기반 차트와 자체 작곡 신시사이저 음원으로 구성',
     'schedule_api_reference':'https://developers.google.com/youtube/data/reference/rest/v3/videos#status.publishAt'}
save(HERE/'upload_job.json',job)
save(HERE/'authorization.json',{'authorization':'direct_user_request','revision':'monthly-v2',
    'request':'쿼터로하지말고 월단위로하자 새로운 실거래가가 없으면 유지하는걸로하고, 그리고 전환이 좀 자연스럽게 바꿔줘 지금 다 끊기는걸로 보여. hyperframes 활용해서 그리고 완료되면 21시 공개로 업로드해줘',
    'decision_context':'기존 판단 위임 지속 + 이번 수정본의 오늘21시 공개 예약 직접 지시. 별도 중간 승인 요청 없이 검수 후 진행.',
    'video_sha256':sha(video),'upload_job_sha256':sha(HERE/'upload_job.json'),'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw',
    'publish_at_kst':'2026-10-29T21:00:00+09:00','new_paid_generation_calls':0,'delete_existing_videos':False})
(HERE/'description.txt').write_text(description+'\n',encoding='utf8')
preflight=json.loads((EP/'director/episode_preflight.json').read_text(encoding='utf8'))
preflight.update(revision='monthly-v2',status='reviewing_monthly_v2_before_scheduled_upload')
preflight['input_contract']={'narration_mode':'none; reuse original instrumental music','timing_basis':'235 monthly snapshots; 56.8s60fps',
   'episode_specific_choices':['TOP20','84<=area<85','12month median/min5 qualified quote','carry previous quote when no new trade or insufficient n','asofmonth shown','today21KSTscheduled public upload'],
   'superseded_historical_defaults':['quarterly snapshots','monthly stop/start hold','hard collision label hiding','no upload requested in v1']}
preflight['approvals']={'basis':'direct user delegation and exact current remake/schedule request',
     'topic':'direct_user_request','screen_copy':'delegated within specific remake scope','budget':{'new_paid_calls':0},
     'pre_upload':{'status':'direct_user_authorized_subject_to_final_QA','authorization_file':'director/monthly-v2/authorization.json'}}
preflight['qa']={'source_frames_checked':3408,'monthly_data_knots':235,'price_carry_validation':'passed; research/monthly-v2/validation.json',
    'actual_encoded_frames':'qa/monthly-v2/encoded/verification.json','independent':'pending','actual_listening_performed':False,'continuous_playback_performed':False}
save(HERE/'episode_preflight.json',preflight)
print(json.dumps({'video_sha256':sha(video),'job_sha256':sha(HERE/'upload_job.json'),'title_characters':len(job['body']['snippet']['title']),'description_utf8_bytes':len(description.encode('utf8'))}))
