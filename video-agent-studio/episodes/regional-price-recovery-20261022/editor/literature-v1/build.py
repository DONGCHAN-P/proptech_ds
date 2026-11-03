"""Build only director-owned scenes and the shared HyperFrames timeline."""
from pathlib import Path
import json, html, shutil, math
ROOT=Path(__file__).resolve().parents[5];EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022';OUT=EP/'outputs/literature-visual-v1';P=OUT/'project'
T=json.loads((P/'timing.json').read_text(encoding='utf8'));DATA=json.loads((P/'assets/price_data.json').read_text(encoding='utf8'))
BLUE='#286cda';GOLD='#c29a44';INK='#173348';MUTED='#607680';PAPER='#f6f4ef'
def tx(x,y,text,size=30,color=INK,weight=400,anchor='start',cls=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}" class="{cls}">{html.escape(str(text))}</text>'
def rect(x,y,w,h,color='#fffef9',r=16,stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}" stroke="{stroke}" stroke-width="2"/>'
def line(x,y,x2,y2,color='#cbd3d5',width=3,cls=''):
    return f'<path d="M{x},{y} L{x2},{y2}" stroke="{color}" stroke-width="{width}" fill="none" class="{cls}"/>'
def house(x,y,scale=1,color=BLUE,cls=''):
    return f'<g class="{cls}"><g transform="translate({x} {y}) scale({scale})"><path d="M0 52 L65 0 L130 52 V145 H0Z" fill="{color}" opacity=".14"/><path d="M-8 53 L65 -5 L138 53 M10 45 V140 H120 V45" stroke="{color}" stroke-width="6" fill="none" stroke-linejoin="round"/><rect x="50" y="83" width="31" height="57" rx="3" fill="{color}"/><rect x="24" y="65" width="18" height="20" fill="{color}" opacity=".5"/><rect x="90" y="65" width="18" height="20" fill="{color}" opacity=".5"/></g></g>'
def job(x,y,s=1,color=BLUE):
    return f'<g transform="translate({x} {y}) scale({s})"><rect x="0" y="20" width="116" height="95" rx="8" fill="{color}" opacity=".15"/><rect x="0" y="20" width="116" height="95" rx="8" stroke="{color}" stroke-width="5" fill="none"/><path d="M37 20 V0 H79 V20 M0 57 H116 M50 51 V67 H66 V51" stroke="{color}" stroke-width="5" fill="none"/></g>'
def person(x,y,s=1,color=BLUE,cls=''):
    return f'<g class="{cls}" transform="translate({x} {y}) scale({s})"><circle cx="27" cy="22" r="21" fill="{color}"/><path d="M0 70 Q0 45 27 45 Q54 45 54 70 V115 H0Z" fill="{color}" opacity=".85"/></g>'
