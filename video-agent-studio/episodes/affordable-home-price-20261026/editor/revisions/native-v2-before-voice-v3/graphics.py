"""Native, message-specific graphics for the approved 45 scenes. No timing estimates."""
from decimal import Decimal
from build import text,rect,svg,e,eok,man,monthly,read,EP

BLUE='var(--blue)';GOLD='var(--gold-ink)';GREEN='var(--green)';INK='var(--ink)';MUTED='var(--muted)'

class Graphic:
    def __init__(self,sid,kind):self.sid=sid;self.kind=kind;self.parts=[];self.targets=[]
    def add(self,key,body,phrases,bounds):
        x,y,w,h=bounds;ident=self.sid+'_'+key
        self.parts.append(f'<g id="{ident}" class="semantic-part">'+body+rect(x,y,w,h,'none',10,'class="focus-ring" stroke="var(--blue)" stroke-width="3" opacity="0"')+'</g>')
        self.targets.append({'id':ident,'phrases':phrases,'bounds':bounds})
    def finish(self):return {'svg':svg(''.join(self.parts)),'targets':self.targets,'kind':self.kind}

def label(x,y,title,value,w=470,color=BLUE,subtitle=None):
    body=rect(x,y,w,128)+text(x+24,y+35,title,24,MUTED,600)+text(x+24,y+85,value,38,color,700)
    if subtitle:body+=text(x+24,y+115,subtitle,22,MUTED)
    return body
def arrow(x1,y1,x2,y2,color=BLUE):
    return f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="3" fill="none"/><path d="M{x2-10} {y2-7} L{x2} {y2} L{x2-10} {y2+7}" stroke="{color}" stroke-width="3" fill="none"/>'
def house(x,y,scale=1):
    return f'<g transform="translate({x},{y}) scale({scale})"><path d="M0 85 L75 20 L150 85 V200 H0 Z" fill="white" stroke="var(--ink)" stroke-width="5"/><path d="M62 200 V135 H98 V200" fill="var(--blue)"/></g>'
def stack_row(x,y,w,amounts,colors,total=None,h=48):
    total=total or sum(amounts);body=''
    for amount,color in zip(amounts,colors):
        size=w*float(amount)/float(total);body+=rect(x,y,size,h,color,3);x+=size
    return body
def timeline(x,y,w,labels):
    body=f'<path d="M{x} {y} H{x+w}" stroke="var(--muted)" stroke-width="3"/>'
    for fraction,label in labels:
        xx=x+w*fraction;body+=f'<circle cx="{xx}" cy="{y}" r="7" fill="var(--blue)"/>'+text(xx,y+43,label,25,anchor='middle')
    return body
def case(data,p,profile='A_first',deduction=0):return data['cases'][f'{profile}_P{p}_C{deduction}']
def case_budget(data):return next(x for x in data['packet']['affordability_A'] if x['profile_id']=='A_first' and x['deduction_krw']==0)

