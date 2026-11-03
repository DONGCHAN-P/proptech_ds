"""Start the authorized next episode only after the first private release is verified."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIRST=HERE.parents[1]
ROOT=FIRST.parents[2]
STUDIO=ROOT/'video-agent-studio'
EP=STUDIO/'episodes/affordable-home-price-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

completed=read(FIRST/'outputs/private-release-v3/completion.json')
assert completed['status']=='private_uploaded_processed_with_Korean_captions'
assert completed['visibility']=='private' and completed['known_required_open']==[]
lock=read(HERE/'next_episode_input_lock.json')
for row in lock['files']:assert sha(HERE/row['path'])==row['sha256'],row['path']
assert not EP.exists(),'Keep existing episode; resume it instead of recreating.'
for sub in ['research','writer','visual','narration','editor','qa','outputs','director/production-v1']:
    (EP/sub).mkdir(parents=True,exist_ok=True)
inputs=EP/'research/prepared-v1';inputs.mkdir()
for name in ['next_episode_research','next_case_engine_prep','next_case_engine_prep_v2','next_policy_independent_qa']:
    shutil.copytree(HERE/name,inputs/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ['next_episode_editorial_plan.json','next_episode_story_findings.json',
             'next_case_independent_arithmetic.json','next_episode_input_lock.json','next_episode_hf_addendum.json']:
    shutil.copy2(HERE/name,inputs/name)
shutil.copy2(HERE/'media_assets.json',EP/'director/production-v1/media_assets.json')
source_files=[p for p in inputs.rglob('*') if p.is_file()]
save(inputs/'inheritance_manifest.json',{'source':rel(HERE),'policy_as_of':'2026-10-26',
    'files':[{'path':p.relative_to(inputs).as_posix(),'sha256':sha(p)} for p in source_files],
    'scope':'Immutable prepared public sources and synthetic cases; current outline separately pinned by independent QA.'})
base=read(inputs/'next_episode_research/policy_facts.json')
delta=read(inputs/'next_episode_research/policy_facts_v2.json')
facts={row['claim_id']:row for row in base['facts']};facts.update({row['claim_id']:row for row in delta['facts']})
save(EP/'research/facts.json',{'episode_id':EP.name,'as_of_kst':'2026-10-26','facts':list(facts.values()),
    'merge_rule':'v2 overrides matching claim_id; retain exact conditions, qualification and primary source IDs.',
    'source_packs':['research/prepared-v1/next_episode_research/sources.json','research/prepared-v1/next_episode_research/sources_v2.json'],
    'remaining_conditions':'Bank/guarantee execution, actual miscellaneous quotes and net education tax after relief remain individual inputs.'})
ledger=read(inputs/'next_case_engine_prep_v2/results.json')
keep=ledger['video_review_subset']['case_ids']
fields=['case_id','profile_id','household_id','price_krw','valuation_krw','deduction_krw','deduction_note',
        'rate_used','rate_status','eligible_under_stated_inputs','limits_krw','binding_constraints','loan_ceiling_krw',
        'transaction_costs','required_loan_krw','cash_required_including_reserve_krw','cash_shortfall_krw',
        'cash_feasible','payment_if_financeable_krw','cash_and_monthly_budget_feasible']
save(EP/'research/verified_case_packet.json',{'policy_as_of':'2026-10-26','source_results_sha256':sha(inputs/'next_case_engine_prep_v2/results.json'),
    'conditions':read(inputs/'next_case_engine_prep_v2/cases.json'),
    'cases':[{k:r[k] for k in fields} for r in ledger['case_results'] if r['case_id'] in keep],
    'affordability_A':ledger['affordability_A'],'conditional_relief_table':ledger['conditional_relief_table'],
    'independent_arithmetic_checks':157,'independent_policy_logic_checks':10,
    'scope':'Prepared conditional illustration; actual script and exact-version dual reviews still required.'})
authorization=read(HERE/'authorization.json')
authorization.update(episode_id=EP.name,first_episode_completed=completed['url'],
    sequence=['용어·전제·가격별 사례 정리','대본 및 근거 양측 검수','무료 TTS·의미 자막','화면 제작·양측 최종 검수','YouTube 비공개 업로드·상태 확인'])
authorization.pop('first_episode_script',None)
save(EP/'director/production-v1/authorization.json',authorization)
now=datetime.now(timezone.utc).isoformat()
outline=read(inputs/'next_episode_editorial_plan.json')
brief=read(STUDIO/'templates/brief.template.json')
brief.update(episode_id=EP.name,title='내 돈 2억5천만원, 감당 가능한 집값은?',
    task_type='new_video',goal=outline['core_message'],policy_as_of='2026-10-26',
    predecessor=completed,authorization=rel(EP/'director/production-v1/authorization.json'),
    opening_question='보유자금 2억5천만원에 주담대 총액상한 6억원을 더하면 8억5천만원 집을 살 수 있을까요?',
    opening_scope='총액상한·LTV·DSR·현금·월 예산을 실제 사례로 차례로 적용해 답한다. 조건부 계산을 보편적 한도로 확대하지 않는다.',
    chapters=outline['chapters'],target_minutes=[14,20],voice='free ko-KR-InJoonNeural; paid Jun not authorized',
    visual_direction='직전 주거비 비교 편의 Pretendard·아이보리·네이비·파랑·골드·초록과 고정 흰 자막 박스 계승. 현금 워터폴·담보 막대·소득 예산·세금 곡선·복비 계단·영수증·상품 필터·금리 시간축으로 자료 역할을 바꾼다.',
    audience_language='합니다체, 첫 등장 용어를 일상어로 설명. 소제목은 번호+주제. 불필요한 부정형 면책·AI 개념 이미지 배지 제거.',
    caption_contract='처음부터 원문·표시문 분리, 숫자·단위 보호, WordBoundary 의미 단위 1~2줄. 앞편 caption-v7 규칙과 실제 글리프 경계 검수 재사용.',
    required_content=outline['editorial_controls'],next_episode_promise='정한 예산 안에서 지역과 단지를 데이터로 비교하는 단계',
    sources=['research/facts.json','research/verified_case_packet.json','research/prepared-v1/next_episode_story_findings.json',
             'research/prepared-v1/next_policy_independent_qa/findings.json'],
    prohibited=['사진·차트의 무관한 반복','글자 잘림','걷는 졸라맨','유료 TTS','무조건 최대 대출 승인 단정','공개·예약 게시'])
save(EP/'brief.json',brief)
state=read(STUDIO/'templates/state.template.json')
state.update(episode_id=EP.name,stage='facts_ready_script_in_progress',updated_at=now,
    topic_status='authorized_by_current_direct_user_request',script_status='pending_dual_content_review',
    budget_status='free_TTS_only_cash_cap0',paid_generation_authorized=False,
    private_upload_authorized_after_exact_dual_QA=True,public_release_authorized=False,
    predecessor_private_upload=completed['url'])
save(EP/'state.json',state)
save(EP/'decisions.json',{'episode_id':EP.name,'decisions':[
    {'id':'affordable-price-topic-direct-20261026','gate':'topic','status':'authorized','approval_basis':'Current direct user request explicitly commissions this episode after first private upload.','at_utc':now},
    {'id':'affordable-price-free-budget-20261026','gate':'budget','status':'authorized_free_only','cash_cap_krw':0,'paid_TTS_authorized':False,'at_utc':now}]})
save(EP/'scenes.json',{'episode_id':EP.name,'scenes':[],'status':'pending_actual_storyboard'})
pre=read(STUDIO/'templates/episode_preflight.json');pre.update(episode_id=EP.name,status='facts_ready_script_pending')
pre['baseline'].update(previous_video=completed['url'],sha256=completed['video_sha256'],
    current_video='config/current_video.json',public_baseline_snapshot=read(ROOT/'config/current_video.json'),script_revision='new_episode_pending',audio_revision='free_InJoon_pending',
    brand_intro='director/production-v1/media_assets.json',brand_outro='director/production-v1/media_assets.json',bgm='Thinking Music / Kevin MacLeod / CC BY 4.0')
pre['story'].update(opening_question=brief['opening_question'],previous_episode_reference=completed['url'],
    next_episode_promise=brief['next_episode_promise'],order=[r['question'] for r in outline['chapters']],
    each_section_answers=['용어의 뜻','대상과 조건','계산 근거','막히는 제약','필요 현금과 월 부담'],candidate_scope='synthetic_affordability_cases')
pre['visual_defaults']['locator']='not_applicable_financial_episode'
pre['representative_previews']=['cash_waterfall','LTV_DSR_constraint','tax_curve_and_broker_step','6_9_12_case_table','policy_and_newborn_timeline','monthly_budget_shock','CTA_outro_boundary']
pre['facts_required']=['official_effective_dates','household_income_debt_assets','region_firstbuyer_and_collateral','DSR_DTI_stress_vs_contract_rate','price_product_tax_fee_thresholds','guarantee_room_deduction','relief_conditions','source_rights_credit']
pre['approvals']['topic'].update(decision_id='affordable-price-topic-direct-20261026',status='authorized_by_direct_user_request')
pre['approvals']['budget'].update(decision_id='affordable-price-free-budget-20261026',status='authorized_free_only',cash_cap=0,credits_cap=0)
pre['approvals']['pre_upload']['visibility']='private'
save(EP/'director/episode_preflight.json',pre)
queue=read(ROOT/'config/video_production_queue_20261026.json')
queue['items'][1].update(status=state['stage'],policy_as_of='2026-10-26',episode_root=rel(EP),brief_sha256=sha(EP/'brief.json'))
save(ROOT/'config/video_production_queue_20261026.json',queue)
print(json.dumps({'episode':rel(EP),'stage':state['stage'],'prepared_cases':len(keep),'policy_claims':len(facts),'new_paid_calls':0},ensure_ascii=False))
