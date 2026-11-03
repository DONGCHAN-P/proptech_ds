from pathlib import Path
import json,shutil,xml.etree.ElementTree as ET,hashlib,copy

EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2]
OUT=EP/'outputs/relocation-space-v1';P=OUT/'project';APPROVED=EP/'outputs/household-space-v1/project'
for d in (P/'assets/fonts',P/'compositions',OUT/'checks',EP/'director/relocation-space-v1'):
    d.mkdir(parents=True,exist_ok=True)
timing=json.loads((EP/'outputs/literature-visual-v1/project/timing.json').read_text('utf-8'))
scene=next(s for s in timing['scenes'] if s['scene_id']=='L004');D=scene['duration'];START=scene['start']
captions=[dict(c,start=round(c['start']-START,9),end=round(c['end']-START,9)) for c in timing['captions'] if c['scene_id']=='L004']
# The source captions' start/end are body times; keep original exact provisional chapter alignment.
assert captions and min(c['start'] for c in captions)>=0
for n in ('Pretendard-Regular.woff2','Pretendard-Bold.woff2'):
    shutil.copy2(APPROVED/'assets/fonts'/n,P/'assets/fonts'/n)
shutil.copy2(APPROVED/'assets/gsap.min.js',P/'assets/gsap.min.js')
asset=EP/'visual/relocation-space-v1/apartment-stages.svg'
if asset.exists():
    shutil.copy2(asset,P/'assets/apartment-stages.svg')
    shutil.copy2(asset.with_name('assets.json'),P/'assets/building_asset_provenance.json')

def apt(panel,x,y,w=290,h=406,ident=''):
    return f'<svg id="{ident}" x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{panel*300} 0 300 420" style="overflow:hidden"><image href="assets/apartment-stages.svg" x="0" y="0" width="900" height="420"/></svg>'

# Reuse the accepted cutaway living room without executing the older builder.
approved=(APPROVED/'compositions/home-space.html').read_text('utf-8')
start=approved.index('<g id="family-home">')
svg_text=approved[approved.index('<svg viewBox=',approved.index('id="world"')):approved.index('</svg></div>',start)+6]
svg_xml=ET.fromstring(svg_text)
family=next(el for el in svg_xml if el.get('id')=='family-home')
for el in list(family):
    if el.tag.endswith('text'):family.remove(el)
family.set('id','accepted-living-room')
room=ET.tostring(family,encoding='unicode')

style='''
#relocation-scene{position:absolute;inset:0;color:#173348}.clip{position:absolute;inset:0}
#relocation-scene .brand{position:absolute;left:80px;top:38px;font-size:22px}#relocation-scene .series{position:absolute;right:80px;top:42px;font-size:18px;color:#526872}#relocation-scene .rule{position:absolute;left:80px;right:80px;top:87px;height:1px;background:#D6DCD9}#relocation-scene .chapter{position:absolute;left:80px;top:127px;font-size:23px;color:#526872}
#relocation-scene .headline{position:absolute;left:80px;top:179px;font-size:59px;font-weight:700;line-height:1.15;letter-spacing:-1.8px;margin:0}#relocation-scene .headline b{color:#286CDA}#relocation-scene .badge{position:absolute;right:80px;top:133px;font-size:19px;color:#526872}#relocation-scene .stage{position:absolute;inset:0;width:100%;height:100%}
#relocation-scene svg text{font-family:inherit}.label{font-size:29px;fill:#173348;font-weight:700}.note{font-size:22px;fill:#526872}.blue{fill:#286CDA}.gold{fill:#967536}.small{font-size:20px;fill:#526872}
#relocation-scene .study{position:absolute;left:84px;top:326px;width:450px;padding:31px 32px;border-top:4px solid #286CDA;background:#EEEDE6}#relocation-scene .study .overline{font-size:24px;color:#526872}#relocation-scene .study h2{font-size:48px;line-height:1.2;letter-spacing:-1px;margin:18px 0 23px}#relocation-scene .study p{font-size:25px;line-height:1.5;margin:0}
#relocation-scene .result-card{position:absolute;top:456px;width:428px;height:252px;padding:28px;background:#E4EBE9;border-radius:5px}#relocation-scene .result-card h3{margin:0 0 18px;font-size:34px}#relocation-scene .result-card .direction{display:flex;align-items:center;gap:30px;color:#286CDA;font-size:39px;font-weight:700}#relocation-scene .result-card .arrow{font-size:90px;line-height:1}#relocation-scene .result-card p{font-size:22px;color:#526872;margin:18px 0 0}
#relocation-scene .condition{position:absolute;left:80px;bottom:196px;font-size:22px;color:#526872;line-height:1.5}#relocation-scene .question{position:absolute;left:865px;right:80px;font-size:37px;padding-bottom:24px;border-bottom:1px solid #CDD6D0;font-weight:700}#relocation-scene .question span{color:#286CDA;margin-right:30px}#relocation-scene .line-note{position:absolute;left:80px;top:867px;font-size:20px;color:#526872}
'''

