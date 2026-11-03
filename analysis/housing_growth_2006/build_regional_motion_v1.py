"""Build a silent regional insert from frozen, local analysis outputs."""
from pathlib import Path
import hashlib
import html
import json
import shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
EP=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020'
SOURCE=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
OUT=EP/'outputs/regional-motion-v1'
(OUT/'assets/fonts').mkdir(parents=True,exist_ok=True)
(OUT/'compositions').mkdir(exist_ok=True)
OLD=EP/'outputs/returns-motion-v1'
for name in ('gsap.min.js',):shutil.copyfile(OLD/'assets'/name,OUT/'assets'/name)
for weight in ('Regular','Bold','ExtraBold'):
    shutil.copyfile(ROOT/f'assets/fonts/Pretendard-{weight}.woff2',OUT/f'assets/fonts/Pretendard-{weight}.woff2')
shutil.copyfile(OLD/'hyperframes.json',OUT/'hyperframes.json')
result=json.loads((SOURCE/'results.json').read_text(encoding='utf8'))
frame=pd.read_csv(SOURCE/'quarterly_index.csv')
summaries={r['region']:r for r in result['summaries']}
quarters=pd.period_range('2020Q1',result['endpoint'],freq='Q')
groups=[('수도권: 서울·경기·인천',['서울','경기','인천']),('부산·대구·대전',['부산','대구','대전']),('세종과 수집 범위',['세종'])]
captions=[
    ['같은 수도권 안에서도 서울·경기·인천의 가격 경로는 달랐습니다.',
     '2020년 1분기를 100으로 맞춰, 상승과 하락 경로를 보겠습니다.',
     '분기 기준으로 다시 계산한 3년·5년·10년 연복리 상승률입니다.',
     '고점 회복 판정은 표본의 거래 수 기준에 따라 달라질 수 있습니다.'],
    ['이번에는 부산·대구·대전을 같은 기간과 같은 축으로 비교합니다.',
     '대구는 행정구역 변경의 영향을 줄이기 위해 군위를 제외했습니다.',
     '3년은 2023년 2분기부터, 5년은 2021년 2분기부터 계산합니다.',
     '10년은 2016년 2분기부터입니다. 출발점과 전체 경로를 함께 봅니다.'],
    ['세종도 같은 기간과 같은 세로축으로 비교합니다.',
     '여기서 이전 고점은 2020~2022년 중 가장 높았던 분기입니다.',
     '광주는 이번 수집 응답이 모두 0건이라, 가격 비교에서 제외합니다.',
     '지역별 경로를 확인한 뒤, 관측 시점을 맞춰 다른 자산과 비교하겠습니다.'],
]
colors=['#286cda','#b35728','#357866']
def pct(v,decimals=1):return f'{v:+.{decimals}f}%'.replace('-','−')
hosts=[]
all_caps=[]
for i,(title,regions) in enumerate(groups):
    scene=f'region{i+1}'
    ticks=[]
    for value in range(0,201,50):
        yy=530-value/200*495
        dash=' stroke-dasharray="7 7"' if value==100 else ''
        ticks.append(f'<line x1="100" x2="1190" y1="{yy}" y2="{yy}" stroke="{"#75818b" if value==100 else "#d9dedf"}"{dash}/><text class="axis" x="78" y="{yy+8}" text-anchor="end">{value}</text>')
    for j,q in enumerate(quarters):
        if q.quarter==1:
            xx=100+j/(len(quarters)-1)*1090
            ticks.append(f'<text class="axis" x="{xx}" y="580" text-anchor="middle">{q.year}</text>')
    paths=[]
    dots=[]
    cards=[]
    legend=[]
    anim=[]
    for k,region in enumerate(regions):
        color=colors[k]
        values=frame[frame.region==region].set_index('quarter')['index']
        y=values.loc[[str(q) for q in quarters]]/values.loc['2020Q1']*100
        coords=[(100+j/(len(quarters)-1)*1090,530-v/200*495) for j,v in enumerate(y)]
        assert all(0<v<200 for v in y), 'Expand shared axis before rendering'
        d=' '.join(('M' if j==0 else 'L')+f'{x:.4f},{yy:.4f}' for j,(x,yy) in enumerate(coords))
        paths.append(f'<path d="{d}" stroke="{color}" fill="none" stroke-width="6" stroke-linejoin="round"/>')
        x,yy=coords[-1]
        dot=f'{scene}-dot{k}'
        dots.append(f'<circle id="{dot}" cx="{x}" cy="{yy}" r="7" fill="{color}" stroke="#f6f4ef" stroke-width="3" opacity="0"/>')
        anim.append(f'tl.fromTo("#{dot}",{{opacity:0}},{{opacity:1,duration:.3}},10.1);')
        r=summaries[region]
        label=region+' (군위 제외)' if region=='대구' else region
        returns=''.join(f'<span>{pct(r[f"cagr_{n}y_pct"],2)}</span>' for n in (3,5,10))
        cards.append(f'<div id="{scene}-stat{k}" class="stat" style="top:{150+k*157}px"><div class="stat-name" style="color:{color}">{label}</div><div class="rate-row">{returns}</div><div class="peak">이전 고점 대비 {pct(r["latest_vs_peak_pct"])}</div></div>')
        anim.append(f'tl.fromTo("#{scene}-stat{k}",{{opacity:0}},{{opacity:1,duration:.5}},{10.4+k*.3});')
        legend.append(f'<span><b style="background:{color}"></b>{label}</span>')
    if i==2:
        cards.append('<div class="missing"><strong>광주: 자료 미확보</strong><p>이번 원본 응답 0건</p><p>실제 무거래를 뜻하지 않습니다.</p><p>재확인 후 비교에 추가합니다.</p></div>')
    cap_nodes=[]
    for k,text in enumerate(captions[i]):
        cap_nodes.append(f'<div id="{scene}-caption{k}" class="caption clip" data-start="{k*5}" data-duration="5" data-track-index="9">{html.escape(text)}</div>')
        all_caps.append({'start':i*20+k*5,'end':i*20+(k+1)*5,'text':text})
    body=f'''<div id="root" data-composition-id="{scene}" data-width="1920" data-height="1080" data-duration="20"><div id="{scene}-body" class="scene-body">
    <div class="brand">│ 데이터로 보는 부동산</div><div class="review-label">자체 지표 · 탐색용 검토본 · {i+1}/3</div>
    <h1>{title}</h1><div class="subtitle">2020년 1분기 = 100 · 2026년 2분기까지 · 모든 장면의 세로축 0~200</div>
    <div class="legend">{''.join(legend)}</div>
    <div class="chart"><svg viewBox="0 0 1320 610" width="1320" height="610"><defs><clipPath id="{scene}-clip"><rect id="{scene}-reveal" x="99" y="0" width="0" height="610"/></clipPath></defs>{''.join(ticks)}<g clip-path="url(#{scene}-clip)">{''.join(paths)}</g>{''.join(dots)}</svg></div>
    <div class="stats"><div class="stats-header">연복리 상승률</div><div class="stats-sub">종료: 2026년 2분기</div><div class="column-head"><span>3년</span><span>5년</span><span>10년</span></div>{''.join(cards)}</div>
    <div class="condition">분기 중위가격 매칭 · 양 분기 각 2건 이상 · 연결마다 단지 30개 이상 · 표본 기준에 따라 결과 변동</div>
    <div class="caption-box"></div>{''.join(cap_nodes)}
    <div class="source">보유 실거래·추가 수집 XML로 계산한 자체 지표 / 공식 지수·투자수익률과 다름 / 2026Q3 제외 / 고점: 지역별 2020~2022 최고 분기</div>
    </div></div>'''
    anim.append(f'tl.fromTo("#{scene}-reveal",{{attr:{{width:0}}}},{{attr:{{width:1095}},duration:8,ease:"none"}},2);')
    anim.append(f'tl.fromTo("#{scene}-body",{{opacity:0}},{{opacity:1,duration:.25}},0);')
    script='<script>{const tl=gsap.timeline({paused:true});'+''.join(anim)+f'window.__timelines["{scene}"]=tl;'+'}</script>'
    (OUT/f'compositions/{scene}.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><body><template><style>#root{position:absolute;inset:0;overflow:hidden;background:#f6f4ef}</style>'+body+script+'</template></body></html>',encoding='utf8')
    hosts.append(f'<div id="mount-{scene}" class="clip" data-composition-id="{scene}" data-composition-src="compositions/{scene}.html" data-start="{i*20}" data-duration="20" data-track-index="{i}" data-width="1920" data-height="1080"></div>')

