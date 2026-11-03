"""가정 예시 전용. 원화, 명목, 월말 납입. 실제 시세/세율/과거수익 아님."""
import json
from pathlib import Path


def payment(principal, annual_rate, months):
    r = annual_rate/12
    return principal/months if r == 0 else principal*r/(1-(1+r)**(-months))


def simulate(house_growth=.02, stock_return=.06, rate=.04, budget=3_000_000,
             owner_cost=300_000, rent_cost=50_000, entry_buy=6_000_000,
             entry_rent=1_000_000, monthly_rent=1_000_000,
             jeonse_loan_rate=.04, rent_loan_rate=.04, execution=1.0):
    assumptions = dict(initial_wealth=250_000_000, house=600_000_000,
                       budget=budget, months=120, loan_months=360,
                       house_growth=house_growth, stock_return=stock_return,
                       rate=rate, owner_cost=owner_cost, rent_cost=rent_cost,
                       entry_buy=entry_buy, entry_rent=entry_rent,
                       monthly_rent=monthly_rent, jeonse_loan_rate=jeonse_loan_rate,
                       rent_loan_rate=rent_loan_rate, execution=execution,
                       hypothetical_house_disposal_rate=.01,
                       hypothetical_investment_disposal_rate=.005)
    specs = {'매매': (600_000_000, 360_000_000, entry_buy, owner_cost, 0, rate),
             '전세': (400_000_000, 200_000_000, entry_rent, rent_cost, 0, jeonse_loan_rate),
             '월세': (100_000_000, 20_000_000, entry_rent, rent_cost, monthly_rent, rent_loan_rate)}
    paths = {}
    for label, (housing, debt, fee, ongoing, rent, loan_rate) in specs.items():
        invested = 250_000_000-(housing-debt)-fee
        cash = 0.0
        initial_nw = housing+invested-debt
        assert abs(initial_nw-(250_000_000-fee)) < .01
        ledger = []
        pay = payment(debt, loan_rate, 360) if label == '매매' else 0
        feasible = invested >= 0
        failure = None if feasible else 'initial_funding'
        total_interest = total_principal = total_cost = 0.0
        for month in range(1, 121):
            if not feasible:
                break
            before = housing+invested+cash-debt
            gain = invested*((1+stock_return)**(1/12)-1)
            appreciation = housing*((1+house_growth)**(1/12)-1) if label == '매매' else 0
            interest = debt*loan_rate/12
            principal = min(debt, pay-interest) if label == '매매' else 0
            outflow = interest+principal+ongoing+rent
            # 엄격 월예산: 기존 자산 매도로 월적자를 보충하지 않는 시나리오.
            if outflow > budget+.0001:
                feasible, failure = False, f'month_{month}_housing_outflow_exceeds_budget'
                break
            surplus = budget-outflow
            invested += gain+surplus*execution
            cash += surplus*(1-execution)
            debt -= principal
            housing += appreciation
            after = housing+invested+cash-debt
            expected_change = budget-interest-ongoing-rent+gain+appreciation
            assert abs((after-before)-expected_change) < .01
            assert min(invested, cash, debt) >= -.01
            total_interest += interest
            total_principal += principal
            total_cost += ongoing+rent
            ledger.append(dict(month=month, housing_asset=housing, debt=debt,
                               invested=invested, cash=cash, interest=interest,
                               principal=principal, housing_cash_outflow=outflow,
                               invest_contribution=surplus*execution,
                               cash_contribution=surplus*(1-execution), networth=after))
        nw = housing+invested+cash-debt if feasible else None
        disposal = (housing*.01 if label == '매매' else 0)+invested*.005
        paths[label] = dict(feasible=feasible, failure=failure,
                            initial_networth_after_entry=initial_nw,
                            initial_invested=250_000_000-(specs[label][0]-specs[label][1])-fee,
                            housing_asset=housing, debt=debt, invested=invested, cash=cash,
                            mortgage_payment=pay, total_interest=total_interest,
                            total_principal=total_principal, total_consumption_cost=total_cost,
                            continuing_networth=nw,
                            assumed_liquidation_cost=disposal if feasible else None,
                            liquidation_networth=nw-disposal if feasible else None,
                            monthly_ledger=ledger)
    winner = max((k for k,v in paths.items() if v['feasible']),
                 key=lambda k: paths[k]['continuing_networth'], default=None)
    return dict(assumptions=assumptions, paths=paths, winner=winner)


