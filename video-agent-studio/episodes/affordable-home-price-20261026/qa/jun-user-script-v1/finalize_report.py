"""수집한 독립 QA 근거를 한국어 findings/handoff로 묶는다. 외부 요청 없음."""
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
put=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inputs=read(OWN/'input_evidence.json')
previews=read(OWN/'preview_evidence.json')
pixels=read(OWN/'pixel_evidence.json')
assert not inputs['failed_checks']
checked=inputs['checked_file_hashes']
for entry in checked: assert sha(ROOT/entry['path'])==entry['sha256'],entry['path']+' changed after QA'
hashes={Path(e['path']).name:e['sha256'] for e in checked}
for p in previews['previews']:
    assert sha(ROOT/p['path'])==p['sha256']
    checked.append({'path':p['path'],'bytes':p['bytes'],'sha256':p['sha256']})
for p in [ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe',ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe',EP/'editor/jun-user-script-v1/preview_plan.json']:
    checked.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)})

guard={
 'method':'generate.mjs 전체 및 stage_generator.py 전체 정적 검토. node --check와 Python AST만 실행. 생성기 엔트리포인트·인증 요청·TTS는 실행하지 않음.',
 'revision':{'generator_sha256':hashes['generate.mjs'],'stage_generator_sha256':hashes['stage_generator.py']},
 'current_authorization':{'path':rel(EP/'director/jun-user-script-v1/authorization.json'),'exists':(EP/'director/jun-user-script-v1/authorization.json').exists(),'runtime_negative_test':'unchecked_생성기_미실행'},
 'checks':[
  {'check':'과거 편 승인 경로 미사용','result':'pass_static','evidence':'generate.mjs:18-34. 현재 EP의 director/jun-user-script-v1/authorization.json만 읽고 현재 script/input SHA, 원문 DOCX SHA, Jun/model, material_facts_cleared를 요구함.'},
  {'check':'승인 누락·불일치 시 네트워크 전 중단','result':'pass_static','evidence':'generate.mjs:20-35의 read/assert가 키 읽기(45-47) 및 최초 GET(54), POST(122)보다 앞섬. 실제 authorization.json 부재를 확인함.'},
  {'check':'7000 포함 크레딧 상한·추가현금0·충전/초과/자동재시도 금지','result':'pass_static','evidence':'generate.mjs:11,25-28,69,87-89,107-113,120-130. 예상 잔여 요청과 실제 사용량을 합산하며 단가1·잔액·초과사용 차단을 새 조회값에 요구함.'},
  {'check':'변경된 입력에 이전 승인 자동 승계 금지','result':'pass_static','evidence':'generate.mjs:22-26,99,103. 고정 input/body SHA와 authorization의 SHA 결합, 요청별 전송문 SHA 검사, 매 POST 전 승인/input/config 재해시.'},
  {'check':'중복 과금·실패 자동 재시도 차단','result':'pass_static','evidence':'generate.mjs:87,94,100-101,112-120,127-147. 배타적 실행 lock/receipt, pending/ambiguous 중단, 완료 파일 SHA 확인 후 skip. POST 재시도 루프 없음. GET429 backoff는 별개.'},
  {'check':'stage_generator는 입력/클라이언트만 준비','result':'pass_static','evidence':'stage_generator.py:25-64. 구 템플릿 문자열을 현재 경로/7장/5797/CAP7000으로 교체하고 각 교체를 assert함. 승인파일 생성·TTS 호출 없음.'},
  {'check':'레거시 경로의 실제 용도','result':'pass_static','evidence':'과거 housing-choice 편은 템플릿과 로컬 FFmpeg 경로, regional-price 편은 sha/readJSON/saveJSON/exists/findFFmpeg/decode 유틸리티만 사용. 구 CAP5807/loadInputs/authorization는 import 또는 호출하지 않음.'}
 ],
 'limitations':['실제 계정·요율·잔액 재조회 없음. 저장된 읽기 전용 스냅샷의 계산/해시만 확인.','승인 후 실행 경로와 제공자 응답 검증의 런타임 결과는 미확인.','QA 통과는 현재 버전의 신규 예산 승인이나 material-fact clearance를 대신하지 않음.']}
assert not guard['current_authorization']['exists']
put(OWN/'guard_evidence.json',guard)