def svg(body):return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1760 640" width="1760" height="640">'+body+'</svg>'
def graph(focus=False):
    q0='2021Q4' if focus else '2006Q1';regions=['서울','경기'];rows={r:[v for v in DATA if v['region']==r and v['quarter']>=q0] for r in regions}
    maxy,miny=(135,75) if focus else (600,50);x0,y0,w,h=125,65,1335,425
    val=lambda r,i:float(rows[r][i]['source_index'])/float(next(v for v in DATA if v['region']==r and v['quarter']==q0)['source_index'])*100
    X=lambda i,n:x0+w*i/(n-1);Y=lambda v:y0+h-(v-miny)/(maxy-miny)*h
    a=tx(125,28,f'{q0}=100 · '+('고점 이후 관측 경로' if focus else '2006년 이후 전체 관측 경로'),24,MUTED)
    ticks=[80,90,100,110,120,130] if focus else [100,200,300,400,500,600]
    for v in ticks:a+=line(x0,Y(v),x0+w,Y(v),'#cbd3d5',2)+tx(99,Y(v)+7,v,22,MUTED,anchor='end')
    for r,c in zip(regions,[BLUE,GOLD]):
        n=len(rows[r]);pts=' '.join(f'{X(i,n):.2f},{Y(val(r,i)):.2f}' for i in range(n))
        a+=f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round" class="draw"/>'
        v=val(r,n-1);a+=f'<circle cx="{x0+w}" cy="{Y(v):.2f}" r="7" fill="{c}"/>'+tx(1490,Y(v)+8,f'{r} {v:.1f}',28,c,700)
    years=['2021Q4','2022Q4','2023Q4','2024Q4','2026Q2'] if focus else ['2006Q1','2010Q1','2014Q1','2018Q1','2022Q1','2026Q2']
    for q in years:
        idx=next(i for i,r in enumerate(rows['서울']) if r['quarter']==q);x=X(idx,len(rows['서울']));a+=tx(x,540,q if focus else q[:4],20,MUTED,anchor='middle')
    if focus:
        idx=next(i for i,r in enumerate(rows['서울']) if r['quarter']=='2024Q3');x=X(idx,len(rows['서울']));y=Y(val('서울',idx))
        a+=line(x,155,x,y-12,BLUE,2)+rect(x-155,96,310,63,'#e6eefc',12)+tx(x,137,'서울 · 2024Q3 최초 복귀',23,BLUE,700,'middle')
        a+=tx(125,600,'경기 · 2026Q2는 2021Q4 고점 대비 −4.08%',27,GOLD,700)
    else:a+=tx(125,600,'같은 단지·전용면적군 연결 · 명목 자체 지수',24,MUTED)
    return a
def links_overview():
    a=''
    for x,title,sub,icon in [(115,'사람','가구 구성과 이동',person(180,145,1.35)),(690,'집','이주와 입주 시점',house(760,140,1.25)),(1265,'직장','실제 통근 연결',job(1335,158,1.25))]:
        a+=f'<g class="reveal">'+rect(x,95,390,410)+icon+tx(x+195,380,title,48,INK,700,'middle')+tx(x+195,430,sub,27,MUTED,anchor='middle')+'</g>'
    a+=line(510,300,665,300,BLUE,5,'draw')+line(1085,300,1240,300,GOLD,5,'draw')
    return a
def observed_questions():
    a=tx(90,80,'가격 경로에서, 설명할 질문으로',38,INK,700)
    for i,(word,first,second,c) in enumerate([('인구','누가 어떤 가구로','움직였나',BLUE),('공급','언제 입주할 수','있는 집인가',GOLD),('교통','어떤 직장까지','연결되나',BLUE)]):
        x=90+i*570;icon=person(x+70,285,.8,c) if i==0 else (house(x+65,270,.6,c) if i==1 else job(x+65,285,.65,c));a+=f'<g class="reveal">'+rect(x,145,520,330)+tx(x+40,220,word,40,c,700)+icon+tx(x+200,340,first,28)+tx(x+200,385,second,28)+'</g>'
    return a+tx(90,565,'관측 결과와 원인 설명을 연결할 자료가 필요합니다.',29,MUTED)
def choice_diagram(idx):
    a=tx(65,45,'한 가구가 실제로 고를 수 있는 집',38,INK,700)+tx(65,91,'종합 해석 · 실제 매물 수를 나타낸 그림이 아닙니다.',22,MUTED)
    labels=[('면적','필요한 공간'),('비용','감당할 예산'),('날짜','이사·입주 시점'),('직장','계속 가능한 출근')]
    for i,(k,d) in enumerate(labels):
        x=65+i*425;c=BLUE if i<=idx else '#b4c0c4';a+=f'<g class="reveal">'+rect(x,135,390,100,'#e6eefc' if i==idx else '#fffef9',12,BLUE if i==idx else 'none')+tx(x+25,177,k,31,c,700)+tx(x+25,211,d,23,MUTED)+'</g>'
    selected=[set(range(9)),{0,1,3,4,6,7},{0,3,4,6},{0,4,6}][min(idx,3)]
    for j in range(9):
        x=115+j*180;c=BLUE if j in selected else '#bfc8ca';a+=house(x,330,.72,c,cls='reveal')
    a+=line(70,280,1660,280,BLUE,3,'draw')+tx(880,570,'가구의 조건 × 이용 가능한 주택',38,INK,700,'middle')
    return a