concept=f'''<section class="clip" id="concept" data-start="0" data-duration="24.2" data-track-index="1"><div class="inner">
<h1 class="headline">새집이 늘기 전에, <b>살 집부터 필요합니다.</b></h1><div class="badge">시간 순서 설명 · 개념도</div>
<svg class="stage" viewBox="0 0 1920 1080" role="img" aria-label="기존 집을 비운 뒤 다른 집에 살다가 새집에 입주하는 순서">
{apt(0,188,300,290,406,'old-home')}{apt(1,188,300,290,406,'building-site')}
<g id="temporary-home"><svg x="649" y="428" width="550" height="282" viewBox="140 340 820 420" style="overflow:hidden">{room}</svg></g>
{apt(2,1437,300,290,406,'finished-home')}
<text class="label" x="333" y="752" text-anchor="middle">기존 집을 비움</text><text id="temporary-label" class="label blue" x="924" y="752" text-anchor="middle">다른 집에서 거주</text><text class="label" x="1582" y="752" text-anchor="middle">새집 입주</text>
<path d="M333 804H1582" stroke="#CBD3D0" stroke-width="8" stroke-linecap="round"/>
<path id="time-line" d="M333 804H1582" stroke="#286CDA" stroke-width="8" stroke-linecap="round" fill="none"/>
<circle cx="333" cy="804" r="10" fill="#967536"/><circle cx="1582" cy="804" r="10" fill="#286CDA"/>
<text id="gap-label" class="label blue" x="924" y="855" text-anchor="middle">그 사이에도 살 집은 필요합니다</text>
</svg><div class="line-note">개념적 사건 순서 · 위치와 기간의 비례를 표시하지 않습니다.</div></div></section>'''

calendar_ticks=''.join(f'<path d="M{720+i*100} 617v{28 if i in (0,9) else 15}" stroke="#728A91" stroke-width="2"/>' for i in range(10))
case=f'''<section class="clip" id="case" data-start="24.2" data-duration="14.4666666667" data-track-index="1"><div class="inner">
<h1 class="headline">실제 이주 목적지를 추적한 <b>가락시영 사례</b></h1><div class="badge">논문 사례 · 주요 이주 기간</div>
<div class="study"><div class="overline">서문규·정재엽·이효중 · 2026</div><h2>가락시영<br>재건축 이주</h2><p>재건축 주민들이<br>어느 지역으로 이동했는지<br>실제 이동 자료로 살폈습니다.</p></div>
<svg class="stage" viewBox="0 0 1920 1080"><text class="label" x="720" y="440">주요 이주</text>
<text x="720" y="548" font-size="64" fill="#173348" font-weight="700">2012.8</text><text x="1478" y="548" font-size="64" fill="#286CDA" font-weight="700">2013.5</text>
<path d="M720 617H1620" stroke="#D3DCD7" stroke-width="12" stroke-linecap="round"/><path id="migration-range" d="M720 617H1620" stroke="#286CDA" stroke-width="12" stroke-linecap="round" fill="none"/>{calendar_ticks}
<text class="note" x="720" y="714">원래 거주지 → 실제 이주 목적지</text><text class="small" x="720" y="758">표시한 날짜는 주요 이주 기간입니다.</text>
</svg><div class="line-note">연구의 분석 기간: 2011년 1분기–2014년 4분기 · 실제 목적지별 유입량은 이 화면에 표시하지 않습니다.</div></div></section>'''

