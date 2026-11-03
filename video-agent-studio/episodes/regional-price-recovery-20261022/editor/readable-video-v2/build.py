"""Build the revised literature film using local, deterministic HyperFrames assets."""
from pathlib import Path
import json, math, re, shutil, hashlib, html, copy
import xml.etree.ElementTree as ET

EP = Path(__file__).resolve().parents[2]
OUT = EP / 'outputs/readable-video-v2'
P = OUT / 'project'
OLD = EP / 'outputs/literature-visual-v1/project'
HOMES = EP / 'outputs/household-space-v1/project'
E = lambda s: html.escape(str(s), quote=True)
FPS = 30
INK, BLUE, MUTED, GOLD = '#173348', '#286CDA', '#526872', '#967536'

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), 'utf-8')

def text(x,y,s,size=30,color=INK,anchor='start',weight=400,cls=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" class="{cls}">{E(s)}</text>'

def lines(x,y,ss,size=30,color=INK,step=None,weight=400):
    return ''.join(text(x,y+i*(step or size*1.5),s,size,color,weight=weight) for i,s in enumerate(ss))

def svg(s):
    return f'<svg class="stage" viewBox="0 0 1760 620">{s}</svg>'

def house(x,y,w=130,color='#89A594',opacity=1):
    # Small architectural model: wall, pitched roof, recessed entry, shaded side.
    return f'''<g opacity="{opacity}" transform="translate({x} {y}) scale({w/130})"><ellipse cx="65" cy="132" rx="78" ry="9" fill="{INK}" opacity=".06"/><path d="M0 48L62 0l68 48v80H0Z" fill="#E7E0D0"/><path d="M62 0l68 48v80l-18-11V45Z" fill="#C0C9BF"/><path d="M-10 48L62-8l80 56-11 7L62 7 0 55Z" fill="{color}"/><rect x="18" y="65" width="30" height="30" fill="#C0D5DB"/><path d="M33 65v30m-15-15h30" stroke="#FFF" stroke-width="3"/><rect x="66" y="66" width="26" height="62" rx="2" fill="#9C8767"/><circle cx="86" cy="99" r="2" fill="#F4E3B6"/></g>'''

def room(which,x,y,w):
    ident='family-home' if which=='family' else 'studio-home'
    g=copy.deepcopy(next(n for n in ROOM_XML if n.get('id')==ident))
    for n in g.iter():
        if n.get('id')=='child-cup-old':n.set('class','child-cup-old')
        n.attrib.pop('id',None)
    for n in list(g):
        if n.tag.endswith('text'):g.remove(n)
    vb='140 340 820 420' if which=='family' else '1100 340 670 420'
    h=w*(420/(820 if which=='family' else 670))
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" overflow="hidden">{ET.tostring(g,encoding="unicode")}</svg>'

def apt(panel,x,y,w=260):
    # Each source panel is separated into its own file: no hidden 900px overflow.
    return f'<image href="assets/apartment-{panel}.svg" x="{x}" y="{y}" width="{w}" height="{w*1.4}"/>'

def note(s):return f'<div class="qualifier">{E(s)}</div>'

def study(source,focus,details):
    r=SOURCES[source]
    title=r['title']
    # Bibliographic title remains complete, with a smaller type only for long titles.
    return f'''<div class="study"><div class="overline">{E(r['display_authors'])} · {r['year']}</div><h2 style="font-size:{32 if len(title)>70 else 37}px">{E(title)}</h2><div class="journal">{E(r['publication'])}</div><div class="focus">{E(focus)}</div><p>{'<br>'.join(E(s) for s in details)}</p></div>'''

def price_chart(zoom=False):
    regions=['서울','경기']; data=[]
    for region in regions:
        rows=[r for r in PRICE if r['region']==region and (not zoom or r['quarter']>='2021Q4')]
        base=next(float(r['source_index']) for r in PRICE if r['region']==region and r['quarter']==('2021Q4' if zoom else '2006Q1'))
        data.append([(r['quarter'],float(r['source_index'])/base*100) for r in rows])
    x0,x1,y0,y1=130,1530,50,470
    low=70 if zoom else 50; high=130 if zoom else math.ceil(max(v for d in data for _,v in d)/50)*50
    yy=lambda v:y1-(v-low)/(high-low)*(y1-y0)
    out=''
    ticks=range(low,high+1,10 if zoom else 50)
    for v in ticks:
        y=yy(v);out+=f'<path d="M{x0} {y}H{x1}" stroke="#D8DFDA" stroke-width="1"/>'+text(x0-25,y+8,str(v),22,MUTED,'end')
    for idx,d in enumerate(data):
        color=[BLUE,GOLD][idx]
        points=[(x0+(x1-x0)*i/(len(d)-1),yy(v)) for i,(_,v) in enumerate(d)]
        path='M'+'L'.join(f'{x:.2f} {y:.2f}' for x,y in points)
        out+=f'<path class="draw-line" d="{path}" fill="none" stroke="{color}" stroke-width="6" stroke-linejoin="round"/>'
        out+=text(1570,points[-1][1]+8,regions[idx],27,color,weight=700)
    for q in (['2021Q4','2022Q4','2023Q4','2024Q4','2026Q2'] if zoom else ['2006Q1','2010Q1','2015Q1','2020Q1','2026Q2']):
        i=next(i for i,(quarter,_) in enumerate(data[0]) if quarter==q)
        out+=text(x0+(x1-x0)*i/(len(data[0])-1),530,q,22,MUTED,'middle')
    out+=text(130,590,'2021년 4분기 = 100' if zoom else '2006년 1분기 = 100 · 명목 가격',23,MUTED)
    if zoom:out+=text(130,18,'서울: 2024Q3 고점 최초 회복',29,BLUE,weight=700)+text(1000,18,'경기: 2026Q2 고점 대비 −4.1%',29,GOLD,weight=700)
    return svg(out)

def visual(scene,index,p):
    n=scene['id'];t=p['text'];k=index
    if n=='L001':
        if k==1:return '<div class="history-view">'+price_chart(False)+'</div><div class="recovery-view">'+price_chart(True)+'</div>'+note('자체 지수 · 동일 단지·면적군 연결 · 가격 경로 비교이며 원인별 기여율은 추정하지 않았습니다.')
        if k==3:
            return svg(text(80,130,'서울',36,BLUE,weight=700)+text(80,255,'2024년 3분기',84,BLUE,weight=700)+text(80,320,'2021Q4 고점 최초 회복',30,MUTED)+text(1020,130,'경기',36,GOLD,weight=700)+text(1020,255,'−4.1%',104,GOLD,weight=700)+text(1020,320,'2026Q2 / 2021Q4 고점 대비',30,MUTED)+lines(80,470,['같은 시기, 다른 회복 속도','이 차이를 만든 생활 조건은 무엇일까?'],40,step=68,weight=700))+note('자체 지수의 관측값 · 같은 가구의 실제 매매 수익률이나 원인별 기여율이 아닙니다.')
        return svg(room('family',40,75,700)+house(1410,350,180)+lines(900,100,['누가 찾는 집인가','언제 들어갈 수 있나','직장에 닿을 수 있나'],44,step=90,weight=700))+note('문헌을 통해 확인할 세 가지 질문 · 현재 지역별 원인 분석의 확정 결과가 아닙니다.')
    if n=='L002':
        if k<=1:
            s=room('family',0,65,900)
            s+='<g class="new-home">'+room('studio',1030,115,650)+'</g>'
            if k==0:
                s+='<g class="family-before">'+text(430,545,'부모 + 성인 자녀',30,INK,'middle')+'</g><g class="family-after">'+text(430,545,'부모 · 기존 집에 거주',30,INK,'middle')+'</g>'
            else:s+=text(430,545,'부모 · 기존 집에 거주',30,INK,'middle')
            s+='<g class="new-home">'+text(1355,545,'자녀의 독립된 집',30,BLUE,'middle')+'</g>'
            s+=text(850,40,'인구 3명   ·   가구 1 → 2',42,BLUE,'middle',700)
            return svg(s)+note('구조 설명용 가상 예시 · 같은 세 사람의 거처가 두 집으로 나뉘는 상황입니다.')
        if k==2:
            return study('R1','주거비와 청년의 이동',['2005–2010년 수도권 취업자 분석','청년 25–39세 · 전세가격·전출·통근'])+svg(room('studio',940,70,700)+lines(940,540,['주거비 상승 ↔ 청년 전출','관련성 관찰 · 현재의 원인 확정 아님'],30,step=47))+note('관찰된 관계를 소개합니다. 인구 전출과 주택 수요 감소를 같은 뜻으로 단정할 수 없습니다.')
        return svg(room('studio',60,60,700)+lines(950,135,['사람 수와 함께','가구 수 · 연령 · 목적지','무슨 집을 찾는지'],45,step=95,weight=700))+note('집을 찾는 주체와 조건을 함께 살피자는 문헌 기반 해석입니다.')
    if n=='L003':
        if k==1:
            ex=FLOOR['examples'][0]
            meta=f"{ex['complex']} · {ex['unit_type']}"
            return f'''<div class="floorplan"><img src="assets/floorplan59.png" alt="{E(meta)} 실제 분양 평면"/></div><div class="floor-meta"><div class="overline">실제 분양 평면 예시</div><h2>남양주왕숙 A-1블록<br>59A</h2><div class="big">전용 {ex['exclusive_area_m2']:g}㎡</div><p>전용 ≈ 18.1평<br>공급 84.46㎡ ≈ 25.5평</p><div class="fine">LH 2025 팸플릿 PDF 9쪽<br>분양 계획도 · 논문 표본단지 아님<br>발코니 확장형 · 시공과 다를 수 있음</div></div>'''+note('59A의 실제 전용면적은 59.92㎡입니다. 공급 = 전용 + 주거공용 · 평면에 표시된 확장 발코니는 전용면적과 구분합니다.')
        if k==2:
            return study('R2','소득과 자산을 함께 구분',['2020년 전국 주거실태조사','주거면적별 자가·임차 선택의 관계'])+svg(house(1040,90,210)+lines(920,400,['소득 조건','보유 자산 조건','필요한 주거면적'],36,step=67,weight=700))+note('조건부 통계 관계입니다. 기존 주택 평가액·부채를 포함한 자산이므로 매수 이전 현금의 인과효과와 다릅니다.')
        if k==0:return svg(room('studio',0,50,670)+room('family',850,60,850)+text(340,535,'독립하며 찾는 공간',33,BLUE,'middle')+text(1270,535,'가족이 함께 쓰는 공간',33,INK,'middle'))+note('주거면적과 임차·매수 선택을 설명하는 가상 상황입니다. 두 방 그림은 실제 분양 평면과 구분합니다.')
        return svg(f'<image href="assets/floorplan59.png" x="70" y="0" width="680" height="555" preserveAspectRatio="xMidYMid meet"/>'+lines(920,120,['같은 지역 안에서도','누가, 얼마를 감당하며','어떤 공간을 찾는가'],44,step=95,weight=700))+note('평면: LH 2025 팸플릿 PDF 9쪽 · 남양주왕숙 A-1 59A 공간 설명 예시 · R2의 표본단지 평면이 아닙니다.')
    if n=='L004':
        if k==0:
            return svg(apt(0,40,25,275)+room('family',560,120,620)+apt(2,1380,25,275)+text(180,475,'기존 집을 비움',30,INK,'middle')+text(870,475,'그동안 살 다른 집',30,BLUE,'middle')+text(1520,475,'새집 입주',30,INK,'middle')+f'<path class="draw-line" d="M180 550H1520" stroke="{BLUE}" stroke-width="5" fill="none"/>'+text(870,610,'이주와 준공 사이의 시간',28,MUTED,'middle'))+note('일반적인 사건 순서를 그린 개념도입니다. 건물은 실제 가락시영의 외관이 아니며 기간·지리 비례가 없습니다.')
        if k==1:
            return study('R3','가락시영 재건축 이주',['분석: 2011Q1–2014Q4','주요 이주: 2012년 8월–2013년 5월'])+svg(text(920,170,'2012.8',64,INK,weight=700)+text(1440,170,'2013.5',64,BLUE,weight=700)+f'<path class="draw-line" d="M930 250H1650" stroke="{BLUE}" stroke-width="10" fill="none"/>'+lines(920,370,['원래 살던 곳','실제 이주한 목적지','목적지의 주택가격'],35,step=76,weight=700))+note('실제 이주 사례를 분석한 논문입니다. 이 화면은 목적지별 유입량을 표시하지 않습니다.')
        if k==2:
            return svg(lines(40,75,['과거의 목적지 분포','도구변수로 유입을 추정'],34,MUTED,step=58)+text(40,285,'59㎡ 아파트',54,INK,weight=700)+text(850,120,'매매가격',34,INK,weight=700)+text(850,260,'↑ 상승 방향',66,BLUE,weight=700)+text(850,385,'환산 임대료',34,INK,weight=700)+text(850,520,'↑ 상승 방향',66,BLUE,weight=700))+note('과거 목적지 분포의 외생성 가정에 의존하는 IV 추정 · OLS 결과와 구분 · 화살표는 효과 크기를 나타내지 않습니다.')
        return svg(apt(1,250,50,280)+room('family',1000,130,700)+text(400,520,'사업지: 거주 가능한 집 일시 감소',30,INK,'middle')+text(1350,520,'목적지: 대체 집을 찾는 수요',30,BLUE,'middle'))+note('문헌 기반 구조 해석 · 실제 목적지·시점·이동량을 결합해 우리 지역에서 검증할 질문입니다.')
    if n=='L005':
        if k==0:
            out=''
            for x,removed,net,label in [(80,800,200,'기존 800가구가 있던 부지'),(1000,0,1000,'기존 주택이 없던 부지')]:
                out+=apt(2,x+150,0,190)+text(x,335,label,31,INK,weight=700)+text(x,425,f'1,000 − {removed:,} = {net:,}',53,BLUE,weight=700)+text(x,500,f'순증 {net:,}가구',33,MUTED)
            return svg(out)+note('가상 산술 예시 · 같은 지역·같은 시점·같은 유형의 주택 재고를 비교한다고 가정합니다. 실제 사업 수치가 아닙니다.')
        if k==2:
            return study('R4','준공 직후와 이후를 구분',['2017–2023년 서울 신규 전세 계약','정비사업 2015–2023년 · 거리·상대 시점'])+svg(apt(2,1110,0,260)+lines(920,450,['준공 직후','시간이 지난 뒤','거리별로 다른 관계'],32,step=62,weight=700))+note('한국주택금융공사 주택금융연구 9권 1호 135–157페이지에서 인용 · 논문 결과를 자체 문장으로 요약합니다.')
        if k==3:return svg(apt(2,170,25,290)+lines(850,90,['필요한 면적이 맞는가','감당할 가격인가','필요한 날 들어갈 수 있나'],44,step=135,weight=700))+note('준공 총량에서 실제 선택 조건으로 이어가는 질문 · 지역별 공급 부족·과잉을 판정한 결과가 아닙니다.')
        return svg(apt(1,80,40,270)+apt(2,760,40,270)+lines(1200,140,['철거·멸실','공급 공백','준공과 입주'],43,step=98,weight=700)+text(200,535,'집을 비우는 날',30,INK)+text(800,535,'들어갈 수 있는 날',30,BLUE))+note('시간 순서 개념도 · 관리처분인가와 실제 철거일은 다릅니다. 영구적 공급 효과를 확정한 화면이 아닙니다.')
    if n=='L006':
        if k==0:
            s=house(25,160,150)+f'<path d="M245 230H1430M245 440H1430" stroke="#C7D6D4" stroke-width="14" fill="none"/>'
            for x,y,label in [(360,230,'집 앞 정류장'),(820,230,'환승'),(1250,230,'직장'),(360,440,'역'),(1250,440,'직장')]:
                s+=f'<circle cx="{x}" cy="{y}" r="18" fill="{BLUE}"/>'+text(x,y+67,label,28,MUTED,'middle')
            s+=text(1590,245,'A',54,BLUE,'middle',700)+text(1590,455,'B',54,BLUE,'middle',700)+text(800,75,'지도상 거리 + 걷기 · 대기 · 환승',43,INK,'middle',700)
            return svg(s)+note('접근성 설명용 개념도 · 실제 노선·통근 시간·직장 수를 표시하지 않습니다.')
        if k==1:
            return study('R5','사업체 수와 통근 연결의 차이',['2019년 수도권 읍·면·동 단면 분석','DIT 상호작용 지수 ↔ ㎡당 아파트 가격'])+svg(''.join(f'<path d="M1300 240L{x} {y}" stroke="#A2BBB7" stroke-width="{w}"/>'+house(x-45,y-40,85) for x,y,w in [(970,100,3),(1600,80,6),(1010,470,5),(1620,480,9)])+house(1240,180,140)+text(1300,575,'실제 통근 흐름의 상호작용',29,BLUE,'middle',700))+note('상호작용 지수 DIT는 도달 가능한 일자리 수나 통근 시간과 다릅니다. 단면의 양의 관계를 인과효과로 보지 않습니다.')
        if k==3:
            return study('R6','실제로 얼마나 쉽게 닿는가',['수도권 교통 접근성 · 2023년 보고서','보행·대기·환승·시간대를 함께 고려'])+svg(lines(1000,120,['걷는 시간','기다리는 시간','갈아타는 조건','이용하는 시간대'],42,step=105,weight=700))+note('ITF의 접근성 분석 보고서입니다. 주택가격 회귀나 철도 개통 후 상승률을 추정한 논문이 아닙니다.')
        if k==2:return svg(text(80,95,'통근 흐름의 연결',49,BLUE,weight=700)+text(950,95,'이동의 편의',49,INK,weight=700)+lines(80,270,['지역 간 출근 유입과 유출','DIT 상호작용 지수'],34,step=84)+lines(950,270,['내 출발지에서 목적지까지','걷기·대기·환승·시간대'],34,step=84)+text(80,535,'서로 다른 값을 구분해 봅니다',39,MUTED,weight=700))+note('통근 상호작용의 단면 관계로 새 철도 노선의 가격 효과를 계산하지 않습니다.')
        return svg(room('studio',0,80,700)+lines(960,135,['같은 출근 조건에서','감당 가능한 비용으로','선택할 수 있는 집은?'],44,step=95,weight=700))+note('통근 연결과 이동 편의는 구분해 확인합니다. 특정 철도 개통의 가격 효과나 미래 상승률을 단정하지 않습니다.')
    if n=='L007':
        filters=['면적 · 비용','입주 날짜','직장 접근성'];counts=[9,6,4,3];stage=[0,2,3][min(k,2)]
        s=''
        for i in range(9):
            s+=house(40+(i%3)*225,40+(i//3)*185,115,opacity=1 if i<counts[stage] else .14)
        for i,label in enumerate(filters):
            s+=text(1000,145+i*125,('✓ ' if stage>i else '')+label,46,BLUE if stage>i else MUTED,weight=700)
        s+=text(1000,565,f'후보 {counts[stage]}개',64,BLUE,weight=700)
        return svg(s)+note('선택 조건을 설명하는 가상 예시 · 후보 개수와 색상은 실제 지역의 주택 수나 선호 비중이 아닙니다.')
    # L008: do not repeat the opening chart. Distinguish observation and tests.
    topics=[('관측한 차이','서울과 경기의 고점 회복 시점'),('찾아볼 수요','가구 · 연령별 이동 · 면적별 거래'),('찾아볼 공급','준공 − 멸실 · 이주 목적지와 시점'),('연결할 조건','통근 흐름 · 실제 교통 접근성')]
    focus=min(k,len(topics)-1)
    s=''
    for i,(head,body) in enumerate(topics):
        y=80+i*135;s+=text(30,y,head,30,BLUE if i==focus else MUTED,weight=700)+text(420,y,body,40,INK,weight=700)+f'<path d="M30 {y+45}H1690" stroke="#D1DAD4"/>'
    return svg(s)+note('앞부분의 가격 차이는 관측 결과이며, 수요·공급·접근성의 원인별 기여율은 앞으로 검증할 대상입니다.')

STYLE='''
.scene{position:absolute;inset:0;color:#173348}.scene *{box-sizing:border-box}.brand{position:absolute;left:80px;top:36px;font-size:22px}.series{position:absolute;right:80px;top:40px;font-size:18px;color:#526872}.rule{position:absolute;top:86px;left:80px;right:80px;height:1px;background:#D2DCD6}.chapter{position:absolute;top:121px;left:80px;font-size:24px;color:#526872}.panel{position:absolute;inset:0}.panel h1{position:absolute;left:80px;top:171px;right:80px;font-size:54px;line-height:1.23;letter-spacing:-1.4px;margin:0;font-weight:700;word-break:keep-all}.picture{position:absolute;left:80px;right:80px;top:280px;height:620px}.stage{position:absolute;inset:0;width:100%;height:100%;font-family:inherit;overflow:visible}.qualifier{position:absolute;left:0;right:0;top:620px;font-size:20px;line-height:1.3;color:#526872;word-break:keep-all}.study{position:absolute;left:0;top:0;width:810px;border-left:5px solid #286CDA;padding:20px 34px;background:#EEEDE6}.overline{font-size:25px;line-height:1.3;color:#526872}.study h2{font-weight:700;line-height:1.3;letter-spacing:-.6px;margin:17px 0;word-break:keep-all}.journal{font-size:23px;color:#526872;line-height:1.5}.focus{font-size:37px;font-weight:700;color:#286CDA;margin:30px 0 20px}.study p{font-size:26px;line-height:1.7;margin:0}.floorplan{position:absolute;left:0;top:0;width:900px;height:596px;background:#FFF;border:1px solid #D7DDD8;padding:10px}.floorplan img{width:100%;height:100%;object-fit:contain}.floor-meta{position:absolute;left:960px;right:0;top:16px}.floor-meta h2{font-size:40px;line-height:1.3;margin:18px 0 25px}.floor-meta .big{font-size:55px;font-weight:700;color:#286CDA}.floor-meta p{font-size:29px;line-height:1.65}.floor-meta .fine{font-size:22px;line-height:1.5;color:#526872}
'''

def split_caption(s):
    # Split on complete words and clauses. Never cut a Korean name, date or unit.
    protected=['Chulhee Lee 님','Elliot Kang 님','이준민 님','심승규 님','홍지훈 님','서문규 님','정재엽 님','이효중 님','유건호 님','강명구 님','김선정 님','남진 님']
    for phrase in protected:s=s.replace(phrase,phrase.replace(' ','\u00a0'))
    s=re.sub(r'\d{4}년\s+(?:\d{1,2}월|\d분기)',lambda m:m[0].replace(' ','\u00a0'),s)
    words=s.split(' ');result=[];line=''
    for word in words:
        if line and len(line)+len(word)+1>48:result.append(line);line=word
        else:line+=((' ' if line else '')+word)
    if line:result.append(line)
    return [c.replace('\u00a0',' ') for c in result]

def main():
    global SOURCES,PRICE,ROOM_XML,FLOOR
    for d in [P/'assets/fonts',P/'compositions',OUT/'checks',EP/'director/readable-video-v2']:d.mkdir(parents=True,exist_ok=True)
    source=OUT/'approved_working_scenes.json'
    scenes=json.loads(source.read_text('utf-8'))['scenes']
    SOURCES=json.loads((Path(__file__).parent/'references.json').read_text('utf-8'))
    FLOOR=json.loads((EP/'research/readable-v2/floorplan_facts.json').read_text('utf-8'))
    assert FLOOR['status']=='verified' and FLOOR['examples'], 'Verified architectural example required'
    shutil.copy2(Path(FLOOR['examples'][0]['additional_image_file']),P/'assets/floorplan59.png')
    for name in ['Pretendard-Regular.woff2','Pretendard-Bold.woff2']:shutil.copy2(HOMES/'assets/fonts'/name,P/'assets/fonts'/name)
    shutil.copy2(HOMES/'assets/gsap.min.js',P/'assets/gsap.min.js')
    PRICE=json.loads((OLD/'assets/price_data.json').read_text('utf-8'))
    h=(HOMES/'compositions/home-space.html').read_text('utf-8')
    a=h.index('<svg viewBox=',h.index('id="world"'));b=h.index('</svg></div>',a)
    ROOM_XML=ET.fromstring(h[a:b+6])
    root=ET.parse(EP/'visual/relocation-space-v1/apartment-stages.svg').getroot()
    for panel,ident in enumerate(['old-apartment','under-construction','new-apartment']):
        node=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','viewBox':f'{panel*300} 0 300 420'})
        for e in root:
            if e.tag.endswith('defs') or e.get('id')==ident:node.append(copy.deepcopy(e))
        ET.ElementTree(node).write(P/f'assets/apartment-{panel}.svg',encoding='unicode')
    totalframes=0;caps=[];result=[];hosts=[]
    for scene in scenes:
        sid=scene['id'];panels=[];motion=[];beatlist=[];local=0
        for idx,p in enumerate(scene['paragraphs']):
            tx=p['text'];chunks=split_caption(tx)
            # Provisional silent review pacing; actual Jun delivery is intentionally not generated.
            frames=max(150,round(len(tx)/6.2*30));dur=frames/30
            beat={'id':f'{sid}-P{idx+1}','start':local/30,'duration':dur,'text':tx,'source_ids':p['source_ids']}
            beatlist.append(beat)
            cumulative=0;weights=[len(c.replace(' ','')) for c in chunks];sw=sum(weights)
            for j,(chunk,weight) in enumerate(zip(chunks,weights)):
                cf=(frames-cumulative) if j==len(chunks)-1 else max(1,round(frames*weight/sw))
                caps.append({'scene_id':sid,'beat_id':beat['id'],'start':(totalframes+local+cumulative)/30,'end':(totalframes+local+cumulative+cf)/30,'text':chunk,'source_ids':p['source_ids']})
                cumulative+=cf
            headline=p.get('screen_headline') or scene['headline']
            # A distinct thought gets a distinct screen. Header persists to avoid slide-like resets.
            visualhtml=visual(scene,idx,p)
            panels.append(f'<section class="clip panel" id="{sid}-p{idx}" data-start="{local/30}" data-duration="{dur}" data-track-index="1"><div class="panel-content"><h1>{E(headline)}</h1><div class="picture">{visualhtml}</div></div></section>')
            at=local/30
            motion.append(f"tl.fromTo('#{sid}-p{idx} .picture',{{opacity:0,y:7}},{{opacity:1,y:0,duration:.65,ease:'sine.out'}},{at});")
            if sid=='L002' and idx==0:
                phrase=tx.index('자녀가 독립')/len(tx)*dur
                motion.append(f"tl.fromTo('#{sid}-p{idx} .new-home',{{opacity:0}},{{opacity:1,duration:1.5,ease:'sine.inOut'}},{at+phrase});")
                motion.append(f"tl.set('#{sid}-p{idx} .family-after',{{opacity:0}},0);tl.set('#{sid}-p{idx} .family-after',{{opacity:1}},{at+phrase+.75});tl.set('#{sid}-p{idx} .family-before',{{opacity:0}},{at+phrase+.75});")
                motion.append(f"tl.fromTo('#{sid}-p{idx} .child-cup-old',{{opacity:1}},{{opacity:0,duration:.5,ease:'sine.inOut',immediateRender:false}},{at+phrase+.25});")
            if sid=='L002' and idx==1:motion.append(f"tl.set('#{sid}-p{idx} .child-cup-old',{{opacity:0}},0);")
            if sid=='L001' and idx==1:
                change=tx.index('이 자체 지수에서 서울은')/len(tx)*dur
                motion.append(f"tl.fromTo('#{sid}-p{idx} .recovery-view',{{opacity:0}},{{opacity:1,duration:.8,ease:'sine.inOut'}},{at+change});tl.fromTo('#{sid}-p{idx} .history-view',{{opacity:1}},{{opacity:0,duration:.8,ease:'sine.inOut',immediateRender:false}},{at+change});")
            motion.append(f"document.querySelectorAll('#{sid}-p{idx} .draw-line').forEach(el=>{{const n=el.getTotalLength();el.style.strokeDasharray=n;tl.fromTo(el,{{strokeDashoffset:n}},{{strokeDashoffset:0,duration:{min(4,dur*.28)},ease:'sine.inOut'}},{at+.5});}});")
            local+=frames
        if scene is scenes[-1]:
            # Extend only the final frame, never a preceding caption.
            local+=90
            panels[-1]=panels[-1].replace(f'data-duration="{dur}"',f'data-duration="{dur+3}"')
        duration=local/30
        scoped_style=STYLE.replace('.scene *','*').replace('.scene{','#root{')
        composition=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template><style>{scoped_style}</style><div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{duration}"><div class="brand">데이터로 보는 부동산</div><div class="series">근거로 읽는 집값</div><div class="rule"></div><div class="chapter">{sid[-1]} / 8 · {E(scene['title'])}</div>{''.join(panels)}</div><script>(()=>{{const tl=gsap.timeline({{paused:true}});{''.join(motion)}window.__timelines['{sid}']=tl;}})();</script></template></body></html>'''
        (P/f'compositions/{sid}.html').write_text(composition,'utf-8')
        hosts.append(f'<div class="clip" id="host-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-width="1920" data-height="1080" data-start="{totalframes/30}" data-duration="{duration}" data-track-index="1"></div>')
        result.append({'id':sid,'title':scene['title'],'start':totalframes/30,'duration':duration,'beats':beatlist})
        totalframes+=local
    duration=totalframes/30
    footers={s['id']:' · '.join(SOURCES[r]['short'] for r in s['references'] if r in SOURCES) if s['id']!='L007' else '문헌 R1–R6를 연결한 종합 해석 · 연결 전체의 인과효과·지역별 기여율을 검증한 결과가 아닙니다.' for s in scenes}
    footers['L006']='김선정 님·남진 님(2022), 국토계획 57(5) · 국제교통포럼(2023), ITF Policy Papers No.117'
    caphtml='''<!doctype html><html lang="ko"><body><template><style>#captions{position:absolute;inset:0}#caption-box{position:absolute;left:80px;right:80px;top:942px;height:70px;background:#FFF;border-radius:12px;display:flex;align-items:center;justify-content:center;padding:8px 30px}#caption-text{font-size:32px;line-height:1.25;color:#173348;text-align:center;word-break:keep-all}#source{position:absolute;left:80px;right:80px;bottom:21px;font-size:18px;line-height:1.35;color:#526872;word-break:keep-all}</style><div id="captions" data-composition-id="captions" data-duration="DURATION" data-width="1920" data-height="1080"><div id="caption-box"><span id="caption-text"></span></div><div id="source"></div></div><script>(()=>{const cues=CUES;const scenes=SCENES;const footers=FOOTERS;const clock={t:0};const tl=gsap.timeline({paused:true});tl.to(clock,{t:DURATION,duration:DURATION,ease:'none',onUpdate:()=>{let c=cues.find(x=>x.start<=clock.t&&x.end>clock.t);let s=scenes.find(x=>x.start<=clock.t&&x.start+x.duration>clock.t);document.getElementById('caption-text').textContent=c?c.text:'';document.getElementById('caption-box').style.opacity=c?'1':'0';document.getElementById('source').textContent=s?footers[s.id]:'';}},0);window.__timelines['captions']=tl;})();</script></template></body></html>'''
    for key,value in [('DURATION',str(duration)),('CUES',json.dumps(caps,ensure_ascii=False)),('SCENES',json.dumps(result,ensure_ascii=False)),('FOOTERS',json.dumps(footers,ensure_ascii=False))]:caphtml=caphtml.replace(key,value)
    (P/'compositions/captions.html').write_text(caphtml,'utf-8')
    hosts.append(f'<div class="clip" id="caption-host" data-track-kind="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-width="1920" data-height="1080" data-start="0" data-duration="{duration}" data-track-index="2"></div>')
    index=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>같은 수도권, 다른 집값 회복</title><script src="assets/gsap.min.js"></script><style>@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2');font-weight:400}}@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}}html,body{{margin:0;width:100%;height:100%;background:#F6F4EF;font-family:Pretendard,sans-serif}}#root{{position:relative;width:100%;height:100%;overflow:hidden}}.clip{{position:absolute;inset:0}}</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{duration}" data-fps="30">{''.join(hosts)}</div><script>window.__timelines['main']=gsap.timeline({{paused:true}});</script></body></html>'''
    (P/'index.html').write_text(index,'utf-8')
    dump(P/'hyperframes.json',{'authoringSkill':'general-video','paths':{'assets':'assets','blocks':'compositions','components':'components'}})
    dump(P/'timing.json',{'revision':'readable-video-v2','duration':duration,'frames':totalframes,'fps':30,'provisional':True,'narration_on_hold':True,'scenes':result,'captions':caps})
    dump(P/'assets/references.json',SOURCES)
    dump(P/'assets/floorplan_facts.json',FLOOR)
    shutil.copy2(source,OUT/'scene_script.json')
    clean=['# 같은 수도권인데, 집값은 왜 다르게 움직일까?','', '가독성 수정본 v2 · 2026-10-25','', '이야기 순서: 가격 차이 → 가구의 분리 → 공간과 거주 방식 → 재건축 이주 → 순증 공급 → 직장 접근성 → 실제 선택지.','', '저자 소개는 개인별 ‘님’ 표기입니다. 각 장 끝 참고 링크는 읽지 않습니다. 상세 제목·서지·연구 범위는 [인용자료](인용자료.md)에 정리했습니다.','']
    for s in scenes:
        clean+=['## '+s['title'],'']
        for para in s['paragraphs']:clean +=[para['text'],'']
        refs=' / '.join(f'[{r}](인용자료.md#{r.lower()})' for r in s['references'])
        clean+=['참고: '+refs,'']
    (OUT/'대본.md').write_text('\n'.join(clean),'utf-8')
    def stamp(seconds):
        ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (OUT/'검토용_임시자막.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"]+5)} --> {stamp(c["end"]+5)}\n{c["text"]}' for i,c in enumerate(caps,1))+'\n','utf-8')
    (P/'BRIEF.md').write_text('''---\nworkflow: general-video\nflow: automation\nlanguage: ko\naspect: 1920x1080\n---\n2026-10-25 사용자가 대본의 가독성 개선, 저자 존칭과 상세 인용, 대표 실제 평면을 요청하고 영상 제작까지 명시 지시했다. 전체 8장을 새 대본과 집 중심 화면으로 제작한다. 기존 음성 생성 보류는 유지한다. 로컬 검토용 전체 MP4이며 게시 승인이나 유료 생성 승인이 아니다.\n''','utf-8')
    print(json.dumps({'duration':duration,'total_with_brand':duration+15,'scenes':len(scenes),'paragraphs':sum(len(s['paragraphs']) for s in scenes),'captions':len(caps)},ensure_ascii=False))

if __name__=='__main__':main()
