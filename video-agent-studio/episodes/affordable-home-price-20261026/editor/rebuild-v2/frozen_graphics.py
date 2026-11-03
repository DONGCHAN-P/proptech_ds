"""Authored recipes for the 34 frozen scenes. Writer graphic=data_chart is NOT a recipe.

Each recipe owns exactly one semantic stage per writer beat. No estimated timings.
All monetary inputs come from the existing case packet/addendum; literal policy
boundaries are traced to the frozen script source IDs, not invented as examples.
"""
from decimal import Decimal
from graphics import Drawing, money, expense_receipt

D=Decimal
BLUE='var(--blue)';GREEN='var(--green)';GOLD='var(--gold)';INK='var(--ink)';MUTED='var(--muted)'


def case(packet,profile='A_first',price=600000000,deduction=0):
    return next(c for c in packet['cases'] if c['profile_id']==profile and D(c['price_krw'])==price and D(c['deduction_krw'])==deduction)


def month(value):return f'{D(str(value))/10000:,.1f}'
def won(value):return ''.join(money(value))


class Art(Drawing):
    def __init__(self,scene,kind):
        super().__init__();self.scene=scene;self.kind=kind;self.notes=[];self.required_assets=[]

    def add(self,index,body,dim=(),hide=(),fills=(),moves=()):
        key='beat'+str(index);self.group(key,body);self.stage(key,[key],dim,fills,moves,hide)

    def summary(self,index,label,value,color=BLUE,decimal_month=False):
        return self.amount('conclusion-'+str(index),label,value,1210,255,470,64,color,display_number=month(value) if decimal_month else None)

    def condition(self,text):
        # Short applied conditions belong to the scene, not a general disclaimer.
        self.parts.append(self.label('applied-condition',text,55,543,1630,28,MUTED,400))

    def finish(self,recipe):
        if len(self.stages)!=len(self.scene['beats']):raise ValueError('Authored stage count differs: '+self.scene['id'])
        result=self.result(self.kind,recipe)
        result.update(required_assets=self.required_assets,design_notes=self.notes)
        return result


def bar_row(a,key,label,value,y,maximum,color=BLUE,x=55,width=1060,show_value=True,decimal_monthly=False):
    body=a.label(key+'-label',label,x,y,640,32)
    if show_value:body+=a.label(key+'-value',month(value)+'만원' if decimal_monthly else won(value),x+660,y,400,40,color)
    body+=a.bar(key+'-fill',x,y+70,float(D(str(value))/D(str(maximum)))*width,color)
    return body


def flow(a,index,label,value=None,position=None):
    """Short factual nodes connected by arrows; no paragraph cards."""
    x,y=position or (55+index*390,120)
    body=a.label('node-'+str(index),label,x,y,370,32)
    if value is not None:body+=a.amount('node-value-'+str(index),'',value,x,y+55,370,64)
    if index and x>100:body+=a.label('arrow-'+str(index),'→',x-60,y+65,50,48,MUTED)
    return body