style='''@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Regular.woff2);font-weight:400}@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Bold.woff2);font-weight:700}@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-ExtraBold.woff2);font-weight:800}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif}#root{position:relative;width:1920px;height:1080px;overflow:hidden}#root>.clip{position:absolute;inset:0}.scene-body{position:absolute;inset:0;background:#f6f4ef}.brand{position:absolute;left:80px;top:32px;font-size:23px}.review-label{position:absolute;right:80px;top:34px;font-size:22px;color:#546973}h1{position:absolute;left:80px;top:91px;margin:0;font-size:49px;font-weight:800}.subtitle{position:absolute;left:80px;top:165px;font-size:23px;color:#546973}.legend{position:absolute;left:110px;top:221px;display:flex;gap:45px;font-size:27px;align-items:center}.legend span{display:flex;align-items:center;gap:12px}.legend b{display:inline-block;width:33px;height:7px;border-radius:5px}.chart{position:absolute;left:70px;top:270px;width:1320px;height:610px}.axis{font-size:24px;fill:#546973}.stats{position:absolute;left:1440px;top:254px;width:400px;height:595px;border-left:2px solid #d6dad7;padding:20px 0 0 29px}.stats-header{font-size:33px;font-weight:700}.stats-sub{font-size:23px;color:#546973;margin-top:8px}.column-head,.rate-row{display:grid;grid-template-columns:110px 110px 110px;text-align:left}.column-head{position:absolute;left:29px;top:106px;font-size:22px;color:#546973}.stat{position:absolute;left:29px;width:355px}.stat-name{font-size:28px;font-weight:700}.rate-row{font-size:29px;font-weight:800;margin-top:14px}.peak{font-size:23px;color:#546973;margin-top:14px}.missing{position:absolute;left:29px;top:330px;width:350px;color:#546973;font-size:23px;line-height:1.6}.missing strong{color:#173348;font-size:28px}.missing p{margin:8px 0}.condition{position:absolute;left:96px;top:884px;font-size:21px;color:#546973}.caption-box{position:absolute;left:96px;top:936px;width:1728px;height:94px;background:#fff;border-radius:13px}.caption{position:absolute;left:120px;top:936px;width:1680px;height:94px;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:700;line-height:1.3}.source{position:absolute;left:96px;top:1044px;font-size:18px;color:#546973}'''
style+='\n.stats{left:1405px;width:435px}.stat{width:390px}.column-head,.rate-row{grid-template-columns:130px 130px 130px}.rate-row{font-size:25px;font-variant-numeric:tabular-nums}'
(OUT/'index.html').write_text('<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>'+style+'</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="60" data-fps="30">'+''.join(hosts)+'</div><script>const tl=gsap.timeline({paused:true});window.__timelines["main"]=tl;</script></body></html>',encoding='utf8')

