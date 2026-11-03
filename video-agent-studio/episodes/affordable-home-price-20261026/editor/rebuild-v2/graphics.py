"""Three data-driven motion specimens. No draft script or old focus-ring code."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape


def money(raw):
    n = int((Decimal(str(raw)) / 10000).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    whole, rest = divmod(n, 10000)
    return ((f'{whole}억 {rest:,}' if rest else f'{whole}억'), '만원' if rest else '원') if whole else (f'{rest:,}', '만원')


class Drawing:
    def __init__(self):
        self.parts, self.objects, self.stages = [], [], []

    def label(self, ident, text, x, y, w, size=28, color='var(--ink)', weight=600):
        self.objects.append({'id': ident, 'type': 'text', 'bbox': [x, y, w, size * 1.4]})
        return f'<div id="{ident}" data-object="text" class="label" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;color:{color};font-weight:{weight}">{escape(str(text))}</div>'

    def amount(self, ident, label, value, x, y, w=480, size=64, color='var(--blue)', display_number=None):
        number, unit = money(value)
        if display_number is not None:number=display_number
        # Number, unit and conditions are separate DOM nodes; never squeeze a unit into a bar.
        return self.label(ident+'-label', label, x, y, w, 32) + f'<div class="amount" style="left:{x}px;top:{y+49}px;width:{w}px;color:{color}"><span id="{ident}" data-object="text" style="font-size:{size}px">{number}</span><span id="{ident}-unit" data-object="text" class="unit">{unit}</span></div>'

    def bar(self, ident, x, y, w, color):
        self.objects.append({'id': ident, 'type': 'shape', 'bbox': [x, y, w, 48]})
        return f'<div id="{ident}" data-object="shape" class="bar" style="left:{x}px;top:{y}px;width:{w}px;background:{color}"></div>'

    def group(self, ident, content):
        self.parts.append(f'<div id="{ident}" class="semantic">{content}</div>')

    def stage(self, key, reveal, dim=(), fills=(), transforms=(), hide=()):
        self.stages.append({'key': key, 'reveal': list(reveal), 'dim': list(dim), 'hide':list(hide), 'fills': list(fills), 'transforms': list(transforms)})

    def result(self, kind, recipe):
        return {'kind': kind, 'html': ''.join(self.parts), 'stages': self.stages,
                'objects': self.objects, 'source_recipe': recipe, 'graphic_bbox': [80, 225, 1740, 585]}


def funding(packet, case_id='A_ordinary_P600000000_C0'):
    c = next(c for c in packet['cases'] if c['case_id'] == case_id)
    common = packet['conditions']['common']
    cash, reserve = map(Decimal, map(str, [common['cash_krw'], common['reserve_krw']]))
    cost, price = Decimal(c['transaction_costs']['total_krw']), Decimal(c['price_krw'])
    equity = price - Decimal(c['required_loan_krw'])
    loan, gap = Decimal(c['loan_ceiling_krw']), Decimal(c['cash_shortfall_krw'])
    assert equity == cash - reserve - cost and equity + loan + gap == price
    d = Drawing(); width = 1060
    reserve_w, cost_w = float(reserve/cash)*width, float(cost/cash)*width
    d.group('cash', d.label('cash-title', '보유현금', 55, 28, 250) + d.label('cash-value', ''.join(money(cash)), 380, 28, 600, 36) + d.bar('cash-fill', 55, 92, width, 'var(--blue)'))
    d.group('reserve', d.bar('reserve-fill', 55+width-reserve_w, 92, reserve_w, 'var(--gold)') + d.label('reserve-label', '예비자금  '+''.join(money(reserve)), 55, 165, 510, 32, 'var(--gold-ink)'))
    d.group('costs', d.bar('cost-fill', 55+width-reserve_w-cost_w, 92, cost_w, 'var(--muted)') + d.label('costs-label', '거래비용  '+''.join(money(cost)), 600, 165, 515, 32))
    d.group('equity', d.amount('equity-value', '집값에 쓸 자기자금', equity, 55, 235, 1000, 56, 'var(--green)'))
    x = 55; equity_w, loan_w = float(equity/price)*width, float(loan/price)*width
    d.group('loan', d.bar('equity-fill', x, 405, equity_w, 'var(--green)') + d.bar('loan-fill', x+equity_w, 405, loan_w, 'var(--blue)') + d.label('loan-label', '은행 한도  '+''.join(money(loan)), 55, 477, 1060, 32, 'var(--blue)'))
    d.group('gap', d.bar('gap-fill', x+equity_w+loan_w, 405, float(gap/price)*width, 'var(--gold)') + d.amount('conclusion', '추가로 필요한 현금', gap, 1210, 255, 470, 64, 'var(--gold-ink)'))
    d.parts.append('<div class="divider"></div>'+d.label('price-condition', '주택가격  '+''.join(money(price)), 1210, 55, 470, 32)+d.label('case-condition', 'A 일반 · LTV 40% · 서울 84㎡', 1210, 115, 470, 28))
    d.stage('cash', ['cash'], fills=['cash-fill'])
    d.stage('reserve', ['reserve'], ['cash-title','cash-value'], fills=['reserve-fill'], transforms=[{'id':'cash-fill','scaleX':float((cash-reserve)/cash)}])
    d.stage('costs', ['costs'], ['reserve-label'], fills=['cost-fill'], transforms=[{'id':'cash-fill','scaleX':float(equity/cash)}])
    d.stage('equity', ['equity'], ['costs-label'], hide=['cash-title','cash-value'])
    d.stage('loan', ['loan'], ['equity'], fills=['equity-fill','loan-fill'], hide=['reserve-label','costs-label'])
    d.stage('gap', ['gap'], ['loan-label'], fills=['gap-fill'])
    return d.result('funding_waterfall', {'file':'research/verified_case_packet.json','case_id':case_id,'values':['conditions/common/cash_krw','conditions/common/reserve_krw','cases/transaction_costs/total_krw','cases/required_loan_krw','cases/loan_ceiling_krw','cases/cash_shortfall_krw'],'derived_equity':'price_krw - required_loan_krw; checked against cash - reserve - costs','policy_as_of':packet['policy_as_of']})


def ltv_dsr(packet, case_id='A_ordinary_P600000000_C0'):
    c = next(c for c in packet['cases'] if c['case_id'] == case_id)
    d = Drawing(); cap = Decimal(c['limits_krw']['regulatory_total']); width = 1060
    collateral, dsr = Decimal(c['limits_krw']['collateral']), Decimal(c['limits_krw']['DSR'])
    d.group('collateral', d.amount('collateral-value', 'LTV：집값을 기준으로', collateral, 55, 25, 1050, 48) + d.bar('ltv-fill', 55, 160, float(collateral/cap)*width, 'var(--blue)'))
    d.group('income', d.label('income-label', '인정소득 연 1억원 × DSR 40% = 연 상환예산 4천만원', 55, 258, 1060, 32))
    d.group('dsr', d.amount('dsr-value', 'DSR：소득과 상환액을 기준으로', dsr, 55, 330, 1050, 48) + d.bar('dsr-fill', 55, 467, float(dsr/cap)*width, 'var(--green)'))
    d.group('limit', d.amount('conclusion', '더 낮은 한도가 적용', c['loan_ceiling_krw'], 1210, 255, 470, 64))
    d.parts.append('<div class="divider"></div>'+d.label('ltv-condition','6억원 × LTV 40%',1210,55,470,32)+d.label('dsr-condition','기존부채 0 · 심사 7% · 30년',1210,115,470,28))
    d.stage('collateral', ['collateral'], fills=['ltv-fill'])
    d.stage('income', ['income'], ['collateral'])
    d.stage('dsr', ['dsr'], ['income'], fills=['dsr-fill'])
    d.stage('limit', ['limit'], ['dsr'])
    return d.result('ltv_dsr', {'file':'research/verified_case_packet.json','case_id':case_id,'values':['limits_krw/collateral','limits_krw/DSR','loan_ceiling_krw','conditions/profiles/A_ordinary'],'scope':'same 6억원 house, same household; annual repayment budget and principal limits distinguished; 7% is screening rate','policy_as_of':packet['policy_as_of']})


def monthly(packet):
    common = packet['conditions']['common']
    a = next(a for a in packet['affordability_A'] if a['profile_id']=='A_first' and a['deduction_krw']==0)
    p = a['mortgage_budget_max']['presentation']['rounded_krw']
    total, ownership, mortgage = [Decimal(str(common[k])) for k in ['housing_savings_budget_monthly_krw','ownership_monthly_plan_krw','mortgage_budget_monthly_krw']]
    saving = total-ownership-mortgage; width=1060
    own_w, save_w, mortgage_w = [float(n/total)*width for n in [ownership,saving,mortgage]]
    d = Drawing()
    d.group('budget', d.amount('budget-value','매달 주거·저축에 쓸 돈',total,55,25,1060,48) + d.bar('budget-fill',55,175,width,'var(--ink)'))
    d.group('ownership', d.bar('ownership-fill',55,175,own_w,'var(--muted)')+d.label('ownership-label','보유·유지비  '+''.join(money(ownership)),55,266,1060,32))
    d.group('saving', d.bar('saving-fill',55+own_w,175,save_w,'var(--green)')+d.label('saving-label','남길 저축  '+''.join(money(saving)),55,337,1060,32,'var(--green)'))
    d.group('mortgage', d.bar('mortgage-fill',55+own_w+save_w,175,mortgage_w,'var(--blue)')+d.amount('mortgage-value','원리금 상환예산',mortgage,55,415,1060,48))
    d.group('price', d.amount('conclusion','이 월예산에 맞춘 집값',p['max_price_krw'],1210,255,470,64))
    d.parts.append('<div class="divider"></div>'+d.label('monthly-condition','A 생애최초 · 약정 4% · 30년',1210,55,470,28)+d.label('monthly-basis','예비자금·거래비용 반영',1210,115,470,28))
    d.stage('budget',['budget'],fills=['budget-fill'])
    d.stage('ownership',['ownership'],['budget-value','budget-value-label'],fills=['ownership-fill'])
    d.stage('saving',['saving'],['ownership-label'],fills=['saving-fill'])
    d.stage('mortgage',['mortgage'],['saving-label'],fills=['mortgage-fill'])
    d.stage('price',['price'],['mortgage'],hide=['ownership-label','saving-label'])
    return d.result('monthly_budget', {'file':'research/verified_case_packet.json','selector':{'profile_id':'A_first','deduction_krw':0},'values':['conditions/common/housing_savings_budget_monthly_krw','conditions/common/ownership_monthly_plan_krw','conditions/common/mortgage_budget_monthly_krw','affordability_A/mortgage_budget_max/presentation/rounded_krw/max_price_krw'],'derived_saving':'housing_savings_budget - ownership - mortgage','policy_as_of':packet['policy_as_of']})


def opening_answers(packet):
    a=next(a for a in packet['affordability_A'] if a['profile_id']=='A_first' and a['deduction_krw']==0)
    bank=Decimal(str(a['bank_assumptions_max']['max_price_krw']))
    budget=Decimal(str(a['mortgage_budget_max']['max_price_krw']))
    d=Drawing()
    for key,label,value,y,color in [('bank','은행 한도까지 사용',bank,45,'var(--muted)'),('budget','월 저축 100만원 유지',budget,305,'var(--blue)')]:
        rounded=(value/Decimal(10000000)).quantize(Decimal('1'),rounding=ROUND_HALF_UP)*10000000
        approx='약 6억 8천' if key=='bank' else '약 5억 7천'
        d.group(key,d.amount(key+'-value',label,rounded,55,y,740,72,color,display_number=approx)+d.bar(key+'-fill',900,y+82,float(value/bank)*730,color))
        d.stage(key,[key],fills=[key+'-fill'])
    d.parts.append(d.label('opening-condition','A 생애최초 · 현금 2억5천만원 · 서울 · 조건부 계산',55,540,1600,28))
    return d.result('opening_answers',{'file':'research/verified_case_packet.json','selector':{'profile_id':'A_first','deduction_krw':0},'exact_krw':{'bank':str(bank),'budget':str(budget)},'display_rounding':'nearest 10,000,000 KRW (HALF_UP); approx label required','policy_as_of':packet['policy_as_of']})


def expense_receipt(packet):
    c=next(c for c in packet['cases'] if c['case_id']=='A_ordinary_P600000000_C0')
    t=c['transaction_costs'];d=Drawing()
    rows=[('tax','취득세·교육세',Decimal(t['acquisition_krw'])+Decimal(t['education_krw'])),('broker','중개보수 · 부가세 포함',Decimal(t['with_vat_krw'])),('registration','등기·채권 등 계획예산',Decimal(t['misc_plan_krw']))]
    for i,(key,label,value) in enumerate(rows):
        y=40+i*155
        d.group(key,d.label(key+'-label',label,55,y,720,32)+d.label(key+'-value',''.join(money(value)),830,y,300,40)+d.bar(key+'-fill',55,y+69,float(value/Decimal(t['total_krw']))*1060,'var(--blue)' if i==0 else 'var(--green)' if i==1 else 'var(--muted)'))
        d.stage(key,[key],fills=[key+'-fill'])
    d.group('total',d.amount('conclusion','거래비용 합계',t['total_krw'],1210,255,470,72))
    d.parts.append('<div class="divider"></div>'+d.label('receipt-condition','6억원 · 무주택 한 채 · 84㎡',1210,55,470,28)+d.label('receipt-tax-basis','중과·감면 전',1210,115,470,28))
    d.stage('total',['total'])
    return d.result('expense_receipt',{'file':'research/verified_case_packet.json','case_id':c['case_id'],'values':'transaction_costs; tax+education, brokerage with VAT, misc plan separately','policy_as_of':packet['policy_as_of']})


def policy_comparison(packet):
    d=Drawing();profiles=['B_didim','B_bogeum','B_newborn'];labels=['디딤돌 신혼','보금자리론 생애최초','신생아 특례']
    for i,(profile,label) in enumerate(zip(profiles,labels)):
        c=next(c for c in packet['cases'] if c['profile_id']==profile and Decimal(c['price_krw'])==600000000 and Decimal(c['deduction_krw'])==0)
        key='product'+str(i);x=55+i*565;value=Decimal(c['loan_ceiling_krw']);h=float(value/Decimal(420000000))*200
        body=d.label(key+'-name',label,x,30,530,32)+d.amount(key+'-value','사례의 대출 한도',value,x,110,530,64,['var(--blue)','var(--green)','var(--gold-ink)'][i])
        d.objects.append({'id':key+'-fill','type':'shape','bbox':[x,455-h,450,h]})
        body+=f'<div id="{key}-fill" data-object="shape" class="bar vertical" style="left:{x}px;top:{455-h}px;width:450px;height:{h}px;background:{["var(--blue)","var(--green)","var(--gold)"][i]};transform-origin:left bottom"></div>'
        body+=d.label(key+'-gap','추가 현금  '+''.join(money(c['cash_shortfall_krw'])),x,490,530,28)
        d.group(key,body);d.stage(key,[key],fills=[key+'-fill'])
    return d.result('policy_comparison',{'file':'research/verified_case_packet.json','profiles':profiles,'price_krw':600000000,'deduction_krw':0,'values':['loan_ceiling_krw','cash_shortfall_krw'],'scope':'B same house/income/assets. Product ceiling alone is not promised approval.','policy_as_of':packet['policy_as_of']})


def rate_sensitivity(packet):
    a=next(a for a in packet['affordability_A'] if a['profile_id']=='A_first' and a['deduction_krw']==0)
    p=a['mortgage_budget_max']['presentation']['rounded_krw'];d=Drawing();total=Decimal(str(packet['conditions']['common']['housing_savings_budget_monthly_krw']))
    for i,(key,label,payment,saving,color) in enumerate([('base','약정 4%',p['payment_on_required_loan_krw'],p['remaining_savings_krw'],'var(--blue)'),('shock','금리 6%',p['payment_shock_same_original_360months_krw'],p['remaining_savings_shock_krw'],'var(--gold)')]):
        y=40+i*260;pw=float(Decimal(payment)/total)*1030;sw=float(Decimal(saving)/total)*1030
        body=d.label(key+'-rate',label,55,y,350,36)+d.label(key+'-pay','월 상환  '+''.join(money(payment)),420,y,700,32)
        body+=d.bar(key+'-pay-fill',55,y+84,pw,color)+d.bar(key+'-saving-fill',55+1030-sw,y+84,sw,'var(--green)')
        body+=d.label(key+'-saving','남는 저축  '+''.join(money(saving)),55,y+165,1060,32)
        d.group(key,body);d.stage(key,[key],fills=[key+'-pay-fill',key+'-saving-fill'])
    d.group('delta',d.amount('conclusion','금리 상승 후 남는 저축',p['remaining_savings_shock_krw'],1210,255,470,72,'var(--gold-ink)'))
    d.parts.append('<div class="divider"></div>'+d.label('shock-condition','같은 원금 · 최초 30년 조건',1210,55,470,28)+d.label('shock-cost','월 유지비 30만원 반영',1210,115,470,28))
    d.stage('delta',['delta'],['base'])
    return d.result('rate_sensitivity',{'file':'research/verified_case_packet.json','selector':{'profile_id':'A_first','deduction_krw':0,'branch':'mortgage_budget_max'},'values':['payment_on_required_loan_krw','payment_shock_same_original_360months_krw','remaining_savings_krw','remaining_savings_shock_krw'],'scope':'actual repayment sensitivity 4 to 6 percent; original principal/360 months, not stress DSR','policy_as_of':packet['policy_as_of']})


def newborn_timeline(addendum):
    c=addendum['case'];d=Drawing()
    # A compressed editorial timeline; labels explicitly carry 5/25 years.
    d.parts.append(d.label('time-origin','대출 실행',55,30,400,32)+d.label('time-reset','5년 · 60회 상환',650,30,600,32)+d.label('time-end','30년',1520,30,170,32))
    d.group('initial',d.bar('initial-fill',55,120,650,'var(--blue)')+d.label('initial-rate','기본 특례금리 2.90%',55,220,780,48)+d.label('initial-monthly','월 상환  '+''.join(money(c['initial_monthly_krw'])),55,310,780,36))
    d.group('balance',d.amount('balance-value','60회 뒤 남은 원금',c['balance_after60_krw'],55,410,1000,56))
    d.group('reset',d.bar('reset-fill',705,120,980,'var(--gold)')+d.label('reset-rate','현행 금리표 3.65%',920,220,770,48,'var(--gold-ink)')+d.amount('conclusion','남은 25년의 월 상환',c['reset_monthly_krw'],920,340,770,72,'var(--gold-ink)'))
    d.parts.append(d.label('reset-condition','우대 전 · 추가 출산/중도상환 0 · 현행 금리표를 적용한 예시',55,545,1630,28))
    d.stage('initial',['initial'],fills=['initial-fill'])
    d.stage('balance',['balance'])
    d.stage('reset',['reset'],['initial'],fills=['reset-fill'])
    return d.result('newborn_rate_timeline',{'file':'research/newborn_policy_addendum_v2.json','case_id':c['case_id'],'values':['initial_annual_rate','initial_monthly_krw','balance_after60_krw','current_schedule_reset_rate','remaining_months','reset_monthly_krw'],'timeline_geometry':'two labelled phases; horizontal extent is editorial, durations explicitly 5/25 years','scope':c['scope'],'policy_as_of':addendum['as_of_kst']})


def price_cases(packet):
    d=Drawing();maximum=Decimal(1200000000)
    for i,price in enumerate([600000000,900000000,1200000000]):
        c=next(c for c in packet['cases'] if c['profile_id']=='A_ordinary' and Decimal(c['price_krw'])==price and Decimal(c['deduction_krw'])==0)
        key='price'+str(i);y=40+i*175;equity=Decimal(price)-Decimal(c['required_loan_krw']);loan=Decimal(c['loan_ceiling_krw']);gap=Decimal(c['cash_shortfall_krw'])
        body=d.label(key+'-label',''.join(money(price))+' 주택',55,y,400,32)+d.label(key+'-shortfall','추가 현금  '+''.join(money(gap)),970,y,680,32,'var(--gold-ink)')
        x=55
        for suffix,value,color in [('equity',equity,'var(--green)'),('loan',loan,'var(--blue)'),('gap',gap,'var(--gold)')]:
            w=float(value/maximum)*1610;body+=d.bar(key+'-'+suffix,x,y+70,w,color);x+=w
        d.group(key,body);d.stage(key,[key],fills=[key+'-'+k for k in ['equity','loan','gap']])
    d.parts.append(d.label('price-legend','초록：자기자금     파랑：은행 한도     골드：추가로 필요한 현금',55,545,1630,28))
    return d.result('price_case_comparison',{'file':'research/verified_case_packet.json','profile_id':'A_ordinary','prices_krw':[600000000,900000000,1200000000],'deduction_krw':0,'values':['required_loan_krw','loan_ceiling_krw','cash_shortfall_krw'],'legend':{'green':'equity','blue':'bank ceiling','gold':'additional cash'},'policy_as_of':packet['policy_as_of']})


def limit_competition(packet):
    c=next(c for c in packet['cases'] if c['case_id']=='A_ordinary_P600000000_C0')
    values=[('ltv','담보 한도',Decimal(c['limits_krw']['collateral']),'var(--blue)'),('dsr','DSR 한도',Decimal(c['limits_krw']['DSR']),'var(--green)'),('dti','DTI 한도',Decimal(c['limits_krw']['DTI']),'var(--muted)')]
    maximum=max(v[2] for v in values);d=Drawing()
    for i,(key,label,value,color) in enumerate(values):
        y=35+i*170
        body=d.label(key+'-label',label,55,y,380,32)+d.label(key+'-value',''.join(money(value)),540,y,590,40)+d.bar(key+'-fill',55,y+76,float(value/maximum)*1060,color)
        d.group(key,body);d.stage(key,[key],fills=[key+'-fill'])
    d.parts.append('<div class="divider"></div>'+d.label('competition-condition','A 일반 · 6억원 · 기존부채 0',1210,55,470,28))
    d.group('binding',d.amount('conclusion','가장 낮은 한도가 적용',c['loan_ceiling_krw'],1210,255,470,64))
    d.stage('binding',['binding'],['dsr','dti'])
    return d.result('limit_competition',{'file':'research/verified_case_packet.json','case_id':c['case_id'],'values':['limits_krw/collateral','limits_krw/DSR','limits_krw/DTI','loan_ceiling_krw'],'axis':'loan principal KRW; all three use the same scale','policy_as_of':packet['policy_as_of']})


BUILDERS={'funding_waterfall':funding,'ltv_dsr':ltv_dsr,'monthly_budget':monthly,'opening_answers':opening_answers,'expense_receipt':expense_receipt,'policy_comparison':policy_comparison,'rate_sensitivity':rate_sensitivity,'price_case_comparison':price_cases,'limit_competition':limit_competition}


def make(kind, packet, newborn=None):
    if kind=='newborn_rate_timeline':
        if newborn is None:raise ValueError('Actual newborn addendum required')
        return newborn_timeline(newborn)
    return BUILDERS[kind](packet)
