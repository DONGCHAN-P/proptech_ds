from pathlib import Path
import json,shutil,html,importlib.util,xml.etree.ElementTree as ET,re,math
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/guide-v3';P=O/'project'
spec=importlib.util.spec_from_file_location('old_visual_helpers',EP/'editor/readable-video-v2/build.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
E=lambda s:html.escape(str(s),quote=True)
INK='#173348';BLUE='#286CDA';MUTED='#526872';GOLD='#967536';SAGE='#E4ECE5'
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
T=old.text;L=old.lines
def canvas(s):return '<svg class="diagram" viewBox="0 0 1760 600">'+s+'</svg>'
def icon(kind,x,y,c=BLUE,scale=1):
    paths={
      'home':'<path d="M2 32L35 4l33 28v36H8V32M27 68V43h18v25M17 34h13v12H17"/>',
      'calendar':'<rect x="5" y="12" width="60" height="54" rx="7"/><path d="M5 29h60M20 4v18M50 4v18M17 41h10m10 0h10M17 53h10m10 0h10"/>',
      'ruler':'<path d="M6 22h60v28H6ZM16 22v10m12-10v16m12-16v10m12-10v16"/>',
      'money':'<rect x="3" y="15" width="65" height="45" rx="6"/><circle cx="35" cy="37" r="12"/><path d="M12 25h6m36 24h6"/>',
      'job':'<rect x="4" y="21" width="62" height="44" rx="6"/><path d="M24 21V8h23v13M4 36q31 18 62 0M30 42h11v11H30"/>',
      'train':'<rect x="13" y="2" width="47" height="57" rx="9"/><path d="M21 12h30v22H21M21 65l-8 9m38-9 8 9"/><circle cx="25" cy="46" r="3"/><circle cx="48" cy="46" r="3"/>',
      'clock':'<circle cx="35" cy="35" r="30"/><path d="M35 13v24l17 10"/>',
      'file':'<path d="M12 3h30l17 17v49H12ZM42 3v20h17M22 35h27M22 47h27M22 59h18"/>',
      'chart':'<path d="M7 5v60h62M16 52l15-19 13 7 21-29"/>',
      'key':'<circle cx="20" cy="24" r="15"/><path d="M32 34l32 32m-12-12 10-10m-21-1 10-10"/>',
      'play':'<rect x="4" y="13" width="62" height="46" rx="12"/><path d="M29 24l18 12-18 12Z"/>',
      'like':'<path d="M24 31l13-24q15 1 9 24h18v31H24ZM7 31h17v31H7Z"/>',
    }
    return f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{paths.get(kind,paths["home"])}</g>'
def pill(x,y,label,active=False,w=370):
    return f'<rect x="{x}" y="{y}" width="{w}" height="88" rx="14" fill="{BLUE if active else SAGE}"/>'+T(x+w/2,y+56,label,30,'#FFF' if active else INK,'middle',700)
def link(x1,y1,x2,y2,color='#AAC0B9',dash=False):return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="4" fill="none"'+(' stroke-dasharray="10 9"' if dash else '')+'/>'
def qualifier(s):return '<div class="qualifier">'+E(s)+'</div>'
def studybar(rid):
    r=REFS[rid]
    return '<div class="studybar"><div class="authors">'+E(r['display_authors'])+' · '+str(r['year'])+'</div><div class="paper-title">'+E(r['title'])+'</div></div>'
def photo(aid,focus):
    return f'<div class="photo"><img src="assets/images/{aid}.png"/><div class="photo-shade"></div><div class="photo-focus">{E(focus)}</div><div class="ai-label">AI 개념 이미지 · 실제 장소 아님</div></div>'
def trio(labels,types,phase):
    out=''
    for i,(label,typ) in enumerate(zip(labels,types)):
        x=190+i*565;c=BLUE if i==phase else MUTED
        out+=f'<circle cx="{x+90}" cy="210" r="112" fill="{SAGE if i!=phase else "#DDE8FA"}"/>'+icon(typ,x+38,155,c,1.5)+T(x+90,390,label,43,c,'middle',700)
    return canvas(out)
def mode_for(pid,j,n):
    # Named semantic destinations. A photo establishes context once; subsequent units explain the mechanism.
    mapping={
      'L001-P1':'questions','L001-P2':'price','L001-P3':'questions',
      'L002-P1':'population','L002-P2':'households','L002-P3':'migration','L002-P4':'directions',
      'L003-P1':'tenure','L003-P2':'floorplan','L003-P3':'tenure','L003-P4':'wealth',
      'L004-P1':'timeline','L004-P2':'case','L004-P3':'identification','L004-P4':'assumption',
      'L005-P1':'arithmetic','L005-P2':'gap','L005-P3':'relative_time','L005-P4':'requirements',
      'L006-P1':'route','L006-P2':'network','L006-P3':'distinction','L006-P4':'journey','L006-P5':'current_plan',
      'L007-P1':'filters','L007-P2':'filters','L007-P3':'matching',
      'L008-P1':'nexttests','L008-P2':'matching_test','L008-P3':'cta'}
    return mapping[pid]
def content(mode,pid,j,n,u,previous):
    phase=min(2,int(j/max(1,n)*3));tx=u['spoken_text'];focus=u['focus']
    if mode=='questions':
        if pid=='L001-P1' and j==0:
            s=T(220,120,'서울',52,BLUE,weight=700)+T(1100,120,'경기',52,GOLD,weight=700)+icon('chart',220,190,BLUE,2)+icon('chart',1100,190,GOLD,2)+T(220,455,'이전 고점 이상으로 회복',42,BLUE,weight=700)+T(1100,455,'이전 고점 아래',42,GOLD,weight=700)
            return canvas(s)+qualifier('출발점: 자체 실거래 지수의 서로 다른 회복 경로 · 2006Q1–2026Q2'),['D1']
        if pid=='L001-P1':return trio(['인구 이동?','새집 공급?','출근의 편의?'],['home','calendar','train'],phase),[]
        s=''
        for i,(label,scope) in enumerate([('가구와 주거비','R1 · R2'),('이주와 순증','R3 · R4'),('통근과 접근성','R5 · R6')]):
            x=85+i*570;s+=f'<rect x="{x}" y="70" width="460" height="420" rx="12" fill="{SAGE if i!=phase else "#DDE8FA"}"/>'+icon('file',x+175,115,BLUE if i==phase else MUTED,1.5)+T(x+230,340,label,38,INK,'middle',700)+T(x+230,415,scope,29,MUTED,'middle')
        return canvas(s)+qualifier('논문 5편과 기관 보고서 1편을 이 순서로 살펴봅니다.'),[]
    if mode=='price':
        z=any('2021년' in v['spoken_text'] for v in previous+[u]);markup=old.price_chart(z).replace('class="stage"','class="diagram"')
        return markup+qualifier('자체 명목 지수 · 동일 단지·면적군 연결 · 공식 지수 아님'),['D1']
    if mode=='population':
        apart=any('독립' in v['spoken_text'] for v in previous+[u])
        family=old.room('family',0,60,900)
        if apart:family=family.replace('class="child-cup-old"','class="child-cup-old" style="opacity:0"')
        s=family+('<g class="new-house">'+old.room('studio',1030,110,650)+'</g>' if apart else '')
        s+=T(850,30,'인구 3명   ·   '+('가구 1 → 2' if apart else '가구 1'),43,BLUE,'middle',700)
        s+=T(440,550,'부모 · 기존 집에 거주' if apart else '부모 + 성인 자녀',29,INK,'middle')
        if apart:s+=T(1350,550,'자녀의 독립된 집',29,BLUE,'middle')
        return canvas(s)+qualifier('설명용 가상 예시 · 같은 세 사람의 거처가 한 집에서 두 집으로 나뉩니다.'),['accepted_household_cutaway']
    if mode=='households':
        return trio(['인구의 총수','가구의 구성','필요한 주거공간'],['chart','home','ruler'],phase)+qualifier('사람 수와 함께 가구의 분리·연령·필요 공간을 살펴보는 설명입니다.'),[]
    if mode in ('migration','directions'):
        s=icon('money',185,110,BLUE,2)+icon('home',1300,110,INK,2)
        s+=T(265,330,'주거비 상승',48,BLUE,'middle',700)+T(1385,330,'청년층 전출',48,INK,'middle',700)
        s+=link(520,210,1110,210,BLUE)+T(810,185,'관련성 관찰' if mode=='migration' else '어느 방향의 관계인가?',35,MUTED,'middle',700)
        s+=T(810,460,'2005–2010년 수도권 취업자 · 청년 25–39세' if mode=='migration' else '높은 주거비가 이동을 유발했을 가능성도 확인합니다.',33,MUTED,'middle')
        return studybar('R1')+canvas(s)+qualifier('관찰된 관계 · 현재 서울 매매가격의 원인을 확정한 결과는 아닙니다.'),['R1']
    if mode=='floorplan':
        ex=FLOOR['examples'][0]
        a=BLUE if j<3 else INK;b=BLUE if j>=3 else MUTED
        s=f'<div class="floor-labels"><div class="eyebrow">LH 공식 분양 평면</div><h2>남양주왕숙 A-1<br>59A</h2><div style="color:{a}" class="area">전용 59.92㎡</div><p>약 18.1평</p><div style="color:{b}" class="area">공급 84.46㎡</div><p>약 25.5평</p><small>전용 + 주거공용 = 공급<br>분양 계획도 · 논문 표본단지 아님</small></div>'
        return s+qualifier('LH 2025 팸플릿 PDF 9쪽 · 발코니 확장형 · 도면의 확장 발코니는 전용면적과 구분합니다.'),['FP59']
    if mode=='tenure':
        selected=0 if ('작은' in tx or '독립한' in tx) else 1 if ('넓은' in tx or '가족이 늘' in tx) else -1
        cells=[('작은 공간','임차'),('큰 공간','임차'),('작은 공간','자가'),('큰 공간','자가')];s=''
        for i,(a,b) in enumerate(cells):
            x=230+(i%2)*790;y=40+(i//2)*260;active=i==selected
            s+=f'<rect x="{x}" y="{y}" width="630" height="220" rx="15" fill="{"#DDE8FA" if active else SAGE}"/>'+icon('ruler' if i<2 else 'key',x+40,y+55,BLUE if active else MUTED,1.1)+T(x+155,y+85,a,34,INK,weight=700)+T(x+155,y+155,b,48,BLUE if active else MUTED,weight=700)
        return (studybar('R2') if pid=='L003-P3' else '')+canvas(s)+qualifier('면적과 자가·임차를 함께 구분합니다. 칸의 크기는 확률이나 거래 비중을 뜻하지 않습니다.'),['R2'] if pid=='L003-P3' else []
    if mode=='wealth':
        s=pill(40,90,'기존 주택의 평가액',phase==0,470)+pill(640,90,'부채 효과 포함',phase==1,470)+pill(1240,90,'소득 조건',phase==2,470)
        s+=link(280,178,880,360)+link(880,178,880,360)+link(1470,178,880,360)+icon('file',820,320,BLUE,1.5)+T(880,530,'매수하기 전의 현금·순자산과 구분',46,BLUE,'middle',700)
        return canvas(s)+qualifier('R2의 총자산 변수에 관한 해석 범위 · 소득 증가의 인과효과로 읽지 않습니다.'),['R2']
    if mode in ('timeline','gap'):
        s=''
        labels=['기존 집을 비움','그동안 살 다른 집','새집 입주']
        for i,label in enumerate(labels):
            x=270+i*600;s+=icon(['key','calendar','home'][i],x-50,110,BLUE if i==phase else MUTED,1.7)+T(x,350,label,40,BLUE if i==phase else INK,'middle',700)
        s+=link(270,440,1470,440,BLUE)+T(870,530,'이주와 입주 사이에도 살 집이 필요합니다',37,MUTED,'middle')
        return canvas(s)+qualifier('시간 순서 개념도 · 실제 기간과 위치의 비례를 표시하지 않습니다.'),[]
    if mode=='case':
        x0,x1=130,1650;xx=lambda m:x0+(x1-x0)*m/48
        s=T(130,70,'분석 기간',29,MUTED)+T(130,130,'2011Q1–2014Q4',48,INK,weight=700)
        s+=f'<rect x="{x0}" y="245" width="{x1-x0}" height="50" rx="12" fill="{SAGE}"/><rect x="{xx(19)}" y="245" width="{xx(29)-xx(19)}" height="50" rx="8" fill="{BLUE}"/>'
        for yr in range(2011,2015):s+=T(xx((yr-2011)*12),350,str(yr),30,MUTED)
        s+=T((xx(19)+xx(29))/2,215,'주요 이주',30,BLUE,'middle',700)+T(880,460,'2012년 8월–2013년 5월',49,BLUE,'middle',700)
        s+=T(880,545,'목적지의 59㎡ 아파트 · 매매가격과 환산 월세',32,MUTED,'middle')
        return studybar('R3')+canvas(s),['R3']
    if mode=='identification':
        phase=2 if any('이 추정에서는' in q['spoken_text'] or '모두 높아지는' in q['spoken_text'] for q in previous+[u]) else 1 if any('과거' in q['spoken_text'] or '도구변수' in q['spoken_text'] for q in previous+[u]) else 0
        if phase==0:
            s=pill(110,190,'이주 유입',True,480)+pill(1140,190,'주택가격',False,480)+link(610,235,1110,235,BLUE)+T(860,170,'방향을 가리기 어려움',34,MUTED,'middle')
        elif phase==1:
            s=pill(70,200,'과거 목적지 분포',True,480)+pill(1140,200,'이주 유입 추정',True,480)+link(580,245,1110,245,BLUE)+T(860,425,'과거의 이동 분포를 활용한 도구변수 추정',40,INK,'middle',700)
        else:s=icon('chart',170,120,BLUE,2)+T(880,65,'IV 추정 결과',37,BLUE,'middle',700)+T(600,170,'매매가격',38,INK,weight=700)+T(600,285,'↑ 상승 방향',65,BLUE,weight=700)+T(1150,170,'환산 월세',38,INK,weight=700)+T(1150,285,'↑ 상승 방향',65,BLUE,weight=700)+T(880,475,'OLS에서는 뚜렷하지 않았던 관계와 구분합니다',34,MUTED,'middle')
        return studybar('R3')+canvas(s)+qualifier('IV 추정은 과거 목적지 분포의 외생성·배제 가정에 의존합니다. 화살표는 효과 크기가 아닙니다.'),['R3']
    if mode=='assumption':
        s=pill(0,160,'과거 목적지',True,420)+pill(670,160,'이주 유입',True,420)+pill(1340,160,'주택가격',True,420)+link(440,205,650,205,BLUE)+link(1110,205,1320,205,BLUE)
        s+=T(880,420,'다른 가격 요인과 얽히지 않는다는 가정',40,MUTED,'middle')+T(880,520,'단일 사건 · 59㎡ 표본 → 서울·경기 전체로 확대하지 않음',33,MUTED,'middle')
        return canvas(s)+qualifier('문헌에서 얻은 후속 질문: 이주 가구가 언제, 어디에서 대체 거처를 찾았는가.'),['R3']
    if mode=='arithmetic':
        subtract=any('팔백' in q['spoken_text'] for q in previous+[u]);net=any('이백' in q['spoken_text'] for q in previous+[u]);s=''
        for idx,(x,removed,total) in enumerate([(80,800,200),(1020,0,1000)]):
            s+=T(x,65,'A · 기존 주택이 있는 부지' if idx==0 else 'B · 기존 주택이 없는 부지',32,INK,weight=700)+icon('home',x+50,120,MUTED,1.6)
            s+=T(x,330,'1,000',92,BLUE,weight=700)
            if subtract:s+=T(x+310,330,'− '+str(removed),72,GOLD,weight=700)
            if net:s+=T(x,485,'순증 '+f'{total:,}'+'채',53,BLUE,weight=700)
        return canvas(s)+qualifier('가상 계산 · 같은 범위·같은 유형의 재고를 비교 · 실제 사업 수치나 가격 효과가 아닙니다.'),['E02']
    if mode=='relative_time':
        labs=['준공 전','준공','준공 직후','시간이 지난 뒤'];s=link(150,280,1590,280)
        for i,label in enumerate(labs):
            x=150+i*480;active=i==min(3,round(j/max(1,n-1)*3));s+=f'<circle cx="{x}" cy="280" r="{20 if active else 12}" fill="{BLUE if active else "#A6BBB2"}"/>'+T(x,380,label,34,BLUE if active else MUTED,'middle',700)
        s+=T(880,100,'2017–2023년 서울 신규 전세 계약',43,INK,'middle',700)+T(880,520,'준공 이후 어느 시점인지 나눠 살펴봅니다',39,BLUE,'middle',700)
        return studybar('R4')+canvas(s)+qualifier('시점·거리별 조건부 관계 · 영구적 순수 공급 효과를 확정한 결과가 아닙니다.'),['R4']
    if mode=='requirements':return trio(['필요한 면적','감당할 가격','입주 가능한 날짜'],['ruler','money','calendar'],phase),[]
    if mode in ('route','journey'):
        stages=['걷기','대기','탑승','환승'];s=''
        for i,label in enumerate(stages):
            x=90+i*450;active=i==min(3,round(j/max(1,n-1)*3));s+=icon(['home','clock','train','train'][i],x+80,100,BLUE if active else MUTED,1.7)+T(x+150,360,label,48,BLUE if active else INK,'middle',700)
            if i<3:s+=link(x+300,200,x+410,200,BLUE)
        s+=T(880,515,'같은 역세권이어도 출근길은 다를 수 있습니다',39,INK,'middle',700)
        return (studybar('R6') if mode=='journey' else '')+canvas(s)+qualifier('접근성 개념도 · 실제 노선·통근 시간·도달 일자리 수를 표시하지 않습니다.'),['R6'] if mode=='journey' else []
    if mode=='network':
        if '사업체 수' in tx or '같은 모형' in tx:
            s=icon('job',160,100,BLUE,2)+T(450,180,'통근 연결',48,BLUE,weight=700)+T(1110,180,'가격과 양의 관계',43,BLUE,weight=700)+icon('home',160,330,MUTED,2)+T(450,410,'사업체 수',48,INK,weight=700)+T(1110,410,'통계적으로 뚜렷하지 않음',37,MUTED,weight=700)
            return studybar('R5')+canvas(s)+qualifier('같은 모형 안의 결과를 비교 · 사업체 수의 효과가 0이라는 뜻은 아닙니다.'),['R5']
        s=icon('job',800,180,BLUE,2)+T(880,430,'통근 유입 · 유출',48,BLUE,'middle',700)
        for i,(x,y) in enumerate([(200,90),(200,430),(1470,90),(1470,430)]):s+=icon('home',x,y,MUTED,1.2)+link(x+100,y+40,820 if i<2 else 960,250)
        s+=T(880,555,'2019년 수도권 읍·면·동 · DIT 상호작용과 가격의 관계',31,MUTED,'middle')
        return studybar('R5')+canvas(s)+qualifier('실제 지리·유입량을 표시한 지도가 아닙니다. 사업체 수의 관계가 뚜렷하지 않았다는 결과를 효과 0으로 읽지 않습니다.'),['R5']
    if mode=='distinction':
        s=icon('job',280,70,BLUE,2)+icon('clock',1180,70,INK,2)+L(110,330,['지역 간 통근 흐름','DIT 상호작용'],43,BLUE,step=90,weight=700)+L(1000,330,['실제로 닿는 편의','보행·대기·환승·시간대'],43,INK,step=90,weight=700)
        return canvas(s)+qualifier('통근 연결 지수와 도달 가능한 일자리 수·이동 시간을 구분합니다. 새 노선의 가격 효과를 계산한 값이 아닙니다.'),['R5']
    if mode=='current_plan':
        s=pill(100,130,'현재 운행 조건',True,620)+pill(1040,130,'앞으로의 계획',False,620)+link(150,315,680,315,BLUE)+link(1090,315,1620,315,BLUE,True)
        s+=T(410,440,'지금 이용할 수 있는가',40,BLUE,'middle',700)+T(1350,440,'언제 이용할 수 있는가',40,MUTED,'middle',700)+T(880,555,'내 직장까지 이어지는 경로를 비교합니다',35,INK,'middle')
        return canvas(s)+qualifier('현재와 계획을 구분하는 질문 · 실제 철도 노선이나 개통 효과를 표시하지 않습니다.'),['R5','R6']
    if mode in ('filters','matching'):
        if pid=='L007-P1':stage=0
        elif pid=='L007-P2':stage=min(3,1+int(j/max(1,n)*3))
        else:stage=3
        counts=[9,6,4,3];s=''
        for i in range(9):
            x=25+(i%3)*280;y=10+(i//3)*185;active=i<counts[stage]
            s+=f'<rect x="{x}" y="{y}" width="225" height="150" rx="12" fill="{SAGE if active else "#F0F0E9"}" opacity="{1 if active else .35}"/>'+icon('home',x+83,y+16,BLUE if active else '#C5CEC5',.75)+T(x+112,y+125,f'후보 {i+1}',26,BLUE if active else '#AEBAB1','middle',700)
        for i,label in enumerate(['면적 · 비용','입주 날짜','직장 접근성']):s+=pill(1060,40+i*140,('✓ ' if stage>i else '')+label,stage>i,610)
        s+=T(1370,565,f'남는 후보 {counts[stage]}개',56,BLUE,'middle',700)
        return canvas(s)+qualifier('가상 선택 예시 · 실제 매물 수나 특정 지역의 충족 비율이 아닙니다.'),['E_selection']
    if mode=='nexttests':return trio(['가구 · 이동','순증 · 이주 시점','통근 · 접근성'],['home','calendar','train'],phase)+qualifier('우리 자료의 가격 경로와 회복 시점에 연결해 추가로 검증할 질문입니다.'),['D1']
    if mode=='matching_test':
        s=''
        for i,label in enumerate(['같은 면적','같은 주택 조건','같은 비교 기간']):s+=pill(30+i*590,160,label,i==phase,530)+icon(['ruler','home','calendar'][i],240+i*590,45,BLUE,1.3)
        s+=T(880,435,'수요 · 공급 · 접근성 자료를 연결',47,BLUE,'middle',700)+T(880,535,'지역별 원인 기여율은 앞으로 확인할 대상입니다',33,MUTED,'middle')
        return canvas(s),['D1']
    if mode=='cta':
        s=icon('play',470,80,BLUE,2.2)+icon('like',1130,80,BLUE,2.2)+T(550,360,'구독',58,BLUE,'middle',700)+T(1210,360,'좋아요',58,BLUE,'middle',700)+T(880,505,'필요한 집의 조건을 데이터로 함께 살펴봅니다',44,INK,'middle',700)
        return canvas(s),[]
    raise ValueError(mode)

STYLE='''#root{position:absolute;inset:0;color:#173348}*{box-sizing:border-box}.brand{position:absolute;left:80px;top:35px;font-size:22px}.series{position:absolute;right:80px;top:39px;font-size:18px;color:#526872}.rule{position:absolute;top:86px;left:80px;right:80px;height:1px;background:#D3DCD6}.section-title{position:absolute;left:80px;top:124px;font-size:25px;color:#526872}.unit{position:absolute;inset:0}.headline{position:absolute;left:80px;right:80px;top:177px;margin:0;font-size:49px;font-weight:700;line-height:1.23;letter-spacing:-1.2px;word-break:keep-all}.content{position:absolute;left:80px;right:80px;top:285px;height:600px}.diagram{position:absolute;inset:0;width:100%;height:100%;font-family:inherit}.qualifier{position:absolute;left:0;right:0;top:606px;font-size:19px;color:#526872;line-height:1.25;word-break:keep-all}.studybar{position:absolute;left:0;right:0;top:0;border-left:4px solid #286CDA;padding:10px 20px;background:#ECEEE7;min-height:90px;z-index:2}.authors{font-size:24px;color:#526872;margin-bottom:5px}.paper-title{font-size:25px;line-height:1.2;word-break:keep-all}.studybar+.diagram{top:110px;height:480px}.photo{position:absolute;inset:0;overflow:hidden;border-radius:3px}.photo img{width:100%;height:100%;object-fit:cover}.photo-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(246,244,239,.97) 0%,rgba(246,244,239,.88) 20%,rgba(246,244,239,.18) 48%,transparent 64%)}.photo-focus{position:absolute;left:45px;top:90px;width:540px;font-size:48px;line-height:1.35;letter-spacing:-1px;font-weight:700;word-break:keep-all}.ai-label{position:absolute;right:22px;bottom:20px;background:rgba(246,244,239,.9);padding:9px 13px;font-size:20px;color:#526872}.floor-image{position:absolute;left:0;top:0;width:1000px;height:590px;background:#FFF;padding:5px;border:1px solid #D4DDD7}.floor-image img{width:100%;height:100%;object-fit:contain}.floor-labels{position:absolute;left:1070px;right:0;top:0}.eyebrow{font-size:23px;color:#526872}.floor-labels h2{font-size:36px;line-height:1.2;margin:12px 0 19px}.area{font-size:42px;font-weight:700}.floor-labels p{font-size:28px;margin:5px 0 16px}.floor-labels small{font-size:21px;line-height:1.45;color:#526872}.chapter-photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.chapter-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(12,29,46,.80),rgba(12,29,46,.38) 54%,rgba(12,29,46,.12))}.chapter-name{position:absolute;left:115px;top:360px;color:#FFF;font-size:86px;font-weight:700;letter-spacing:-2px}.chapter-sub{position:absolute;left:120px;top:315px;color:#D7E0E5;font-size:24px}.chapter-ai{position:absolute;right:80px;top:55px;color:#FFF;font-size:20px}'''

def main():
    global REFS,FLOOR
    sem=json.loads((O/'semantic_units.json').read_text('utf-8'))
    refs=json.loads((P/'assets/references.json').read_text('utf-8'));REFS=refs;old.SOURCES=refs
    old.PRICE=json.loads((EP/'outputs/literature-visual-v1/project/assets/price_data.json').read_text('utf-8'))
    h=(EP/'outputs/household-space-v1/project/compositions/home-space.html').read_text('utf-8');a=h.index('<svg viewBox=',h.index('id="world"'));b=h.index('</svg></div>',a);old.ROOM_XML=ET.fromstring(h[a:b+6])
    FLOOR=json.loads((P/'assets/floorplan_facts.json').read_text('utf-8'));old.FLOOR=FLOOR
    assets=json.loads((O/'assets.json').read_text('utf-8'));chapters={c['scene_id']:c for c in assets['chapters']}
    titles=['가격 회복','인구와 가구','주거 공간','재건축 이주','순증 공급','일자리·통근','선택의 조건','다음 분석']
    oldscenes=json.loads((EP/'outputs/readable-video-v2/scene_script.json').read_text('utf-8'))['scenes']
    sourceparas={f'{s["id"]}-P{i+1}':p for s in oldscenes for i,p in enumerate(s['paragraphs'])}
    photos={'L002-P2':'smallroom','L003-P1':'budget','L004-P1':'relocation','L005-P2':'supply','L006-P1':'commute'}
    caps=[];host=[];rows=[];usage=[];global_frames=0;story=[]
    for si,scene in enumerate(sem['scenes']):
        sid=scene['id'];local=105;panels=[];motion=[];srows=[]
        ch=chapters[sid];impath='assets/images/'+Path(ch['image_file']).name
        panels.append(f'<section class="clip" id="{sid}-chapter" data-start="0" data-duration="3.5" data-track-index="1"><div class="chapter-inner"><img class="chapter-photo" src="{impath}"/><div class="chapter-shade"></div><div class="chapter-sub">데이터로 보는 부동산</div><div class="chapter-name">{si+1}. {E(titles[si])}</div><div class="chapter-ai">AI 개념 이미지</div></div></section>')
        motion.append(f"tl.fromTo('#{sid}-chapter .chapter-name',{{opacity:0,y:9}},{{opacity:1,y:0,duration:.65,ease:'sine.out'}},.1);")
        usage.append({'asset_id':ch['asset_id'],'scene_id':sid,'kind':'chapter','start':global_frames/30,'end':(global_frames+105)/30,'file':impath})
        for para in scene['paragraphs']:
            pid=para['id'];units=para['units'];previous=[];photoframes=0;previous_mode=None
            durations=[round(max(2,len(u['spoken_text'])/6.2)*30) for u in units]
            photo_indices=[]
            if pid in photos:
                for z,f in enumerate(durations[:2]):
                    if sum(durations[q] for q in photo_indices)+f<=360:photo_indices.append(z)
                if photo_indices:
                    ps=local+sum(durations[:photo_indices[0]]);pd=sum(durations[q] for q in photo_indices)
                    panels.append(f'<section class="clip" id="{pid}-photo" data-start="{ps/30}" data-duration="{pd/30}" data-track-index="1"><div class="content">{photo(photos[pid],"")}</div></section>')
            if pid=='L003-P2':panels.append(f'<section class="clip" id="{pid}-plan" data-start="{local/30}" data-duration="{sum(durations)/30}" data-track-index="1"><div class="content"><div class="floor-image"><img src="assets/floorplan59.png" alt="LH 남양주왕숙 A-1 59A 공식 분양 평면"/></div></div></section>')
            for j,u in enumerate(units):
                unitid=f'{pid}-U{j+1:02}';frames=durations[j];duration=frames/30
                mode=mode_for(pid,j,len(units));ids=[]
                if j in photo_indices:
                    aid=photos[pid];body='<div class="photo-focus">'+E(u['focus'])+'</div>';ids=[aid];photoframes+=frames;visualtype='generated_concept_image';mode='photo_'+aid
                    usage.append({'asset_id':aid,'scene_id':sid,'kind':'body_photo','start':(global_frames+local)/30,'end':(global_frames+local+frames)/30,'file':f'assets/images/{aid}.png'})
                else:body,ids=content(mode,pid,j,len(units),u,previous);visualtype='real_plan' if mode=='floorplan' else 'data' if mode=='price' else 'diagram'
                rawsource=sourceparas[pid]['source_ids']
                screen_headline=u['focus']
                if re.search(r'R[1-6]|개인 저자|발행 연도',screen_headline):
                    rid=next((q for q in rawsource if q in refs and q.startswith('R')),None)
                    screen_headline={'R1':'주거비와 청년 이동의 관계','R2':'소득과 자산을 나눠 본 주거 선택','R3':'가락시영 이주 사례의 분석','R4':'준공과 주변 전세가격의 관계','R5':'통근 연결과 주택가격의 관계','R6':'이동·대기·환승까지 보는 접근성'}.get(rid,'연구가 살펴본 대상과 조건')
                r={'id':unitid,'scene_id':sid,'paragraph_id':pid,'start':(global_frames+local)/30,'end':(global_frames+local+frames)/30,'local_start':local/30,'duration':duration,'spoken_text':u['spoken_text'],'display_text':u['display_text'],'focus':u['focus'],'screen_headline':screen_headline,'meaning_boundary':u['reason'],'mode':mode,'asset_ids':ids,'source_ids':rawsource,'visual_type':visualtype,'timing_basis':'provisional_text_weight_after_manual_semantic_boundaries'}
                rows.append(r);srows.append(r);caps.append({k:r[k] for k in ['id','scene_id','paragraph_id','start','end','spoken_text','display_text','source_ids']})
                panels.append(f'<section class="clip unit" id="{unitid}" data-start="{local/30}" data-duration="{duration}" data-track-index="1"><div class="unit-inner"><h1 class="headline">{E(screen_headline)}</h1><div class="content">{body}</div></div></section>')
                if mode!=previous_mode:motion.append(f"tl.fromTo('#{unitid} .content',{{opacity:0}},{{opacity:1,duration:.3,ease:'sine.out'}},{local/30});")
                if mode=='population' and '독립' in u['spoken_text'] and not any('독립' in q['spoken_text'] for q in previous):motion.append(f"tl.fromTo('#{unitid} .new-house',{{opacity:0}},{{opacity:1,duration:1.1,ease:'sine.inOut'}},{local/30});")
                previous.append(u);previous_mode=mode;local+=frames
        if si==7:
            local+=90
            panels[-1]=panels[-1].replace(f'data-duration="{duration}"',f'data-duration="{duration+3}"')
        D=local/30
        body=f'<div class="clip" id="{sid}-chrome" data-start="3.5" data-duration="{D-3.5}" data-track-index="0"><div class="brand">데이터로 보는 부동산</div><div class="series">근거로 읽는 집값</div><div class="rule"></div><div class="section-title">{si+1}. {E(titles[si])}</div></div>'+''.join(panels)
        safe_style=STYLE+'.chapter-ai{background:rgba(12,29,46,.8);padding:8px 12px;border-radius:4px}'
        doc=f'<!doctype html><html lang="ko"><body><template><style>{safe_style}</style><div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{D}">{body}</div><script>(()=>{{const tl=gsap.timeline({{paused:true}});{"".join(motion)}window.__timelines["{sid}"]=tl;}})();</script></template></body></html>'
        (P/f'compositions/{sid}.html').write_text(doc,'utf-8')
        host.append(f'<div class="clip" id="host-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{global_frames/30}" data-duration="{D}" data-track-index="1"></div>')
        story.append({'id':sid,'title':titles[si],'start':global_frames/30,'duration':D,'chapter_duration':3.5,'units':srows});global_frames+=local
    D=global_frames/30;footers={s['id']:' · '.join(refs[r]['short'] for r in s['references']) for s in oldscenes}
    footers['L006']='김선정 님·남진 님(2022), 국토계획 57(5) · 국제교통포럼(2023), ITF Policy Papers No.117'
    footers['L007']='문헌 R1–R6를 연결한 종합 해석 · 원인별 기여율 추정이 아닙니다.'
    end=caps[-1]['end']
    capdoc='''<!doctype html><html lang="ko"><body><template><style>#root{position:absolute;inset:0}#caption-box{position:absolute;left:80px;right:80px;top:926px;height:90px;background:#FFF;border-radius:12px;display:flex;align-items:center;justify-content:center;padding:5px 32px}#caption-text{font-size:31px;line-height:1.25;color:#173348;text-align:center;word-break:keep-all;max-width:1660px;white-space:pre-line}#source{position:absolute;left:80px;right:80px;bottom:21px;font-size:18px;line-height:1.2;color:#526872;word-break:keep-all}</style><div id="root" data-composition-id="captions" data-width="1920" data-height="1080" data-duration="DURATION"><div id="caption-box"><span id="caption-text"></span></div><div id="source"></div></div><script>(()=>{const cues=CUES;const scenes=SCENES;const sources=FOOTERS;const clock={t:0};const tl=gsap.timeline({paused:true});tl.to(clock,{t:DURATION,duration:DURATION,ease:'none',onUpdate:()=>{const c=cues.find(c=>c.start<=clock.t&&clock.t<c.end);const s=scenes.find(s=>s.start<=clock.t&&clock.t<s.start+s.duration);document.getElementById('caption-text').textContent=c?c.display_text:'';document.getElementById('caption-box').style.opacity=clock.t>=CAPEND?'0':'1';document.getElementById('source').textContent=s?(clock.t<s.start+3.5?'AI 개념 이미지 · 주제 전환 배경 · 실제 장소·통계 증거 아님':sources[s.id]):'';}},0);window.__timelines['captions']=tl;})();</script></template></body></html>'''
    capdoc=capdoc.replace("document.getElementById('source').textContent=s?", "const footer=document.getElementById('source');const chapter=s&&clock.t<s.start+3.5;footer.style.color=chapter?'#FFFFFF':'#526872';footer.style.background=chapter?'rgba(12,29,46,.8)':'transparent';footer.style.padding=chapter?'5px 9px':'0';footer.textContent=s?")
    for a,b in [('DURATION',str(D)),('CUES',json.dumps(caps,ensure_ascii=False)),('SCENES',json.dumps(story,ensure_ascii=False)),('FOOTERS',json.dumps(footers,ensure_ascii=False)),('CAPEND',str(end))]:capdoc=capdoc.replace(a,b)
    (P/'compositions/captions.html').write_text(capdoc,'utf-8')
    host.append(f'<div class="clip" id="caption-host" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{D}" data-track-index="2" data-track-kind="captions"></div>')
    index=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>지역별 가격 회복 · 제작 가이드 반영 v3</title><script src="assets/gsap.min.js"></script><style>@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2');font-weight:400}}@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}}html,body{{margin:0;width:100%;height:100%;font-family:Pretendard,sans-serif;background:#F6F4EF}}#root{{position:relative;width:100%;height:100%;overflow:hidden}}.clip{{position:absolute;inset:0}}</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{D}" data-fps="30">{''.join(host)}</div><script>window.__timelines['main']=gsap.timeline({{paused:true}});</script></body></html>'''
    (P/'index.html').write_text(index,'utf-8');dump(P/'hyperframes.json',{'authoringSkill':'general-video','paths':{'assets':'assets','blocks':'compositions','components':'components'}})
    dump(P/'timing.json',{'revision':'guide-v3','duration':D,'frames':global_frames,'fps':30,'provisional':True,'narration_on_hold':True,'scenes':story,'captions':caps,'units':rows,'asset_usage':usage})
    dump(O/'화면설계.json',{'units':rows})
    def stamp(secs):
        ms=round(secs*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (O/'의미단위_임시자막.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"]+5)} --> {stamp(c["end"]+5)}\n{c["display_text"]}' for i,c in enumerate(caps,1))+'\n','utf-8')
    md=['# 같은 수도권인데, 집값은 왜 다르게 움직일까?','','제작 가이드 반영 v3 · 의미 단위별 낭독 대본','', '줄바꿈은 문장·절·짧은 완결구절의 호흡입니다. 원문은 v2에서 보존했으며 화면 표기 변환과 상세 장면표는 별첨입니다.','']
    for s in sem['scenes']:
        md+=['## '+s['title'],'']
        for p in s['paragraphs']:
            md+=['  \n'.join(u['spoken_text'] for u in p['units']),'']
    md+=['[논문별 상세 인용자료](인용자료.md) · [의미 단위·표시 자막·화면 대상](의미단위_대본과_표기표.md)','']
    (O/'대본.md').write_text('\n'.join(md),'utf-8')
    (P/'BRIEF.md').write_text('---\nworkflow: general-video\nflow: automation\nlanguage: ko\naspect: 1920x1080\n---\n사용자가 이전가이드 재적용 후 다시제작을 지시했다. 의미단위162개, 중복없는독립이미지챕터8개, 새내장이미지9개, 주제별근거와모션을 반영한다. 기존음성생성보류, 기존대본·MP4보존, 외부전송·업로드없음.\n','utf-8')
    print(json.dumps({'duration':D,'total_with_brand':D+15,'frames':global_frames,'semantic_units':len(rows),'chapter_cards':8,'image_usage_records':len(usage)},ensure_ascii=False))
if __name__=='__main__':main()