estimate='''<section class="clip" id="estimate" data-start="38.6666666667" data-duration="17.8666666666" data-track-index="1"><div class="inner">
<h1 class="headline">이주 유입과 <b>두 가격 지표</b>를 함께 봤습니다.</h1><div class="badge">연구의 추정 결과 · 59㎡ 아파트</div>
<svg class="stage" viewBox="0 0 1920 1080"><text class="label" x="84" y="387">과거 목적지 분포</text><text class="note" x="84" y="438">이전에 어느 지역으로 이동했는가</text><path id="estimate-connector" d="M462 416H724" fill="none" stroke="#286CDA" stroke-width="5"/>
<text class="label blue" x="770" y="387">이주 유입 추정</text><text class="note" x="770" y="438">과거의 이동 분포를 활용</text></svg>
<div class="result-card" id="sale-result" style="left:770px"><h3>매매가격</h3><div class="direction"><span class="arrow">↑</span><span>상승 방향</span></div><p>59㎡ 아파트</p></div>
<div class="result-card" id="rent-result" style="left:1296px"><h3>환산 임대료</h3><div class="direction"><span class="arrow">↑</span><span>상승 방향</span></div><p>전세 등을 월세 기준으로 환산</p></div>
<div class="condition">과거 목적지 분포의 외생성 가정에 의존하는 도구변수 추정 결과입니다.<br>화살표는 추정 방향만 표시하며, 효과의 크기나 지역별 상승률을 비교하지 않습니다.</div>
</div></section>'''

two_markets=f'''<section class="clip" id="two-markets" data-start="56.5333333333" data-duration="16.0333333334" data-track-index="1"><div class="inner">
<h1 class="headline">같은 사업도 <b>사업지와 목적지</b>에 다르게 작용합니다.</h1><div class="badge">문헌에 기반한 구조 해석</div>
<svg class="stage" viewBox="0 0 1920 1080">{apt(1,228,296,315,441,'origin-site')}<svg x="1138" y="417" width="550" height="282" viewBox="140 340 820 420" style="overflow:hidden">{room.replace('id="','id="destination-')}</svg>
<text class="label" x="385" y="326" text-anchor="middle">원래 사업지</text><text class="label" x="1413" y="326" text-anchor="middle">대체 거주 지역</text>
<g id="origin-effect"><text class="label" x="385" y="795" text-anchor="middle">거주 가능한 집</text><text x="385" y="855" font-size="38" fill="#967536" font-weight="700" text-anchor="middle">일시 감소</text></g>
<g id="destination-effect"><text class="label" x="1413" y="795" text-anchor="middle">집을 찾는 수요</text><text x="1413" y="855" font-size="38" fill="#286CDA" font-weight="700" text-anchor="middle">증가 가능</text></g>
<path d="M762 556H1010" stroke="#C6D0CC" stroke-width="2"/><text class="note" x="886" y="524" text-anchor="middle">주민의 이동</text>
</svg></div></section>'''

questions=f'''<section class="clip" id="questions" data-start="72.5666666667" data-duration="14" data-track-index="1"><div class="inner">
<h1 class="headline">정비사업 <b>경계 밖</b>의 대체 거주도 봐야 합니다.</h1><div class="badge">우리 데이터에 연결할 후속 질문</div>
<svg class="stage" viewBox="0 0 1920 1080"><rect x="151" y="322" width="522" height="455" rx="5" fill="#E6EBE4"/><path d="M170 341H654V758H170Z" fill="none" stroke="#97ADA3" stroke-width="2" stroke-dasharray="11 10"/>{apt(1,276,362,280,392,'question-site')}<text class="label" x="413" y="837" text-anchor="middle">사업지 안의 공급 + 경계 밖의 이동</text></svg>
<div id="question-where" class="question" style="top:358px"><span>01</span>어느 지역으로 이동했나</div>
<div id="question-when" class="question" style="top:506px"><span>02</span>언제 대체 집이 필요했나</div>
<div id="question-howmany" class="question" style="top:654px"><span>03</span>얼마나 이동했나</div>
<div class="line-note">실제 목적지와 이동량을 결합해 확인할 질문입니다. 현재 서울·경기의 원인별 기여율을 추정한 결과가 아닙니다.</div>
</div></section>'''