first=read(OWN/'issue_JUN-IN-001.json')
first['status']='resolved_verified'
first['checked_revision']={'revision':'jun-user-script-v1_LF_inputs_reverified','narration_manifest_sha256':hashes['narration_manifest.json'],'generation_input_sha256':hashes['generation_input.json'],'generate_mjs_sha256':hashes['generate.mjs']}
first['resolution']={'method':'제작 담당의 완료 주장과 별개로 독립 audit_inputs.py에서 7개 장을 재검증','evidence':rel(OWN/'input_evidence.json'),'independent_checks':17,'failed_checks':0,'all7_input_bytes_equal_request_UTF8':True,'CRLF_count_each_chapter':0,'billed_characters':5797,'C01_actual_and_declared_sha256':'69369d48ddd267125a3114cc603db3d34a362102755d063ab9937947fd98668b','generator_entrypoint_executed':False}
put(OWN/'issue_JUN-IN-001.json',first)

caption_suggestions=[
 {'cue_id':'P008Q04','scene_id':'S02','display_lines':['내 통장에 있는 돈하고','저 가격이 바로 연결되지는 않거든요.']},
 {'cue_id':'P009Q02','scene_id':'S03','display_lines':['대출을 더 받았다고','그만큼 내 재산이 생기는 것도 아닙니다.']},
 {'cue_id':'P038Q01','scene_id':'S16','display_lines':['현금 1억 원을 더 모으니까','볼 수 있는 집값이 많이 올라갔죠.']},
 {'cue_id':'P039Q01','scene_id':'S17','text':'그리고 현금 2억 원이 있어도 내 소득으로 대출이 2억 원까지만 가능하다면,','display_lines':['그리고 현금 2억 원이 있어도','내 소득으로 대출이 2억 원까지만 가능하다면,']},
 {'cue_id':'P039Q02','scene_id':'S17','text':'같은 준비금을 남겼을 때 집값 예산은 3억 7천만 원입니다.','display_lines':['같은 준비금을 남겼을 때 집값 예산은','3억 7천만 원입니다.']}
]
cap_issue={'issue_id':'JUN-CAP-003','scene_id':['S02','S03','S16','S17'],'timecode':None,'severity':'recommended',
 '문제':'일부 자막의 폭 균형용 경계가 저/가격, 내/재산, 볼/수 및 가능하다면 조건절을 나눈다. 원문·금액 누락은 없으나 호흡 단위 개선을 권장한다.',
 'evidence':{'caption_plan_sha256':hashes['caption_plan.json'],'cue_ids':[x['cue_id'] for x in caption_suggestions],'method':'156큐 전체 텍스트 열람 및 문맥 검토. 음성 싱크 평가 아님.'},
 '수정안':{'exact_proposals':caption_suggestions,'constraints':'P039의 가능하다면,을 Q01로 이동하면 두 큐의 source_start/source_end도 원문 범위로 갱신. 원문 순서·숫자·156큐 수 유지. 모든 변경은 실제 음성 정렬 이후 확정 가능.'},
 'owner':'narration/editor','status':'open_optional','checked_revision':hashes['caption_plan.json']}
put(OWN/'issue_JUN-CAP-003.json',cap_issue)
dep_issue={'issue_id':'JUN-DEP-004','scene_id':'S01-S31','timecode':None,'severity':'recommended',
 '문제':'클라이언트가 다른 편의 common.mjs와 FFmpeg를 참조하지만 현재 generation_readiness는 이 실행 의존성의 해시를 고정하지 않는다. 현재 승인 경로 누출이나 잘못된 상한 사용은 발견하지 못했다.',
 'evidence':{'generator_sha256':hashes['generate.mjs'],'references':['generate.mjs:8 regional-price-recovery-20261022/narration/production-v1/common.mjs','generate.mjs:36 housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'],'checked_dependency_hashes':[x for x in checked if x['path'].endswith('/common.mjs') or x['path'].endswith('/ffmpeg.exe')]},
 '수정안':'새 유료 실행 전 common.mjs와 선택된 FFmpeg의 절대 경로·SHA를 generation_readiness/input_lock의 dependencies에 기록하고 실행 전 일치 여부를 확인한다. 현재 공용 코드는 그대로 읽기 전용으로 사용해도 된다.',
 'owner':'director/narration','status':'open_optional','checked_revision':hashes['generate.mjs']}
put(OWN/'issue_JUN-DEP-004.json',dep_issue)