def followup(idx):
    if idx==0:
        return tx(90,70,'확인한 것',36,BLUE,700)+rect(90,115,760,375)+tx(130,185,'자체 가격 경로',32,INK,700)+tx(130,238,'2006Q1–2026Q2',29,BLUE)+house(145,295,.8)+tx(320,355,'서울·경기 회복 시점의 차이',29)+rect(905,115,760,375)+tx(945,185,'문헌의 사례',32,INK,700)+tx(945,265,'주거비와 청년 이동',29)+tx(945,335,'재건축 이주 목적지의 가격',29)+tx(945,405,'통근 연결과 평균가격',29)+tx(90,560,'가격 관측과 문헌 근거를 구분해 연결합니다.',28,MUTED)
    if idx==1:
        a=tx(80,65,'자료를 더 연결할 세 비교',38,INK,700)
        for i,(left,right) in enumerate([('인구 추세가 비슷한 곳','가구 구성·면적별 선택'),('준공이 비슷한 곳','멸실·이주와 입주 공백'),('역 거리가 비슷한 곳','통근 조건·일자리 연결')]):
            y=125+i*145;a+=f'<g class="reveal">'+rect(80,y,1595,115)+tx(125,y+70,left,31)+line(670,y+56,860,y+56,BLUE,4,'draw')+tx(910,y+70,right,31,BLUE,700)+'</g>'
        return a+tx(80,615,'후속 검증 계획 · 비교할 주택의 면적·품질 조건도 맞춥니다.',25,MUTED)
    return choice_diagram(3)
def scene_file(scene,bodies,extra=''):
    markup=''.join(f'<section class="clip beat" id="{b["id"]}" data-start="{b["start"]:.6f}" data-duration="{b.get("visual_duration",b["duration"]):.6f}" data-track-index="1">{svg(body)}</section>' for b,body in zip(scene['beats'],bodies))
    tween=''
    for b in scene['beats']:
        bid=b['id'];start=b['start'];tween+=f'''document.querySelectorAll('#{bid} .reveal').forEach((el,i)=>tl.fromTo(el,{{opacity:0,y:18}},{{opacity:1,y:0,duration:.65,immediateRender:false,ease:'power2.out'}},{start}+.35+i*.24));document.querySelectorAll('#{bid} .draw').forEach((el,i)=>{{const n=el.getTotalLength();tl.fromTo(el,{{strokeDasharray:n,strokeDashoffset:n}},{{strokeDashoffset:0,duration:1.4,immediateRender:false,ease:'power1.inOut'}},{start}+.5+i*.15)}});'''
    return f'''<!doctype html><html><head><meta charset="utf-8"></head><body><template><style>#{scene['scene_id']}-root{{position:absolute;inset:0;width:100%;height:100%}}#{scene['scene_id']}-root .focus-history{{opacity:0}}</style><div id="{scene['scene_id']}-root" data-composition-id="{scene['scene_id']}" data-width="1920" data-height="1080" data-duration="{scene['duration']:.6f}" data-fps="30">{markup}</div><script>(()=>{{const tl=gsap.timeline({{paused:true}});{tween}{extra}window.__timelines['{scene['scene_id']}']=tl;}})();</script></template></body></html>'''