motion='''(() => {
const tl=gsap.timeline({paused:true});
tl.fromTo('#old-home',{opacity:0,y:10},{opacity:1,y:0,duration:.8,ease:'sine.out'},.1);
tl.fromTo('#building-site',{opacity:0},{opacity:1,duration:1,ease:'sine.inOut'},12.4);
tl.fromTo('#old-home',{opacity:1},{opacity:0,duration:1,ease:'sine.inOut',immediateRender:false},12.4);
tl.fromTo('#temporary-home',{opacity:0},{opacity:1,duration:1.2,ease:'sine.inOut'},13.5);
tl.fromTo('#temporary-label',{opacity:0},{opacity:1,duration:.7,ease:'sine.inOut'},13.8);
tl.fromTo('#finished-home',{opacity:.13},{opacity:1,duration:1.5,ease:'sine.inOut'},20.1);
tl.fromTo('#gap-label',{opacity:0},{opacity:1,duration:.8,ease:'sine.inOut'},14);
for(const [selector,start,duration] of [['#time-line',9.5,11.2],['#migration-range',27.8,7.6],['#estimate-connector',39.5,1.3]]){
 const el=document.querySelector(selector),len=el.getTotalLength();el.style.strokeDasharray=String(len);el.style.strokeDashoffset=String(len);
 tl.fromTo(el,{strokeDashoffset:len},{strokeDashoffset:0,duration,ease:'sine.inOut'},start);
}
tl.fromTo('#sale-result',{opacity:0,y:10},{opacity:1,y:0,duration:.8,ease:'power2.out'},44.5);
tl.fromTo('#rent-result',{opacity:0,y:10},{opacity:1,y:0,duration:.8,ease:'power2.out'},49.1);
tl.fromTo('#origin-effect',{opacity:0},{opacity:1,duration:.8,ease:'sine.inOut'},59.4);
tl.fromTo('#destination-effect',{opacity:0},{opacity:1,duration:.8,ease:'sine.inOut'},64.2);
for(const [selector,at] of [['#question-where',74.2],['#question-when',77.3],['#question-howmany',80.1]])tl.fromTo(selector,{opacity:0,x:14},{opacity:1,x:0,duration:.7,ease:'power2.out'},at);
window.__timelines['relocation-scene']=tl;
})();'''
html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template><style>{style}</style><div id="relocation-scene" data-composition-id="relocation-scene" data-duration="{D}" data-width="1920" data-height="1080"><div class="brand">데이터로 보는 부동산</div><div class="series">근거로 읽는 집값</div><div class="rule"></div><div class="chapter">03 · 재건축 이주</div>{concept}{case}{estimate}{two_markets}{questions}</div><script>{motion}</script></template></body></html>'''
(P/'compositions/relocation.html').write_text(html,'utf-8')

cap='''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template>
<style>#relocation-captions{position:absolute;inset:0}#relocation-captions .caption{position:absolute;left:96px;right:96px;top:932px;height:80px;border-radius:14px;background:#FFF;display:flex;align-items:center;justify-content:center;color:#173348;font-size:31px;line-height:1.2;letter-spacing:-.4px}#relocation-captions #caption-text{max-width:1648px;text-align:center;word-break:keep-all}#relocation-captions .source{position:absolute;left:96px;bottom:23px;font-size:17px;color:#526872;white-space:pre-line}</style>
<div id="relocation-captions" data-composition-id="relocation-captions" data-duration="DURATION" data-width="1920" data-height="1080"><div id="caption-box" class="caption"><span id="caption-text"></span></div><div id="source-text" class="source"></div></div>
<script>(()=>{const cues=CUES;const clock={t:0};const tl=gsap.timeline({paused:true});tl.to(clock,{t:DURATION,duration:DURATION,ease:'none',onUpdate:()=>{let cue=cues.find(c=>c.start<=clock.t&&c.end>clock.t);document.getElementById('caption-text').textContent=cue?cue.text:'';document.getElementById('caption-box').style.opacity=cue?'1':'0';document.getElementById('source-text').textContent=clock.t<24.2?'시간 순서 설명용 개념도 · 실제 공사기간·이동량을 나타내지 않습니다.':clock.t<56.5333334?'서문규·정재엽·이효중(2026), 「국토계획」 61(4) · 가락시영 · 59㎡ · 2011Q1–2014Q4':clock.t<72.5666667?'문헌에 기반한 구조 해석 · 서문규·정재엽·이효중(2026) · 실제 이동량·기여율 미표시':'후속 검증 질문 · 실제 이주 목적지·시점·이동량을 함께 확인해야 합니다.';}},0);window.__timelines['relocation-captions']=tl;})();</script></template></body></html>'''.replace('DURATION',str(D)).replace('CUES',json.dumps(captions,ensure_ascii=False))
(P/'compositions/captions.html').write_text(cap,'utf-8')
index=(APPROVED/'index.html').read_text('utf-8').replace('집 공간으로 설명하는 가구 분리','재건축 이주 · 집과 시간표').replace('data-duration="20"',f'data-duration="{D}"').replace('home-space','relocation-scene').replace('home-captions','relocation-captions').replace('compositions/relocation-scene.html','compositions/relocation.html')
(P/'index.html').write_text(index,'utf-8')
shutil.copy2(APPROVED/'hyperframes.json',P/'hyperframes.json')
(P/'timing.json').write_text(json.dumps({'scene_id':'L004','duration':D,'provisional':True,'narration_on_hold':True,'source_start':START,'beats':scene['beats'],'captions':captions},ensure_ascii=False,indent=2),'utf-8')
(P/'BRIEF.md').write_text('''---
workflow: general-video
flow: automation
storyboard: no
aspect: 1920x1080
language: ko
length: 86.566667s
---
## Accepted direction
2026-10-25 사용자: 인물 없이 집 공간으로 설명한 household-space-v1에 “맘에들어 다음”. 그 장면과 방식의 수락을 기록하고, 기존 승인 대본 L004 재건축 이주 장 전체로 진행한다.
## Constraints
승인 대본·기존 영상·수락한 가구 분리 시안을 보존한다. 음성 생성 보류, 새 유료 미디어·외부 전송·업로드 없음. 논문 결과/개념 순서/구조 해석/후속 질문을 구분한다. 실제 목적지별 이동 지도나 효과 크기는 만들지 않는다.
''','utf-8')
(P/'STORYBOARD.md').write_text('''# 재건축 이주 장