preview_results=[]
for p in previews['previews']:
    preview_results.append({'id':p['id'],'scene_ids':['S18','S19'] if p['id']=='S18_S19' else [p['id']],
      'path':p['path'],'sha256':p['sha256'],'bytes':p['bytes'],
      'codec':'h264','resolution':[1920,1080],'fps':'30/1','duration_s':float(p['probe']['format']['duration']),
      'audio_streams':0,'full_technical_decode':'pass','snapshot_only':True,
      'sample_times_s':[f['time_s'] for f in p['frames']],
      'full_size_manually_viewed_time_s':10.7 if p['id']=='S18_S19' else p['frames'][-1]['time_s'],
      'small_size':[640,360],'all_listed_samples_manually_viewed_small':True,
      'snapshot_result':'확인한 표본에서 본문·금액·단위·하단 자막 잘림 없음. 원문 가정과 표시값 일치.',
      'continuous_playback':False,'actual_listening':False})

findings={
 'task_id':'JUN-USER-SCRIPT-V1-INPUT-QA','role':'qa','revision':'jun-user-script-v1','checked_at_utc':datetime.now(timezone.utc).isoformat(),
 'status':'input_QA_pass_and_representative_snapshot_review_only',
 'summary':{'critical_open':0,'required_open':0,'required_resolved_verified':1,'recommended_open':2,'false_positive_closed':1},
 'findings':[first,cap_issue,dep_issue],
 'false_positive_reviews':[{'issue_id':'JUN-VIS-002','scene_id':['S18','S19','S21'],'timecode':{'S18_S19':10.7,'S21':359/30},'status':'false_positive_closed','classification':'not_a_real_defect',
   'rejected_hypothesis':'상단 브랜드/상태 글자가 캔버스 y=0에서 잘린다는 초기 인상',
   'evidence':{'pixel_receipt':rel(OWN/'pixel_evidence.json'),'header_contact':rel(OWN/'header_contact.png'),'actual_dark_pixel_bounds':pixels['headers'],'S18_S19_MP4_SHA':'b199942863c47795bf1fb75dc653280d36dee82a0e3a63559a59d5d2c2fd51bf'},
   'conclusion':'독립 추출 프레임에서 세 시안 모두 브랜드 y32..51, 상태 y34..53. 상단 잘림 없음. 실제 헤더 결함·수정·재렌더 필요로 기록하지 않는다. 상위의 v1/v2 동일 SHA 확인과도 일치.'}],
 'input_validation':{'evidence':rel(OWN/'input_evidence.json'),'independent_checks':17,'failed':0,'source_paragraphs':48,'scenes':31,'transformations':175,
   'original_body_characters_excluding_separators':5701,'reading_characters_excluding_separators':5715,'reading_delta':14,'chapter_internal_LF_separators':82,'billed_characters':5797,'chapter_characters':[550,731,1026,838,1026,803,823],
   'proposed_cap':7000,'correction_headroom':1203,'additional_cash_cap_krw':0,'new_version_budget_approval_required':True,'generation_authorized':False,
   'caption_cues':156,'protected_spans':119,'checked_caption_line_or_cue_boundaries':262,'amount_unit_splits':0,'max_line_characters':31,'caption_timing_measured':False,
   'P033Q03':['오늘은 조금 내려서','2억 6천6백만 원짜리 집을 예로 들게요.']},
 'generator_review':{'evidence':rel(OWN/'guard_evidence.json'),'result':'현재 승인 부재 시 정적 경로상 fail-closed. 과거 승인 재사용 없음.','generator_entrypoint_executed':False,'node_syntax_check':'pass','Python_AST_check':'pass','new_TTS_POST_calls':0,'new_authenticated_requests':0},
 'preview_review':{'evidence':rel(OWN/'preview_evidence.json'),'pixel_evidence':rel(OWN/'pixel_evidence.json'),'previews':preview_results,'unique_sampled_frames_manually_viewed':26,'full_resolution_unique_frames':3,'headers_explicitly_viewed_as_full_pixel_crop':3,'small_frame_size':[640,360],
   'boundary_samples':'각 짧은 시안의 첫·마지막 상태, S18→S19 5.9667/6/6.0333초를 표본 확인','camera_zoom':'시안은 고정 카메라. 막대 scaleX 전개를 실제 표본에서 확인. 최대 카메라 줌 장면 별도 없음.',
   'money_proportions':{'S13':'자기자금8000만원 200px / 대출1억8600만원 465px = 80:186. 준비금2000만원은 분리.','S18_S19':'자기자금2.6/3.5/4.4억의 실제 파란 막대312/420/528px. 대출4억 금색 막대는 세 행 모두 동일. 경계선 포함 픽셀483px.','S21':'세금1016만4000+중개/VAT290만4000=1306만8000; 잔여2693만2000, 합계4000만원. 약1016/290/1307/2693만원의 원문과 반올림 일치. 금색/초록 픽셀234/484는 1306.8:2693.2 비율에 래스터화 오차 이내.'},
   'continuous_playback':'unchecked','actual_listening':'unchecked','narration_sync':'unchecked_no_voice_yet','full_film_render':'unchecked_not_in_task','all31_scene_visual_QA':'unchecked_only_4_representative_scene_IDs'},
 'checked_file_hashes':checked,
 'limitations':['금융정책/세법의 새 자료 조사나 유효성 승인 범위는 포함하지 않음. 사용자 원문의 낭독·표시 보존 및 내부 계산 대조 범위.','저장된 계정 스냅샷18981 잔액은 현재 실시간 잔액 검증이 아님.','표본 프레임/전체 기술 디코드는 연속 시청·실제 청취·주관적 모션 품질 검수와 다름.','실제 음성 확정 후 자막 싱크·수치 발음·호흡·전체31장면 및 경계는 별도 검수.'],
 'ownership':'qa/jun-user-script-v1/만 작성. state.json/scenes.json/decisions.json 및 다른 담당 파일 수정 없음.'}