def make(sid,data):
    g=Graphic(sid,'')
    if sid=='S001':
        g.kind='thematic_photo_and_funding_equation'
        g.parts.append('<image href="assets/hero-budget-v1.png" x="0" y="0" width="1740" height="590" preserveAspectRatio="xMidYMid slice"/>'+rect(26,30,950,528,'#ffffffed'))
        g.add('cash',label(60,65,'보유자금','2억5천만원',390),['보유자금','2억 5천'],(50,55,420,145))
        g.add('cap',label(60,220,'수도권·규제지역 · 시가 15억 이하','총액상한 6억원',820,GOLD),['수도권','15억','6억 원','8억 5천'],(50,210,840,145))
        g.add('sum',text(85,410,'2억5천 + 6억 = 8억5천만원',40,BLUE,700)+text(85,465,'담보 → 소득 → 거래비용 → 월 예산',30,INK,600),['실제 범위','담보','매달'],(50,375,850,130))
    elif sid=='S002':
        g.kind='two_budget_axes_bridge'
        g.add('cash',label(60,85,'구입 시점의 현금','2억5천만원',590),['보유자금','2억 5천'],(50,70,620,155))
        g.add('monthly',label(60,330,'매달 주거·저축에 배정','300만원',590,GREEN),['월 300','월 예산'],(50,315,620,155))
        g.add('price',arrow(710,152,1130,275)+arrow(710,397,1130,275)+house(1220,155,1.15)+text(1310,465,'매수 가격 범위',36,BLUE,700,'middle'),['이번에는','가격 범위','연결'],(1100,100,500,410))
    elif sid=='S003':
        g.kind='constraint_intersection_ranges'
        for i,(label_,start,width,phrases,color) in enumerate([('현금',160,1050,['현금'],BLUE),('은행 심사',430,1100,['6억','심사','한도'],GOLD),('월 생활·저축',290,1000,['생활','월 예산'],GREEN)]):
            y=100+i*135;g.add(str(i),text(50,y+35,label_,28,weight=600)+rect(start,y+58,width,40,color,5),phrases,(35,y-5,1660,112))
        g.add('intersection',rect(600,80,460,405,'none',8,'stroke="var(--blue)" stroke-width="4" stroke-dasharray="9 7"')+text(830,535,'세 조건이 만나는 가격 범위',32,BLUE,700,'middle'),['맞춰','2026년'],(570,65,520,490))
    elif sid=='S004':
        g.kind='cash_dates_calendar'
        for i,(lab,phrase) in enumerate([('현금',['잔금일','보유자금']),('주식 현금화',['주식','현금화']),('전세보증금 반환',['전세보증금','날짜'])]):
            x=55+i*550;g.add(str(i),rect(x,75,510,205)+rect(x,75,510,46,BLUE,8)+text(x+255,108,lab,27,'white',600,'middle')+text(x+255,201,'잔금일에 사용 가능',30,anchor='middle'),phrase,(x-5,65,520,230))
        g.add('reserve',text(80,390,'준비할 현금 2억5천만원',38,BLUE,700)+arrow(640,383,850,383)+text(890,390,'예비자금 3천만원 유지',36,GREEN,700),['2억 5천','3천만','예비자금'],(50,325,1630,160))
    elif sid=='S005':
        g.kind='cash_allocation_waterfall'
        g.add('base',label(40,60,'보유자금','2억5천만원',470)+stack_row(80,270,800,[220,30],[BLUE,GREEN])+text(80,355,'구입 배정 2억2천만원',34,BLUE,700)+text(80,410,'예비 3천만원은 별도 통장에 유지',28,GREEN,600),['2억 2천','배정','예비자금'],(30,45,900,420))
        g.add('cost',arrow(940,290,1100,290)+rect(1140,80,510,400)+text(1180,145,'구입 배정액',30,weight=600)+text(1180,225,'− 세금·중개보수·등기비',29,GOLD,600)+text(1180,337,'= 집값 자기자금',35,BLUE,700),['세금','거래비용','자기자금'],(1100,60,580,455))
    elif sid=='S006':
        g.kind='deposit_balance_same_cash_flow'
        g.add('own',label(45,180,'한 묶음의 자기자금','계약금 + 잔금',530),['자기자금','계약금'],(30,160,560,170))
        g.add('loan',label(640,345,'실행할 대출','잔금에 합산',460,GREEN),['대출','충당'],(620,330,500,165))
        g.add('property',arrow(600,240,1230,240)+arrow(1130,410,1250,300)+house(1360,105,1.25)+text(1455,450,'집값',36,BLUE,700,'middle'),['집값','거래비용','다시 계산','하나의'],(1200,70,450,440))
    elif sid=='S007':
        g.kind='property_collateral_ratio'
        g.parts.append(house(95,65,1.35))
        g.add('valuation',label(440,65,'매매가격 P / 담보평가액 V','이번 사례 V = P',1100),['담보가치','매매가격','담보평가액'],(420,50,1140,160))
        g.add('ratio',rect(440,280,1100,72,MUTED)+rect(440,280,440,72,BLUE)+text(440,410,'담보평가액 × 적용 LTV',35,BLUE,700),['LTV','비율','빌릴'],(420,245,1140,195))
        g.add('scope',text(75,535,'가구 A · 서울 규제지역 · 전용 84㎡ 아파트 한 채 · 매매가와 평가액 동일 가정',27,weight=600),['84㎡','가구 A','서울'],(55,475,1620,80))
    elif sid=='S008':
        g.kind='ltv_ratio_and_eligibility_branch'
        for i,(lab,pct,color,phrases) in enumerate([('A 일반 무주택',40,BLUE,['일반','40%']),('A 생애최초',70,GREEN,['생애최초','70%']),('서민실수요 조건',60,'var(--gold)',['서민실수요','60%','9천','8억'])]):
            y=80+i*145
            g.add(str(i),text(45,y+32,lab,27,weight=600)+rect(390,y,1150,48,'white')+rect(390,y,1150*pct/100,48,color,4)+text(1590,y+34,f'{pct}%',33,BLUE,700,'middle')+(text(390,y+93,'연소득 9천만원 이하 + 집값 8억원 이하 + 무주택',25,GOLD,600) if i==2 else ''),phrases,(30,y-10,1660,115))
        g.add('A',text(60,555,'A 인정소득·가구소득 각 연 1억원 → 서민실수요 60% 분기의 소득 기준 초과',26,weight=600),['1억','A는'],(45,505,1650,65))
    elif sid in ['S009','S010']:
        g.kind='collateral_deduction_layers' if sid=='S009' else 'guarantee_application_branches'
        if sid=='S009':
            g.add('prior',text(50,85,'담보평가액 × LTV',32,BLUE,700)+stack_row(50,135,1500,[80,20],[BLUE,MUTED])+text(50,245,'먼저 갚을 권리',28,MUTED),['먼저','권리','담보'],(30,45,1640,230))
            g.add('deduct',label(70,340,'보증으로 보완되지 않은 공제','5,500만원',700,GOLD)+arrow(825,400,1020,400)+text(1070,410,'대출상한에서 차감',34,BLUE,700),['방공제','공제','5,500'],(50,315,1620,170))
        else:
            g.add('process',label(45,50,'실행 은행 취급 확인','가입 요건 심사',700)+arrow(800,110,1000,110)+text(1080,125,'보증 승인 여부',34,BLUE,700),['은행','가입','별도 절차'],(30,30,1640,170))
            g.add('scope',text(70,245,'기존 임차인 0 · 선순위 권리 0인 집을 가정',27,weight=600),['임차인','선순위','집을 가정'],(45,200,1600,65))
            g.add('zero',label(75,300,'보증 승인 등으로 공제 보완','공제 0원',710,GREEN),['0원','기본 계산','공제액'],(55,280,750,180))
            g.add('left',label(920,300,'보완되지 않고 남은 공제','5,500만원',710,GOLD),['남을','살펴','임차인','선순위'],(900,280,750,180))
    elif sid=='S011':
        g.kind='annual_income_dsr_budget'
        g.add('income',text(45,85,'은행 인정 연소득 1억원',36,BLUE,700)+rect(50,150,1530,100,'white')+rect(50,150,612,100,BLUE),['연소득','1억'],(30,45,1600,230))
        g.add('service',text(60,330,'40% → 연간 원리금 상환예산 4천만원',40,BLUE,700)+text(60,405,'주담대와 다른 대출의 원금·이자를 함께 반영',29,weight=600),['DSR','40%','4천만','모든 대출'],(40,280,1610,170))
        g.add('debt',text(70,535,'A 기존 부채 0원 · 다른 부채가 늘면 주택대출에 쓸 여유 감소',28,GREEN,600),['기존 부채','기존 부채가 없는'],(45,480,1600,80))
    elif sid=='S012':
        g.kind='dsr_dti_debt_components'
        for i,(label_,parts,phrases) in enumerate([('DSR',['주담대 원리금','다른 대출 원리금'],['DSR','모든']),('DTI',['주담대 원리금','다른 부채 이자'],['DTI','이자'])]):
            y=100+i*195;body=text(45,y+20,label_,36,BLUE,700)
            for j,p in enumerate(parts):body+=rect(270+j*655,y-35,610,105,'white')+text(575+j*655,y+30,p,31,anchor='middle')
            g.add(str(i),body,phrases,(30,y-65,1640,160))
        g.add('ratios',text(70,525,'A 서울 투기과열지구 · DTI 일반 40% / 생애최초 60% → 담보·소득 중 작은 한도',28,GREEN,600),['40%','60%','가장 작은'],(45,470,1650,85))
    elif sid=='S013':
        g.kind='actual_rate_versus_stress_rate_routes'
        g.add('actual',label(50,75,'계약금리 · 실제 월 상환액 계산','연 4%',700)+arrow(800,140,1030,140)+text(1100,155,'납부 계산',36,BLUE,700),['실제','계약금리','4%'],(30,55,1640,180))
        g.add('stress',label(50,340,'변동형 30년 · 수도권 스트레스 심사','4% + 3%p = 7%',850,GOLD)+arrow(970,400,1140,400)+text(1200,415,'한도 심사',36,GOLD,700),['스트레스','7%','3%포인트','30년'],(30,310,1640,190))
    elif sid=='S014':
        g.kind='equal_payment_principal_interest_structure'
        body=''
        for i,(a,b) in enumerate([(25,75),(55,45),(85,15)]):
            x=80+i*460;body+=stack_row(x,100,360,[a,b],[BLUE,GOLD])+text(x+180,230,['초기','상환 중','만기 가까이'][i],26,anchor='middle')
        g.add('annuity',body+text(80,295,'원금 비중 증가 + 이자 비중 감소 → 매달 합계 일정',30,BLUE,700),['원리금균등','매달 같은','원금과 이자'],(45,65,1510,270))
        g.add('ceiling',label(70,390,'심사금리 7%로 계산한 DSR 상한','약 '+eok(case(data,600000000)['limits_krw']['DSR']),1000),['5억','DSR','상환 여유','기존 부채'],(50,365,1640,175))
    elif sid=='S015':
        g.kind='transaction_process_to_three_receipts'
        for i,(head,sub,phrases) in enumerate([('집 취득','취득세 + 지방교육세',['취득세','지방교육세']),('거래 중개','중개보수',['중개보수','대가']),('소유권 기록','등기수수료 + 채권 부담',['등기','소유권','채권'])]):
            x=45+i*560;body=rect(x,80,520,355)+text(x+260,155,head,34,BLUE,700,'middle')+f'<path d="M{x+80} 210 H{x+440} M{x+80} 250 H{x+440} M{x+80} 290 H{x+360}" stroke="var(--line)" stroke-width="8"/>'+text(x+260,385,sub,28,anchor='middle')
            g.add(str(i),body,phrases,(x-8,65,536,390))
    elif sid in ['S016','S018']:
        g.kind='acquisition_tax_rate_curve' if sid=='S016' else 'brokerage_rate_step_thresholds'
        is_tax=sid=='S016';xs=[150,800,1450];ys=[400,200,200] if is_tax else [400,300,200]
        g.parts.append('<path d="M100 90 V450 H1600" stroke="var(--muted)" stroke-width="2"/>')
        g.parts.append(f'<path d="M150 400 '+('L800 200 H1550' if is_tax else 'H800 V300 H1450 V200 H1550')+'" stroke="var(--blue)" stroke-width="7" fill="none"/>')
        prices=[6,9,12];rates=[1,3,3] if is_tax else [.4,.5,.6]
        for i,(x,y,pct,p_) in enumerate(zip(xs,ys,rates,prices)):
            body=f'<circle cx="{x}" cy="{y}" r="9" fill="var(--blue)"/>'+text(x,y-30,f'{pct}%',36,BLUE,700,'middle')+text(x,500,f'{p_}억원',29,anchor='middle')
            if not is_tax:body+=text(x,555,['부가세 포함 264만원','부가세 포함 495만원','부가세 포함 792만원'][i],24,GREEN,600,'middle')
            phrases=[f'{p_}억',f'{pct}%']+([] if is_tax else [['264만'],['495만'],['792만']][i])
            g.add(str(i),body,phrases,(max(5,x-135),y-70,270,580-(y-70)))
        g.add('scope',text(100,45,'취득가액에 따른 세율 · 무주택·전용 84㎡·중과·감면 전' if is_tax else '서울 상한 요율 · 상한 안 협의 · 일반과세 부가세 10%',27,weight=600),['84㎡','무주택','중과','감면'] if is_tax else ['취득세','계단','중개보수','협의','10%'],(75,5,1600,60))
    elif sid=='S017':
        g.kind='tax_component_stacked_columns'
        totals=[]
        for i,price in enumerate([600000000,900000000,1200000000]):
            c=case(data,price);a=Decimal(c['transaction_costs']['acquisition_krw']);b=Decimal(c['transaction_costs']['education_krw']);total=a+b;totals.append(total);x=150+i*530;h=float(total/39600000)*320
            body=rect(x,430-h,290,h*10/11,BLUE,3)+rect(x,430-h/11,290,h/11,'var(--gold)',3)+text(x+145,85,man(total),40,BLUE,700,'middle')+text(x+145,485,f'{price//100000000}억원 주택',29,anchor='middle')
            g.add(str(i),body,[f'{price//100000000}억',man(total).replace('만원','만 원')],(x-20,45,330,465))
        g.add('scope',text(80,555,'파랑 취득세 + 골드 지방교육세 · 전용 84㎡ · 농어촌특별세 비과세 조건 · 중과·감면 전',25,weight=600),['농어촌특별세','국민주택규모','면적','주택 종류','비용표'],(55,510,1640,65))
    elif sid=='S019':
        g.kind='fee_receipt_triptych_only'
        for i,price in enumerate([600000000,900000000,1200000000]):
            costs=case(data,price)['transaction_costs'];x=35+i*560;body=rect(x,65,535,460)+text(x+28,115,f'{price//100000000}억원 주택',34,BLUE,700)
            for j,(lab,v) in enumerate([('취득세',costs['acquisition_krw']),('지방교육세',costs['education_krw']),('중개보수·부가세',costs['with_vat_krw']),('기타 계획예산',costs['misc_plan_krw'])]):body+=text(x+28,180+j*55,lab,25)+text(x+507,180+j*55,man(v),28,weight=600,anchor='end')
            body+=f'<path d="M{x+25} 415 H{x+510}" stroke="var(--line)"/>'+text(x+28,480,'합계',27,weight=600)+text(x+507,480,man(costs['total_krw']),38,BLUE,700,'end')
            g.add(str(i),body,[f'{price//100000000}억','150만','기타','채권','견적'],(x-5,50,545,490))
        g.parts.append(text(55,565,'무주택·84㎡·감면 전 / 기타 150만원은 채권·등기·법무사·인지 등 매물별 견적으로 바꿀 계획예산',24,MUTED))
    elif sid=='S020':
        g.kind='conditional_tax_relief_alternative_paths'
        g.add('first',label(55,65,'생애최초 · 12억원 이하 보통 아파트','최대 200만원',740)+text(80,255,'본인·배우자 소유 이력',27)+text(80,305,'거주·추징 등 적용 요건 확인',27),['생애최초','200만','소유 이력'],(35,45,780,300))
        g.add('birth',label(920,65,'출산·양육 · 12억원 이하','최대 500만원',740,GREEN)+text(945,255,'2028년 말까지 출산',28,GREEN,600)+text(945,305,'취득: 출산 전 1년 ~ 출산 후 5년',27),['출산','500만','2028년','1년','5년'],(900,45,780,300))
        g.add('choose',timeline(160,405,1400,[(0,'각 감면 요건 확인'),(.5,'동시 적격이면 큰 감면 하나'),(1,'감면 후 세액 별도 확인')])+text(120,545,'출산 감면: 1가구 1주택(취득 후 3개월 내 포함) · 자녀와 거주 · 추징 요건 확인',25,weight=600),['겹치면','큰 감면','비용표','교육세','별도'],(45,365,1650,210))
    else:return make_later(sid,data)
    return g.finish()