def stamp(s):return f'{s//3600:02}:{s//60%60:02}:{s%60:02},000'
(OUT/'regional_motion_v1.srt').write_text(''.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}\n\n' for i,c in enumerate(all_caps,1)),encoding='utf8')
(OUT/'data.json').write_text(json.dumps({'analysis':result,'captions':all_caps,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE/'results.json',SOURCE/'quarterly_index.csv')}},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'BRIEF.md').write_text('---\nworkflow: general-video\nflow: automation\nstoryboard: no\naspect: 1920x1080\nlanguage: ko\nlength: 60s\n---\n\nExtend the existing housing-choice regional introduction to all usable collected cities. Concept: the same start date reveals different regional price paths. Three 20-second group scenes with line-chart reveals and 3/5/10-year CAGR tables. Preserve cream/Pretendard/blue channel design; silent, captions only. Seven regions, Gwangju unavailable (zero raw records). Exploratory custom indices, not official data; matching sensitivity explicitly stated. User has requested local motion graphics and the regional expansion; no paid generation or upload.\n',encoding='utf8')
(OUT/'STORYBOARD.md').write_text('---\nmode: autonomous\n---\n\nDesign: warm cream background, Pretendard, regional price lines as focus, shared grid and period labels as anchors, CAGR table at right, explanatory captions at bottom. Reuse the established comparison-insert typography and palette. All paths reveal by x-coordinate clip width with a deterministic paused GSAP timeline; no future dots leak before reveal.\n\n'+''.join(f'## Scene {i+1}\nstatus: built\nstart: {i*20}\nduration: 20\nsrc: compositions/region{i+1}.html\nmessage: {title}\nrules: mask reveal; linear chronological trace; fade statistics\n\n' for i,(title,_) in enumerate(groups)),encoding='utf8')
(OUT/'package.json').write_text(json.dumps({'private':True,'name':'regional-motion-v1','scripts':{'check':'hyperframes check','render':'hyperframes render -o regional_motion_v1.mp4'}},indent=2),encoding='utf8')
print(f'Built 60s regional motion source: {OUT}')
