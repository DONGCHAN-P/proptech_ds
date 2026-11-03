import hashlib
import json
import wave
from datetime import datetime, timezone
from pathlib import Path

EP=Path('C:/projects/realestate_reco/video-agent-studio/episodes/newlywed-apartment-picks-20261101')
QA=EP/'qa/top20-enhance-v2'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj): (QA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

tp=EP/'director/top20-enhance-v2/locked_timing.json'
t=read(tp);old=read(EP/'director/top20-production-v1/locked_timing.json')
prior=read(QA/'content_timing_qa.json');words=read(t['words_file'])['words']
audio_sha=sha(t['audio_file']);delta=prior['timing']['added_duration_s']
checks={
 'script_sha256':t['script_sha256']==sha(EP/'director/top20-enhance-v2/script_v5.md'),
 'previous_script_sha256':t['previous_script_sha256']==sha(EP/'director/top20-production-v1/script_v4.md'),
 'word_count':t['word_count']==len(words)==1065,
 'audio_body_duration_s':abs(t['audio_body_duration_s']-(old['audio_body_duration_s']+delta))<1e-9,
 'proposals_v5_sha256':t['source_scene_proposals_v5_sha256']==sha(EP/'director/top20-enhance-v2/scene_proposals_v5.json'),
 'audio_unchanged':audio_sha==t['audio_sha256']==prior['checked_revision']['audio_sha256'],
 'added_scenes_unchanged':sha(EP/'director/top20-enhance-v2/added_scenes.json')==prior['checked_revision']['added_scenes_sha256'],
 'total_duration_unchanged':t['duration_s']==prior['timing']['duration_s'],
 'last_speech_and_outro_unchanged':t['last_spoken_end_s']==prior['timing']['last_speech_end_s'] and t['brand_outro']['start_s']==prior['timing']['outro_start_s'],
}
checks['old_scene_clocks_unchanged']=all(
 abs(next(n for n in t['scenes'] if n['scene_id']==s['scene_id'])['start_s']-s['start_s']-(delta if s['start_s']>=429.4889342403628 else 0))<1e-8
 and abs(next(n for n in t['scenes'] if n['scene_id']==s['scene_id'])['end_s']-s['end_s']-(delta if s['start_s']>=429.4889342403628 else 0))<1e-8
 for s in old['scenes'])
checks['new_scene_clocks_unchanged']=all(
 next(n for n in t['scenes'] if n['scene_id']==s['scene_id'])['start_s']==s['start_s']
 and next(n for n in t['scenes'] if n['scene_id']==s['scene_id'])['end_s']==s['end_s']
 for s in prior['timing']['new_word_mapping'])
with wave.open(t['audio_file'],'rb') as f:
 checks['physical_audio_duration_unchanged']=f.getnframes()/f.getframerate()==prior['timing']['duration_s']
if not all(checks.values()): raise RuntimeError(json.dumps(checks))
rel= dict(issue_id='EV2-C01',status='closed_verified',checked_revision=sha(tp),checks=checks,
 evidence=dict(timing=str(tp),audio_sha256=audio_sha,previous_content_timing_qa=str(QA/'content_timing_qa.json')),
 unchanged_evidence_reused='원본53구 수치 재계산·PCM splice 검수는 이전 기록을 재사용. 이번에는 변경 필드/실파일SHA/장면시계만 재검수.',
 asr_reuse='ASR 이전 timing SHA는 당시 입력 기록으로 보존. 실제 음성SHA와 장면시계가 같아 재실행하지 않음.',
 actual_listening=False)
save('EV2-C01_recheck.json',rel)

samples=[
 ('S006',85,'representatives-old-lock/frame-00-at-85s.png','사진 중심: 큰 사진·명확한 수량·작은 위치안내. 미공개15/16위 노출은 최신 표본에서 해결됨.'),
 ('S013',252,'representatives-old-lock/frame-01-at-252s.png','인접 비교:8483/8473쌍과10쌍 차이가 읽힘. 기존 대형 지도보다 비교에 초점을 둠.'),
 ('S022',416,'representatives-old-lock/frame-02-at-416s.png','상위권:자연 비율 사진의 상하 여백 감소,5개 구 규모 목록 구분. 서해구 표기는 현행 공식 명칭에 부합.'),
 ('N001',442.574,'snapshots-main-locked/frame-28-at-442.574s.png','같은53개구·같은기준일·전체/초혼 구분 명시.1~4위 동일.동안/마포 초혼 순위와 수량은 해당 표본에서 아직 숨겨진 상태로 최종 표시값 검수는 인코딩 후 수행.'),
 ('N002',471.246,'snapshots-main-locked/frame-29-at-471.246s.png','남동16→27/5588,원미20→24/5982,미추홀10→20/6162가 직접 계산 결과와 일치.행·제목·출처·자막 잘림 미발견.'),
 ('I002',222.413,'snapshots-main-locked/frame-16-at-222.413s.png','초혼7634/6746·차이888과재혼영통733이 읽힘.재혼권선 최종값은 아직 숨겨져 있음.일부 상태만으로 모션 속도·전구간을 판정하지 않음.'),
 ('S006',85.051,'snapshots-main-locked/frame-08-at-85.051s.png','미공개15/16위의 지명·수량·막대 길이를 숨기고 소개된17~19위만 보임.흰 자막박스 유지;85.051초는84.5757~85.2794초 큐 사이이므로 빈 글자는 정상.'),
 ('S013',251.021,'snapshots-main-locked/frame-17-at-251.021s.png','미공개8/9위 지명·수량·막대 길이 숨김 확인.251.021초는250.7131~251.4353초 큐 사이로 빈 글자는 정상.'),
]
evidence=[]
for sid,sec,relpath,observation in samples:
 p=EP/'editor/top20-enhance-v2/evidence'/relpath
 evidence.append(dict(scene_id=sid,timecode_s=sec,path=str(p),sha256=sha(p),size=p.stat().st_size,
                      source_kind='editor_preview_PNG_not_final_encoded_frame',inspected_with='view_image',observation=observation))
receipt_path=EP/'editor/top20-enhance-v2/evidence/check-main-receipt.json'
r=read(receipt_path)
place=dict(checked_at=datetime.now(timezone.utc).isoformat(),scene_id='S022',verdict='서해구 현행 명칭 확인;시안 유지',
           source_title='인천광역시 서구 명칭 변경에 관한 법률',
           source_url='https://www.law.go.kr/LSW/lsInfoR.do?efYd=20260701&lsiSeq=286453&urlMode=lsInfoR&viewCls=lsInfoR',
           effective_date='2026-07-01',law_number='제21734호',
           scope='기존 인코딩 서구와 새 시안 서해구 차이만 공식 명칭 확인;순위 원자료 재조사 없음')
save('place_name_verification.json',place)
report=dict(task_id='top20-enhance-QA-v2',stage='representative_pre_render',created_at=datetime.now(timezone.utc).isoformat(),
 verdict='대표 시안 범위 통과;전체 렌더 전 확인된 차단0',critical_open=0,required_open=0,
 checked_revision=dict(timing_sha256=sha(tp),observed_check_receipt_sha256=sha(receipt_path),
                       observed_check_project_sha256=r['project_sha256'],freeze_pending=True),
 evidence=evidence,metadata_recheck=str(QA/'EV2-C01_recheck.json'),place_verification=str(QA/'place_name_verification.json'),
 decisions=[
  '사진 중심/인접 비교/상위권 세 구도는 유지.기준본의 같은 대형지도 반복과 사진 여백을 개선함.',
  '최신 S006/S013 미래순위 마스킹 직접 확인.같은 규칙의 나머지 장면은 최종 인코딩 후 확인.',
  'N001/N002의53개구·기준일·전체/초혼 비교를 확인.연도별 순위변화로 표현하지 않음.',
  'PNG 대표 시안으로 사전 통과 가능.대표 MP4는 요구하지 않으며 최종 MP4에서 전체 범위를 검수.',
  '체크영수증의 현재 관측 project SHA는81d57037…;이전 전달47a9625…와 구분하고 최종 freeze의 정확한 SHA에 연결할 것.',
 ],
 coverage=dict(preview_png_count=len(evidence),actual_final_encoded_frame_count=0,all_scenes=False,all_boundaries=False,
               continuous_playback=False,actual_listening=False,motion='unchecked;일부 정지 상태의 단계 노출만 확인',
               small_device_playback='unchecked',final_values_hidden_in_sample=['N001 동안/마포16/17위·6510/6487쌍','I002 재혼권선1563쌍·차이830쌍']),
 next_gate=dict(owner='director/editor',render_permission='사용자 기존 로컬 제작 범위;추가 승인 질문 없음',
                expected_receipt='editor/top20-enhance-v2/render_receipt_main_v1.json',
                final_report='qa/top20-enhance-v2/main_final.json',
                required_fields=['video_sha256','critical_open','required_open','full_decode','scope','evidence'],
                note='최종 인코딩 수신 후 정확한 파일SHA·480초초과·전체decode·모든장면/경계/긴자막/최대줌 검수.그 전 최종 통과파일을 만들지 않음.로컬검토본이며 업로드는 범위 밖.'))
save('representatives_review.json',report)
f=read(QA/'findings.json')
for finding in f['findings']:
 if finding['issue_id']=='EV2-C01':
  finding['status']='closed_verified';finding['checked_revision']=sha(tp)
  finding['resolution_evidence']=str(QA/'EV2-C01_recheck.json')
 if finding['issue_id'] in ['EV2-B01','EV2-B02','EV2-B04']:
  finding['status']='representative_scope_accepted_final_encoded_check_pending'
  finding['representative_evidence']=str(QA/'representatives_review.json')
save('findings.json',f)
save('issue_REPRESENTATIVES_HANDOFF.json',dict(issue_id='EV2-REPRESENTATIVES-HANDOFF',recipients=['director','editor:01a19bab-9d3b-7ed1-9e83-49c83b4661e9'],
 scene_id=['S006','S013','S022','N001','N002','I002'],문제='대표시안 차단0;EV2-C01 닫힘',
 evidence=str(QA/'representatives_review.json'),제안='세 구도·미래순위 마스킹·단계별 수치 노출을 유지해로컬 렌더 진행.최종freezeSHA와 MP4/receipt를 전달.',
 영향='N001/I002 숨겨진 최종값과 모든장면/경계/긴자막은 최종인코딩 검수에서 확인.서해구는 공식 현행명칭이므로 서구로 되돌리지 않음.',
 direct_message_sent=False,delivery_method='직접 메시지 도구 없음;공유QA파일로 총괄 전달'))
save('handoff.json',dict(task_id='top20-enhance-QA-v2',status='representatives_pass_final_encode_pending',
 artifacts=[str(QA/n) for n in ['baseline_audit.json','content_timing_qa.json','EV2-C01_recheck.json','representatives_review.json','issue_REPRESENTATIVES_HANDOFF.json']],
 input_revision=report['checked_revision'],verified=['변경 메타데이터/음성·시계 불변성','8개 시안PNG 직접 확인','미래순위 마스킹','현재서해구 공식명칭'],
 unresolved=[],pending=['최종freeze·인코딩handoff','최종MP4전체검수','실제청취·연속재생미실시'],
 affected_scenes=['S006','S013','S022','N001','N002','I002'],next_owner=['director','editor']))
for name in ['EV2-C01_recheck.json','representatives_review.json','findings.json','handoff.json']:
 read(QA/name)
print(json.dumps(dict(status='representatives_pass',metadata_closed=True,preview_pngs=len(evidence),critical_open=0,required_open=0,
 report=str(QA/'representatives_review.json'),observed_project_sha256=r['project_sha256']),ensure_ascii=False))
