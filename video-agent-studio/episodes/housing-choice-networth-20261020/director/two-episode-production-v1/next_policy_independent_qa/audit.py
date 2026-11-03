"""담당 폴더에만 기록하는 읽기전용 정책·사례 QA."""
import sys
sys.dont_write_bytecode = True
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
FILES = [
    'next_episode_research/sources.json', 'next_episode_research/policy_facts.json',
    'next_episode_research/sources_v2.json', 'next_episode_research/policy_facts_v2.json',
    'next_episode_research/gaps_v2.json', 'next_case_engine_prep_v2/engine.py',
    'next_case_engine_prep_v2/assumptions.json', 'next_case_engine_prep_v2/cases.json',
    'next_case_engine_prep_v2/results.json', 'next_case_engine_prep_v2/tests/test_engine.py',
    'next_case_independent_arithmetic.json', 'next_episode_editorial_plan.json',
    'next_episode_story_findings.json',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


packet = read('next_case_engine_prep_v2/cases.json')
assumptions = read('next_case_engine_prep_v2/assumptions.json')
results = read('next_case_engine_prep_v2/results.json')
arithmetic = read('next_case_independent_arithmetic.json')
editorial = read('next_episode_editorial_plan.json')
manifest = [dict(path=p, sha256=digest(ROOT / p), bytes=(ROOT / p).stat().st_size) for p in FILES]
spec = importlib.util.spec_from_file_location('qa_case_engine', ROOT / 'next_case_engine_prep_v2/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
cases = engine.expand_cases(packet)
checks = []


def check(name, result):
    checks.append(dict(check=name, passed=bool(result)))
    assert result, name


def case(profile):
    return next(c for c in cases if c['profile_id'] == profile and c['price_krw'] == 600000000 and c['deduction_krw'] == 0)


check('157검사 기록이 현재 v2 결과에 귀속', arithmetic['source_sha256'] == digest(ROOT / 'next_case_engine_prep_v2/results.json') and arithmetic['checks'] == 157 and arithmetic['failed'] == 0)
check('결과의 엔진·입력 해시 일치', all(digest(ROOT / 'next_case_engine_prep_v2' / f) == h for f, h in results['input_sha256'].items()))
check('디딤돌/보금자리 6억 포함·초과 제외', all(engine.evaluate(case(p))['eligible_under_stated_inputs'] and not engine.evaluate(dict(case(p), price_krw=600000001))['eligible_under_stated_inputs'] for p in ['B_didim', 'B_bogeum']))
check('신생아 9억 포함·초과 제외', engine.evaluate(dict(case('B_newborn'), price_krw=900000000))['eligible_under_stated_inputs'] and not engine.evaluate(dict(case('B_newborn'), price_krw=900000001))['eligible_under_stated_inputs'])
check('기금 순자산5.11억 포함·초과 제외', all(engine.evaluate(dict(case(p), net_assets_krw=511000000))['eligible_under_stated_inputs'] and not engine.evaluate(dict(case(p), net_assets_krw=511000001))['eligible_under_stated_inputs'] for p in ['B_didim', 'B_newborn']))
check('B의 신혼/최근출산 자격 분기', not engine.evaluate(dict(case('B_didim'), married_within_7_years=False))['eligible_under_stated_inputs'] and not engine.evaluate(dict(case('B_newborn'), child_within_2_years=False))['eligible_under_stated_inputs'])
check('정책상품 DSR40 미대입·DTI60 적용', all(packet['profiles'][p]['dsr_ratio'] is None and packet['profiles'][p]['dti_ratio'] == '.6' for p in ['B_didim', 'B_bogeum', 'B_newborn']))
subset = set(results['video_review_subset']['case_ids'])
check('반사실·상품부적격 제외한 후보18개', len(subset) == 18 and all((r['case_id'] in subset) == (r['deduction_scenario_status'] != 'counterfactual_sensitivity' and r['eligible_under_stated_inputs']) for r in results['case_results']))
check('감면 기본표 미적용·미합산·순세금 미확정', all(not r['applied_to_base'] and not r['additive'] and r['net_tax_after_relief_krw'] is None for r in results['conditional_relief_table']))
proposal = editorial['case_design_proposal']
check('현재 구성안 핵심 입력과 사례 일치', proposal['cash_krw'] == packet['common']['cash_krw'] and proposal['reserve_krw'] == packet['common']['reserve_krw'] and proposal['annual_bank_recognized_income_krw'] == packet['profiles']['A_ordinary']['annual_income_krw'] and proposal['separate_policy_household']['household_income_krw'] == packet['profiles']['B_didim']['annual_income_krw'])

revision = dict(case_engine=results['revision'], results_sha256=digest(ROOT / 'next_case_engine_prep_v2/results.json'), policy_v2_sha256=digest(ROOT / 'next_episode_research/policy_facts_v2.json'), editorial_sha256=digest(ROOT / 'next_episode_editorial_plan.json'))
recorded_editorial_hash = next(x['sha256'] for x in assumptions['input_versions'] if Path(x['path']).name == 'next_episode_editorial_plan.json')
findings = []


def finding(number, scene, claims, case_ids, problem, evidence, correction, status):
    findings.append(dict(issue_id=f'NQA-{number:02}', scene_id=scene, timecode=None,
                         severity='recommended', claim_ids=claims, case_ids=case_ids,
                         **{'문제': problem, 'evidence': evidence, '수정안': correction},
                         owner='director / future_writer / case_engine_owner',
                         status=status, checked_revision=revision))


finding(1, 'PREP_METADATA', [], ['A_*', 'B_*'],
        'assumptions.json의 구성안 입력 해시가 현재 파일과 다릅니다.',
        [dict(path='next_case_engine_prep_v2/assumptions.json', location='input_versions[next_episode_editorial_plan.json]', recorded_sha256=recorded_editorial_hash, current_sha256=revision['editorial_sha256']),
         dict(path='next_episode_editorial_plan.json', location='case_design_proposal', observation='현재 현금·예비자금·A 인정소득·B 합산소득은 사례와 일치. 157검사 결과 해시는 현재v2와 일치.')],
        '대본 입력 고정 때 현재 구성안 해시와 실제 변경 범위를 기록합니다. 수치가 같다는 이유로 옛 구성안 전체의 검수를 승계하지 않습니다.',
        'open_metadata_refresh_before_script_lock')
finding(2, 'PREP_CH03_CH06', ['L01','L03','L04','L06','M01','M02','M03','M04','M08','M09'],
        ['A_ordinary_*','A_first_*','B_bogeum_P600000000_C0','B_newborn_P900000000_C55000000'],
        '조건부 담보 상한을 일반 실행한도로 넓히지 않도록 전제를 유지해야 합니다.',
        [dict(path='next_case_engine_prep_v2/cases.json', location='notes / profiles', observation='서울 투과·V=P·기존부채/선순위/임대차0, A 인정·가구소득1억. 서민실수요 소득9천 이하 예외와 구분.'),
         dict(path='next_episode_research/evidence/v2/bogeum_2026_p31.png', location='PDF31쪽/인쇄27쪽', observation='아파트 방수공제 없음. 실제 임대차 있으면 임대보증금 반영 원문 직접 열람.')],
        'A C0은 보증승인 등 조건부, C55는 미커버1방5500만원 가정으로 병기합니다. 보금자리 빈 아파트0은 자체규정입니다. 신생아9억 C0/보금자리 C55 반사실은 현재 후보에서 제외합니다. 6/9/12 상품·세금 문턱과 15/25 일반 총액 문턱을 구분합니다.',
        'condition_already_recorded_preserve_at_script_gate')
finding(3, 'PREP_CH07_CH08', ['D01','D02','D03','D04','D05','B01','B02','B03','N01','N02','N03','N04','P01','P02','P03','P04','HFV2_01','HFV2_02','HFV2_03','HFV2_04','HFV2_05'],
        ['B_didim_*','B_bogeum_*','B_newborn_*'],
        '가구B의 자격·거주·신혼 예외를 가구A 및 다른 상품에 자동 적용하지 않아야 합니다.',
        [dict(path='next_case_engine_prep_v2/cases.json', location='common / B profiles', observation='별도B 합산소득8000만·순자산2.5억·신혼/생초/최근2년출산·84㎡. 합산8500만 이하라 신혼1인소득 예외 미사용.'),
         dict(path='next_episode_research/evidence/v2/didim_20260618_p34.png', location='PDF34쪽/인쇄31쪽', observation='실행1개월내 전입·전입일부터2년 거주 원문 직접 열람.'),
         dict(path='next_episode_research/policy_facts_v2.json', location='HFV2_01~05', observation='10/19 현행FAQ는 총괄 직접열람 인계. 이번QA의 실시간 원문 재열람 아님.')],
        'B 무주택·신혼·출산·자산·면적을 별도 표시합니다. 디딤돌/보금자리 주택6억, 신생아9억과 각3.2/4.2/4억 대출한도를 분리합니다. 정책신규 규제DSR 예외에도 DTI·신용·보증·거주 심사가 남습니다. 신혼 설명은 HFV2_01~05를 우선하고 1인소득/부채와 부부 확인항목을 섞지 않습니다.',
        'condition_already_recorded_preserve_at_script_gate')
finding(4, 'PREP_CH02_CH05', ['T01','T02','T03','T04','T05','C01','C02','C03','C04','C05','C06','C07'], ['A_*','B_*'],
        '무감면 총비용과 감면후 확정세금, 기타 계획비를 구분해야 합니다.',
        [dict(path='next_case_engine_prep_v2/results.json', location='transaction_costs / conditional_relief_table', observation='6/9/12억 비용1074만/3615만/4902만원. 중개상한+일반과세VAT10%·기타150만 계획예산 포함. 감면 미차감·미합산·순납부세액null.'),
         dict(path='next_episode_research/gaps_v2.json', location='G05~G08', observation='감면후 교육세·실제비용 미확정은 정당한 조건부 입력.')],
        '중과없는84㎡ 통상아파트·감면전·일반과세 중개사 상한 가정을 표시합니다. 생초200만/출산500만은 자격별 최대액이며 자동700만 합산이나 기본표 자동차감을 하지 않습니다. 기타150만은 견적이 아니며 예비3000만은 비용이 아닌 잔존현금입니다.',
        'condition_already_recorded_preserve_at_script_gate')
finding(5, 'PREP_CH04_CH08_CH09', ['L02','S01','S03','N03'], ['A_first_P600000000_C0','B_newborn_P600000000_C0','A_first/C0/affordability'],
        '심사금리·초기상품금리·계획금리와 월예산 역산의 의미를 유지해야 합니다.',
        [dict(path='next_episode_research/evidence/stress_page_1.png', location='PDF1쪽', observation='수도권/규제 스트레스하한3.0%p·변동형100% 직접 열람. A 심사7%는4%+3%p 가정.'),
         dict(path='next_case_engine_prep_v2/assumptions.json', location='credit_assumptions', observation='디딤돌/보금자리4% 계획가정. 신생아2.9%는 기본특례5년 초기금리, 이후 미확정.'),
         dict(path='next_episode_story_findings.json', location='I07~I09', observation='역산6억8019만/5억6586만원·월액은 현재v2와 일치.')],
        '은행 월납부는4%, DSR 심사는7%로 나눕니다. 신생아2.9%를30년 고정이나 확정 총이자로 설명하지 않습니다. 4→6%는 동일 최초원금/360개월 민감도입니다. A 생초6억 C0의 필요대출 월액 약186.5만원은 목표170만원을 넘는다는 점도 분리합니다.',
        'condition_already_recorded_preserve_at_script_gate')

pages = ['bankreg_20261002_p8.png','bankreg_20261002_p9.png','bank_rules_annex18_20260630_p9.png','didim_20260618_p19.png','didim_20260618_p28.png','didim_20260618_p34.png','bogeum_2026_p20.png','bogeum_2026_p21.png','bogeum_2026_p31.png']
pages = ['next_episode_research/evidence/v2/' + p for p in pages] + ['next_episode_research/evidence/stress_page_1.png']
merged = {}
for file in ['policy_facts.json','policy_facts_v2.json']:
    for fact in read('next_episode_research/' + file)['facts']:
        merged[fact['claim_id']] = fact
coverage = dict(
    input_manifest=manifest, merge_rule='동일claim_id는v2우선; 신혼세칙은HFV2상세항목우선', merged_claim_count=len(merged),
    code_review='engine.py 및 tests/test_engine.py 열람. 원본results를 쓰는 engine.main/전체테스트 미실행. evaluate로 자격·제외 논리만 확인.',
    arithmetic_reuse='현재v2 SHA일치157checks/0failed 재사용;157산술 재실행 없음', independent_logical_checks=checks,
    primary_pages_visually_inspected=[dict(path=p,sha256=digest(ROOT/p)) for p in pages],
    cached_pdf_sha256_verified={p:digest(ROOT/'next_episode_research/evidence/v2'/p) for p in ['bankreg_20261002.pdf','bank_rules_annex18_20260630.pdf','didim_20260618.pdf','bogeum_2026.pdf']},
    inherited_evidence='웹원문 LTV/상품소득·자산·세금/요율·10월 신혼FAQ 등은 제공 출처팩 열람기록 사용. 이번QA가 모든 원문을 재열람했다는 의미 아님.',
    primary_policy_inference='P01 상품명별 신규DSR예외는2024 FSC명시자료와2026 감독규정/세칙·상품DTI를 교차한 해석. 단일2026조문에 상품명이 직접 열거된다는 주장은 하지 않음.',
    live_browsing='미실행: 캐시 대조에서 새 정책 불일치 미발견. 전면최신성 수집 범위 아님.',
    tools_limit='지정Python의fitz/pypdf/pdfplumber없음. 제공 공식PDF 캐시PNG10쪽 실제열람으로 대체.',
    actual_listening='unchecked / 대상미제작', continuous_playback='unchecked / 대상미제작', mp4_frames='범위밖', paid_api_calls=0, external_payloads_sent=0)
report = dict(task_id='next-policy-independent-qa-v1', reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              status='approved_with_scope', critical=0, required=0, recommended=5, checked_revision=revision,
              approval_scope='현재 연구준비본의 정책·사례 논리만. 실제대본/미디어/상품실행/업로드 승인이 아님.',
              conclusion='검토한 조건부 사례와v2정책 병합에서 확인된 필수오류 없음. 기존 미확정 실행입력과 주장조건 유지.',
              approved_conditional_case_ids=sorted(subset), coverage=coverage,
              audit_summary=['A: 서울투과·인정/가구소득1억·부채0·V=P·30년변동4%/심사7%·일반40/생초70. LTV/DTI/DSR/총액/매매가의 최솟값과 담보차감 순서 적합.',
                             'B: 별도 합산8000만·순자산2.5억·신혼/생초/최근출산·84㎡. 6억/9억 상품가격과3.2/4.2/4억 상품한도를 구분. DSR예외와 DTI/거주 의무 분리.',
                             '은행C0/5500만 조건부와 보금자리 빈아파트0 구분. 신생아6억초과 보증은2025회신·현행FAQ 교차해석의 제한을 유지. 전은행금지/자동면제 단정 없음.',
                             '감면전 비용·VAT·계획예산·잔존예비현금 구분. 최저 필요대출/빌릴수있는상한/부족자금/월목표 구분. 현재 구성메모는v2 수치 반영.'],
              open_items=['NQA-01 구성안 입력해시 갱신(권장)', 'G05 감면후교육세/총세금', 'G10/CE_G01 실제은행 MCI/MCG/HF보증 승인', 'G07/G08/CE_G03 실제 채권/등기/법무사/인지 견적', 'CE_G02 정책 실제심사금리/신생아 특례종료후금리'],
              next_gate='첫영상 비공개업로드 실제완료 후 총괄지시로 대본 작성·현재시점 조건표현 별도검수.')
write('findings.json', dict(task_id=report['task_id'], status='approved_with_scope', scope='research_preparation_only', summary=dict(critical=0,required=0,recommended=5), findings=findings))
write('policy_and_case_review.json', report)
write('issue_NQA-HANDOFF.json', dict(issue_id='NQA-HANDOFF', scene_id='PREP_CH02~CH09',
      **{'문제':'필수수정0건. 입력구성안 해시1건 갱신과 기존 주장조건 보존 권장.', 'evidence':'findings.json NQA-01~05; policy_and_case_review.json coverage', '제안':'첫업로드 완료후 대본게이트에서 반영.', '영향':'다음편 버전추적/조건표현. 첫영상 렌더·업로드 영향없음.'},
      owner='video_director', status='ready_for_director', delivery='직접 에이전트 메시지도구 없음. 로컬issue파일/최종응답으로 인계.'))
write('handoff.json', dict(task_id=report['task_id'], status='approved_with_scope', owner='video_qa',
      output_paths=[(OUT/p).as_posix() for p in ['findings.json','policy_and_case_review.json','issue_NQA-HANDOFF.json']],
      input_versions='policy_and_case_review.json coverage.input_manifest:13개파일SHA256',
      validation=dict(required=0,recommended=5,independent_logical_checks=len(checks),all_passed=all(c['passed'] for c in checks),arithmetic='해시일치157검사 재사용',primary_review='원문 캐시PNG10쪽 실제열람',playback_listening='unchecked/범위밖'),
      unresolved=report['open_items'], affected_scenes=['PREP_CH02','PREP_CH03','PREP_CH04','PREP_CH05','PREP_CH06','PREP_CH07','PREP_CH08','PREP_CH09'],
      next_owner='video_director; 첫업로드 실제완료 후 대본담당',
      scope='연구준비 논리만 승인. 실제대본 승인 아님. 다른담당/공통상태 변경·신규episode/미디어/TTS/업로드·유료/외부전송 없음.'))
print(json.dumps(dict(status='approved_with_scope',logical_checks=len(checks),required=0,recommended=5,files=[p.name for p in OUT.glob('*.json')]),ensure_ascii=False))