def make_scene(scene,packet,newborn):
    sid=scene['id'];a=Art(scene,'unassigned');common=packet['conditions']['common']
    c6=case(packet);ordinary=case(packet,'A_ordinary');c9=case(packet,price=900000000);c12=case(packet,price=1200000000)
    aff=next(v for v in packet['affordability_A'] if v['profile_id']=='A_first' and v['deduction_krw']==0)
    bank=aff['bank_assumptions_max'];budget=aff['mortgage_budget_max'];nb=newborn['case']
    recipe={'frozen_scene_id':sid,'source_ids':scene['source_ids'],'file':'research/verified_case_packet.json','values':[],'policy_as_of':packet['policy_as_of'],'numerical_display':'exact case ledger unless a rounded display is explicitly recorded'}
    if sid=='R001':
        a.kind='two_price_before_after'
        a.add(0,flow(a,0,'보유현금',common['cash_krw'],(55,60))+a.bar('cash-source',55,300,600,BLUE),fills=['cash-source'])
        for i,(label,branch,rounded,y) in enumerate([('현금·은행 기준',bank,'약 6억 8천',65),('월 상환 목표 기준',budget,'약 5억 7천',315)],1):
            value=branch['max_price_krw'];body=a.amount('answer'+str(i),label,value,800,y,840,72,BLUE if i==1 else GREEN,display_number=rounded)
            a.add(i,body)
        a.add(3,flow(a,3,'6억원 주택',600000000,(800,165)),hide=['beat1','beat2'])
        a.condition('A · 서울 · 생애최초 · 보증 승인으로 공제 보완 · 4% · 30년')
        recipe.update(selector='affordability_A/A_first/C0',exact_krw={'bank':bank['max_price_krw'],'monthly':budget['max_price_krw']},rounded_display={'bank':'약 6억8천만원','monthly':'약 5억7천만원'})
    elif sid=='R002':
        a.kind='household_input_flow'
        for i,(label,value) in enumerate([('현금 2억5천 · 월 예산 300만',None),('적용 기준일 2026.10.26',None),('A 소득 1억원 · 기존부채 0',None),('서울 · 전용84㎡',None)]):
            a.add(i,flow(a,i,label,value,(55+i%2*850,65+i//2*250)))
        a.condition('은행 인정소득=가구소득 · 매매가=담보평가액 · 임차인/선순위 권리 0')
    elif sid=='R003':
        a.kind='reserve_transfer_waterfall'
        a.add(0,a.label('cash-context','보유현금 2억5천만원',55,25,1000,32)+a.bar('cash-part',55,130,880,BLUE)+a.bar('reserve-part',935,130,120,GOLD)+a.amount('reserve-value','분리한 예비자금',common['reserve_krw'],1210,80,470,64,'var(--gold-ink)'),fills=['cash-part','reserve-part'])
        a.add(1,a.amount('available','구입자금',D(str(common['cash_krw']))-D(str(common['reserve_krw'])),55,245,1060,72))
        a.add(2,a.label('contract-calendar','계약금 지급 → 잔금 지급',55,440,1060,36)+a.bar('payment-time',55,500,1060,MUTED),fills=['payment-time'])
    elif sid=='R004':
        g=expense_receipt(packet);g['kind']='transaction_receipt_sum';g['source_recipe'].update(source_ids=scene['source_ids']);return g
    elif sid=='R005':
        a.kind='equity_needed_loan_ratio';equity=D(c6['price_krw'])-D(c6['required_loan_krw']);ew=float(equity/600000000)*1060
        a.add(0,a.amount('equity','집값에 넣을 자기자금',equity,55,40,1060,64,GREEN))
        a.add(1,a.label('house-value','집값 6억원',55,235,1060,32)+a.bar('equity-fill',55,320,ew,GREEN),fills=['equity-fill'])
        a.add(2,a.bar('required-fill',55+ew,320,1060-ew,BLUE)+a.summary(2,'잔금에 필요한 대출',c6['required_loan_krw']),fills=['required-fill'])
        a.condition('필요대출과 은행 지급 한도는 별도 확인')
    elif sid=='R006':
        a.kind='ltv_40_70_comparison';required=D(c6['required_loan_krw']);scale=1060/600000000
        a.add(0,bar_row(a,'ordinary','일반 LTV 40%',ordinary['limits_krw']['collateral'],35,600000000),fills=['ordinary-fill'])
        a.add(1,a.summary(1,'추가로 필요한 현금',ordinary['cash_shortfall_krw'],'var(--gold-ink)'))
        a.add(2,bar_row(a,'first','생애최초 LTV 70%',c6['limits_krw']['collateral'],315,600000000,BLUE)+a.summary(2,'생애최초 담보 한도',c6['limits_krw']['collateral']),dim=['beat0'],hide=['beat1'],fills=['first-fill'])
        a.condition('담보평가액=매매가(V=P) · 공제 전 담보 한도')
    elif sid=='R007':
        a.kind='annual_income_to_repayment'
        a.add(0,bar_row(a,'income','인정소득 · 연간',100000000,40,100000000),fills=['income-fill'])
        a.add(1,bar_row(a,'repayment','원리금 심사예산 · 연간',40000000,255,100000000,GREEN)+a.summary(1,'연 상환 심사예산',40000000),fills=['repayment-fill'])
        a.add(2,a.label('prior-debt','신용대출 원리금 → 같은 연 상환예산에 포함',55,455,1070,32),dim=['beat1'])
        recipe['direction_only']='existing debt effect; no invented debt amount/ratio'
    elif sid=='R008':
        a.kind='screening_payment_rate_branch'
        a.add(0,flow(a,0,'실제 납부 · 4% · 30년',None,(55,55)))
        a.add(1,flow(a,1,'심사 경로 · 4% + 3%p = 7%',None,(55,280)))
        a.add(2,a.summary(2,'DSR 원금 한도',c6['limits_krw']['DSR']),dim=['beat0'])
        a.add(3,a.label('payment-arrow','→ 실제 월 납부 계산에는 계약금리 4%',55,440,1070,32,BLUE),dim=['beat1','beat2'])
        a.condition('수도권 변동형 · 기존부채 0 · 360개월')
    elif sid=='R009':
        a.kind='minimum_limit_competition';vals=[D(c6['limits_krw'][k]) for k in ['collateral','DSR','DTI']];maximum=max(vals)
        a.add(0,a.label('dti-choice','일반 DTI 40% → A 생애최초 DTI 60%',55,15,1650,32))
        body='';fills=[]
        for i,(label,v,color) in enumerate(zip(['담보','DSR','DTI'],vals,[BLUE,GREEN,MUTED])):
            key='limit'+str(i);body+=bar_row(a,key,label,v,95+i*140,maximum,color,show_value=i!=2);fills.append(key+'-fill')
        a.add(1,body,fills=fills)
        a.add(2,a.summary(2,'적용되는 가장 작은 한도',c6['loan_ceiling_krw']))
        recipe.update(case_id=c6['case_id'],values=['limits_krw/collateral','limits_krw/DSR','limits_krw/DTI'],DTI_numeric_label=False)
    elif sid=='R010':
        a.kind='deduction_on_off';deducted=case(packet,deduction=55000000)
        a.add(0,bar_row(a,'before','공제 전 담보 4억2천만원',420000000,35,420000000)+a.amount('deduction','남는 공제액',55000000,1210,55,470,64,'var(--gold-ink)'),fills=['before-fill'])
        a.add(1,a.amount('after','공제 뒤 담보 한도',deducted['loan_ceiling_krw'],55,260,1060,64),moves=[{'id':'before-fill','scaleX':365000000/420000000}],dim=['beat0'])
        a.add(2,a.summary(2,'추가로 필요한 현금',deducted['cash_shortfall_krw'],'var(--gold-ink)'))
        a.condition('은행 담보대출 공제 · 서울5,500만원 · 기존 임차인/선순위 권리0')
    elif sid=='R011':
        a.kind='purchase_to_monthly_target';monthly=D(c6['payment_if_financeable_krw'])
        a.add(0,bar_row(a,'purchase','6억원 구입자금 · 필요대출',c6['required_loan_krw'],30,600000000),fills=['purchase-fill'])
        a.add(1,bar_row(a,'actual-pay','실제 월 상환',monthly,225,2200000,decimal_monthly=True)+a.summary(1,'월 상환액',monthly,decimal_month=True),hide=['beat0'],fills=['actual-pay-fill'])
        a.add(2,a.label('monthly-parts','월300만원 − 소유비30만원 − 저축100만원',55,45,1060,32))
        a.add(3,bar_row(a,'target','월 상환 목표',1700000,365,2200000,GREEN)+a.summary(3,'상환 목표',1700000),hide=['conclusion-1','conclusion-1-label','conclusion-1-unit'],fills=['target-fill'])
        a.condition('소유비 월30만원은 계획값 · 계약금리4% · 30년')
    elif sid=='R030':
        a.kind='monthly_budget_parts_to_price'
        total=D(str(common['housing_savings_budget_monthly_krw']))
        ownership=D(str(common['ownership_monthly_plan_krw']))
        mortgage=D(str(common['mortgage_budget_monthly_krw']))
        saving=total-ownership-mortgage
        assert (total,ownership,saving,mortgage)==(3000000,300000,1000000,1700000)
        ow,sw,mw=[float(v/total)*1060 for v in [ownership,saving,mortgage]]
        body=a.label('monthly-total','매달 주거·저축 예산 300만원',55,45,1060,40)
        body+=a.bar('total-background',55,200,1060,INK)
        body+=a.bar('ownership-part',55,200,ow,MUTED)+a.bar('saving-part',55+ow,200,sw,GREEN)
        body+=a.label('ownership-legend','소유비 30만원',55,300,1060,32,MUTED)
        body+=a.label('saving-legend','남길 저축 100만원',55,370,1060,32,GREEN)
        a.add(0,body,fills=['total-background','ownership-part','saving-part'])
        body=a.bar('mortgage-part',55+ow+sw,200,mw,BLUE)
        body+=a.label('mortgage-legend','원리금 상환 목표 170만원',55,440,1060,32,BLUE)
        body+=a.summary(1,'원리금 상환 목표',mortgage,BLUE)
        a.add(1,body,fills=['mortgage-part'])
        a.add(2,a.summary(2,'이 월 예산에 맞춘 집값',budget['max_price_krw'],GREEN),hide=['conclusion-1','conclusion-1-label','conclusion-1-unit'])
        a.condition('A · 생애최초 · 공제 보완 · 약정4% · 30년 · 예비자금·거래비용 반영')
        recipe.update(selector='affordability_A/A_first/C0/mortgage_budget_max',parts_krw={'total':str(total),'ownership':str(ownership),'saving':str(saving),'mortgage':str(mortgage)},precise_result_narration_once=True)
    elif sid=='R029':
        branch=bank if sid=='R029' else budget;a.kind='bank_price_reverse' if sid=='R029' else 'monthly_price_reverse'
        if sid=='R029':
            entries=[('현금·은행 기준 집값',branch['max_price_krw']),('이 집값의 거래비용',branch['transaction_cost_krw']),('계약금리4%의 월 상환',branch['payment_on_required_loan_krw'])]
        else:entries=[('소유비30만원 + 남길 저축100만원',None),('원리금 상환 목표',1700000),('월 상환 목표 기준 집값',branch['max_price_krw'])]
        for i,(label,value) in enumerate(entries):
            body=flow(a,i,label,None,(55,55+i*145))
            if value is not None:body+=a.summary(i,label,value,GREEN if sid=='R030' else BLUE)
            a.add(i,body,hide=['beat'+str(i-1)] if i else [])
        a.condition('A · 생애최초 · 공제 보완 · 4% · 30년 · 감면 전 · 만원 단위 탐색')
        recipe.update(selector='affordability_A/A_first/C0/'+('bank_assumptions_max' if sid=='R029' else 'mortgage_budget_max'),precise_result_narration_once=True)
    elif sid=='R031':
        a.kind='savings_remaining_comparison'
        for i,(name,branch) in enumerate([('현금·은행 기준',bank),('월 상환 목표 기준',budget)]):
            y=30+i*235;pay=D(branch['payment_on_required_loan_krw']);saving=D(branch['remaining_savings_krw']);pw=float(pay/3000000)*1060;sw=float(saving/3000000)*1060
            body=a.label('budget-name'+str(i),name,55,y,1060,32)+a.bar('pay'+str(i),55,y+75,pw,BLUE)+a.bar('save'+str(i),55+1060-sw,y+75,sw,GREEN)+a.label('saving'+str(i),'남길 저축  '+won(saving),55,y+150,1060,36,GREEN)
            a.add(i,body,fills=['pay'+str(i),'save'+str(i)])
        a.add(2,a.summary(2,'목표로 남긴 저축',1000000),dim=['beat0'])
        a.condition('월300만원 · 소유비30만원 · 계약금리4% · 30년')
    elif sid=='R032':
        a.kind='A_original_principal_rate_shock';recipe.update(override_required=True,household='A',original_months=360,forbidden=['B newborn balance','60 repayments','remaining 300 months'])
        a.add(0,a.label('rate-path','A의 두 최초원금 · 각각 신규360개월 · 금리4% → 6%',55,25,1620,32))
        a.add(1,bar_row(a,'bank-shock','현금·은행 기준 · 월 상환 약285만원',bank['payment_shock_same_original_360months_krw'],135,3300000,GOLD),fills=['bank-shock-fill'])
        shortage=-D(bank['remaining_savings_shock_krw'])
        a.add(2,a.summary(2,'월 예산 대비 부족',shortage,'var(--gold-ink)'))
        a.add(3,bar_row(a,'budget-shock','월 상환 목표 기준 · 상환 약213만원',budget['payment_shock_same_original_360months_krw'],355,3300000,BLUE)+a.summary(3,'월예산 기준 남는 저축',budget['remaining_savings_shock_krw'],GREEN),dim=['beat1'],hide=['conclusion-2','conclusion-2-label','conclusion-2-unit'],fills=['budget-shock-fill'])
        a.condition('같은 최초 대출원금 · 금리4%/6% · 각각360개월')
    elif sid=='R033':
        a.kind='budget_adjustment_directions'
        a.add(0,a.label('current-monthly','6억원 집 · 월186.5만원  ↔  목표170만원',55,40,1650,40)+a.bar('loan-direction',55,165,1060,BLUE),fills=['loan-direction'])
        a.add(1,flow(a,1,'추가 현금 ↑ → 대출 ↓',None,(55,285)),moves=[{'id':'loan-direction','scaleX':.82}])
        a.add(2,flow(a,2,'저축 목표 조정 ↔ 구입가격 조정',None,(650,420)))
        recipe['direction_only']='graph change shows direction only; no invented adjustment KRW'
    elif sid=='R012':
        a.kind='continuous_acquisition_tax_curve'
        path='<svg width="1060" height="220" viewBox="0 0 1060 220"><path d="M40 180 H280 L520 100 L760 20 H1020" fill="none" stroke="#286cda" stroke-width="6"/></svg>'
        a.add(0,a.label('curve-label','취득세율 · 6억원1% → 9억원3% → 이후3%',55,20,1650,32)+'<div id="tax-curve" class="bar" data-object="shape" style="left:55px;top:85px;width:1060px;height:220px;background:transparent">'+path+'</div>',fills=['tax-curve'])
        taxes=[D(c['transaction_costs']['acquisition_krw'])+D(c['transaction_costs']['education_krw']) for c in [c6,c9,c12]]
        a.add(1,bar_row(a,'tax9','9억원 세금 · 6억원은660만원',taxes[1],335,taxes[2],GREEN),fills=['tax9-fill'])
        a.add(2,a.summary(2,'12억원 취득세·교육세',taxes[2]))
        a.condition('무주택 한 채 · 84㎡ 일반 아파트 · 중과/감면 전 · 농어촌특별세0')
        recipe['curve_points']=[{'price_krw':600000000,'rate':.01},{'price_krw':900000000,'rate':.03},{'price_krw':1200000000,'rate':.03}]
    elif sid=='R013':
        a.kind='brokerage_steps_to_total_receipt'
        a.add(0,a.label('broker-step','중개보수 상한 요율   6억원0.4% → 9억원0.5% → 12억원0.6%',55,20,1650,32)+a.bar('step1',55,110,300,BLUE)+a.bar('step2',355,85,300,GREEN)+a.bar('step3',655,60,300,GOLD),fills=['step1','step2','step3'])
        a.add(1,a.label('broker-including-vat','부가세 포함   264만원 → 495만원 → 792만원',55,220,1650,36))
        a.add(2,a.label('other-plan','각 가격대에 기타 계획예산150만원 추가',55,345,1650,32))
        a.add(3,a.summary(3,'12억원 집의 총 거래비용',c12['transaction_costs']['total_krw'])+a.label('all-total','총비용   1,074만원 / 3,615만원 / 4,902만원',55,465,1060,32))
        a.condition('일반과세 중개사 부가세10% 포함 · 협의 가능한 상한 예산')
    elif sid=='R014':
        a.kind='conditional_relief_amount_callouts'
        a.add(0,a.amount('first-relief','생애최초 · 조건 해당 시 최대',2000000,55,50,740,72))
        a.add(1,a.amount('birth-relief','출산·양육 · 조건 해당 시 최대',5000000,900,50,740,72,GREEN))
        a.add(2,a.label('relief-selection','적격 감면 중 큰 감면 하나 선택',55,355,1620,40)+a.label('relief-arrow','200만원   ← 선택 →   500만원',55,455,1620,40),dim=['beat0','beat1'])
        recipe['not_calculated']='no net tax after relief; r2 uses two maximum-amount callouts and one selection, no source excerpt required'
    elif sid in ['R015','R016']:
        a.kind='needed_DSR_cash_gap';c=c9 if sid=='R015' else c12;price=D(c['price_krw']);eq=price-D(c['required_loan_krw']);loan=D(c['loan_ceiling_krw']);gap=D(c['cash_shortfall_krw']);scale=1060/float(price)
        a.add(0,a.label('house-context',won(price)+' 주택 · 필요대출 '+won(c['required_loan_krw']),55,35,1660,32)+a.bar('equity-fill',55,160,float(eq)*scale,GREEN),fills=['equity-fill'])
        a.add(1,a.bar('bank-fill',55+float(eq)*scale,160,float(loan)*scale,BLUE)+a.label('DSR-stop','DSR 한도  '+won(loan),55,285,1060,36),fills=['bank-fill'])
        a.add(2,a.bar('gap-fill',55+float(eq+loan)*scale,160,float(gap)*scale,GOLD)+a.summary(2,'추가로 필요한 현금',gap,'var(--gold-ink)'),fills=['gap-fill'])
        a.condition('A · 생애최초 · 공제 보완 · 추가 현금은 보유2억5천만원 대비')
        recipe['case_id']=c['case_id']
    elif sid=='R017':
        a.kind='regulatory_total_15_25_step'
        for i,(label,value,x,w) in enumerate([('시가15억원 이하',600000000,55,470),('15억원 초과~25억원 이하',400000000,595,470*4/6),('25억원 초과',200000000,1135,470*2/6)]):
            body=a.label('step-label'+str(i),label,x,45,550,28)+a.amount('cap'+str(i),'대출 총액상한',value,x,155,550,64)+a.bar('cap-fill'+str(i),x,350+i*45,w,[BLUE,GREEN,GOLD][i])
            a.add(i,body,fills=['cap-fill'+str(i)])
        a.add(3,a.label('first-band-prices','6억원 · 9억원 · 12억원 주택 → 모두 첫 구간',55,475,1640,36))
        a.condition('일반 구입 주담대 · 수도권/규제지역')
        recipe.update(file='director/rebuild-v2/frozen-script-v3/scenes_v3.json',policy_literal_source_ids=scene['source_ids'],boundary_price_krw=[1500000000,2500000000],caps_krw=[600000000,400000000,200000000])
    elif sid=='R018':
        a.kind='A_to_B_profile_handoff'
        a.add(0,flow(a,0,'A → B · 같은 보유현금',common['cash_krw'],(55,45)))
        a.add(1,a.label('B-profile','B · 합산소득8천만원 · 신혼 · 생애최초 · 최근 출산',55,265,1640,36))
        a.add(2,a.summary(2,'같은 6억원 집의 필요대출',c6['required_loan_krw']))
        a.condition('B · 합산소득8천만원 · 신혼 · 생애최초 · 최근 출산')
    elif sid in ['R019','R020']:
        a.kind='policy_product_capacity';profile='B_didim' if sid=='R019' else 'B_bogeum';c=case(packet,profile);cap=D(c['loan_ceiling_krw']);required=D(c['required_loan_krw'])
        if sid=='R019':
            a.add(0,a.label('newlywed-conditions','B 합산8천만원 → 신혼 소득기준8,500만원 이하',55,25,1640,32))
            a.add(1,bar_row(a,'product','디딤돌 상품 한도',cap,175,420000000),fills=['product-fill'])
            a.add(2,a.summary(2,'추가로 필요한 현금',c['cash_shortfall_krw'],'var(--gold-ink)'))
        else:
            a.add(0,bar_row(a,'product','생애최초 보금자리론 한도',cap,35,420000000),fills=['product-fill'])
            a.add(1,a.label('valuations','시세 → 감정가 → 실제 매매가 : 6억원 기준 확인',55,270,1640,32))
            a.add(2,bar_row(a,'needed','실제로 필요한 대출',required,380,420000000,GREEN),fills=['needed-fill'])
        a.condition('B · 6억원 · 보금자리론 자체 공제 기준 · 임대차 없는 아파트' if sid=='R020' else 'B · 6억원 · 상품 한도 · 보증/담보 심사 조건')
        recipe['case_id']=c['case_id']
    elif sid=='R021':
        a.kind='three_product_bars_against_need';required=D(c6['required_loan_krw']);line_y=515-float(required/420000000)*200
        a.add(0,a.label('need-label','B의 필요대출 3억9,074만원',55,15,1640,32)+f'<div id="need-line" data-object="shape" style="position:absolute;left:55px;top:{line_y}px;width:1630px;height:3px;background:#173348"></div>')
        for i,(label,profile,color) in enumerate([('디딤돌','B_didim',BLUE),('보금자리론 생애최초','B_bogeum',GREEN),('신생아 특례','B_newborn',GOLD)],1):
            cap=D(str(packet['conditions']['profiles'][profile]['product_cap_krw']));x=55+(i-1)*555;h=float(cap/420000000)*200
            body=a.label('product-name'+str(i),label,x,80,535,32)+a.amount('product-cap'+str(i),'상품상한',cap,x,125,535,64)+f'<div id="product-fill{i}" data-object="shape" class="bar vertical" style="left:{x}px;top:{515-h}px;width:480px;height:{h}px;transform-origin:left bottom;background:{color}"></div>'
            a.add(i,body,dim=['beat'+str(i-1)] if i>1 else [],fills=['product-fill'+str(i)])
        a.condition('B · 같은 필요대출 기준 · 상품별 한도')
        recipe['values']=['conditions/profiles/B_didim/product_cap_krw','conditions/profiles/B_bogeum/product_cap_krw','conditions/profiles/B_newborn/product_cap_krw']
    elif sid=='R022':
        a.kind='move_in_horizontal_timeline'
        a.add(0,a.label('policy-DTI','세 정책상품 · DTI60%',55,25,1630,32))
        a.add(1,a.label('move-in','실행일 → 1개월 안에 전입',55,155,1630,36)+a.bar('one-month',55,230,1630/25,BLUE),fills=['one-month'])
        a.add(2,a.label('residence','전입일을 시작으로 실거주2년',55,300,1630,36)+a.bar('two-years',55,375,1630*24/25,GREEN),fills=['two-years'])
        a.add(3,a.label('bogeum-moving','보금자리론 : 실행일 → 6개월 안 전입·서류',55,455,1630,32)+a.bar('six-months',55,503,1630*6/25,GOLD).replace('style="','style="height:24px;',1),fills=['six-months'])
        a.condition('현행 신규 신청 · 전입 연장/실거주 유예는 개별 조건 확인')
        recipe.update(axis='row origins explicitly execution date / actual move-in date',pixels_per_month=1630/25)
    elif sid=='R023':
        a.kind='B_birth_income_asset_filters'
        texts=['접수일 기준 ← 2년 안 출산 → B','B 부부합산 소득 8천만원','B 순자산 2억5천만원','현재 검토 주택 6억원']
        for i,text in enumerate(texts):a.add(i,flow(a,i,text,None,(55+i%2*850,65+i//2*250)))
        a.condition('B · 접수 전2년 내 출산 · 합산소득8천만원 · 순자산2억5천만원')
    elif sid=='R024':
        a.kind='eligibility_to_required_principal';c=case(packet,'B_newborn')
        a.add(0,a.label('house-range','대상주택9억원 이하 → 현재6억원',55,35,1640,40))
        a.add(1,bar_row(a,'newborn-cap','상품 한도',400000000,185,420000000),fills=['newborn-cap-fill'])
        a.add(2,bar_row(a,'newborn-needed','필요한 금액만 실행',c['required_loan_krw'],380,420000000,GREEN),fills=['newborn-needed-fill'])
        a.condition('B · 생애최초 · 6억원 · 보증 가입 승인 조건 · 85㎡ 이하 · DTI60%')
    elif sid in ['R025','R026']:
        a.kind='newborn_60_300_month_timeline';recipe.update(file='research/newborn_policy_addendum_v2.json',case_id=nb['case_id'])
        if sid=='R025':
            a.add(0,a.label('initial-rate','초기 기본금리2.9% · 총30년',55,35,1640,40))
            a.add(1,a.summary(1,'처음의 월 상환액',nb['initial_monthly_krw'],decimal_month=True)+a.label('target-line','월 상환 목표170만원',55,260,1060,32))
            a.add(2,a.label('first-five','처음5년 · 60개월',55,420,1060,36)+a.bar('first-60-months',55,490,1060/6,BLUE),fills=['first-60-months'])
        else:
            a.add(0,a.label('spread','초기2.9% + 0.75%포인트',55,25,1630,40))
            a.add(1,a.label('reset-rate','5년 뒤 현행 금리표 예시3.65%',55,145,1630,40,'var(--gold-ink)'))
            a.add(2,a.amount('remaining-balance','60회 상환 뒤 잔액',nb['balance_after60_krw'],55,300,1060,56))
            a.add(3,a.summary(3,'남은300개월의 월 상환',nb['reset_monthly_krw'],'var(--gold-ink)',decimal_month=True))
        a.condition('기본금리 · 우대/추가출산/중도상환0 · 2026.10.19 금리표 · 접수일 기준 산식 예시')
    elif sid=='R027':
        a.kind='nine_eok_product_cap_first'
        a.add(0,bar_row(a,'house9','9억원 주택',900000000,25,900000000,MUTED),fills=['house9-fill'])
        a.add(1,a.bar('cap4',55,200,1060*4/9,BLUE)+a.summary(1,'상품 대출상한',400000000),fills=['cap4'])
        a.add(2,a.label('binding-product','적용 한도 : 상품상한4억원',55,325,1060,36,BLUE))
        a.add(3,a.label('next-cost-input','남은 집값 + 예비자금 + 거래비용 → 다음 계산',55,445,1640,32))
        a.condition('서울·생초70%·공제5,500만원 반영 후 담보5억7,500만원 · 상품4억원이 더 작음')
    elif sid=='R028':
        a.kind='nine_eok_required_cash_gap';c=case(packet,'B_newborn',900000000,55000000)
        a.add(0,bar_row(a,'remaining-house','9억원 − 대출4억원',500000000,25,600000000,GREEN),fills=['remaining-house-fill'])
        a.add(1,a.amount('all-cash','예비3천 + 비용3,615 포함 필요현금',c['cash_required_including_reserve_krw'],55,245,1060,64)+a.label('cash-add','남은 집값 + 예비자금 + 거래비용',55,185,1060,32))
        a.add(2,a.summary(2,'보유현금 대비 추가 현금',c['cash_shortfall_krw'],'var(--gold-ink)'))
        recipe['case_id']=c['case_id']
    elif sid=='R034':
        a.kind='three_inputs_to_listing_range_CTA'
        for i,label in enumerate(['자기자금 : 현금 − 예비·비용','은행의 대출 가능 범위 → 월 상환 목표','정한 예산 → 지역과 단지 비교']):
            a.add(i,flow(a,i,label,None,(55+i%2*800,65+i//2*280)),dim=['beat'+str(i-1)] if i else [])
        a.notes.append('Chapter08 comparison photo is one continuous background use; schematic overlays give way to it at final CTA. No new property claims.')
    else:raise ValueError('Unimplemented frozen scene '+sid)
    return a.finish(recipe)