scenes={s['scene_id']:s for s in T['scenes']}
s=scenes['L001'];bodies=[graph(False),'<g class="full-history">'+graph(False)+'</g><g class="focus-history">'+rect(0,0,1760,640,PAPER,0)+graph(True)+'</g>',observed_questions(),links_overview()]
assert len(bodies)==len(s['beats'])
b=s['beats'][1];at=b['start']+b['duration']*.48
extra=f"tl.to('#{b['id']} .full-history',{{opacity:0,duration:.4}},{at});tl.fromTo('#{b['id']} .focus-history',{{opacity:0}},{{opacity:1,duration:.4,immediateRender:false}},{at});"
(P/'compositions/L001.html').write_text(scene_file(s,bodies,extra),encoding='utf8')
s=scenes['L007'];(P/'compositions/L007.html').write_text(scene_file(s,[choice_diagram(min(i,3)) for i,_ in enumerate(s['beats'])]),encoding='utf8')
s=scenes['L008'];(P/'compositions/L008.html').write_text(scene_file(s,[followup(i) for i,_ in enumerate(s['beats'])]),encoding='utf8')
sources={
'L001':'보유 아파트 실거래 · 동일 단지·전용면적군 자체 지수 · 2006Q1–2026Q2',
'L002':'Lee·Kang(2022), Seoul Journal of Economics 35(1) · 수도권 취업자, 주분석 2005–2010',
'L003':'이준민·심승규·홍지훈(2022), 부동산분석 8(1) · 전국 2020 주거실태조사',
'L004':'서문규·정재엽·이효중(2026), 국토계획 61(4) · 가락시영 사례, 59㎡, 2011Q1–2014Q4',
'L005':'가상 순증 계산 / 유건호·강명구(2025), 주택금융연구 9(1) · 서울 신규 전세 2017–2023',
'L006':'김선정·남진(2022), 국토계획 57(5) · ITF(2023), 수도권 접근성 보고서',
'L007':'앞서 인용한 문헌을 연결한 종합 해석 · 서울·경기 원인별 기여율 추정 결과 아님',
'L008':'자체 가격 집계와 문헌 사례 / 가구·이주·통근 자료를 연결할 후속 검증 계획'}
tags=['자체 집계','구조 예시 · 연구 결과','연구 결과','연구 결과','가상 계산 · 연구 결과','개념도 · 연구 결과','종합 해석','관측 / 후속 과제']
headers=[];mounts=[];chapters=[]
bg_candidates=list((ROOT/'video-agent-studio/assets/chapter-backgrounds').glob('**/*.png')) if (ROOT/'video-agent-studio/assets/chapter-backgrounds').exists() else []
if bg_candidates:shutil.copy2(bg_candidates[0],P/'assets/chapter_background.png')
for i,s in enumerate(T['scenes']):
    sid=s['scene_id'];mounts.append(f'<div id="{sid}-mount" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{s["start"]:.6f}" data-duration="{s["duration"]:.6f}" data-width="1920" data-height="1080" data-track-index="{i+1}" data-track-kind="graphics"></div>')
    headers.append(f'<div class="clip" id="header-{sid}" data-start="{s["start"]:.6f}" data-duration="{s["duration"]:.6f}" data-track-index="12"><h1 class="scene-title">{html.escape(s["title"])}</h1><div class="evidence-tag">{tags[i]}</div><div class="source">{html.escape(sources[sid])}</div></div>')
    art='<div class="chapter-art" style="background-image:url(assets/chapter_background.png);background-size:cover;background-position:center"></div>' if bg_candidates else '<div class="chapter-art" style="background-image:url(assets/집.png);background-size:contain;background-repeat:no-repeat"></div>'
    chapters.append(f'<div class="chapter-panel clip" id="chapter-{sid}" data-start="{s["start"]:.6f}" data-duration="3" data-track-index="11">{art}<div class="chapter-kicker">데이터로 보는 부동산 · 근거로 읽는 집값</div><h2>{html.escape(s["title"])}</h2><div class="chapter-rule"></div></div>')
