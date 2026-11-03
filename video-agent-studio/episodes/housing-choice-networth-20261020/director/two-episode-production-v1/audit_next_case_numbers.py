"""Independent arithmetic checks of the next episode's prepared case ledger."""
import hashlib
import json
from datetime import datetime, timezone
from math import isclose
from pathlib import Path

BASE = Path(__file__).resolve().parent
source = BASE/'next_case_engine_prep_v2/results.json'
data = json.loads(source.read_text(encoding='utf-8'))
checks = []

def check(name, actual, expected, tolerance=1.0):
    passed = abs(float(actual)-float(expected)) <= tolerance
    checks.append({'check':name,'actual':float(actual),'expected':float(expected),'passed':passed})
    assert passed, name

# The independent reference discounts each of 360 individual payments.
# It does not import or call the case engine's annuity functions.
def present_value(payment, annual):
    return sum(payment/(1+annual/12)**month for month in range(1,361))

base_costs = {
    600000000: (6000000,600000,2640000,10740000),
    900000000: (27000000,2700000,4950000,36150000),
    1200000000: (36000000,3600000,7920000,49020000),
}
for row in data['case_results']:
    if row['case_id'] not in data['video_review_subset']['case_ids']:
        continue
    name = row['case_id']
    price = int(row['price_krw'])
    acqu,educ,broker,total = base_costs[price]
    cost = row['transaction_costs']
    for field, expected in [('acquisition_krw',acqu),('education_krw',educ),('with_vat_krw',broker),('total_krw',total)]:
        check(name+'/'+field,cost[field],expected)
    check(name+'/cash_needed_loan',row['required_loan_krw'],price+total+30000000-250000000)
    available = min(float(v) for v in row['limits_krw'].values() if v is not None)
    check(name+'/minimum_limit',row['loan_ceiling_krw'],available)
    check(name+'/cash_shortfall',row['cash_shortfall_krw'],max(0,price+total+30000000-available-250000000))
    if row['payment_if_financeable_krw'] is not None:
        check(name+'/360_discounted_payments',present_value(float(row['payment_if_financeable_krw']),float(row['rate_used'])),row['required_loan_krw'])
    if name.startswith('A_'):
        check(name+'/DSR_independent',row['limits_krw']['DSR'],present_value(100000000*.4/12,.07))

for profile in data['affordability_A']:
    for label in ['bank_assumptions_max','mortgage_budget_max']:
        row=profile[label]
        check(profile['profile_id']+'/'+str(profile['deduction_krw'])+'/'+label+'/funding_identity',
              250000000-30000000-float(row['transaction_cost_krw'])+float(row['required_loan_krw']),row['max_price_krw'])
        check(profile['profile_id']+'/'+str(profile['deduction_krw'])+'/'+label+'/payment',
              present_value(float(row['payment_on_required_loan_krw']),.04),row['required_loan_krw'])

out = {'status':'arithmetic_pass_only_policy_and_script_reviews_still_required',
       'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
       'checks':len(checks),'failed':0,'detail':checks,
       'scope':'Prepared conditional cases only; current official policy evidence is reviewed separately.',
       'at_utc':datetime.now(timezone.utc).isoformat()}
(BASE/'next_case_independent_arithmetic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='detail'}))