def fixtures():
    # 손계산 가능한 0금리 원금상환과 유상 주거비가 있는 순자산 보존.
    assert abs(payment(360, 0, 360) - 1) < 1e-9
    x = simulate(house_growth=0, stock_return=0, rate=0,
                 owner_cost=0, rent_cost=0, entry_buy=0, entry_rent=0,
                 monthly_rent=0, jeonse_loan_rate=0, rent_loan_rate=0)
    for v in x['paths'].values():
        assert abs(v['continuing_networth'] - (250_000_000 + 3_000_000*120)) < .01
    # 실제 월세 지급액만큼 순자산 감소해야 함.
    y = simulate(house_growth=0, stock_return=0, rate=0,
                 owner_cost=0, rent_cost=0, entry_buy=0, entry_rent=0,
                 monthly_rent=1_000_000, jeonse_loan_rate=0, rent_loan_rate=0)
    assert abs(y['paths']['월세']['continuing_networth'] - 490_000_000) < .01
    # 30년 만기, 최종 원금 및 닫힌식으로 계산한 10년 잔액 일치.
    p = payment(360_000_000, .04, 360)
    r = .04/12
    expected = 360_000_000*(1+r)**120-p*((1+r)**120-1)/r
    z = simulate()
    assert abs(z['paths']['매매']['debt'] - expected) < .01
    balance = 360_000_000
    for _ in range(360):
        balance = balance*(1+r)-p
    assert abs(balance) < .01
    assert simulate(budget=100_000)['paths']['매매']['feasible'] is False
    invalid = simulate(entry_buy=11_000_000)['paths']['매매']
    assert invalid['feasible'] is False and invalid['failure'] == 'initial_funding'
    assert invalid['continuing_networth'] is None
    assert invalid['liquidation_networth'] is None
    assert invalid['monthly_ledger'] == []
    # 임차인의 보증금 채권과 대출은 각각 잔존. 초기비용은 단 한 번 차감.
    assert z['paths']['전세']['housing_asset'] == 400_000_000
    assert z['paths']['전세']['debt'] == 200_000_000
    assert z['paths']['월세']['debt'] == 20_000_000
    assert z['paths']['매매']['initial_networth_after_entry'] == 244_000_000
    assert z['paths']['전세']['initial_networth_after_entry'] == 249_000_000
    return ['zero_return_wealth_conservation', 'rent_consumption_identity',
            'amortization_closed_form', 'loan_maturity_zero', 'budget_infeasible',
            'deposit_asset_and_loan_preserved', 'entry_fee_once', 'monthly_wealth_identity_all_paths',
            'initial_funding_invalid_response']


