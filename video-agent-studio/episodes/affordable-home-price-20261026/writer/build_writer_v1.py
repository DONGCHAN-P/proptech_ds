"""고정 대본을 읽어 writer 전용 검토 패킷 생성. 음성·렌더·외부 호출 없음."""
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

W = Path(__file__).resolve().parent
EP = W.parent
ROOT = EP.parents[2]
FROZEN_SCRIPT_SHA = '26ed3cb78465bfde7bf52655df535e0d5b6fd8287e24c105c94266f757e7717f'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(name, value):
    (W / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def rel(p):
    return p.relative_to(ROOT).as_posix()

assert sha(W / 'script_v1.md') == FROZEN_SCRIPT_SHA, '고정 대본 변경: 새 버전과 재검토 필요'
facts = read(EP / 'research/facts.json')
packet = read(EP / 'research/verified_case_packet.json')
brief = read(EP / 'brief.json')
visual = read(EP / 'visual/assets.json')
fact_by_id = {f['claim_id']: f for f in facts['facts']}
case_by_id = {c['case_id']: c for c in packet['cases']}
afford = next(a for a in packet['affordability_A'] if a['profile_id'] == 'A_first' and a['deduction_krw'] == 0)

script = (W / 'script_v1.md').read_text(encoding='utf-8-sig')
body = script.split('---', 2)[2].strip()
chapters = []
paragraphs = []
for chapter in re.split(r'(?m)^## ', body)[1:]:
    heading, text = chapter.split('\n', 1)
    ps = text.strip().split('\n\n')
    chapters.append({'chapter': len(chapters) + 1, 'heading': heading, 'paragraph_count': len(ps)})
    paragraphs.extend((len(chapters), p.strip()) for p in ps)

# 한 항목이 한 문단에 대응하며 고정 구성 순서를 따른다. 실제84㎡ 평면을 만들지 않는다.
# 각 항목: 근거 / 사례 / 인사이트 / 도식명 / 메시지 / 발화에 맞춘 동작
specs = [
('L04 M01', '', 'I04', 'cash_addition_filters', '현금과 총액상한에서 실제 가격 범위를 찾는 질문', 'HB01 오른쪽 열쇠·폴더를 배경으로 2억5천·6억·8억5천 산술을 작은 오버레이에 연결하고 담보→소득→비용→월 예산 필터를 순차 강조'),
('', '', 'I01', 'series_budget_bridge', '첫 주거 선택 편의 현금과 월 예산을 이번 자금 계획으로 연결', '현금2억5천과 월300 두 축에서 매수 가격 범위로 이어지는 자금 흐름; 전편 차트를 재생하지 않고 전편 제목과 연결 표시만 사용'),
('L04 M01', '', 'I01 I07', 'three_constraint_intersection', '현금·심사·생활 예산을 모두 맞출 가격 범위', '세 개의 범위 막대를 한 축에 놓고 겹치는 부분만 강조; 기준일을 출처 구역에 표시'),
('', '', 'I01', 'cash_availability_calendar', '보유자금은 잔금일의 실제 사용 가능 현금', '잔금일 달력으로 현금화 날짜가 모이고 2억5천에서 예비3천을 남김; 자산 가격을 가정하지 않음'),
('', '', 'I01', 'cash_reserve_waterfall', '예비자금은 남길 현금, 비용은 지급할 돈', '2억5천→예비3천 별도 통장→구입 배정2억2천→거래비용→자기자금 순 워터폴; 아직 가격별 비용 수치를 적용하지 않음'),
('', '', 'I01', 'deposit_balance_funding', '계약금과 잔금을 하나의 자기자금으로 연결', '한 자금 봉투가 계약금·잔금으로 나뉘고 대출과 함께 집값을 충당; 임의 계약금 비율을 표시하지 않음'),
('L01 L03 M01', '', 'I02', 'collateral_ratio_definition', '매매가와 평가액을 확인한 뒤 담보 비율 적용', 'V=P 라벨과 아파트 외곽 아이콘 옆 담보 막대; 실제 구조·평면은 묘사하지 않고 전용84㎡를 조건 행에 표시'),
('L01 L03 L06', '', 'I02', 'ltv_profile_bars', '일반40·생초70과 별도 서민실수요60 요건', '비율 막대40/70을 비교하고 별도 분기60에 소득9천·가격8억·무주택을 함께 묶음; A 인정/가구소득1억을 고정'),
('M01 M02', '', 'I06', 'priority_deduction_stack', '방공제는 담보 한도에서 반영하는 임차인 보호 공제', '담보 배분도에서 선순위 권리와 미커버1방5500만 층을 분리; 5500만을 지출 영수증에 넣지 않음'),
('M01 M03 M04', '', 'I06', 'guarantee_approval_branches', 'C0은 은행 취급·보증 심사를 통과한 조건부 가지', '실행은행 취급확인→가입 심사→공제 보완 C0/공제 잔존 C55 두 갈래; 기존 임차인0·선순위0 조건 유지'),
('L02', '', 'I03', 'annual_income_service_budget', '은행 인정소득1억의 연 DSR 상환예산4천', '연소득 막대의40%를 원리금 예산으로 분리; A 기존부채0을 붙이고 다른 부채가 생길 때 줄어드는 공간을 도식화'),
('L06 P03', '', 'I03', 'dsr_dti_debt_components', 'DSR과 DTI의 부채 포함 범위 구별', 'DSR의 모든 대출 원리금과 DTI의 주담대 원리금/기타이자를 나란히 쌓음; A 일반40·생초60을 각 적용 지점에 표시'),
('L02 S01 S02 S03', '', 'I03', 'contract_assessment_rate_pair', '실제4%와 스트레스 심사7%를 역할별로 구별', '계약4%가 납부 계산기로, 4%+3%포인트=7%가 심사 계산기로 이동; 변동형100% 적용만 강조'),
('L02 S01', 'A_first_P600000000_C0', 'I03', 'annuity_principal_interest', '원리금균등의 월액과 심사 한도는 서로 다른 계산', '원금+이자 누적 막대에서 매월 합계 일정 관계를 설명한 뒤 DSR 한도 약5억103만을 별도 축에 표시; 6억 집 전체 자금표는 아직 노출하지 않음'),
('T01 T02 C01 C05 C06 C07', '', 'I10', 'purchase_cost_process', '세금·복비·등기 비용의 뜻을 먼저 설명', '집 취득→세금 영수증, 거래 중개→중개 영수증, 소유권 장부→등기 수수료·채권의 연결 도식'),
('T01 T03', '', 'I04 I10', 'acquisition_rate_curve', '취득세율은6~9억 사이 점차 증가', '가로축 전체 취득가액·세로축 세율의 곡선; 6억1%,9억3%와 9억초과3%를 표시; 6<P<=9 구간 공식은 검증값 그대로 사용'),
('T01 T02 T03', 'A_ordinary_P600000000_C0 A_ordinary_P900000000_C0 A_ordinary_P1200000000_C0', 'I10', 'tax_components_columns', '감면 전 취득세와 지방교육세 합계', '가격6/9/12별 취득세·교육세 누적 막대660/2970/3960만원을 발화 순서로 강조; 전용84㎡·중과/감면 전 조건을 숫자 옆에 표시'),
('C01 C02', '', 'I10', 'broker_rate_steps', '중개보수 상한 요율과 부가세 포함 예산', '확인된6/9/12억 기준점에서0.4/0.5/0.6% 계단과 264/495/792만원 영수증을 분리; 검증되지 않은 중간 구간 수치는 추가하지 않음'),
('T01 T02 T03 C01 C02 C03 C04 C05 C06 C07', 'A_ordinary_P600000000_C0 A_ordinary_P900000000_C0 A_ordinary_P1200000000_C0', 'I01 I10', 'transaction_receipt_triptych', '기타150만 계획예산까지 포함한 총비용', '세 개 영수증을 세금·복비VAT·기타 계획150만으로 쌓아 총1074/3615/4902만원 표시; 기타는 견적으로 교체할 계획항목, 예비자금3천은 영수증 밖 통장에 유지'),
('T04 T05', '', 'I10', 'relief_alternative_paths', '생초200·출산500 감면은 요건별 선택', '취득세 본표 옆 서로 대안인 감면 가지 두 개와 적격 조건; 동시적격 시 큰 감면 하나를 선택하는 구조. 감면후교육세·순납부세액은 확인 항목으로 남김'),
('L01 M01', 'A_ordinary_P600000000_C0', 'I01 I02', 'six_hundred_cash_funding', '6억 일반 사례의 필요대출과 추가 현금', '자기자금20926만·필요대출39074만과 일반한도24000만·추가현금15074만을 세 열로 분리해 연결'),
('L03 M01 M02 M03 M04', 'A_first_P600000000_C0 A_first_P600000000_C55000000', 'I02 I06', 'six_hundred_guarantee_comparison', '생초6억은 보증 승인 여부로 충당 가능 범위가 달라짐', 'C0 한도42000만과 C55 한도36500만을 나란히 표시하고 필요39074만 기준선을 고정; C55 부족2574만만 별도 현금 칸으로 이동'),
('L02', 'A_first_P600000000_C0', 'I07', 'needed_loan_monthly_payment', '6억 집 필요대출 월186.5만과 목표170만 비교', '필요39074만→계약4%·30년 원리금균등→월186.5만 연결; 목표170만 가이드를 아래에 둬 차이를 직접 표시'),
('L02 L03 L04 M01', 'A_first_P900000000_C0 A_first_P1200000000_C0 A_ordinary_P900000000_C0 A_ordinary_P1200000000_C0', 'I03', 'nine_twelve_constraint_table', '9·12억 생초의 제약은 DSR', '두 가격 행에 필요대출·한도·추가현금을 별도 열로 표시. 발화 중9억 행에서12억 행으로 강조 이동; 일반40% 비교는 작은 별도 보조행으로만 제공'),
('L04 T01 T04 B02 N03', '', 'I04', 'separate_threshold_axes', '상품·세금 문턱과 일반 총액 문턱은 별도 축', '상단6/9/12억 상품·세금 축과 하단15/25억 일반총액 축을 별도 표시; 15억이하6억·15초과25이하4억·25초과2억의 경계를 정확히 연결'),
('D01 D03 N01 N02', '', 'I05', 'household_b_profile', '정책대출은 별도 가구B로 전환', 'A 조건 행을 종료하고 B 소득8천·순자산2억5천·부채0·혼인7년내·생초·최근출산의 실물 장부형 프로필로 교체'),
('D01 D02 D03 M06 P01 P03', 'B_didim_P600000000_C0', 'I05', 'didim_eligibility_and_cap', '주택가격 자격6억과 대출한도3.2억을 구별', '소득8500·순자산51100·가격6억·면적85 네 필터 뒤 상품한도32000만과 필요39074만을 비교해 추가7074만을 표시'),
('B01 B02 B03 M09 P04 HFV2_04', 'B_bogeum_P600000000_C0', 'I05 I06', 'bogeum_three_valuations', '보금자리 가격평가와 자체 방수공제 기준', '시세·감정·매매가 세 평가가 모두6억이하인 문턱 뒤 생초42000만/필요39074만. 빈 아파트 자체 공제0을 보증 자동면제와 구분하는 원자료 근거 라벨'),
('B01 HFV2_01 HFV2_02 HFV2_03 HFV2_04 HFV2_05', '', 'I05', 'bogeum_single_income_branch', '현행 신혼1인 소득특례와 부부 확인항목', '기존 합산기준 경로 옆 별도1인<=7000만 경로; DTI는 소득 입증 차주1인의 소득·부채, 우대/실수요/기존상환과 보유수는 각 부부 확인으로 가지를 분리; 시행2026-10-19를 출처 행에 표시'),
('D01 D04 P01 P03 HFV2_04', 'B_didim_P600000000_C0', 'I05', 'didim_single_income_and_review', '디딤돌1인 예외와 정책 신규 DSR·DTI 처리', '합산8500초과 신혼/신청인6000이하 분기에서 DTI1인으로 연결하고 B는 합산기준 경로에 유지. 규제DSR 예외 뒤 DTI·신용·보증·내부심사 게이트를 유지'),
('D05 B04 P03 P04', 'B_didim_P600000000_C0 B_bogeum_P600000000_C0', 'I05', 'policy_residence_clocks', '상품별 전입 마감과 거주 기산점', '디딤돌 실행→1개월 내 전입→전입일부터2년, 수도권 보금자리 실행→6개월 내 전입/서류의 서로 다른 두 가로 시간축; B 생초DTI60을 조건 행에 표시'),
('N01 N02', '', 'I09', 'newborn_birth_income_filters', '출생일·접수일·맞벌이 소득요건을 함께 확인', 'NB01은 이 신생아 장의 도입에만 사용. 접수 전2년·2023-01-01이후 출생의 시간창, 외벌이1.3억/맞벌이2억과 한사람1.3억, 순자산51100만 필터를 네이티브 오버레이로 제시'),
('N03 M06 M07 P01 P03', 'B_newborn_P600000000_C0 B_newborn_P600000000_C55000000', 'I05 I06', 'newborn_six_hundred_funding', '신생아6억은 보증 승인 조건에서 필요대출이 한도 안', '사진을 내려 자금 도표로 전환. 가격9억·면적85·DTI60·상품4억 필터, B 6억 주택 보증 승인 C0→필요39074만. 미커버C55 한도36500만은 동일 조건 비교로만 보조 표시'),
('N03', 'B_newborn_P600000000_C0', 'I09', 'newborn_initial_rate_time_axis', '2.9% 초기 기본금리와 처음5년을 함께 표시', '30년 대출 전체 축에서 처음5년만 초기2.9%로 색칠. 필요39074만의 초기 월162.6만을 그 구간에 붙이고 이후 구간은 변경규정 확인으로 표시; 이후금리를 임의 삽입하지 않음'),
('N03 M07 M08', 'B_newborn_P900000000_C55000000', 'I05 I06', 'newborn_nine_hundred_cash_waterfall', '주택9억 자격과4억 대출 상한 사이 필요한 현금', '9억 집→서울C55 담보상한57500만→상품한도4억의 최솟값 순서; 대출4억·총필요현금56615만을 비용3615만/예비3천과 함께 분리'),
('N04', 'B_newborn_P900000000_C55000000', 'I05', 'newborn_shortfall_movein', '추가현금31615만과 실제 전입·거주 계획', '필요현금56615만에서 보유25000만을 빼 추가31615만을 연결한 뒤 실행1개월 내 전입·전입일부터2년 시간축으로 인계; NB01을 다른 주제로 재사용하지 않음'),
('L02 L03 M01 M03 M04', '', 'I07', 'bank_affordability_price_envelope', '조건 충족 계획에서 은행·현금상 가격상한68019만', 'A 생초 C0 조건 행을 복원하고 현금·비용·담보·소득의 교집합 끝점68019만을 표시; 보편적 승인한도처럼 표시하지 않음'),
('', '', 'I07', 'monthly_budget_allocation', '주거·저축 월300에서 상환170을 정해 가격 역산', '월300을 소유30·저축100·상환170으로 분해하고 가격56586만까지 되돌아가는 연결선; 소유30은 계획값으로 표시'),
('', '', 'I07', 'price_payment_savings_pair', '심사 가격과 월 목표 가격이 만드는 저축 여유', '68019만/56586만 두 행의 상환227/170·소유30·저축43/100 예산 막대를 비교; 인정소득 연1억과 배정예산 월300을 서로 다른 축에 표시'),
('', '', 'I08', 'same_principal_rate_sensitivity', '같은 최초원금·새360개월에서4%와6% 비교', '각 가격별 원금을 고정한 두 패널에서 금리4→6, 상환227→285/170→213, 저축43→15부족/100→57을 순서대로 강조. 5년후 잔액이나 남은기간 계산으로 표시하지 않음'),
('', 'A_first_P600000000_C0', 'I07', 'six_hundred_monthly_target_gap', '6억 사례의 월186.5와 목표170을 가구 선택으로 연결', '월 목표170 기준선과 필요대출 월186.5 차이를 보여준 뒤 현금·저축·가격 세 조절값을 같은 자금표에 연결; 새로운 시나리오 수치는 추가하지 않음'),
('M01 M03', '', 'I01 I06', 'cash_and_confirmed_loan_inputs', '잔금 자기자금과 해당 집의 은행 확인 범위', '첫 입력은 현금에서 예비·비용을 떼는 자금 흐름, 둘째는 인정소득·기존부채·평가액·보증을 은행 확인 범위로 연결'),
('', '', 'I07 I08', 'monthly_input_price_range', '세번째 입력 월 상환예산에서 매물 범위 확정', '월 생활·소유·저축 봉투와 금리 시나리오를 세 입력 교집합에 연결; 정책 자격은 해당 가구만 별도 연결'),
('', '', '', 'next_complex_selection_cta', '예산 안의 지역·단지 비교와 구독·좋아요', '이미 정한 예산 범위 안으로 후보 단지 비교 항목이 들어오는 네이티브 비교판; 후속편 예고 후 구독·좋아요 아이콘과 감사 문구를 안정적으로 유지'),
]
assert len(paragraphs) == len(specs) == 44

input_paths = [
    EP / 'brief.json', EP / 'state.json', EP / 'research/facts.json',
    EP / 'research/verified_case_packet.json',
    EP / 'research/prepared-v1/next_episode_story_findings.json',
    EP / 'research/prepared-v1/next_episode_editorial_plan.json',
    EP / 'research/prepared-v1/next_policy_independent_qa/findings.json',
    EP / 'director/episode_preflight.json', EP / 'visual/assets.json',
    ROOT / 'video-agent-studio/WORKFLOW.md',
    ROOT / 'video-agent-studio/agents/video_writer.toml',
    ROOT / 'video-agent-studio/guides/제작_기본가이드.md',
    ROOT / 'video-agent-studio/guides/지역_상세지도와_의미단위_자막.md',
    ROOT / 'video-agent-studio/guides/자료화면_설계_원칙.md',
    ROOT / 'video-agent-studio/guides/호출_효율_운영.md',
    ROOT / 'config/video_call_policy.json',
]
input_revisions = {rel(p): {'sha256': sha(p)} for p in input_paths}

digits = '영일이삼사오육칠팔구'
def sino(n):
    n = int(n)
    if n == 0:
        return '영'
    if n >= 10000:
        hi, lo = divmod(n, 10000)
        return sino(hi) + '만' + (sino(lo) if lo else '')
    out = ''
    for power, suffix in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        q, n = divmod(n, power)
        if q:
            out += ('' if q == 1 and power > 1 else digits[q]) + suffix
    return out

def read_number(s):
    s = s.replace(',', '')
    if '.' in s:
        a, b = s.split('.')
        return sino(a) + '점' + ''.join(digits[int(c)] for c in b)
    return sino(s)

pron_re = re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일|LTV|DSR|DTI|(?<![A-Za-z])[AB](?![A-Za-z])|\d[\d,]*(?:\.\d+)?(?:%포인트|%|㎡)?')
def speaking(text):
    transformed = []
    parts = []
    last = 0
    offset = 0
    for m in pron_re.finditer(text):
        a = m.group()
        if re.fullmatch(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', a):
            y, mo, day = map(int, re.findall(r'\d+', a))
            month = '시월' if mo == 10 else '유월' if mo == 6 else sino(mo) + '월'
            b = sino(y) + '년 ' + month + ' ' + sino(day) + '일'
        elif a in {'LTV', 'DSR', 'DTI', 'A', 'B'}:
            b = {'LTV': '엘티브이', 'DSR': '디에스알', 'DTI': '디티아이', 'A': '에이', 'B': '비'}[a]
        else:
            nm = re.match(r'\d[\d,]*(?:\.\d+)?', a).group()
            suffix = a[len(nm):]
            b = read_number(nm) + {'%포인트': ' 퍼센트 포인트', '%': ' 퍼센트', '㎡': ' 제곱미터', '': ''}[suffix]
        prefix = text[last:m.start()]
        parts.append(prefix)
        offset += len(prefix)
        transformed.append({'display_start': m.start(), 'display_end': m.end(), 'display': a, 'spoken_start': offset, 'spoken_end': offset + len(b), 'spoken': b, 'reason': '숫자·단위·약어의 발음층 분리'})
        parts.append(b)
        offset += len(b)
        last = m.end()
    parts.append(text[last:])
    return ''.join(parts), transformed

numeric_re = re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d[\d,]*(?:\.\d+)?억(?:\s*\d[\d,]*(?:\.\d+)?(?:천)?만)?\s*원|\d[\d,]*(?:\.\d+)?(?:천)?만\s*원|\d[\d,]*(?:\.\d+)?(?:%포인트|%|㎡|개월|년|원|억)')
def semantic_candidates(p):
    # 문장과 쉼표 뒤 절 경계를 보존. 글자수로 자르거나 타이밍을 부여하지 않는다.
    units = re.split(r'(?<=[.?!])\s+|(?<=,)\s+', p)
    return [u for u in units if u]

source_names = ['research/facts.json', 'research/verified_case_packet.json', 'research/prepared-v1/next_episode_story_findings.json']
scenes = []
numeric_occurrences = []
pron_scenes = []
claim_rows = []
first_in_chapter = set()
for i, ((ch, text), spec) in enumerate(zip(paragraphs, specs), 1):
    claim_s, case_s, insight_s, graphic, message, action = spec
    claims = claim_s.split()
    cases = case_s.split()
    sid = f'S{i:03d}'
    assert all(c in fact_by_id for c in claims)
    assert all(c in case_by_id for c in cases)
    spoken, transforms = speaking(text)
    units = semantic_candidates(text)
    assert ' '.join(units) == text
    protected = []
    for m in numeric_re.finditer(text):
        occ = {'scene_id': sid, 'display_start': m.start(), 'display_end': m.end(), 'display': m.group(), 'protect_across_cues_and_lines': True}
        numeric_occurrences.append(occ)
        protected.append(m.group())
    if ch <= 2 or ch == 10:
        condition_set = 'COMMON_PLANNING'
    elif ch <= 6 or ch == 9:
        condition_set = 'A_BANK'
    else:
        condition_set = 'B_POLICY'
    first = ch not in first_in_chapter
    first_in_chapter.add(ch)
    scene = {
        'scene_id': sid, 'chapter': ch, 'chapter_heading': chapters[ch - 1]['heading'],
        'message': message, 'display_text': text, 'narration_text': spoken,
        'spoken_text': spoken, 'claim_ids': claims, 'case_ids': cases,
        'story_finding_ids': insight_s.split(), 'condition_set_id': condition_set,
        'material_type': 'ai_concept' if sid in ['S001', 'S032'] else 'data_chart',
        'supporting_material_types': ['data_chart'] if sid in ['S001', 'S032'] else [],
        'visual_purpose': '설명' if sid not in ['S001', 'S032'] else '분위기 배경과 별도의 사실 설명 오버레이',
        'graphic_id': graphic, 'visual_direction': action,
        'emphasis_order': [u for u in protected][:10],
        'asset_ids': ['HB01'] if sid == 'S001' else ['NB01'] if sid == 'S032' else [f'G_{sid}_{graphic}'],
        'asset_status': '기존 raster manifest 확보, writer는 이미지 미열람' if sid in ['S001', 'S032'] else '네이티브 도표 제작 예정',
        'source_evidence': [{'claim_id': cid, 'basis_date': fact_by_id[cid]['basis_date'], 'source_ids': fact_by_id[cid]['source_ids'], 'evidence_locations': fact_by_id[cid]['evidence_locations']} for cid in claims],
        'model_source': 'research/verified_case_packet.json' if cases or ch == 9 else None,
        'rights_scope': '도표는 검증 수치의 자체 재구성. 원자료 캡처·raster 권리와 취득 기록은 visual/assets.json 및 원 소스팩을 승계',
        'fallback': f'{graphic}의 같은 관계·같은 수치를 편집 가능한 SVG로 제작; 빈 문장 카드로 바꾸지 않음',
        'caption_candidates': [{'unit_id': f'{sid}_U{j:02d}', 'display_text': u, 'start': None, 'end': None, 'timing_basis': 'unassigned'} for j, u in enumerate(units, 1)],
        'caption_layout': '의미 단위 후보. 최종 1~2줄과 실제 글리프 경계는 음성 정렬·렌더 후 검수',
        'protected_numeric': protected,
        'chapter_entry_id': f'CH{ch:02d}' if first else None,
        'script_revision': 'v1', 'audio_revision': None,
        'start': None, 'end': None, 'timing_basis': 'estimate',
        'estimated_duration_seconds': round(len(text) / 5.67, 2),
        'status': 'proposal_pending_dual_content_review',
    }
    if ch == 9:
        scene['affordability_source'] = 'research/verified_case_packet.json#/affordability_A/profile=A_first,deduction=0'
    if sid == 'S020':
        scene['relief_source'] = 'research/verified_case_packet.json#/conditional_relief_table'
    scenes.append(scene)
    pron_scenes.append({'scene_id': sid, 'display_text': text, 'spoken_text': spoken, 'transforms': transforms})
    claim_rows.append({'scene_id': sid, 'chapter': ch, 'claim_ids': claims, 'case_ids': cases, 'story_finding_ids': insight_s.split(), 'basis': '확정 facts와 조건부 사례의 해설' if claims or cases else '사용자 브리프·구성 연결 또는 패킷 역산값', 'condition_set_id': condition_set})

chapter_graphics = ['keys_budget', 'cash_envelopes', 'collateral_house_bar', 'annual_income_ledger', 'tax_receipts', 'three_price_markers', 'policy_application_folders', 'newborn_home', 'monthly_budget_calendar', 'candidate_neighborhoods']
chapter_entries = []
for c, bg in zip(chapters, chapter_graphics):
    n = c['chapter']
    chapter_entries.append({
        'chapter_entry_id': f'CH{n:02d}', 'title': c['heading'],
        'before_scene_id': next(s['scene_id'] for s in scenes if s['chapter'] == n),
        'material_type': 'ai_concept' if n in [1, 8] else 'data_chart',
        'visual_purpose': '주제 전환의 분위기 배경. 가격·실제 주택 구조의 근거는 본문 도표',
        'background_asset_id': 'HB01' if n == 1 else 'NB01' if n == 8 else f'CH_NATIVE_{bg}',
        'background_direction': '확보 raster를 자연스럽게 유지하고 번호+주제만 별도 레이어' if n in [1, 8] else f'{bg} 주제의 저밀도 네이티브 입체·선화 배경. 본문 첫 수치판과 다른 구도, 단색 제목판 금지',
        'estimated_hold_seconds': 3.0, 'timing_basis': 'estimate', 'start': None, 'end': None,
        'title_only_short_topic': True, 'spoken_heading': False,
        'screen_AI_badge': False, 'text_baked_into_background': False,
    })

condition_sets = {
    'COMMON_PLANNING': {'cash_krw': 250000000, 'reserve_retained_cash_krw': 30000000, 'misc_transaction_plan_krw': 1500000, 'monthly_housing_plus_savings_budget_krw': 3000000, 'reserve_is_expense': False, 'misc_is_actual_quote': False},
    'A_BANK': {
        'household': 'A', 'annual_bank_recognized_income_krw': 100000000, 'annual_household_income_krw': 100000000,
        'existing_debt_krw': 0, 'region': '서울 규제지역·투기과열지구', 'area_sqm': 84,
        'valuation_equals_purchase_price': True, 'prior_claims_krw': 0, 'existing_tenancy': False,
        'contract_rate': '4%', 'assessment_rate': '7%', 'stress_addition': '3%포인트', 'term_months': 360,
        'repayment': '원리금균등', 'DSR_percent': 40, 'DTI_ordinary_percent': 40, 'DTI_firstbuyer_percent': 60,
        'LTV_ordinary_percent': 40, 'LTV_firstbuyer_percent': 70,
        'C0': '실행은행 취급·보증 심사 통과 등으로 미커버공제0인 조건부 모델',
        'C55': '서울 미커버1방5500만원 공제 가정. 실제 공제방수·금액은 상품별 확인',
        'qualified_enduser': {'LTV_percent': 60, 'household_income_max_krw': 90000000, 'price_max_krw': 800000000, 'no_home': True, 'A_uses_this_exception': False},
        'screen_condition_labels': ['A · 인정소득/가구소득 각 연1억 · 부채0', '서울 투기과열지구 · 전용84㎡ · 평가액=가격 · 선순위/임대차0', '변동4% · 30년 · 심사7% · DSR40% · 보증 승인 C0 또는 미커버 C55'],
    },
    'B_POLICY': {
        'household': 'B — A와 별개', 'combined_income_krw': 80000000, 'net_assets_krw': 250000000,
        'cash_krw': 250000000, 'reserve_retained_cash_krw': 30000000, 'existing_debt_krw': 0,
        'married_within_7_years': True, 'first_purchase': True, 'no_home_household': True,
        'child_within_2_years_before_application': True, 'born_on_or_after': '2023-01-01',
        'region': '서울', 'area_sqm': 84, 'valuation_equals_purchase_price': True, 'existing_tenancy': False, 'prior_claims_krw': 0,
        'DTI_percent_in_B_examples': 60, 'new_policy_regulatory_DSR': 'P01 신규 예외 틀, 내부 심사 가능',
        'didim_and_bogeum_4percent': '패킷의 상환/DTI 계획 가정, 실제 공시금리로 표현하지 않음',
        'newborn_rate': '소득6천초과~8500이하·30년 기본 초기2.9%, 기본 특례5년, 이후금리 미확정',
        'guarantee_rules': {'didim_first_6eok': 'M06 적격 보증 가입·실행시 임대차 없음', 'bogeum_vacant_apt': 'M09 자체규정 방수공제0', 'newborn_6eok_C0': 'M07 적격 보증 승인 필요', 'newborn_9eok': 'M08 보증가격 문턱6억 초과, C55 반영'},
        'income_exception_unused_for_B': True,
        'bogeum_B_existing_income_route': '신혼 1자녀 합산9000만원 이하 기존기준(HFV2_04); B8000만원으로 충족',
        'screen_condition_labels': ['별도 B · 부부합산 연8천 · 순자산/보유현금2억5천 · 부채0', '혼인7년내 · 무주택·생초 · 접수전2년내 출산 · 서울84㎡', '신용·보증·상품별 DTI·전입/거주 요건 확인'],
    },
    'TRANSACTION': {'home': '중과 없는84㎡ 통상아파트 한 채', 'tax_relief_applied': False, 'rural_special_tax_krw': 0, 'broker': '서울·상한 내 협의·일반과세VAT10% 상한계획', 'misc_plan_krw': 1500000, 'education_tax_after_relief': None},
}

display_count = sum(len(t) for _, t in paragraphs)
estimate = round(display_count / 5.67, 2)
common = {'episode_id': brief['episode_id'], 'script_revision': 'v1', 'frozen_script_sha256': FROZEN_SCRIPT_SHA, 'policy_as_of': '2026-10-26'}
save('scene_proposals_v1.json', {
    **common, 'status': 'writer_proposal_pending_Claude_and_Codex_review',
    'ownership': 'writer only; director가 공통 scenes.json에 반영할 제안',
    'timing': {'basis': 'estimate', 'measured': False, 'display_characters_narration': display_count, 'visible_characters_with_headings_and_linebreaks': len(body), 'rate_display_chars_per_second': 5.67, 'reference': '실제 첫 편 실적·사용자 인계', 'estimated_narration_seconds': estimate, 'estimated_chapter_holds_seconds': 30, 'estimated_narration_plus_chapters_minutes': round((estimate + 30) / 60, 2), 'brand_intro_outro': '기존 승인 클린 자산의 실제 길이를 editor가 더함; 타임록 후 확정', 'audio_created': False},
    'style_contract': {'font': '기존 채널 Pretendard', 'palette': '직전 첫 편의 아이보리·네이비·파랑·골드·초록 토큰 계승, 새 HEX 팔레트 지정 없음', 'body_captions': '고정 흰 박스·1~2줄·숫자/단위/날짜/약어 보호·출처 아래 별도 영역', 'caption_source': '이 파일 display_text와 pronunciation_notes_v1.json spoken_text의 변환 범위', 'no_white_caption_box': ['무낭독 브랜드 인트로', '무낭독 브랜드 아웃트로', '마지막 발화 후 무음 CTA 유지'], 'actual_glyph_bounds_check': '렌더 담당 필수; writer 미실행', 'chapter_backgrounds': '독립 배경+짧은 번호·주제. HB01 도입, NB01 신생아 장만 사용', 'forbidden': ['걷는 졸라맨', '무관한 동일 raster/차트 반복', '큰 문장 카드로 자료 대체', '시청자 AI 배지', '불필요한 부정형 면책 벽', '생성 이미지를 실제84㎡ 평면으로 제시']},
    'condition_sets': condition_sets,
    'scene_count_body': len(scenes), 'chapter_entries': chapter_entries,
    'raster_asset_use': [{'asset_id': a['asset_id'], 'path': a['path'].replace('\\', '/'), 'sha256_from_manifest': a['sha256'], 'writer_observed': 'manifest만 읽음, 이미지 미열람', 'scene_ids': ['S001'] if a['asset_id'] == 'HB01' else ['S032'], 'chapter_ids': ['CH01'] if a['asset_id'] == 'HB01' else ['CH08'], 'thumbnail_background_candidate': a['asset_id'] == 'HB01', 'role': '분위기', 'data_evidence': False} for a in visual['raster_assets']],
    'scenes': scenes,
    'last_spoken_to_outro': {'hold_seconds_target': 3, 'basis': '실제 발화 종료 정렬 후 적용', 'timing_locked': False},
    'input_revisions': input_revisions,
})

used_claims = sorted({c for s in scenes for c in s['claim_ids']})
used_cases = sorted({c for s in scenes for c in s['case_ids']})
save('claim_map_v1.json', {
    **common, 'evidence_scope': '총괄 확정 facts/사례/이전 독립 검증을 보존해 연결. writer는 정책 웹 재조사·산술157건·논리10건을 재실행하지 않음',
    'input_revisions': input_revisions,
    'scene_map': claim_rows,
    'used_facts_with_exact_conditions': [fact_by_id[c] for c in used_claims],
    'used_case_ids': used_cases,
    'case_basis': 'verified_case_packet.json의18개 승인 후보 중 이 대본/장면에서 쓰는 사례만 연결; 반사실 제외',
    'additional_derivations': {'relief_overlap_and_net_education_tax': packet['conditional_relief_table'], 'affordability_A_first_C0': afford, 'source_case_results_sha256': packet['source_results_sha256']},
    'story_findings_coverage': {f'I{i:02d}': [s['scene_id'] for s in scenes if f'I{i:02d}' in s['story_finding_ids']] for i in range(1, 11)},
    'unspoken_unused_rules': '나머지 facts의 예외·경과조치는 낭독으로 추가하지 않음. 사용 주장에 달린 exact_conditions는 이 파일에서 보존',
    'inherited_qa_recommendations': {'NQA-01': '현 구성안의 실제 SHA를 새로 고정; 옛 입력 해시 검수를 전체 승계하지 않음', 'NQA-02': 'C0/C55·보금자리 자체0·6/9/12와15/25 분리', 'NQA-03': '별도 B·신혼1인소득/부채·전입/거주 기산점 보존', 'NQA-04': '무감면 총액·기타계획150·잔존예비3천·감면 미합산 보존', 'NQA-05': '실제4/심사7/초기2.9·5년/동일최초원금360개월을 분리'},
})

def round_manwon(v):
    return int((Decimal(str(v)) / Decimal(10000)).quantize(Decimal(1), rounding=ROUND_HALF_UP))

case_numbers = [{k: c[k] for k in ['case_id', 'deduction_krw', 'deduction_note', 'limits_krw', 'loan_ceiling_krw', 'required_loan_krw', 'cash_required_including_reserve_krw', 'cash_shortfall_krw', 'payment_if_financeable_krw', 'transaction_costs']} for cid, c in case_by_id.items() if cid in used_cases]
save('protected_numeric_v1.json', {
    **common, 'rounding': {'cash_tables': '원 단위 원본 보존·표시만원은 반올림; 낭독에 약 표시', 'monthly_six_hundred_and_newborn': '만원 소수1자리', 'monthly_budget_comparison': '만원 정수 반올림', 'price_solver': '1만원 격자의 조건부 최대값, 실제 실행상한과 구별'},
    'protected_occurrences': numeric_occurrences,
    'case_numbers_exact': case_numbers,
    'affordability_exact': afford,
    'critical_pairs': [
        {'scenes': ['S001', 'S025'], 'keep': '현금2억5천+총액상한6억=산술8억5천; 실제는 담보·소득·비용·월예산 필터'},
        {'scenes': ['S013'], 'keep': '계약4% vs 심사7%=4%+3%포인트; %와 %포인트 역할 구분'},
        {'scenes': ['S019'], 'keep': '세금660/2970/3960 + 복비VAT264/495/792 + 기타계획150 = 총1074/3615/4902만원; 예비3천은 별도 잔존현금'},
        {'scenes': ['S022'], 'keep': '6억 생초 C0 42000만 vs C55 36500만, 필요39074만, C55 추가2574만'},
        {'scenes': ['S023', 'S041'], 'keep': '필요39074만원의4%·30년 월186.5만원 vs 목표170만원'},
        {'scenes': ['S020'], 'keep': '생초최대200/출산최대500은 각 요건·큰 감면 하나; 순교육세 미산출'},
        {'scenes': ['S027', 'S028', 'S033'], 'keep': '별도 B: 디딤돌32000만, 보금자리생초42000만, 신생아40000만; 주택가격과 대출한도 구분'},
        {'scenes': ['S034'], 'keep': '신생아 초기기본2.9%·월162.6만·처음5년; 만기30년 전체금리로 확대하지 않음'},
        {'scenes': ['S037', 'S038'], 'keep': 'A생초C0 조건부 상한68019만 vs 월상환170·저축100·소유30 조건56586만'},
        {'scenes': ['S040'], 'keep': '각 가격의 동일 최초원금·새360개월:4→6%, 월227→285/170→213, 저축43→15부족/100→57'},
    ],
    'approximate_case_display_manwon': [{'case_id': c['case_id'], 'ceiling': round_manwon(c['loan_ceiling_krw']), 'needed': round_manwon(c['required_loan_krw']), 'additional_cash': round_manwon(c['cash_shortfall_krw'])} for c in case_numbers],
})

save('pronunciation_notes_v1.json', {
    **common, 'status': '미합성·미청취 발음 제안',
    'owner_next': 'narration — 고정 대본의 내용검토 통과 후 사용',
    'pronunciation_dictionary': [
        {'display': 'DSR', 'spoken': '디에스알', 'meaning': '모든 대출 연 원리금/은행 인정 연소득'},
        {'display': 'LTV', 'spoken': '엘티브이', 'meaning': '담보가치 대비 대출 비율'},
        {'display': 'DTI', 'spoken': '디티아이', 'meaning': '주담대 원리금과 기타부채 이자/해당 소득'},
        {'display': '%포인트 / pp', 'spoken': '퍼센트 포인트', 'meaning': '금리 차이의 단위. 퍼센트와 구분; pp를 영문으로 읽지 않음'},
        {'display': '원리금균등', 'spoken': '원리금균등', 'meaning': '원금과 이자의 합계액'},
        {'display': '84㎡ / 85㎡', 'spoken': '팔십사 제곱미터 / 팔십오 제곱미터'},
        {'display': 'A / B', 'spoken': '에이 / 비'},
        {'display': '2026년 10월 26일', 'spoken': '이천이십육년 시월 이십육일'},
        {'display': 'C0 / C55', 'spoken': '낭독문에 코드 추가하지 않음', 'meaning': '보증 승인 등 공제0 / 서울 미커버5500만원 내부 분기'},
    ],
    'emphasis_notes': [
        {'scenes': ['S001', 'S003'], 'words': ['어느 가격', '담보', '소득', '거래비용', '매달 남길 돈']},
        {'scenes': ['S022'], 'words': ['보증', '필요한', '추가 현금']},
        {'scenes': ['S026'], 'words': ['별도의 가구 B']},
        {'scenes': ['S034'], 'words': ['기본 초기금리', '처음 5년']},
        {'scenes': ['S040'], 'words': ['최초 대출원금', '새로 360개월', '저축 여유']},
        {'scenes': ['S044'], 'words': ['정한 예산 안', '구독과 좋아요', '감사합니다']},
    ],
    'delivery': '합니다체·차분한 정보 전달. 숫자 앞뒤를 구 단위로 읽고 문장 말미 충분히 유지. 의미 후보의 길이를 기준으로 빠르게 몰아 읽지 않음',
    'caption_contract': 'WordBoundary/실제 정렬은 spoken_text 문자 범위 기준. 아래 명시 변환을 적용해 display_text를 복원. 숫자·단위·날짜·약어를 큐/줄 사이 분할하지 않음',
    'scenes': pron_scenes,
    'timing_basis': 'estimate only; 실제 WordBoundary·청취·타이밍은 이후 담당',
})

expected_headings = ['1. 출발점', '2. 보유자금', '3. 담보 한도', '4. 소득 심사', '5. 거래비용', '6. 가격별 계산', '7. 정책대출', '8. 신생아 특례', '9. 월 예산', '10. 다음 선택']
checks = []
def check(name, result, evidence):
    checks.append({'check': name, 'result': 'pass' if result else 'fail', 'evidence': evidence})

check('고정 대본 SHA', sha(W / 'script_v1.md') == FROZEN_SCRIPT_SHA, FROZEN_SCRIPT_SHA)
check('번호+주제 10장·정확한 첫/끝 표제', [c['heading'] for c in chapters] == expected_headings, expected_headings)
check('프런트메타데이터 v1', re.search(r'(?m)^version: v1$', script) is not None, '본문 ## 앞 version:v1')
check('본문은 서술 문단·무대지시/출처 부록 없음', not re.search(r'(?m)^(?:[-*] |\d+\) |\[|### )', body), '44개 서술문단, 10개 ##')
check('표시문자수5000~6500', 5000 <= len(body) <= 6500 and 5000 <= display_count <= 6500, {'narration': display_count, 'visible_with_headings_breaks': len(body)})
check('첫 문단20~30초 추정', 20 <= scenes[0]['estimated_duration_seconds'] <= 30, scenes[0]['estimated_duration_seconds'])
check('본문과44장면 표시문 완전일치', [p for _, p in paragraphs] == [s['display_text'] for s in scenes], '서술문단 순서 1:1')
check('의미 단위 후보 재조합 원문일치', all(' '.join(u['display_text'] for u in s['caption_candidates']) == s['display_text'] for s in scenes), '문장/쉼표 절 경계; 타이밍 없음')
check('숫자 보호어가 의미 후보 경계를 넘지 않음', all(any(o['display'] in u['display_text'] for u in scenes[int(o['scene_id'][1:])-1]['caption_candidates']) for o in numeric_occurrences), len(numeric_occurrences))
check('사용 claim·case ID 유효 및 반사실 제외', all(c in fact_by_id for c in used_claims) and all(c in case_by_id for c in used_cases) and 'B_newborn_P900000000_C0' not in used_cases and 'B_bogeum_P600000000_C55000000' not in used_cases, {'claims': len(used_claims), 'cases': len(used_cases)})
check('I01~I10 모두 연결', all(any(f'I{i:02d}' in s['story_finding_ids'] for s in scenes) for i in range(1, 11)), 'claim_map_v1.json/story_findings_coverage')
check('HB01 도입·NB01 신생아 장 전용', [s['scene_id'] for s in scenes if 'HB01' in s['asset_ids']] == ['S001'] and [s['scene_id'] for s in scenes if 'NB01' in s['asset_ids']] == ['S032'], 'manifest만 읽음, 이미지 미검수')
check('모든 장면 실제 시각 미지정·예상 시간', all(s['start'] is None and s['end'] is None and s['timing_basis'] == 'estimate' for s in scenes), '음성/영상 생성 없음')
check('현재 구성안 해시를 새로 고정', rel(EP / 'research/prepared-v1/next_episode_editorial_plan.json') in input_revisions, input_revisions[rel(EP / 'research/prepared-v1/next_episode_editorial_plan.json')])

# 발음 변환표가 표시문·낭독문 범위에 정확히 대응하는지 검사한다.
span_ok = True
for s in pron_scenes:
    for t in s['transforms']:
        span_ok &= s['display_text'][t['display_start']:t['display_end']] == t['display']
        span_ok &= s['spoken_text'][t['spoken_start']:t['spoken_end']] == t['spoken']
check('발음층 변환 범위 일치', span_ok, '숫자·약어 변환 전후의 문자 범위 검사, 합성·청취 검수와 구별')

validation = {
    **common, 'status': 'writer_structural_checks_only', 'checks': checks,
    'passed': sum(c['result'] == 'pass' for c in checks), 'failed': sum(c['result'] == 'fail' for c in checks),
    'content_review': 'main의 Claude+Codex 독립 검토 대기. writer 구조 검사로 내용 승인 대체하지 않음',
    'not_performed': ['정책 웹 재조사', '선행157산술·10논리검사 재실행', 'raster 실제 열람', 'TTS·청취', '영상 렌더·실제 프레임·연속재생', '외부 전송·업로드'],
}
save('validation_v1.json', validation)
assert validation['failed'] == 0, validation

output_names = ['script_v1.md', 'scene_proposals_v1.json', 'claim_map_v1.json', 'protected_numeric_v1.json', 'pronunciation_notes_v1.json', 'validation_v1.json', 'build_writer_v1.py']
outputs = [{'path': rel(W / n), 'sha256': sha(W / n), 'bytes': (W / n).stat().st_size} for n in output_names]
save('handoff.json', {
    'task_id': 'affordable-home-price-writer-v1', 'role': 'writer',
    'status': 'draft_frozen_pending_dual_content_review',
    'summary': f'10장·44본문 장면의 v1 초안을 고정했습니다. 낭독 표시문 {display_count}자, 표제/줄바꿈 포함 {len(body)}자. 본문 약{estimate/60:.2f}분·장 전환 포함 약{(estimate+30)/60:.2f}분 estimate입니다. 본문은 main의 고정 요청 이후 변경하지 않았습니다. HB01은 도입/썸네일 후보, NB01은 신생아 장 전용. 수치/정책은 확정 패킷을 연결했으며 독립 내용 검토를 기다립니다.',
    'frozen_script_sha256': FROZEN_SCRIPT_SHA,
    'input_revisions': input_revisions, 'outputs': outputs,
    'affected_scene_ids': [s['scene_id'] for s in scenes],
    'checks': [{'check': 'writer 구조·연결 검사', 'result': 'pass', 'evidence': rel(W / 'validation_v1.json')}, {'check': 'Claude+Codex 내용 검토', 'result': 'pending', 'evidence': None}],
    'open_issue_ids': [],
    'unresolved': ['내용 검토와 정확한 버전별 승인', '실제 음성·발음 청취·WordBoundary 정렬·타임록', '네이티브 도표와 장 배경 구현 및 실제 글리프/프레임 검수', '계획용 기타150만·소유월30만의 개인별 실제 견적/지출', '개인별 보증·신용·은행 실행 조건 및 감면후 교육세 포함 순납부세액'],
    'scope_notes': ['18개 승인 조건부 사례 패킷 중 사용 사례만 연결; 제외 반사실 미사용', '숫자의 정책 전제와 정확 조건은 claim_map 및 protected_numeric에서 보존', '공통 state/scenes/decisions 및 다른 담당 산출물 수정 없음', '금융정책 신규 조사·Claude 호출·TTS·업로드 없음'],
    'next_role': 'director → Claude+Codex 내용 검토 → 승인 후 narration/visual/editor',
    'next_action': '이 frozen_script_sha256과 출력별 SHA를 검토 대상으로 고정. 수정이 필요하면 writer에 장면ID·근거 전달 후 새 버전을 발급',
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
})
assert sha(W / 'script_v1.md') == FROZEN_SCRIPT_SHA
print(json.dumps({'frozen_script_sha256': FROZEN_SCRIPT_SHA, 'narration_display_characters': display_count, 'visible_characters': len(body), 'body_scenes': len(scenes), 'estimate_narration_minutes': round(estimate/60, 2), 'estimate_with_chapter_holds_minutes': round((estimate+30)/60, 2), 'checks_passed': validation['passed'], 'checks_failed': validation['failed'], 'handoff': rel(W / 'handoff.json')}, ensure_ascii=False))
