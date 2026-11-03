"""익명 주택구입 사례의 조건부 상한 계산. 실행: python -B engine.py

입력 cases.json/assumptions.json → results.json. 외부 호출·기존 금융모형 변경 없음.
Decimal 계산값과 표시/낭독 반올림을 분리하며 실제 은행 승인을 계산하지 않는다.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
import hashlib
import json

getcontext().prec = 40
ROOT = Path(__file__).resolve().parent


def d(value):
    return Decimal(str(value))


def payment(principal, annual_rate, months):
    principal, rate = d(principal), d(annual_rate) / 12
    if not rate:
        return principal / months
    return principal * rate / (1 - (1 + rate) ** -months)


def pv(monthly_budget, annual_rate, months):
    budget, rate = max(d(0), d(monthly_budget)), d(annual_rate) / 12
    if not rate:
        return budget * months
    return budget * (1 - (1 + rate) ** -months) / rate


def service_ceiling(income, ratio, existing_annual_service, annual_rate, months):
    return pv(max(d(0), d(income) * d(ratio) - d(existing_annual_service)) / 12,
              annual_rate, months)


def tax(price):
    price = d(price)
    if price <= 600000000:
        percent = d(1)
    elif price <= 900000000:
        percent = (price / 100000000 * 2 / 3 - 3).quantize(d('.0001'), rounding=ROUND_HALF_UP)
    else:
        percent = d(3)
    acquisition = price * percent / 100
    return dict(rate_percent=percent, acquisition_krw=acquisition,
                education_krw=acquisition / 10, agricultural_krw=d(0))


def brokerage(price):
    price = d(price)
    if price < 50000000:
        base = min(price * d('.006'), d(250000))
    elif price < 200000000:
        base = min(price * d('.005'), d(800000))
    else:
        rate = '.004' if price < 900000000 else '.005' if price < 1200000000 else '.006' if price < 1500000000 else '.007'
        base = price * d(rate)
    return dict(before_vat_krw=base, vat_krw=base / 10, with_vat_krw=base * d('1.1'))


def regulatory_cap(price):
    return d(600000000 if price <= 1500000000 else 400000000 if price <= 2500000000 else 200000000)


def costs(price, misc_plan):
    taxes, broker = tax(price), brokerage(price)
    total = sum((taxes['acquisition_krw'], taxes['education_krw'], taxes['agricultural_krw'],
                 broker['with_vat_krw'], d(misc_plan)))
    return dict(**taxes, **broker, misc_plan_krw=d(misc_plan), total_krw=total)


def expand_cases(packet):
    cases = []
    for profile_id, profile in packet['profiles'].items():
        for price in packet['grid']['prices_krw']:
            for deduction in packet['grid']['deductions_krw']:
                note = '보증승인 등으로 미커버 차감0을 가정; 자동면제 아님' if not deduction else '서울1방 미커버5500만원 차감 가정'
                scenario_status = 'conditional_assumption'
                if profile['product'] == 'bogeum':
                    note = '빈 아파트 자체 방수공제0' if not deduction else '추가 담보차감 민감도; 보금자리 빈 아파트의 현행 방공제 아님'
                    scenario_status = 'current_apartment_rule' if not deduction else 'counterfactual_sensitivity'
                elif profile['product'] == 'newborn' and price > 600000000 and not deduction:
                    note = '6억초과 HF보증 불가 회신과 구별한 공제제거 반사실 민감도; 현행 보증승인 가능 주장 아님'
                    scenario_status = 'counterfactual_sensitivity'
                cases.append(dict(packet['common'], **profile, profile_id=profile_id,
                                  case_id=f'{profile_id}_P{price}_C{deduction}', price_krw=price,
                                  deduction_krw=deduction, deduction_note=note,
                                  deduction_scenario_status=scenario_status))
    return cases


def evaluate(case):
    c = case
    price, income, rate = d(c['price_krw']), d(c['annual_income_krw']), d(c['annual_rate'])
    reasons = []
    for key, actual in [('price_ceiling_krw',price), ('income_ceiling_krw',income), ('asset_ceiling_krw',d(c['net_assets_krw']))]:
        if c.get(key) is not None and actual > d(c[key]):
            reasons.append(key)
    if c['product'] == 'bogeum' and not c['first_purchase']:
        reasons.append('first_purchase')
    if c['product'] == 'didim' and not c['married_within_7_years']:
        reasons.append('married_within_7_years')
    if c['product'] == 'newborn' and not c['child_within_2_years']:
        reasons.append('child_within_2_years')
    eligible = not reasons
    collateral = max(d(0), price * d(c['ltv']) - d(c['prior_claim_krw'])
                     - d(c['tenancy_deduction_krw']) - d(c['deduction_krw']))
    limits = dict(collateral=collateral,
                  DTI=service_ceiling(income,c['dti_ratio'],c['existing_annual_dti_krw'],c['dti_rate'],c['months']),
                  DSR=service_ceiling(income,c['dsr_ratio'],c['existing_annual_dsr_krw'],rate+d(c['stress_add']),c['months']) if c['dsr_ratio'] else None,
                  regulatory_total=regulatory_cap(price) if c['product']=='bank' else None,
                  product=d(c['product_cap_krw']) if c.get('product_cap_krw') else None,
                  purchase_price=price)
    ceiling = min(v for v in limits.values() if v is not None) if eligible else d(0)
    binding = [k for k,v in limits.items() if v is not None and abs(v-ceiling)<d('.000001')] if eligible else ['eligibility']
    fees = costs(price,c['misc_plan_krw'])
    required = max(d(0),price+fees['total_krw']+d(c['reserve_krw'])-d(c['cash_krw']))
    cash_feasible = eligible and required <= ceiling
    pmt = payment(ceiling,rate,c['months']) if eligible else None
    pmt_needed = payment(required,rate,c['months']) if eligible else None
    shock = payment(ceiling,'.06',c['months']) if c['product']=='bank' else None
    surplus = d(c['housing_savings_budget_monthly_krw'])-d(c['ownership_monthly_plan_krw'])
    return dict(case_id=c['case_id'],profile_id=c['profile_id'],household_id=c['household_id'],
                label=c['label'],deduction_scenario_status=c['deduction_scenario_status'],deduction_note=c['deduction_note'],
                rate_used=str(rate),dti_rate_used=c['dti_rate'],rate_status=c.get('rate_status','계산용 약정4%·스트레스 심사7%'),
                eligible_under_stated_inputs=eligible,eligibility_failures=reasons,
                price_krw=price,valuation_krw=price,deduction_krw=d(c['deduction_krw']),
                limits_krw=limits,binding_constraints=binding,loan_ceiling_krw=ceiling,
                transaction_costs=fees,required_loan_krw=required,
                usable_house_price_equity_krw=d(c['cash_krw'])-d(c['reserve_krw'])-fees['total_krw'],
                cash_required_including_reserve_krw=price+fees['total_krw']+d(c['reserve_krw'])-ceiling,
                cash_shortfall_krw=max(d(0),required-ceiling),cash_feasible=cash_feasible,
                payment_at_ceiling_krw=pmt,payment_at_required_loan_hypothetical_krw=pmt_needed,
                payment_if_financeable_krw=pmt_needed if cash_feasible else None,
                mortgage_budget_krw=d(c['mortgage_budget_monthly_krw']),
                cash_and_monthly_budget_feasible=cash_feasible and pmt_needed<=d(c['mortgage_budget_monthly_krw']),
                savings_after_ceiling_payment_krw=surplus-pmt if pmt is not None else None,
                payment_at_ceiling_shock_krw=shock,
                shock_payment_increase_krw=shock-pmt if shock is not None else None,
                savings_after_ceiling_shock_krw=surplus-shock if shock is not None else None,
                policy_dti_sensitivity_7pct_krw=service_ceiling(income,c['dti_ratio'],c['existing_annual_dti_krw'],'.07',c['months']) if c['product']!='bank' else None)


def affordable(case, monthly_budget=None):
    x = evaluate(case)
    capacity = x['loan_ceiling_krw']
    if monthly_budget is not None:
        capacity = min(capacity,pv(monthly_budget,case['annual_rate'],case['months']))
    return x['eligible_under_stated_inputs'] and x['required_loan_krw'] <= capacity


def solve_affordability(case, monthly_budget=None, step=10000, max_price=3000000000):
    # 정수 가격 격자의 이분탐색. 세율 반올림·중개요율 상승·대출상한 하락도 자금부족을 줄이지 않는다.
    if affordable(dict(case,price_krw=max_price),monthly_budget):
        raise ValueError('탐색 상단에서도 가능: 도메인 확장 후 다시 계산 필요')
    low, high = 0, max_price//step
    while low < high:
        mid = (low+high+1)//2
        if affordable(dict(case,price_krw=mid*step),monthly_budget):
            low = mid
        else:
            high = mid-1
    price = low*step
    x = evaluate(dict(case,price_krw=price))
    capacity = min(x['loan_ceiling_krw'],pv(monthly_budget,case['annual_rate'],case['months'])) if monthly_budget is not None else x['loan_ceiling_krw']
    selected = payment(x['required_loan_krw'],case['annual_rate'],case['months'])
    shock = payment(x['required_loan_krw'],'.06',case['months'])
    return dict(max_price_krw=price,grid_krw=step,search_max_krw=max_price,
                condition='은행심사 가정상한 기준' if monthly_budget is None else '월170만원 목표 + 은행심사 가정상한 기준',
                affordable_10k_below=affordable(dict(case,price_krw=price-step),monthly_budget),
                affordable_at_max=affordable(dict(case,price_krw=price),monthly_budget),
                affordable_10k_above=affordable(dict(case,price_krw=price+step),monthly_budget),
                bank_binding_constraints=x['binding_constraints'],
                monthly_budget_cap_binding=monthly_budget is not None and capacity<x['loan_ceiling_krw'],
                loan_ceiling_krw=x['loan_ceiling_krw'],available_loan_with_budget_krw=capacity,
                required_loan_krw=x['required_loan_krw'],transaction_cost_krw=x['transaction_costs']['total_krw'],
                payment_on_required_loan_krw=selected,payment_shock_same_original_360months_krw=shock,
                remaining_savings_krw=d(case['housing_savings_budget_monthly_krw'])-d(case['ownership_monthly_plan_krw'])-selected,
                remaining_savings_shock_krw=d(case['housing_savings_budget_monthly_krw'])-d(case['ownership_monthly_plan_krw'])-shock)


def money_layers(values):
    return dict(calculation_krw_decimal={k:format(d(v),'f') if v is not None else None for k,v in values.items()},
                rounded_krw={k:int(d(v).quantize(d(1),rounding=ROUND_HALF_UP)) if v is not None else None for k,v in values.items()},
                reading_manwon={k:int((d(v)/10000).quantize(d(1),rounding=ROUND_HALF_UP)) if v is not None else None for k,v in values.items()})


def add_display(row):
    values = {k:v for k,v in row.items() if k.endswith('_krw') and not isinstance(v,dict)}
    values.update({f'limit_{k}':v for k,v in row.get('limits_krw',{}).items()})
    values.update({f'cost_{k}':v for k,v in row.get('transaction_costs',{}).items() if k.endswith('_krw')})
    layers = money_layers(values)
    row['presentation'] = dict(rounded_krw=layers['rounded_krw'],reading_manwon=layers['reading_manwon'])
    return row


def main():
    packet = json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))
    assumptions = json.loads((ROOT/'assumptions.json').read_text(encoding='utf-8'))
    cases = expand_cases(packet)
    solver_rows = []
    for c in cases:
        if c['household_id']=='A' and c['price_krw']==600000000:
            solver_rows.append(dict(profile_id=c['profile_id'],deduction_krw=c['deduction_krw'],deduction_note=c['deduction_note'],
                                    bank_assumptions_max=add_display(solve_affordability(c,**dict(step=packet['solver']['grid_krw'],max_price=packet['solver']['search_max_krw']))),
                                    mortgage_budget_max=add_display(solve_affordability(c,c['mortgage_budget_monthly_krw'],step=packet['solver']['grid_krw'],max_price=packet['solver']['search_max_krw']))))
    relief = [dict(price_krw=p,base_acquisition_krw=tax(p)['acquisition_krw'],
                   conditional_firstbuyer_max_reduction_krw=min(tax(p)['acquisition_krw'],d(2000000)),
                   conditional_child_max_reduction_krw=min(tax(p)['acquisition_krw'],d(5000000)),
                   applied_to_base=False,additive=False,net_tax_after_relief_krw=None) for p in packet['grid']['prices_krw']]
    result = dict(task_id=packet['task_id'],as_of_kst=packet['as_of_kst'],status='research_calculation_only_not_approval',
                  money_format='*_krw: 반올림 전 Decimal 계산값(문자열). presentation은 원단위/낭독만원 별도 반올림. 가능 판정은 원 계산값 사용.',
                  limitations=['가정상한은 실제 은행 승인액 아님. 반사실 민감도는 현재 보증가능 주장 아님.','디딤돌·보금자리4%는 계산가정. 신생아2.9%는 초기 특례금리로만 해석.','세금 끝수/실제견적/보증승인/장래금리 미확정. 감면은 기본표에 미차감.'],
                  input_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['engine.py','cases.json','assumptions.json']},
                  policy_inputs=assumptions['input_versions'],case_results=[add_display(evaluate(c)) for c in cases],
                  affordability_A=solver_rows,conditional_relief_table=relief,
                  source_and_gap_file='assumptions.json',paid_api_calls=0)
    (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda v:format(v,'f') if isinstance(v,Decimal) else str(v))+'\n',encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),solver_profiles=len(solver_rows),output='results.json'),ensure_ascii=False))


if __name__=='__main__':
    main()
