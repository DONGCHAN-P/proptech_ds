"""신생아 최신 캐시 원문 및 60회 후 상환액만 독립 검수. 원본 수정 없음."""
import datetime
from decimal import Decimal as D, getcontext
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

getcontext().prec = 65
OUT = Path(__file__).resolve().parent
EP = OUT.parents[1]
INPUTS = ['research/newborn_policy_addendum_v2.json', 'research/facts_v2.json',
          'research/evidence/director-newborn-v1/KB.html',
          'research/evidence/director-newborn-v1/NHUF.html',
          'research/evidence/director-newborn-v1/receipt.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((EP/path).read_text(encoding='utf-8-sig'))


def write(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip += 1
        if not self.skip and tag in ['tr','td','th','p','li','br','h3','h4']:
            self.parts.append(' | ')

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip = max(0, self.skip-1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


addendum = read(INPUTS[0])
facts = read(INPUTS[1])
receipts = read(INPUTS[4])
manifest = [dict(path=p, sha256=sha(EP/p), bytes=(EP/p).stat().st_size) for p in INPUTS]
texts = {}
for source in ['KB','NHUF']:
    parser = TextParser()
    parser.feed((EP/f'research/evidence/director-newborn-v1/{source}.html').read_text(encoding='utf-8-sig'))
    texts[source] = re.sub(r'\s+', ' ', ''.join(parser.parts))

checks = []
excerpts = []


def check(label, value):
    checks.append(dict(check=label, passed=bool(value)))
    assert value, label


def evidence(source, term, length, claim):
    text = texts[source]
    offset = text.find(term)
    check(f'{claim}/{source} 원문 위치:{term}', offset >= 0)
    excerpt = text[offset:offset+length]
    excerpts.append(dict(claim_id=claim, source_id=source,
                         path=f'research/evidence/director-newborn-v1/{source}.html',
                         normalized_text_offset=offset, excerpt=excerpt))
    return excerpt


for receipt in receipts:
    path = EP/f"research/evidence/director-newborn-v1/{receipt['source_id']}.html"
    check(f"{receipt['source_id']} 캐시 SHA/크기와 취득기록 일치", sha(path) == receipt['sha256'] and path.stat().st_size == receipt['bytes'])
for source in addendum['sources']:
    receipt = next(r for r in receipts if r['source_id'] == source['source_id'])
    check(f"{source['source_id']} addendum이 동일 캐시를 인용", source['sha256'] == receipt['sha256'])

income = evidence('NHUF', '6. (소득)', 390, 'N01/N01B')
check('합산1.3억/맞벌이합산2억/부부각1인1.3억', all(t in income for t in ['모두 소득','2억원 이하','각 1인의 소득이 1.3억원 이하']))
evidence('NHUF', '맞벌이 :', 100, 'N01B')
adoption = evidence('NHUF', '② ’23.1.1. 이후 출생아', 150, 'N01/N01A')
check('입양아 접수일현재 만2살미만', '대출접수일 기준 입양아의 나이는 만2살 미만' in adoption)
evidence('KB', '대출접수일 기준 2년 내 자녀를 출산', 170, 'N01A')
reset = evidence('NHUF', '2. 특례금리 적용 종료시 금리', 390, 'N05A')
check('취급시 소득8500이하·접수일기준 차이 가산', all(t in reset for t in ['대출취급시 산정된','8.5천만원 이하','대출접수일 기준','차이만큼 가산금리']))
kb_reset = evidence('KB', '특례금리 종료 후 금리 (A1 또는 A2)', 400, 'N05A')
check('KB현행 2026.10.19표 A1+.75pp', '8천5백만원 이하' in kb_reset and '2026.10.19 기준' in kb_reset and '연0.75%p' in kb_reset)
kb_date = evidence('KB', '특례금리(A):', 250, 'N05A_BASE')
check('KB초기금리표 2026.10.19기준', '2026.10.19 기준' in kb_date)
kb_rate = evidence('KB', '6천만원 초과 8천5백만원 이하', 110, 'N05A_BASE')
check('KB80m소득구간30년2.90', '연 2.65%' in kb_rate and '연 2.75%' in kb_rate and '연 2.85%' in kb_rate and '연 2.90%' in kb_rate)
header = evidence('KB', '기금 운용계획 변경에 따라 변동사항을 소득수준, 만기', 235, 'N05A_TABLE_HEADER')
check('KB금리표 열순서10년/15년/20년/30년', bool(re.search(r'10년\s*\|\s*15년\s*\|\s*20년\s*\|\s*30년', header)))
check('특례기본5년 직접확인', '특례금리 적용시 금리(기본 5년)' in texts['NHUF'])
n01 = next(x for x in facts['facts'] if x.get('claim_id') == 'N01')
check('facts_v2 N01 각1인·입양나이 수정반영', 'each_partner_dual_income_max' in n01['value'] and n01['value']['each_partner_dual_income_max'] == 1.3 and '만2세미만' in n01['exact_conditions'])

# 기존 engine/PMT/PV나 총괄의 검증 결과를 호출하지 않는다.
# 첫 월액은 유한 할인합으로 계산하고, 전환 후 월액은 잔액 순환의 근을 이분법으로 구한다.
case = addendum['case']
principal = D(case['principal_krw'])
r1, r2 = D('0.029')/12, D('0.0365')/12
discount_sum = sum((1+r1)**(-k) for k in range(1,361))
initial = principal / discount_sum
balance = principal
for _ in range(60):
    balance = balance * (1+r1) - initial


def final_balance(monthly):
    value = balance
    for _ in range(300):
        value = value*(1+r2)-monthly
    return value


lower, upper = D(0), balance
for _ in range(220):
    mid = (lower+upper)/2
    if final_balance(mid) > 0:
        lower = mid
    else:
        upper = mid
monthly = (lower+upper)/2
increase = monthly-initial
numbers = dict(principal_krw=principal, initial_monthly_krw=initial,
               balance_after60_krw=balance, reset_annual_rate=D('0.0365'),
               remaining_months=300, reset_monthly_krw=monthly,
               monthly_increase_krw=increase, final_balance_after300_krw=final_balance(monthly))
for name in ['initial_monthly_krw','balance_after60_krw','reset_monthly_krw','monthly_increase_krw']:
    check('독립 계산과 입력값 일치:'+name, abs(numbers[name]-D(case[name])) < D('1e-20'))
check('300회 뒤 잔액 수렴', abs(final_balance(monthly)) < D('1e-45'))
check('명시된 전환횟수/잔여기간/금리 조건', case['initial_months'] == 60 and case['original_months'] == 360 and case['remaining_months'] == 300 and D(case['initial_annual_rate']) == D('.029') and D(case['current_schedule_reset_rate']) == D('.0365') and D(case['current_schedule_reset_spread_pp']) == D('.75'))

revision = dict(addendum=addendum['revision'], addendum_sha256=sha(EP/INPUTS[0]), facts_v2_sha256=sha(EP/INPUTS[1]))
findings = []


def finding(identifier, claims, problem, support, correction):
    findings.append(dict(issue_id=identifier, scene_id='CH08/신생아특례/대본장면ID미확정', timecode=None,
                         claim_ids=claims, case_id=case['case_id'], severity='recommended',
                         **{'문제':problem, 'evidence':support, '수정안':correction},
                         owner='director / writer', status='verified_condition_preserve_in_v2_script', checked_revision=revision))


finding('NBD-01',['N01','N01A','N01B'], '수정된 기본자격을 대본에도 유지할 필요가 있습니다.',
        'NHUF 대출대상6 및 맞벌이 주석: 둘 다 소득·합산2억이하·각1인1.3억이하. 출산범위②와KB자격: 입양아 접수일현재 만2살미만. facts_v2 수정확인.',
        '적어도한명1.3억 표현을 사용하지 않습니다. 기본 입양나이<2와 특별/우선공급 별도예외를 섞지 않습니다. 대본v2 실제반영은 이번 검수범위가 아닙니다.')
finding('NBD-02',['N05A','N05A_BASE'], '3.65%와176.4만원을 현재 접수표를 적용한 B 기본사례에 한정해야 합니다.',
        '신규취급시 소득8000만은8500만이하 A1. NHUF접수일산식·KB2026.10.19기준+.75%p·30년2.90% 확인. 캐시NHUF 금리숫자는 동적빈셀이라2.90%숫자는KB표로 확인.',
        '서울·우대전·거치없음·원리금균등·추가출산/중도상환/자산가산0 조건으로 첫60회월162.6만→잔액346755901원→남은300개월월176.4만을 설명합니다. 최초원금390740000원을 다시300개월 상환하는 계산이나 미래시장금리 예측으로 바꾸지 않습니다.')
write('source_excerpts.json', dict(scope='지정최신캐시원문관련부분직접열람', input_manifest=manifest, excerpts=excerpts))
write('arithmetic_delta.json', dict(method='정밀도65 Decimal 유한360회할인합+60회잔액순환+300회최종잔액의220단계이분법. 기존엔진/총괄코드미사용.', results=numbers, checks=checks, money_scope='월금리=연금리/12·원단위반올림전모형. 실제은행일할/반올림/승인결과미계산.'))
write('findings.json', dict(status='approved_with_scope', required=0, critical=0, recommended=len(findings), findings=findings))
artifacts = [dict(path=(OUT/p).as_posix(),sha256=sha(OUT/p),bytes=(OUT/p).stat().st_size) for p in ['findings.json','source_excerpts.json','arithmetic_delta.json']]
report = dict(status='approved_with_scope', approval_scope='지정 신생아 기본자격·현재접수표 금리·60회 후 상환액 차이만',
              required=0, critical=0, recommended=len(findings), checked_revision=revision,
              reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              input_manifest=manifest, artifacts_sha256=artifacts, sources_retrieved_at_utc={r['source_id']:r['retrieved_at_utc'] for r in receipts},
              source_verdict='N01/N01A/N01B와N05A는지정최신KB/NHUF캐시의직접본문을지지. KB의2026.10.19 기준표 사용; 과거8월캐시미사용. 2.90숫자KB직접확인·NHUF는구간/산식확인.',
              arithmetic_verdict='새독립계산4개수치오차각1e-20원미만·잔여300회후잔액1e-45원미만. 기존157개재실행없음.',
              results=numbers, checks_passed=len(checks), checks_failed=0,
              conditions=['합산8000만원·수도권서울·30년·비거치원리금균등 기본사례','현재2026.10.19표2.9%·A1접수일산식+.75%p=3.65%','첫60회후잔액과남은300개월사용','추가출산·우대·중도상환·자산초과가산0','상품승인/미래정책·실제고지액 확정아님'],
              not_reviewed=['작성중v2대본의실제반영·SC01~04종결','기존157개·본편전체·이전편','추가출산연장세부·모든상품자격·공급유형예외','현재소스카탈로그ID매핑(총괄담당)','Claude/TTS/렌더/업로드'],
              actual_listening='unchecked', continuous_playback='unchecked', live_browsing=False, external_payloads=0, paid_calls=0,
              peer_delivery='직접에이전트메시지도구없음.담당폴더issue파일/최종응답으로인계.')
write('review.json', report)
write('issue_NBD-HANDOFF.json', dict(issue_id='NBD-HANDOFF',scene_id='CH08',problem='새필수오류0. NBD-01/02는검증된조건유지사항.',evidence='review.json/source_excerpts.json/arithmetic_delta.json',proposal='v2대본반영과기존SC02/03종결은총괄이실제대본을읽고별도판정.',impact='신생아자격과전환금리·상환액장면.다른장면변경요구없음.',owner='director/writer',status='ready_for_director'))
write('handoff.json', dict(status='approved_with_scope', output_paths=[(OUT/p).as_posix() for p in ['findings.json','review.json','source_excerpts.json','arithmetic_delta.json','issue_NBD-HANDOFF.json']],
      input_versions='review.json input_manifest 및 KB/NHUF 20:23UTC receipt SHA',
      validation=dict(required=0,recommended=2,checks_passed=len(checks),independent_math='유한할인합/잔액순환/이분법;기존엔진미사용',initial_monthly_krw=str(initial),balance_after60_krw=str(balance),reset_monthly_krw=str(monthly)),
      unresolved=['v2대본반영/SC종결은전체대본검수담당','소스카탈로그ID매핑은총괄범위'],affected_scenes=['CH08/N01','CH08/N05A'],next_owner='video_director / writer',scope='원문·산술차이만승인.대본/TTS/미디어승인아님.새유료/외부/원본수정없음.'))
print(json.dumps(dict(status='approved_with_scope',required=0,recommended=2,checks_passed=len(checks),initial_monthly=str(initial),balance60=str(balance),monthly_after60=str(monthly)),ensure_ascii=False))