- 0–24.2초: 기존 집을 비운 뒤 다른 집에 살다가 새집에 입주하는 시간 순서. 승인한 집 단면 자산과 가상 건물을 사용한다. 기간과 지리 비례가 없는 개념도다.
- 24.2–38.667초: 가락시영 연구 사례. 주요 이주 기간 2012.8–2013.5와 연구 분석 기간을 구분한다.
- 38.667–56.533초: 과거 목적지 분포를 활용한 유입 추정, 59㎡ 매매가격·환산 임대료의 상승 방향. IV 가정과 방향성 표시를 명시한다.
- 56.533–72.567초: 원래 사업지의 거주 가능 주택 일시 감소와 대체 거주지 수요 증가 가능성을 나란히 구분한다.
- 72.567–86.567초: 경계 밖의 실제 목적지·시점·이동량을 함께 살필 세 질문. 결과 없는 지도·수치 미제시.

기존 대본·자막의 잠정 시간표를 사용한다. 최종 Jun 음성 동기와 연속 재생은 별도 검수 대상이다.
''','utf-8')
assets={'source_script_sha256':timing['script_sha256'],'accepted_household_sample_sha256':'67851a459535ba6f93feba957aa28abfd0af615d20e7af7322d78aa71a38424a','source_timing':'literature-visual-v1/project/timing.json','visuals':'Original conceptual SVG interiors/buildings, not an actual Garak Siyoung image or plan','new_paid_media_calls':0,'voice_generated':False,'source_R3':'https://www.kpaj.or.kr/_PR/view/?aidx=50743&bidx=4543','no_effect_size_adopted':True,'human_animation':False}
(P/'assets/provenance.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'project':str(P),'duration':D,'captions':len(captions),'building_asset_ready':asset.exists()}))
