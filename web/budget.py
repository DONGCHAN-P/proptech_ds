"""Affordability scenarios in 만원. User assumptions, NOT a bank/policy decision."""
import math

VERSION = 'cashflow-assumptions-v1'


def monthly_payment(principal, rate, years, method):
    months = years * 12
    interest = rate / 1200
    if method == 'principal':
        return principal / months + principal * interest
    return principal / months if interest == 0 else principal * interest / (-math.expm1(-months * math.log1p(interest)))


def calculate(data):
    limits = {'cash': (0, 10000000), 'reserve': (0, 10000000), 'annual_income': (0, 1000000),
              'monthly_income': (0, 100000), 'monthly_expenses': (0, 100000),
              'existing_payment': (0, 100000), 'rate': (0, 30), 'years': (1, 50),
              'ltv': (0, 100), 'dsr': (0, 100), 'stress': (0, 20), 'cost_rate': (0, 30),
              'fixed_cost': (0, 100000), 'payment_share': (0, 100)}
    d = {}
    for name, (low, high) in limits.items():
        try:
            value = float(data[name])
        except (KeyError, ValueError, TypeError):
            raise ValueError(f'Invalid field: {name}') from None
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'Invalid field: {name}')
        d[name] = value
    method = data.get('method', 'annuity')
    if method not in ('annuity', 'principal'):
        raise ValueError('Invalid repayment method')
    capacity = max(0, d['monthly_income'] - d['monthly_expenses'] - d['existing_payment']) * d['payment_share'] / 100
    annual_capacity = max(0, d['annual_income'] * d['dsr'] / 100 - 12 * d['existing_payment']) / 12
    loan_ceiling = min(capacity / monthly_payment(1, d['rate'], d['years'], method),
                       annual_capacity / monthly_payment(1, d['rate'] + d['stress'], d['years'], method))
    cash = max(0, d['cash'] - d['reserve'])
    scenarios = []
    for key, factor in [('conservative', .8), ('base', .9), ('ceiling', 1.)]:
        low, high = 0., 10000000.
        def available(price):
            loan = min(price * d['ltv'] / 100, loan_ceiling * factor)
            costs = price * d['cost_rate'] / 100 + d['fixed_cost']
            return price + costs - loan <= cash
        if not available(0):
            high = 0
        for _ in range(70):
            middle = (low + high) / 2
            if available(middle):
                low = middle
            else:
                high = middle
        price = math.floor(low * 100) / 100
        loan = min(price * d['ltv'] / 100, loan_ceiling * factor)
        costs = price * d['cost_rate'] / 100 + d['fixed_cost'] if price else 0
        payment = monthly_payment(loan, d['rate'], d['years'], method)
        months = d['years'] * 12
        interest = (payment * months - loan if method == 'annuity'
                    else loan * d['rate'] / 1200 * (months + 1) / 2)
        scenarios.append(dict(key=key, price=round(price, 2), loan=round(loan, 2), costs=round(costs, 2),
                              monthly_payment=round(payment, 2), total_interest=round(interest, 2),
                              reserve=round(d['reserve'], 2), remaining_cash=round(d['cash'] - price - costs + loan, 2)))
    notices = ['입력한 LTV·DSR·스트레스·부대비용 가정의 시나리오이며 은행 심사 한도가 아닙니다.',
               '세금·감면·정책대출·기존 부채별 DSR 산정은 자동 판정하지 않습니다.',
               '원금균등상환은 첫 달 상환액으로 부담을 제한합니다.']
    if d['reserve'] > d['cash']:
        notices.insert(0, '희망 비상금이 보유 현금보다 큽니다. 현재 입력으로는 매수에 쓸 현금이 없습니다.')
    return dict(version=VERSION, policy_mode='user_assumptions', unit='만원', scenarios=scenarios,
                monthly_capacity=round(capacity, 2), assumptions=d, method=method,
                limitations=notices)