put(OWN/'findings.json',findings)
handoff={'task_id':findings['task_id'],'role':'qa','status':'completed_scoped_input_and_snapshot_QA',
 'input_revisions':{name:hashes[name] for name in ['narration_manifest.json','generation_input.json','budget_proposal.json','caption_plan.json','generate.mjs','stage_generator.py']},
 'outputs':[rel(OWN/x) for x in ['findings.json','input_evidence.json','guard_evidence.json','preview_evidence.json','pixel_evidence.json','header_contact.png']],
 'affected_scene_ids':[f'S{i:02}' for i in range(1,32)],
 'checks':[{'check':'원문48문단/31장면·발음변환175·5797 과금문자·156자막','result':'pass','evidence':rel(OWN/'input_evidence.json')},{'check':'JUN-IN-001 LF/SHA 회귀','result':'resolved_verified','evidence':rel(OWN/'issue_JUN-IN-001.json')},{'check':'대표 MP4 3개·26 표본·금액 비례','result':'pass_sampled_only','evidence':rel(OWN/'preview_evidence.json')},{'check':'상단 잘림 가설','result':'false_positive_closed','evidence':rel(OWN/'pixel_evidence.json')},{'check':'실제 청취/연속 재생/음성 싱크/전체31장면','result':'unchecked','evidence':None}],
 'open_issue_ids':['JUN-CAP-003','JUN-DEP-004'],'required_open_issue_ids':[],
 'next_role':'director','next_actions':['선택적 자막 의미 경계/실행 의존성 해시 개선안 판단.','유료 생성 전 현재 버전 SHA를 명시한 신규 예산 승인과 material-fact clearance 유지.','실제 음성 이후 정렬·발음·싱크 및 본편 QA 진행.'],
 'authority':'승인파일 미작성, 생성기·TTS·인증 요청 미실행. 상단 잘림은 오탐이며 헤더 수정 필요 없음.',
 'summary':'원문48문단/31장면, 값 보존175변환, 7장5797문자, 7000상한·현금0, 156자막 대조 통과. LF/SHA 필수문제 독립 재검증으로 해결. 실제 대표 MP43개 26표본·원본크기3프레임·640축소·금액비례 확인. 상단 잘림 오탐 폐기. 권장2건, 필수미해결0. 청취/연속재생/전체본은 미검수.'}
handoff['input_revisions']['source_doc_sha256']='f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73'
handoff['checked_file_hashes']={'reference':rel(OWN/'findings.json'),'count':len(checked)}
put(OWN/'handoff.json',handoff)
print(json.dumps({'findings':rel(OWN/'findings.json'),'handoff':rel(OWN/'handoff.json'),'summary':findings['summary'],'checked_files':len(checked)},ensure_ascii=False))