if __name__ == '__main__':
    checks = fixtures()
    cases = [('기본', {}), ('집0%_주식2%', dict(house_growth=0, stock_return=.02)),
             ('집4%_주식2%', dict(house_growth=.04, stock_return=.02)),
             ('집0%_주식8%', dict(house_growth=0, stock_return=.08)),
             ('집4%_주식8%', dict(house_growth=.04, stock_return=.08)),
             ('전세금리2%_매수6%', dict(rate=.06, jeonse_loan_rate=.02)),
             ('전세금리6%_매수2%', dict(rate=.02, jeonse_loan_rate=.06)),
             ('차액투자0%', dict(execution=0)),
             ('차액투자50%', dict(execution=.5)),
             ('월예산10만원_불가능', dict(budget=100_000))]
    runs = {name: simulate(**kw) for name, kw in cases}
    result = dict(revision='illustrative-v1', hypothetical_only=True,
                  unit='KRW nominal', checks_passed=checks,
                  note='모든 가격·임대료·비용·수익·금리는 가정. ETF는 원화 환율 포함 총수익, 추가 배당/환율 가산 없음. 세금 모형 아님.',
                  cases=runs)
    dest = Path(__file__).with_name('illustrative_results.json')
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    base = runs['기본']['paths']
    lines = ['# 가상 월별 3방식 비교 — illustrative-v1', '',
             '**전 수치가 설명용 가정이다. 시세·실제 ETF 과거수익·법정세율·대출 승인 가능성의 검증이 아니다.**', '',
             '동일 가구 초기 순자산 2억5천만원, 월 가용 주거·저축 예산 300만원, 동일 주거서비스로 가정한 6억원 집에서 10년 거주한다. 공통 생활비는 이미 예산 밖에서 동일하게 차감했다고 둔다. 명목 원화 모형이며 물가 조정은 하지 않는다.', '',
             '매매는 자기자금 2억4천만원·대출 3억6천만원·진입비 600만원. 전세는 보증금 4억원·전세대출 2억원·진입비 100만원. 월세는 보증금 1억원·보증금대출 2천만원·월세 100만원·진입비 100만원. 전세/월세 대출은 매월 이자만 내고 만기 원금은 보증금 반환 때 갚는 것으로 가정한다. 보증금은 100% 반환, 갱신 증액/반환 지연은 없다. 모든 금리는 기본 연4%이며 10년 고정한다.', '',
             '매매 대출은 30년 원리금균등, 월금리는 연금리/12. 집값은 기본 연2% 복리. ETF는 기본 원화 명목 연6% 총수익을 가정하며 배당·환율 효과를 이미 포함한 한 개 수익률이다. 배당과 FX를 더하지 않는다. 운용 중 세금·보수 모형은 생략한 가정 수익이며 실제 세후 성과가 아니다. 월 수익률=(1+연수익률)^(1/12)-1. 월초 금융자산에 수익을 적용한 후 월말 잉여예산을 넣는다.', '',
             '소유자 월 유지·보유비 30만원, 임차인 월 추가비 5만원을 가정한다. 매매 30만원은 임차인보다 더 부담하는 보유세/수선/보험 등 비용 묶음이며 특정 법정 세율이 아니다. 공통 관리비는 공통 생활비로 처리한다. 10년 동안 비용·월세는 명목 고정하고 인상률은 0으로 둔다.', '',
             '초기 남은 금융자금은 세 방식 모두 즉시 ETF에 100% 투자한다. 차액투자 실행률은 이후 월 잉여액에만 적용한다. 실행률 0/50%의 미투자 잔액은 소비하지 않고 0% 현금으로 쌓인다. 따라서 이는 저축을 포기한 실험이 아니라 투자수익만 포기한 실험이다.', '',
             '## 초기 및 첫 달 현금흐름', '',
             '| 방식 | 초기 금융자산(만원) | 진입 직후 순자산(만원) | 월 주거 현금지출(만원) | 월 ETF 적립(만원) |',
             '|---|---:|---:|---:|---:|']
    for k,v in base.items():
        m=v['monthly_ledger'][0]
        lines.append(f"| {k} | {v['initial_invested']/1e4:,.2f} | {v['initial_networth_after_entry']/1e4:,.2f} | {m['housing_cash_outflow']/1e4:,.2f} | {m['invest_contribution']/1e4:,.2f} |")
    lines += ['', '매매의 월 원리금은 171.87만원, 첫 달 이자 120만원·원금 51.87만원이다. 원금은 현금에서 나가지만 부채도 같은 금액 줄어든다. 이를 순자산에서 비용으로 또 빼지 않는다. 세 방식 모두 남는 월예산을 동일한 ETF 규칙으로 투자한다.', '',
              '## 10년 후 기본 결과', '',
              '| 방식 | 집/반환보증금(만원) | 금융자산(만원) | 남은 부채(만원) | 계속거주 순자산(만원) | 가정 청산비(만원) | 청산액(만원) |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for k,v in base.items():
        vals=[v['housing_asset'],v['invested']+v['cash'],v['debt'],v['continuing_networth'],v['assumed_liquidation_cost'],v['liquidation_networth']]
        lines.append('| '+k+' | '+' | '.join(f'{n/1e4:,.2f}' for n in vals)+' |')
    lines += ['', '계속거주 순자산=집 또는 반환보증금+금융자산−잔존부채. 초기자금은 이 자산들에 이미 들어 있으므로 끝에 다시 더하지 않는다. 매매 집값은 7억3,139.67만원이지만 대출 2억8,362.23만원이 남는다. 전세금 4억원 자체를 전세인의 순자산으로 보면 대출 2억원을 놓친다.', '',
              '청산은 전원 같은 시점 퇴거·자산 매도를 가정한다. 집에는 매도가의 1%, ETF에는 평가액의 0.5%를 일회 처분비로 차감하고 보증금은 전액 회수한다. 이 비율은 설명용 거래마찰이지 양도세·배당세 등 실제 세제 계산이 아니다. 청산 뒤 대체 거주비는 포함하지 않아 이후 거주생활의 우위를 뜻하지 않는다. 실제 대본에서는 계속거주 표를 기본으로 쓰고 청산 표는 별도 가정으로 제시한다.', '',
              '## 민감도 — 계속거주 순자산, 억원', '',
              '| 조건 | 매매 | 전세 | 월세 | 이 가정에서 최대 |', '|---|---:|---:|---:|---|']
    for name,run in runs.items():
        vals=[f"{v['continuing_networth']/1e8:.4f}" if v['feasible'] else '불가능' for v in run['paths'].values()]
        lines.append('| '+name+' | '+' | '.join(vals)+f" | {run['winner'] or '없음'} |")
    lines += ['', '표에서 명시하지 않은 값은 기본과 같다. 금리 반전 행은 매매/전세 금리만 바꾸며 월세 보증금대출은 4% 유지한다. 이는 기간 중 변동금리 경로가 아니라 처음부터 다른 고정금리 조건이다. 주식2/8%는 원화 총수익 가정, 집0/4%는 가격상승만이다. 같은 주거조건에서도 자본수익·금리 조합에 따라 최대 순자산 방식이 바뀐다. 국내 과거 10년 실증 승패로 표현하지 않는다.', '',
              '월 주거 현금지출이 예산을 넘으면 엄격한 월예산 기준에서 해당 경로를 불가능 처리한다. 기존 ETF 매도·추가 차입·외부 지원으로 적자를 메우는 경로는 이 모형에 없다. 월예산 10만원 행은 세 경로 모두 첫 달 불가능이다. 이는 모든 현실적 자금조달이 불가능하다는 뜻이 아니라 이 고정 월예산/무매도 정책의 불가능 판정이다.', '',
              '## 식과 실행 검증', '',
              '`월 상환액 = L*r/(1-(1+r)^(-360)); r=연금리/12`',
              '`월 원금 = 월 상환액−월초 부채*r; 월말 부채=월초 부채−원금`',
              '`금융자산 증가=월초 투자액*월총수익+월예산−이자−원금−월세−기타비용`',
              '`월 순자산 증가=월예산−이자−월세−기타비용+ETF 평가수익+집값 상승`', '',
              '마지막 식에는 원금이 없다. 현금과 부채에서 상쇄되기 때문이다. 보증금도 회수할 자산으로 계속 남기므로 초기 지출과 기말 자산을 연결한다. 귀속임대료·포기한 투자수익은 별도 가산/차감하지 않는다.', '',
              '표준 라이브러리만 사용. 실행 명령: `tools/python311/python.exe -X utf8 video-agent-studio/episodes/housing-choice-networth-20261020/research/illustrative_model.py`.', '',
              '통과 fixture: '+', '.join(checks)+'. 매월 모든 경로에서 순자산 보존식 오차 0.01원 이내, 부채·현금·ETF 잔액 음수 없음. 10년 대출잔액을 닫힌식과 대조하고 30년 상환잔액이 0에 수렴하는지 확인했다. 원자료 JSON에는 각 조건 120개월 원금·이자·납입·잔액을 남겼다(불가능 조건은 첫 달 중단).', '',
              '본 실행은 작성자 자체 검증이다. 독립 QA는 아직 수행하지 않았다. 보증금 증액/재대출·변동금리·소득/규제·정교한 세제·수익률 변동성·CPI는 범위 밖이며 미래 투자 성과 예측도 아니다.']
    Path(__file__).with_name('illustrative_model_note.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('fixtures:', ', '.join(checks))
    for name, run in runs.items():
        vals = {k: round(v['continuing_networth']/1e8, 4) if v['feasible'] else '불가능'
                for k,v in run['paths'].items()}
        print(name, vals, '최대:', run['winner'])
