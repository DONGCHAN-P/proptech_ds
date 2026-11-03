"""독립 QA: 연구 파일을 import만 하며 연구 산출물을 덮어쓰지 않는다."""
import importlib.util, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'research/illustrative_model.py'
spec = importlib.util.spec_from_file_location('subject', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks=[]
def close(a,b):
    assert abs(a-b)<0.01, (a,b,a-b)
def annuity(rate,n):
    return n if rate==0 else ((1+rate)**n-1)/rate
def independent(g=.02,s=.06,rate=.04):
    # 상환액은 360회 할인현금흐름 합으로 독립 산출.
    r=rate/12
    p=360_000_000/sum((1+r)**(-t) for t in range(1,361))
    # 잔존부채는 남은 240회 상환액의 120월 시점 현재가치.
    debt=p*sum((1+r)**(-t) for t in range(1,241))
    q=(1+s)**(1/12)-1
    fv=lambda initial,c:initial*(1+s)**10+c*annuity(q,120)
    return {'매매':600_000_000*(1+g)**10+fv(4_000_000,2_700_000-p)-debt,
            '전세':200_000_000+fv(49_000_000,3_000_000-50_000-200_000_000*.04/12),
            '월세':80_000_000+fv(169_000_000,3_000_000-50_000-1_000_000-20_000_000*.04/12)},p,debt

results=[]
for name,g,s in [('baseline',.02,.06),('flat_house_low_stock',0,.02),('high_house_low_stock',.04,.02)]:
    actual=m.simulate(house_growth=g,stock_return=s)
    expected,p,debt=independent(g,s)
    for label,v in actual['paths'].items(): close(v['continuing_networth'],expected[label])
    close(actual['paths']['매매']['debt'],debt)
    close(actual['paths']['매매']['mortgage_payment'],p)
    results.append(dict(case=name,networth=expected,payment=p,mortgage_balance=debt))
checks.append('three_cases_discounted_cashflow_and_terminal_closed_form')

base=m.simulate()
for label,v in base['paths'].items():
    close(v['initial_networth_after_entry'],250_000_000-(6_000_000 if label=='매매' else 1_000_000))
    for row in v['monthly_ledger']:
        close(row['housing_cash_outflow']+row['invest_contribution']+row['cash_contribution'],3_000_000)
checks.append('equal_initial_wealth_and_all_month_budget_allocation')
v=base['paths']['매매']; close(360_000_000-v['debt'],v['total_principal'])
close(v['total_principal']+v['total_interest'],v['mortgage_payment']*120)
checks.append('principal_debt_and_interest_cash_reconciliation')
for label,deposit,debt in [('전세',400_000_000,200_000_000),('월세',100_000_000,20_000_000)]:
    v=base['paths'][label]; close(v['housing_asset'],deposit); close(v['debt'],debt)
    close(v['liquidation_networth'],deposit-debt+v['invested']*.995+v['cash'])
checks.append('deposit_return_repay_debt_not_double_counted')
for execution in [0,.5]:
    run=m.simulate(execution=execution)
    for label,v in run['paths'].items():
        c=base['paths'][label]['monthly_ledger'][0]['invest_contribution']
        close(v['cash'],120*c*(1-execution))
        q=1.06**(1/12)-1
        close(v['invested'],v['initial_invested']*1.06**10+c*execution*annuity(q,120))
checks.append('execution_shortfall_retained_as_zero_interest_cash')
assert all(not v['feasible'] and v['continuing_networth'] is None for v in m.simulate(budget=100_000)['paths'].values())
initial_failure=None
try:
    invalid=m.simulate(entry_buy=11_000_000)['paths']['매매']
    assert not invalid['feasible'] and invalid['failure']=='initial_funding'
    assert invalid['continuing_networth'] is None and invalid['liquidation_networth'] is None
    assert invalid['monthly_ledger']==[]
except AssertionError:
    initial_failure='QA-M01: initial_funding flag set but monthly loop raises AssertionError'
checks.append('monthly_funding_rejected; initial_funding_failed' if initial_failure else 'monthly_and_initial_funding_infeasible_rejected')
for label,v in base['paths'].items():
    close(v['assumed_liquidation_cost'],v['invested']*.005+(v['housing_asset']*.01 if label=='매매' else 0))
    close(v['continuing_networth']-v['liquidation_networth'],v['assumed_liquidation_cost'])
checks.append('continuing_vs_hypothetical_liquidation_separated')
# 월세 수준 민감도는 미래 가치 미분으로 계산: 월 20만원 차이의 120회 누적.
low=m.simulate(monthly_rent=800_000)['paths']['월세']['continuing_networth']
high=m.simulate(monthly_rent=1_200_000)['paths']['월세']['continuing_networth']
close(low-high,400_000*annuity(1.06**(1/12)-1,120))
checks.append('rental_price_sensitivity_independent_fv_derivative')
result=dict(status='required_issue_open' if initial_failure else 'passed_with_limits',initial_failure=initial_failure,model_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),checks=checks,case_results=results,rent_sensitivity=dict(monthly_800000=low,monthly_1200000=high),limits=['세금·규制·시세·외부 출처 진위 독립 검증 아님','집값·ETF 수익률 매월 일정, 비용·임대료 명목 고정','동일 주거서비스 및 보증금 전액 반환 가정은 시장 검증 아님','미디어·청취·연속재생 범위 아님'])
Path(__file__).with_name('check_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
if not initial_failure:
    for filename in ['findings.json','handoff.json']:
        path=Path(__file__).with_name(filename)
        if path.exists():
            data=json.loads(path.read_text(encoding='utf-8'))
            if filename=='findings.json':
                issue=data['items'][0]
                issue['status']='closed_independently_retested'
                issue['checked_revision']=result['model_sha256']
                issue['evidence']+=' 修正後に同一入力の正常返却・failure・None値・空ledgerを独立再実行で確認。'
                data['coverage']['budget_principal_deposit_cash_liquidation']='passed'
            else:
                data['status']='passed_with_limits'
                data['input_revisions']['model_sha256']=result['model_sha256']
                data['open_issue_ids']=[]
                data['checks'][0]['result']='8 independent groups passed; QA-M01 independently closed'
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