captions=''.join(f'<div class="caption-cue clip" id="cue-{i}" data-start="{c["start"]:.6f}" data-duration="{c["end"]-c["start"]:.6f}" data-track-index="1">{html.escape(c["text"])}</div>' for i,c in enumerate(T['captions']))
cap=f'<template><style>#captions-root{{position:absolute;inset:0;width:100%;height:100%}}</style><div id="captions-root" data-composition-id="captions" data-width="1920" data-height="1080" data-duration="{T["body_duration"]:.6f}"><div class="caption-box">{captions}</div></div><script>window.__timelines["captions"]=gsap.timeline({{paused:true}});</script></template>'
(P/'compositions/captions.html').write_text(cap,encoding='utf8')
capmount=f'<div id="captions-mount" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{T["last_caption_end"]:.6f}" data-width="1920" data-height="1080" data-track-index="13" data-track-kind="captions"></div>'
shell=f'<template><style>#shell-root{{position:absolute;inset:0;width:100%;height:100%}}</style><div id="shell-root" data-composition-id="shell" data-width="1920" data-height="1080" data-duration="{T["body_duration"]:.6f}">{"".join(headers)}{"".join(chapters)}</div><script>window.__timelines["shell"]=gsap.timeline({{paused:true}});</script></template>'
(P/'compositions/shell.html').write_text(shell,encoding='utf8')
shellmount=f'<div id="shell-mount" class="clip" data-composition-id="shell" data-composition-src="compositions/shell.html" data-start="0" data-duration="{T["body_duration"]:.6f}" data-width="1920" data-height="1080" data-track-index="10" data-track-kind="graphics" style="z-index:80"></div>'
# Brand intro/outro are assembled from the unchanged approved local masters after body export.
index=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>논문 인용형 화면 검토본 v1</title><link rel="stylesheet" href="assets/common.css"><style>@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2')}}@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}}#root{{width:100%;height:100%;position:relative}}.edition{{color:#526872}}</style><script src="assets/gsap.min.js"></script></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{T['body_duration']:.6f}" data-fps="30"><div class="brand">│ 데이터로 보는 부동산</div><div class="edition">근거로 읽는 집값</div>{''.join(mounts)}{capmount}{shellmount}</div><script>window.__timelines['main']=gsap.timeline({{paused:true}});</script></body></html>'''
(P/'index.html').write_text(index,encoding='utf8')
(P/'BRIEF.md').write_text('''---
workflow: general-video
flow: automation
storyboard: no
message: "주거 수요·공급·일자리는 가구가 실제 선택할 수 있는 집에서 연결된다"
aspect: 1920x1080
language: ko
length: provisional-visual-review-568.267s
---

## Intent
2026-10-23 사용자 승인 대본 literature-video-v1의 8장면 화면 제작. 기존 가격 곡선 반복을 가구 분해·이주 공백·순증 공급·통근 구조·선택지 도식으로 전환한다. 대본 SHA는 timing.json에 고정한다.

## Assets
로컬 Pretendard·GSAP·기존 집 아이콘과 클린 브랜드 마스터만 재사용한다. 새 유료 호출·음성 생성·외부 전송·업로드 없음. 원논문은 직접 인용 링크와 자체 문장 요약으로 사용하며 원문 도판을 복제하지 않는다.

## Customizations
timing.json의 텍스트 기반 임시 길이와 자막. 실제 Jun 타이밍이 아니다. 물가 미조정 자체 가격지수와 가상 그림·문헌 결과·종합 해석·후속 검증을 구분한다. 근거는 자막 아래 별도 영역에 표시한다. 과거 대본·원본·MP4는 보존한다.

## Production scope
사용자가 이 대본으로 화면 제작 진행을 명시 승인했다. 로컬 화면 검토 렌더는 승인 범위의 확인용 산출물이다. 최종 내레이션 본편·음성 생성·업로드는 포함하지 않는다. 제작자의 기본 선택은 기존 general-video/GSAP 유지와 장면별 sub-composition이다.
''',encoding='utf8')
print(json.dumps({'built_director_scenes':['L001','L007','L008'],'root':'index.html','caption_count':len(T['captions']),'duration':T['body_duration'],'chapter_background':str(bg_candidates[0]) if bg_candidates else 'reused house icon concept background'},ensure_ascii=False))