def make_later(sid,data):
    g=Graphic(sid,'')
    if sid=='S021':
        g.kind='six_eok_funding_gap_bridge';c=case(data,600000000,'A_ordinary')
        own=Decimal(600000000)-Decimal(c['required_loan_krw']);need=Decimal(c['required_loan_krw']);cap=Decimal(c['loan_ceiling_krw']);gap=Decimal(c['cash_shortfall_krw'])
        g.add('house',house(60,65,.8)+text(250,125,'6억원 주택',38,BLUE,700)+text(250,175,'A 일반 무주택 · LTV 40%',27),['6억','A가'],(30,40,1660,175))
        g.add('need',stack_row(75,255,1500,[own,need],[GREEN,BLUE])+text(75,225,'자기자금 '+eok(own),29,GREEN,700)+text(1550,225,'필요대출 '+eok(need),29,BLUE,700,'end'),['자기자금','필요한 대출','3억 9,074','2억 926'],(45,190,1630,145))
        g.add('gap',stack_row(75,410,1500,[own,cap,gap],[GREEN,BLUE,'var(--gold)'])+text(75,515,'일반 담보한도 '+eok(cap),32,BLUE,700)+text(1550,515,'추가현금 '+eok(gap),32,GOLD,700,'end'),['40%','2억 4천','1억 5,074','추가 현금'],(45,365,1630,190))
    elif sid=='S022':
        g.kind='guarantee_zero_and_uncovered_deduction_bars'
        need=Decimal(case(data,600000000)['required_loan_krw'])
        for i,ded in enumerate([0,55000000]):
            c=case(data,600000000,deduction=ded);y=95+i*245;cap=Decimal(c['loan_ceiling_krw']);w=float(cap/450000000)*1250
            body=text(45,y-28,'공제 보완 · 0원' if not ded else '남은 공제 5,500만원',28,GREEN if not ded else GOLD,600)+rect(100,y,1400,58,'white')+rect(100,y,w,58,BLUE)+text(1550,y+42,eok(cap),32,BLUE,700,'middle')
            if ded:body+=text(110,y+140,'추가현금 '+man(c['cash_shortfall_krw']),31,GOLD,700)
            else:body+=text(110,y+140,'필요대출 '+eok(need)+'을 한도 안에서 충당',30,GREEN,600)
            g.add(str(i),body,['생애최초','70%','4억 2천','충당'] if not ded else ['5,500','3억 6,500','2,574','줄이는'],(25,y-65,1670,230))
        x=100+float(need/450000000)*1250;g.parts.append(f'<path d="M{x} 75 V430" stroke="var(--ink)" stroke-width="3" stroke-dasharray="7 6"/>'+text(100,565,'점선: 필요한 대출 3억9,074만원 · 공제는 대출상한에 반영',25,weight=600))
    elif sid in ['S023','S041']:
        g.kind='monthly_payment_target_gauge' if sid=='S023' else 'monthly_gap_and_three_adjustments'
        payment=Decimal(case(data,600000000)['payment_if_financeable_krw']);target=Decimal(1700000)
        g.add('payment',label(55,50,'필요대출 3억9,074만원 · 연 4% · 30년','월 약 '+monthly(payment),1050),['생애최초','6억','186.5','4%','30년'],(35,30,1660,165))
        x=150;scale=7;g.add('target',rect(x,260,float(payment/10000)*scale,65,BLUE)+f'<path d="M{x+170*scale} 220 V385" stroke="var(--gold-ink)" stroke-width="4" stroke-dasharray="7 6"/>'+text(150,430,'월 목표 170만원',31,GOLD,700)+text(1580,430,'차이 약 '+monthly(payment-target),31,BLUE,700,'end'),['목표','170만','생활 예산','차이','대조'],(55,210,1630,250))
        if sid=='S041':g.add('choices',text(90,535,'현금 추가  ↔  저축 목표 조정  ↔  매수 가격 조정',31,GREEN,700),['현금','저축','가격을 조정'],(55,475,1630,90))
        else:g.add('living',text(75,535,'자금 조달 조건 → 생활 예산 확인',29,GREEN,700),['자금 조달','생활 예산'],(45,480,1650,80))
    elif sid=='S024':
        g.kind='nine_twelve_minimum_constraint_comparison'
        g.parts.append(text(55,48,'A 생애최초 · 수도권·규제지역 · 공제 보완 · 약정 4% / 심사 7%',25,weight=600))
        for i,p in enumerate([900000000,1200000000]):
            c=case(data,p);y=100+i*225;body=text(65,y+40,f'{p//100000000}억원',40,BLUE,700)
            for x,label_,key,col in [(345,'필요대출','required_loan_krw',INK),(800,'DSR 대출상한','loan_ceiling_krw',BLUE),(1260,'추가현금','cash_shortfall_krw',GOLD)]:body+=text(x,y+5,label_,25,MUTED,600)+text(x,y+70,eok(c[key]),34,col,700)
            body+=rect(345,y+110,1250,24,'white')+rect(345,y+110,1250*float(Decimal(c['loan_ceiling_krw'])/Decimal(c['required_loan_krw'])),24,BLUE)
            g.add(str(i),body,[f'{p//100000000}억','7억 1,615','2억 1,512'] if i==0 else ['12억','10억 2,902','5억 2,799'],(35,y-25,1660,195))
        g.add('limits',text(65,565,'담보차감후상한·총액상한·DSR 등 심사값 중 가장 작은 값 적용',26,GREEN,600),['담보 한도','총액상한','DSR','5억 103'],(45,525,1650,60))
    elif sid=='S025':
        g.kind='separate_policy_threshold_axes'
        g.add('products',text(45,70,'세금·정책상품의 주택가격',30,BLUE,700)+timeline(230,135,1270,[(0,'6억원'),(.5,'9억원'),(1,'12억원')]),['6억','9억','12억','세금','상품 자격'],(25,40,1670,180))
        body=text(45,285,'수도권·규제지역 일반 구입 주담대 총액상한',29,weight=700)
        for i,(label_,val) in enumerate([('시가 15억원 이하','6억원'),('15억 초과 ~ 25억 이하','4억원'),('25억원 초과','2억원')]):body+=label(55+i*560,340,label_,val,520,[BLUE,GOLD,GREEN][i])
        g.add('totals',body,['15억','25억','총액','4억 원','2억 원'],(30,245,1670,260))
        g.add('binding',text(70,555,'6·9·12억원 사례는 모두 시가 15억원 이하 구간 → 담보·소득 심사까지 결합',26,BLUE,600),['첫 구간','실제 상한'],(45,510,1650,65))
    elif sid=='S026':
        g.kind='household_B_financial_ledger'
        g.add('profile',text(90,32,'정책상품 · 별도의 가구 B',26,GREEN,700),['정책상품','별도의 가구 B'],(70,3,1600,42))
        g.parts.append(rect(45,45,1635,490,'white',8)+rect(45,45,24,490,GREEN,4))
        for i,(key,head,val,phrases) in enumerate([('income','부부합산 연소득','8천만원',['8천','별도의 가구 B']),('assets','순자산 / 기존 부채','2억5천만원 / 0원',['순자산','부채']),('family','무주택 신혼 · 생애최초','혼인 7년 이내 / 접수 전 2년 내 출산',['7년','출산','2년']),('same','A와 같은 구입 조건','현금·예비자금 / 서울 84㎡',['현금과','84㎡'])]):
            y=105+i*115;g.add(key,text(105,y,head,26,MUTED,600)+text(640,y,val,32,GREEN if i==2 else BLUE,700)+f'<path d="M100 {y+28} H1610" stroke="var(--line)"/>',phrases,(85,y-45,1550,85))
    elif sid in ['S027','S028','S033']:
        g.kind={'S027':'didim_eligibility_to_product_limit','S028':'bogeum_three_valuation_gates','S033':'newborn_eligibility_to_funding'}[sid]
        if sid=='S027':
            fields=[('신혼 합산소득','8,500만원 이하'),('순자산','5억1,100만원 이하'),('주택가격','6억원 이하'),('전용면적','85㎡ 이하')];c=case(data,600000000,'B_didim')
        elif sid=='S028':
            fields=[('시세','6억원 이하'),('감정가','6억원 이하'),('실제 매매가','6억원 이하')];c=case(data,600000000,'B_bogeum')
        else:
            fields=[('주택가격','9억원 이하'),('서울 전용면적','85㎡ 이하'),('DTI','60% 이내')];c=case(data,600000000,'B_newborn')
        w=1570/len(fields)
        body=''
        for i,(a,b) in enumerate(fields):body+=label(50+i*(w+15),65,a,b,w-25,BLUE)+f'<path d="M{75+i*(w+15)} 210 L{75+i*(w+15)} 250" stroke="var(--green)" stroke-width="4"/>'
        g.add('eligibility',body,['소득','순자산','주택','면적','시세','감정','매매가','85㎡','DTI'],(30,40,1670,235))
        need=Decimal(c['required_loan_krw']);cap=Decimal(c['loan_ceiling_krw'])
        body=label(55,310,'B의 대출상한',eok(cap),700,GREEN)+label(920,310,'6억원 집의 필요대출',eok(need),700,BLUE)
        body+=text(75,525,'추가현금 '+man(c['cash_shortfall_krw']) if sid=='S027' else ('서울 생애최초 LTV 70% · 임대차 없는 아파트 방수공제 0' if sid=='S028' else '보증 가입요건 충족·승인으로 공제 보완 · 상품한도 4억원'),27,GREEN,600)
        g.add('funding',body,['상품 한도','3억 2천','4억 2천','3억 9,074','7,074','공제','보증','한도 안'],(35,285,1660,280))
    elif sid in ['S029','S030']:
        g.kind='single_income_exception_branch_bogeum' if sid=='S029' else 'single_income_exception_branch_didim'
        is_bogeum=sid=='S029';limit='7천만원 이하' if is_bogeum else '6천만원 이하'
        g.add('normal',label(45,65,'기존 신혼 합산기준 경로','B는 합산기준 충족',720,GREEN),['합산기준','B는','기존'],(25,45,760,170))
        g.add('exception',label(925,65,'합산기준 초과 시 1인 소득특례','신청인 '+limit,740,BLUE),['한 사람','7천만','6천만','8,500','예외','특례'],(905,45,780,170))
        g.add('dti',arrow(1290,240,1290,300)+rect(920,330,740,100,'white')+text(1290,390,'DTI: 그 1인의 소득·부채',31,BLUE,700,'middle'),['DTI','그 사람','신청인 한 사람'],(900,285,780,170))
        note='배우자: 우대·실수요 요건 / 주택보유수: 부부 합산' if is_bogeum else '정책 신규 DSR 예외 → DTI·신용·보증·실행심사 확인'
        g.add('checks',text(70,525,note,29,weight=600),['배우자','주택보유수','신용','보증','규제 DSR','실행 조건'],(45,475,1650,90))
    elif sid=='S031':
        g.kind='two_product_residence_clocks'
        g.add('didim',text(60,80,'디딤돌 · B DTI 60%',30,BLUE,700)+timeline(190,160,1350,[(0,'실행'),(.3,'1개월 안에 전입'),(1,'전입일부터 2년 실거주')]),['디딤돌','1개월','2년','60%'],(30,45,1670,210))
        g.add('bogeum',text(60,340,'수도권 보금자리론 · B 생애최초 DTI 60%',29,GREEN,700)+timeline(190,420,1350,[(0,'실행'),(1,'6개월 안에 전입·입증서류')]),['보금자리론','6개월','입주 계획','자격'],(30,300,1670,230))
        g.add('plan',text(70,570,'자격·대출한도 → 입주 계획',27,BLUE,700),['자격과 한도','입주 계획'],(40,530,1650,55))
    elif sid=='S032':
        g.kind='newborn_photo_and_eligibility_filters'
        g.parts.append('<image href="assets/newborn-home-v1.png" x="1040" y="0" width="700" height="590" preserveAspectRatio="xMidYMid slice"/>')
        rows=[('birth','접수 전 2년 내 출산·입양','2023.1.1 이후 출생 · 입양아 접수일 현재 만 2세 미만',['2년','2023','입양','2세']),('income','외벌이 1억3천만원 이하','맞벌이: 합산 2억원 이하 AND 부부 각자 1억3천만원 이하',['소득','외벌이','맞벌이','각자']),('assets','순자산 5억1,100만원 이하','동일 가구 B의 신생아 특례 구입자금',['순자산','5억 1,100','같은 B'])]
        for i,(key,head,sub,phrases) in enumerate(rows):
            y=45+i*180;body=rect(25,y,990,155,'#fffffff2')+text(55,y+55,head,30,BLUE,700)+text(55,y+111,sub,24,weight=600)
            g.add(key,body,phrases,(15,y-10,1010,175))
    elif sid=='S034':
        g.kind='first_5_years_and_application_rate_formula';c=data['reset']['case']
        g.add('initial',label(45,55,'B · 30년 중 처음 5년','연 2.9% / 월 약 162.6만원',1120),['30년','2.9%','162.6','5년'],(25,35,1660,165))
        g.add('formula',rect(45,255,1630,125,'white')+text(75,300,'대출접수일 기준',26,GREEN,700)+text(75,350,'생초 신혼 디딤돌 최저기본금리 − 신생아 최저특례금리',32,weight=600),['이후','대출접수일','최저','차이를'],(25,235,1670,165))
        g.add('reset',text(65,465,'신규 합산소득 8,500만원 이하인 B · KB 2026.10.19 표',27,weight=600)+text(65,535,'기본금리 2.9% + 0.75%p = 3.65%',39,BLUE,700),['8,500','2026년','0.75','3.65'],(25,415,1670,150))
    elif sid=='S034R':
        g.kind='remaining_balance_300_months_and_budget'
        # Reuse the reviewed ratio/row geometry, with separate semantic focus regions.
        from build import reset
        raw=reset(data);g.parts.append(raw[raw.index('>')+1:raw.rindex('</svg>')])
        g.add('balance','',['60회','3억 4,676','300개월','176.4'],(35,65,1670,275))
        g.add('budget','',['300만','170만','초기와','기본 사례'],(30,350,1670,225))
        g.parts.append(text(1400,415,'월 상환 목표 170만원',22,GOLD,600,'middle'))
    elif sid=='S035':
        g.kind='nine_eok_collateral_min_product_cash'
        c=case(data,900000000,'B_newborn',55000000)
        g.add('deduct',text(55,80,'9억원 × LTV 70% − 공제 5,500만원',38,BLUE,700)+rect(65,140,1480,48,BLUE)+text(65,245,'담보차감후상한 5억7,500만원',33,BLUE,700),['9억','5,500','70%','5억 7,500'],(30,35,1660,240))
        g.add('minimum',arrow(730,285,1030,285)+label(1070,300,'더 작은 상품한도 적용','대출상한 4억원',565,GREEN),['상품 한도','4억 원','작아','대출 상한'],(1010,265,660,185))
        g.add('cash',text(60,515,'예비자금·비용 포함 필요현금 '+eok(c['cash_required_including_reserve_krw']),35,GOLD,700),['필요한 현금','5억 6,615'],(30,460,1660,100))
    elif sid=='S036':
        g.kind='newborn_cash_shortfall_to_move_in_clock';c=case(data,900000000,'B_newborn',55000000)
        g.add('shortfall',label(45,45,'필요현금 5억6,615만원 − 보유 2억5천만원','추가현금 '+eok(c['cash_shortfall_krw']),1580,GOLD),['보유한','추가 현금','3억 1,615','가격대'],(25,25,1680,180))
        g.add('price',text(65,240,'금리 혜택과 함께 자금표가 맞는 가격대 선택',30,BLUE,700),['금리 혜택','자금표','가격대'],(40,195,1660,70))
        g.add('residence',timeline(200,345,1300,[(0,'실행'),(.38,'1개월 내 전입'),(1,'전입일부터 2년 실거주')])+text(65,510,'신생아 특례 신규 신청 · 출산가구의 실제 이사 일정과 연결',28,BLUE,700),['1개월','2년','실거주','이사'],(25,265,1680,290))
    elif sid=='S037':
        g.kind='affordability_price_envelope';c=case_budget(data)['bank_assumptions_max']
        chain=text(55,70,'A 생애최초 · 보증 승인 등 공제 0 · 현금·비용·은행 심사 결합',28,weight=600)
        for i,lab in enumerate(['현금','비용','담보','소득']):chain+=rect(80+i*400,135,330,100,'white')+text(245+i*400,198,lab,31,BLUE,700,'middle')+(arrow(420+i*400,184,465+i*400,184) if i<3 else '')
        g.add('conditions',chain,['생애최초','보증','현금과 비용','가정','실행 조건'],(30,30,1660,260))
        g.add('price',label(75,365,'위 가정과 심사 조건을 맞춘 가격 상한','약 '+eok(c['max_price_krw']),1500),['6억 8,019','가격 상한','생활','매달'],(50,340,1570,190))
        g.add('living',text(75,560,'매수 예산에는 매달 유지할 생활도 반영',28,GREEN,700),['매수 예산','매달 유지','생활도'],(45,520,1650,65))
    elif sid=='S038':
        g.kind='monthly_envelopes_to_affordable_price';c=case_budget(data)['mortgage_budget_max']
        for i,(head,val,col,phr) in enumerate([('소유비 계획',30,MUTED,['소유','30만']),('저축 목표',100,GREEN,['저축','100만']),('대출 상환 목표',170,BLUE,['170만','상환 목표'])]):
            x=55+i*555;body=rect(x,85,520,280,'white')+f'<path d="M{x} 85 L{x+260} 215 L{x+520} 85" stroke="var(--line)" stroke-width="4" fill="none"/>'+text(x+260,275,f'{val}만원',42,col,700,'middle')+text(x+260,330,head,28,anchor='middle')
            g.add(str(i),body,phr,(x-8,65,536,330))
        g.add('reverse',text(70,460,'월 주거·저축 배정액 300만원 → 월 상환 목표로 역산',30,weight=600)+text(70,535,'감당할 집값 약 '+eok(c['max_price_krw']),39,BLUE,700),['300만','역산','5억 6,586','계획값'],(40,410,1650,155))
    elif sid in ['S039','S040']:
        g.kind='bank_limit_vs_monthly_budget_rows' if sid=='S039' else 'same_principal_new_360_month_rate_shock'
        d=case_budget(data)
        scope='A · 인정 연소득 1억원 / 월 생활비 배정 후 주거·저축 예산 300만원' if sid=='S039' else 'A · 각 가격의 최초원금 동일 · 각각 새 360개월 · 금리 4% / 6% 비교'
        g.add('scope',text(45,45,scope,25,weight=600),['은행이 인정한','인정소득','월 300','생활비'] if sid=='S039' else ['4%','6%','최초','360개월'],(30,5,1670,60))
        for i,k in enumerate(['bank_assumptions_max','mortgage_budget_max']):
            c=d[k];y=105+i*230;price=eok(c['max_price_krw'])
            if sid=='S039':
                pay=Decimal(c['payment_on_required_loan_krw']);saving=Decimal(c['remaining_savings_krw']);body=text(50,y+35,price,34,BLUE,700)+stack_row(50,y+85,1530,[300000,pay,saving],[MUTED,BLUE,GREEN],3000000)+text(50,y+180,'보유비 30만원',24,MUTED)+text(620,y+180,'상환 약 '+monthly(pay),29,BLUE,700)+text(1570,y+180,'저축 약 '+monthly(saving),29,GREEN,700,'end')
            else:
                pay=Decimal(c['payment_on_required_loan_krw']);shock=Decimal(c['payment_shock_same_original_360months_krw']);saving=Decimal(c['remaining_savings_krw']);ss=Decimal(c['remaining_savings_shock_krw'])
                body=text(50,y+25,price,31,BLUE,700)+text(50,y+83,'금리 4% → 6%',28,weight=600)+rect(430,y+45,float(pay/3000000)*950,40,BLUE)+rect(430,y+105,float(shock/3000000)*950,40,'var(--gold)')+text(1450,y+77,monthly(pay),29,BLUE,700)+text(1450,y+137,monthly(shock),29,GOLD,700)+text(60,y+190,'저축 여유 '+monthly(saving)+' → '+('약 '+monthly(-ss)+' 부족' if ss<0 else monthly(ss)),27,GREEN,600)
            phrases=(['은행 조건','227만','43만','높은 가격','285만','15만'] if i==0 else ['월 목표','170만','100만','예산에 맞춘','213만','57만'])
            g.add(str(i),body,phrases,(30,y-15,1670,225))
        if sid=='S040':g.parts.append(text(50,580,'각 가격의 최초원금 동일 · 각각 새 360개월 상환 · B의 60회 후 잔액·남은 300개월과 별도 계산',23,MUTED))
    elif sid=='S042':
        g.kind='cash_and_bank_confirmation_two_input_workflow'
        g.add('inputs',text(65,30,'매물 검색 전 세 숫자 정리',26,GREEN,700),['매물','세 숫자','정리'],(40,1,1650,40))
        body=text(65,75,'① 집값에 넣을 자기자금',35,BLUE,700)
        for i,lab in enumerate(['보유자금','− 예비자금','− 거래비용']):body+=rect(65+i*530,125,480,80,'white')+text(305+i*530,177,lab,29,BLUE,600,'middle')
        g.add('cash',body+text(65,260,'집값 자기자금으로 연결',30,GREEN,600),['첫째','보유자금','자기자금','예비자금'],(30,40,1670,250))
        g.add('bank',text(65,365,'② 해당 집·가구에 은행이 확인한 대출 범위',34,GREEN,700)+text(65,460,'인정소득 → 기존 부채 → 담보평가 → 보증·은행 확인',30,weight=600),['둘째','은행','인정소득','기존 부채','담보평가','보증'],(30,315,1670,210))
    elif sid=='S043':
        g.kind='three_inputs_to_search_price_intersection'
        body=text(60,75,'③ 매달 유지할 상환액',36,BLUE,700)
        for i,lab in enumerate(['생활비','소유 지출','저축 목표','금리 변화']):body+=rect(65+i*410,125,365,85,'white')+text(247+i*410,180,lab,29,BLUE,600,'middle')
        g.add('monthly',body+text(75,265,'매달 지출과 저축을 유지할 수 있는 상환 예산',28,weight=600),['셋째','생활비','저축','금리'],(30,40,1670,250))
        g.add('intersection',arrow(500,330,1100,430)+arrow(900,330,1100,430)+arrow(1400,330,1100,430)+label(600,435,'자기자금 + 확인 대출 + 월 상환 예산','매물 검색 가격 범위',1050,BLUE),['세 숫자','가격 범위','정책상품','자금표'],(40,300,1650,275))
    elif sid=='S044':
        g.kind='next_episode_candidates_and_CTA'
        body=''
        for i,(lab,sub) in enumerate([('가격','예산 안 후보'),('일자리 접근성','생활권 연결'),('교통·생활','조건 비교')]):
            x=140+i*525;body+=house(x,60,.65)+text(x+40,270,lab,31,BLUE,700,'middle')+text(x+40,325,sub,26,anchor='middle')
        g.add('next',body,['다음 편','지역','단지','가격','일자리','교통'],(35,30,1670,350))
        g.add('cta',text(350,455,'구독  +  좋아요',43,BLUE,700)+text(1150,455,'시청해 주셔서 감사합니다',32,GREEN,700,'middle'),['구독','좋아요','도움','감사'],(45,390,1650,160))
    else:raise ValueError('Missing authored scene graphic: '+sid)
    return g.finish()
