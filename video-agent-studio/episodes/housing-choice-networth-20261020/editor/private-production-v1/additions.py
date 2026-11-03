"""New message-specific scenes, using the frozen chapter graphic primitives."""
import csv
import html


def scene(sid, title, body, js, at, source, kind='editorial_diagram'):
    return dict(id=sid, title=title, html=body, js=js, at=at, src=source, assets=[], material_type=kind, origin='new_message_scene')


def additions(F, facts, csv_path, housing_asset, period_check):
    tx, box, panel, card, sub = F.tx, F.box, F.panel, F.card, F.sub
    blue, gold, green = F.BUY, F.JEONSE_INK, F.WOLSE
    out = {}
    # Full 2006 history; selected ten-year interval is a subset of the same data geometry.
    data = list(csv.DictReader(csv_path.open(encoding='utf-8-sig')))
    regions = ['서울', '경기', '인천', '부산', '대구', '대전', '세종']
    colors = ['#286cda', '#94702a', '#3f8f7f', '#7a5291', '#7b432b', '#465d6b', '#705238']
    qs = sorted({r['quarter'] for r in data})
    assert qs[0] == '2006Q1' and qs[-1] == '2026Q2'
    lo, hi = 85, max(float(r['index']) for r in data) * 1.06
    x0, x1, y0, y1 = 125, 1210, 430, 60
    X = lambda q: x0 + qs.index(q) / (len(qs)-1) * (x1-x0)
    Y = lambda v: y0 - (v-lo)/(hi-lo)*(y0-y1)
    h = tx('s2g-unit', 45, 15, '자체 실거래 연결지수 · 지역별 시작분기 = 100', 21, 600)
    svg = [f'<svg class="abs" style="left:0;top:0" width="1740" height="540" viewBox="0 0 1740 540">']
    for value in range(100, int(hi)+1, 100):
        svg.append(f'<line x1="{x0}" x2="{x1}" y1="{Y(value):.2f}" y2="{Y(value):.2f}" stroke="#d0cec5"/>')
        h += tx(f's2g-y{value}', 50, Y(value)-13, str(value), 19, 400, 'var(--muted)', w=60, align='right')
    svg.append(f'<rect id="s2g-window" x="{X("2016Q2"):.2f}" y="{y1}" width="{x1-X("2016Q2"):.2f}" height="{y0-y1}" fill="#286cda" fill-opacity=".055"/>')
    for q in ['2016Q2', '2026Q2']:
        svg.append(f'<line id="s2g-guide-{q}" x1="{X(q):.2f}" x2="{X(q):.2f}" y1="{y1}" y2="{y0}" stroke="#286cda" stroke-width="2" stroke-dasharray="7 5"/>')
    for i, (region, color) in enumerate(zip(regions, colors)):
        rows = sorted((r for r in data if r['region']==region), key=lambda r:r['quarter'])
        d = ' '.join(('M' if j==0 else 'L')+f'{X(r["quarter"]):.2f},{Y(float(r["index"])):.2f}' for j,r in enumerate(rows))
        svg.append(f'<path id="s2g-line{i}" d="{d}" fill="none" stroke="{color}" stroke-width="{4 if i<3 else 2.5}" opacity="{1 if i<3 else .48}" pathLength="1"/>')
        for q in ['2016Q2', '2026Q2']:
            r = next(r for r in rows if r['quarter']==q)
            svg.append(f'<circle id="s2g-point{i}-{q}" cx="{X(q):.2f}" cy="{Y(float(r["index"])):.2f}" r="{7 if i<3 else 4}" fill="{color}" stroke="#fff" stroke-width="2"/>')
        period = next(p for p in facts['regional'][i]['periods'] if p['start']=='2016Q2')
        sample=next(p for p in period_check['periods'] if p['region']==region and p['start']=='2016Q2' and p['end']=='2026Q2')
        if abs(sample['cagr_pct']-period['cagr_pct'])>1e-8:raise ValueError('Regional QA period/value mismatch')
        h += tx(f's2g-legend{i}', 1315, 42+i*62, f'{region}  {period["cagr_pct"]:.1f}%', 24, 700 if i<3 else 600, color, w=360,extra='line-height:1.15;')
        h += tx(f's2g-count{i}',1315,74+i*62,f'{sample["min_matched_complexes"]:,}~{sample["max_matched_complexes"]:,}단지',22,400,'var(--muted)',w=360,extra='line-height:1.15;')
    svg.append('</svg>')
    h += ''.join(svg)
    for q in ['2006Q1','2011Q1','2016Q2','2021Q1','2026Q2']:
        h += tx('s2g-x'+q, X(q)-65, 447, q, 20, 700 if q in ['2016Q2','2026Q2'] else 400, blue if q in ['2016Q2','2026Q2'] else 'var(--muted)', w=130, align='center')
    h += tx('s2g-period', 1315, 7, '연평균 · 분기 연결 단지 수', 22, 600, w=360)
    h += tx('s2g-note', 125, 495, '동일 단지·면적 / 분기별 각 2건 이상 / 연결 30단지 이상 · 세종 2015Q1 시작', 22, 400, 'var(--muted)', w=1100)
    js = '''[0,1,2,3,4,5,6].forEach(i=>{tl.fromTo('#s2g-line'+i,{strokeDasharray:1,strokeDashoffset:1},{strokeDashoffset:0,duration:2.4,ease:'none'},S0('s2g',.35));});
fade('#s2g-window, [id^=s2g-guide], [id^=s2g-point]',T('2016년 2분기부터'));
const regionTimes=[T('서울 약'),T('경기 6.6%'),T('인천 4.0%')];
regionTimes.forEach((t,i)=>{tl.fromTo('#s2g-legend'+i,{scale:1},{scale:1.05,duration:.35,yoyo:true,repeat:1},t);});'''
    out['regional'] = scene('s2g','2006년부터 본 집값 · 강조 구간은 최근 10년',panel('s2g-p',h,wide=True),js,'집값은 먼저 짚고', '자료: 국토교통부 실거래 기반 자체 연결지수 · 기준 2026Q2 · 분기마다 연결 표본 갱신', 'data_chart')
    # Conservative 2% is a planning assumption, not a historical summary.
    value = facts['sensitivity'][1]['house_end_krw']/1e8
    h = box('s2p-start',80,105,450,170,sub('지금 집값',24)+ '<span style="font-size:58px">6억원</span>',size=32)
    h += F.arrow('s2p-arrow',550,190,330)
    h += box('s2p-end',910,105,690,170,sub('연 2% · 10년 뒤',26)+f'<span style="font-size:58px;color:{blue}">약 {value:.2f}억원</span>',border=blue,size=32)
    h += box('s2p-plan',80,350,1520,105,'상승폭이 작아도 대출 상환과 저축을 이어갈 계획',size=32)
    out['planning'] = scene('s2p','보수적인 예산 계획 · 집값 연 2%에서 출발',panel('s2p-p',h,wide=True),"enter('#s2p-start',S0('s2p',.3));growX('#s2p-arrow',T('그래서 첫 계산은'),1.2);enter('#s2p-end',T('6억원 집이'));enter('#s2p-plan',T('상승폭이 작아도'));",'다만 앞으로 감당할', '자료: 자체 예시 모형 · 6억원 × 1.02^10 · 계획을 위한 집값 시나리오', 'data_chart')
    # House-growth-only comparison with tenants fixed.
    h = tx('s8h-fixed',60,25,'고정: 투자 연 6% · 대출 연 4% · 월세·보증금 유지',26,600)
    for i,r in enumerate(facts['sensitivity']):
        x=100+i*415
        h += f'<div id="s8h-focus{i}" style="position:absolute;left:{60+i*415}px;top:65px;width:390px;height:420px;border:3px solid {blue};border-radius:12px;background:rgba(40,108,218,.035)"></div>'
        h += tx(f's8h-head{i}',x-30,80,f'집값 연 {r["house_growth_pct"]:g}%',30,700,blue,w=390,align='center')
        items=[(n,r['networth_krw'][n]/1e8,c,ink,f'{r["networth_krw"][n]/1e8:.2f}억') for n,c,ink in F.HH]
        h += F.vbars(f's8h-v{i}',x,420,items,29,barw=76,gap=40,val_size=23,lab_size=22)
    h += tx('s8h-unit',60,495,'10년 후 평가 순자산 · 억원 · 바뀌는 입력은 집값 상승률 한 가지',22,400,'var(--muted)',w=1600)
    js="""[0,1,2,3].forEach(k=>[0,1,2].forEach(i=>{grow('#s8h-v'+k+'-b'+i,S0('s8h',.4+k*.18),1.2);fade('#s8h-v'+k+'-v'+i,S0('s8h',1.6+k*.18));}));
tl.set('[id^=s8h-focus]',{opacity:0},0);
const focusTimes=[T('집값 상승률만 바꿉니다'),T('집값이 연 2%'),T('연 4%로 바꾸면'),T('연 6%라면')];
focusTimes.forEach((t,i)=>{tl.to('#s8h-focus'+i,{opacity:1,duration:.25},t);if(i<3)tl.to('#s8h-focus'+i,{opacity:0,duration:.2},focusTimes[i+1]-.2);});"""
    out['sensitivity'] = scene('s8h','집값만 0% · 2% · 4% · 6%로 변경',panel('s8h-p',h,wide=True),js,None,'자료: 자체 예시 모형(2026.10) · 초기 2억5천만원 · 월 300만원 · 같은 집·10년', 'data_chart')
    L=facts['leverage_example']
    h=F.hstack('s8l-stack',80,80,1460,100,6,[(2.4,blue,'자기자금 2억4천만원','#fff'),(3.6,'#9aa4a8','대출 3억6천만원','#173348')],label_size=30)
    h+=tx('s8l-base',80,20,'가격이 움직이는 대상 = 집 전체 6억원',32,700)
    h+=box('s8l-move',80,270,690,145,sub('첫해 집값 +2%',26)+'평가액 +1,200만원',size=39,border=blue)
    h+=box('s8l-equity',830,270,710,145,sub('집에 넣은 자기자금 대비',26)+'비용 반영 전 +5%',size=39,border=blue)
    h+=tx('s8l-note',80,465,'이자·보유비용·원금 상환까지 연결해 최종 순자산 계산 · 하락도 집 전체에 작용',24,600,w=1540)
    out['leverage']=scene('s8l','대출을 더하면 집 전체 가격이 움직입니다',panel('s8l-p',h,wide=True),"growX('#s8l-stack-s0',T('자기자금은'),.9);growX('#s8l-stack-s1',T('6억원 집 전체'),.9);enter('#s8l-move',T('1천200만원'));enter('#s8l-equity',T('5%에 해당'));enter('#s8l-note',T('이자와 보유비용'));",'여기에는 대출의 효과','자료: 자체 예시 모형 · 첫해 단순 가격 변화 · 이자·보유비용 연결 전 자기자금 대비 변화','data_chart')
    # New conclusion: one actual message per scene; retain household colors, budget form primitives.
    closing=[
      ('s10choice','내 상황에 맞추는 세 가지 입력','매매와 전세, 월세를 고를 때는', [('보유자금','집과 투자계좌의 출발점'),('월 지출 여력','상환과 차액 투자'),('거주 기간','오래 유지할 생활 계획')]),
      ('s10invest','기본 결과와 추가 투자성과의 조건','이번 계산에서 투자수익은', [('기본 연 6% 결과','전세·월세 순자산이 매매보다 큼'),('추가 성과의 조건','같은 집값·계약 조건에서 우위 확대'),('투자 실행','주거비를 내며 차액 투자 지속')]),
      ('s10stable','실거주 매매 · 자산 형성과 주거 안정','한편 실거주 매매에는', [('종자돈 + 대출','집을 보유하는 출발 구조'),('장기 보유 + 원금 상환','남은 빚을 줄이는 과정'),('생활 터전','살 집을 안정적으로 확보하는 가치')]),
      ('s10life','오래 유지할 생활 계획','제 관점에서는', [('생활비','대출 상환과 함께 유지'),('비상자금','예상 밖 변화에 대비'),('거주 계획','가족의 생활 터전을 오래 유지')]),
      ('s10hold','보유를 이어갈 수 있는 가격','그래서 집값이 크게', [('소득 감소','매달 감당할 현금흐름'),('금리 상승','계속 갚을 수 있는 상환액'),('가격 범위','보유를 유지할 수 있는 예산')]),
    ]
    out['closing']=[]
    for sid,title,at,items in closing:
        h=''
        for i,(label,detail) in enumerate(items):
            h+=box(f'{sid}-b{i}',60+i*560,95,510,300,sub(label,32,blue,700)+sub(detail,27,'var(--ink)',400),size=32)
        js=f"[0,1,2].forEach(i=>enter('#{sid}-b'+i,S0('{sid}',.35+i*.24)));"
        out['closing'].append(scene(sid,title,panel(sid+'-p',h,wide=True),js,at,'자체 예시 모형의 선택 조건 정리 · 투자 역량·저축 실행·주거 안정에 관한 화자 관점'))
    # One use only: a living-space illustration linked to duration and household plans.
    living=next(s for s in out['closing'] if s['id']=='s10life')
    investing=next(s for s in out['closing'] if s['id']=='s10invest')
    investing['js']="enter('#s10invest-b0',T('전세와 월세의 순자산이'));enter('#s10invest-b2',T('차액을 계속 투자하고'));enter('#s10invest-b1',T('같은 집값과 계약 조건에서'));"
    h='<img id="s10life-home" src="assets/housing-stability-v1.png" alt="생활 공간" style="position:absolute;left:40px;top:20px;width:940px;height:510px;object-fit:contain"/>'
    for i,(label,detail) in enumerate([('생활비','상환과 함께 유지'),('비상자금','예상 밖 변화에 대비'),('거주 계획','가족의 생활 터전을 오래 유지')]):
        h+=box(f's10life-b{i}',1060,35+i*170,610,140,sub(label,29,blue,700)+sub(detail,26,'var(--ink)',400),size=31)
    living['html']=panel('s10life-p',h,wide=True,h=590)
    living['js']="fade('#s10life-home',S0('s10life',.2),.5);enter('#s10life-b0, #s10life-b1',T('생활비와 비상자금을'));enter('#s10life-b2',T('한 지역에서 오래 살 계획'));"
    living['assets']=[housing_asset]
    living['material_type']='ai_concept_living_space'
    living['src']='주거 안정과 생활 계획을 설명하는 그림 · 생활비·비상자금·장기 거주에 관한 화자 관점'
    sid='s10next'
    h=tx('s10next-heading',70,35,'다음 편 · 감당 가능한 매매 가격',37,700,blue)
    for i,label in enumerate(['종자돈','월소득','추가 비용','비상자금','월 상환액']):
        h+=box(f's10next-f{i}',70+i*330,140,290,115,label,size=32)
    h+=F.arrow('s10next-a',870,285,65,'d')
    h+=box('s10next-range',450,375,840,120,'내가 살 수 있는 집의 가격 범위',size=40,border=blue,color=blue)
    out['closing'].append(scene(sid,'다음 편 · 내 돈과 소득으로 가격 범위 계산',panel(sid+'-p',h,wide=True),"[0,1,2,3,4].forEach(i=>enter('#s10next-f'+i,S0('s10next',.3+i*.2)));grow('#s10next-a',T('가격 범위를'),.6);enter('#s10next-range',T('가격 범위를',.4));",'다음 시간에는','다음 편 예고 · 종자돈·월소득·부대비용·비상자금·월 상환액'))
    return out
