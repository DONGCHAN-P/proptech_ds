from pathlib import Path
import shutil,json,hashlib

EP=Path(__file__).resolve().parents[2]
OUT=EP/'outputs/household-space-v1';P=OUT/'project'
OLD=EP/'outputs/character-quality-v1/project'
for d in (P/'assets/fonts',P/'compositions',OUT/'checks'):
    d.mkdir(parents=True,exist_ok=True)
for name in ('Pretendard-Regular.woff2','Pretendard-Bold.woff2'):
    shutil.copy2(OLD/'assets/fonts'/name,P/'assets/fonts'/name)
shutil.copy2(OLD/'assets/gsap.min.js',P/'assets/gsap.min.js')

def mug(x,y,color='#D8C2A0',ident=''):
    return f'<g {"id="+chr(34)+ident+chr(34) if ident else ""}><ellipse cx="{x+11}" cy="{y+19}" rx="18" ry="4" fill="#C2B8A7" opacity=".25"/><path d="M{x} {y}h22v15q-11 7-22 0Z" fill="{color}"/><path d="M{x+22} {y+3}h5q7 8-5 10" fill="none" stroke="{color}" stroke-width="4"/><ellipse cx="{x+11}" cy="{y}" rx="11" ry="3" fill="#F7F3E7"/><ellipse cx="{x+11}" cy="{y+1}" rx="8" ry="1.5" fill="#8C7057"/></g>'

def shell(x,w,wall,side,ident):
    return f'''<g id="{ident}">
    <ellipse cx="{x+w/2+15}" cy="730" rx="{w*.52}" ry="17" fill="#173348" opacity=".06"/>
    <path d="M{x} 354h{w}l32 22v348H{x+32}l-32-22Z" fill="{side}"/>
    <path d="M{x+32} 376h{w-32}v326H{x+32}Z" fill="{wall}"/>
    <path d="M{x} 702h{w}l32 22H{x+32}Z" fill="#D1C1A8"/>
    <path d="M{x+32} 724h{w}v12H{x+32}Z" fill="#B9A88D"/>
    <path d="M{x+32} 376v326" stroke="#B1AFA4" stroke-width="2" opacity=".5"/>
    <path d="M{x+78} 702l32 22m120-22l32 22m120-22l32 22m120-22l32 22" stroke="#A99475" stroke-width="1.4" opacity=".4"/>
    </g>'''

def window(x,y,w=170,h=144):
    return f'''<g><rect x="{x-5}" y="{y-5}" width="{w+10}" height="{h+10}" rx="2" fill="#BBCACD"/>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ECF2F0"/>
    <path d="M{x} {y+h-35}l{w*.25}-22 {w*.21} 17 {w*.3}-32 {w*.24} 18v19H{x}Z" fill="#D3DFD9"/>
    <path d="M{x+w/2} {y}v{h}M{x} {y+h*.6}h{w}" stroke="#B2C5C9" stroke-width="4"/>
    <path d="M{x-12} {y-8}h29l-6 {h+33}h-39Z" fill="#F4F0E6"/>
    <path d="M{x+w-10} {y-8}h26l12 {h+33}h-31Z" fill="#F4F0E6"/>
    <path d="M{x+6} {y+4}l-9 {h+10}M{x+w+5} {y+4}l10 {h+10}" stroke="#DCD6CA" stroke-width="2"/>
    </g>'''

family=shell(160,750,'#E5E0D4','#CFC8B9','family-shell')+window(213,402,175,145)+'''
<g id="family-furnishings">
<path d="M438 684h343l23 18H420Z" fill="#B6C1B7"/>
<rect x="465" y="563" width="284" height="112" rx="22" fill="#758C82"/>
<rect x="484" y="532" width="247" height="88" rx="21" fill="#869C91"/>
<rect x="473" y="603" width="273" height="49" rx="13" fill="#7C9388"/>
<path d="M568 541v64m78-64v64" stroke="#D6DDD2" stroke-width="2" opacity=".45"/>
<path d="M484 671v24m247-24v24" stroke="#304B47" stroke-width="10"/>
<path d="M491 551l46-3 4 47-46 3Z" fill="#D9CCAB"/>
<path d="M676 554l33 8-10 39-33-8Z" fill="#B5C2B7"/>
<path d="M494 664h155l12 9H482Z" fill="#AE8D68"/>
<path d="M505 671v29m134-29v29" stroke="#725F4B" stroke-width="6"/>
<path d="M524 650h57v11h-57Z" fill="#F3EBDD"/><path d="M524 647h57v5h-57Z" fill="#466C87"/>
<path d="M237 604h155l13 11H225Z" fill="#B7956F"/>
<path d="M246 613v88m138-88v88" stroke="#8C7055" stroke-width="7"/>
<path d="M253 627h-22v50h22M383 627h21v50h-21" fill="none" stroke="#9F8B6E" stroke-width="7"/>
<rect x="563" y="413" width="120" height="87" rx="1" fill="#F3EEE2"/>
<path d="M578 481l30-43 22 29 21-18 18 32Z" fill="#A8BAAC"/>
<circle cx="650" cy="433" r="11" fill="#BEA36C"/>
<path d="M777 502v192m-28 0h56" stroke="#A38B66" stroke-width="5"/>
<path d="M749 472h57l20 45h-96Z" fill="#E2CD9C"/>
<path d="M828 663v-72m0 42q-51-49-33-69q43 6 33 69m0 17q34-61 62-47q-5 41-62 47" fill="#7F9784"/>
<path d="M802 659h55l-9 43h-37Z" fill="#B89779"/>
</g>'''+mug(265,592,'#D1B48D')+mug(308,592,'#8DA397')+mug(351,592,'#7297BA','child-cup-old')

studio=shell(1122,590,'#E0E8E7','#C4D2D0','studio-shell')+window(1172,405,175,130)+'''
<g id="studio-furnishings">
<path d="M1437 569h243v113h-243Z" fill="#BAA88C"/>
<rect x="1451" y="540" width="217" height="48" rx="5" fill="#B2A186"/>
<rect x="1427" y="574" width="265" height="91" rx="13" fill="#EEE9DB"/>
<path d="M1523 575h153q17 0 17 19v67h-170Z" fill="#91A8B0"/>
<path d="M1523 646h170v19h-170Z" fill="#7D969F"/>
<rect x="1446" y="579" width="64" height="32" rx="10" fill="#F8F2E4"/>
<path d="M1443 677v24m231-24v24" stroke="#8F7B60" stroke-width="8"/>
<path d="M1178 569h220l15 10h-252Z" fill="#AE906D"/>
<path d="M1183 579v123m210-123v123" stroke="#88765E" stroke-width="7"/>
<path d="M1244 534h94l13 30h-115Z" fill="#80939C"/>
<path d="M1248 503h83v50h-83Z" fill="#526E7E"/>
<path d="M1254 508h71v39h-71Z" fill="#DCE7E5"/>
<path d="M1262 520h49m-49 8h37m-37 8h42" stroke="#A7BDBE" stroke-width="3"/>
<path d="M1239 563h111l-9 5h-91Z" fill="#B6C2C4"/>
<rect x="1252" y="608" width="70" height="55" rx="9" fill="#91A396"/>
<path d="M1287 657v37m-25 7h50" stroke="#657C74" stroke-width="5"/>
<path d="M1466 451h188v9h-188Z" fill="#B19C80"/>
<path d="M1480 400h13v50h-13Z" fill="#728D83"/><path d="M1495 408h12v42h-12Z" fill="#B69B72"/><path d="M1510 395h15v55h-15Z" fill="#66859B"/>
<path d="M1607 414v35m0-13q-28-30-17-38q23 2 17 38m0 1q22-33 36-22q-4 22-36 22" fill="#7E9782"/>
<path d="M1591 436h33l-6 15h-21Z" fill="#C1A07E"/>
<rect x="1141" y="640" width="44" height="62" rx="6" fill="#A79170"/>
<path d="M1152 641v-12h21v12m-10 0v61" stroke="#6D7063" stroke-width="3" fill="none"/>
<circle cx="1150" cy="705" r="4" fill="#526C70"/><circle cx="1177" cy="705" r="4" fill="#526C70"/>
</g>'''+mug(1363,555,'#7297BA','child-cup-new')

scene='''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template>
<style>
#home-space{position:absolute;inset:0;color:#173348}#home-space .brand{position:absolute;left:80px;top:38px;font-size:22px}#home-space .series{position:absolute;right:80px;top:42px;font-size:18px;color:#526872}#home-space .rule{position:absolute;left:80px;right:80px;top:87px;height:1px;background:#D6DCD9}
#home-space .kicker{position:absolute;left:80px;top:126px;font-size:23px;color:#526872}#home-space .headline{position:absolute;left:78px;top:171px;font-size:65px;font-weight:700;line-height:1.12;letter-spacing:-2px}#home-space .headline b{color:#286CDA}#home-space .concept{position:absolute;right:80px;top:132px;font-size:19px;color:#526872}
#home-space #world{position:absolute;inset:0;transform-origin:0 0}#home-space svg{width:100%;height:100%;overflow:visible}#home-space svg text{font-family:inherit}.room-label{font-size:24px;fill:#173348;font-weight:700}.room-note{font-size:20px;fill:#526872}
#home-space .numbers{position:absolute;left:82px;top:818px;height:75px;display:flex;align-items:center;gap:48px}#home-space .stat{display:flex;align-items:baseline;gap:20px}#home-space .stat .label{font-size:25px;color:#526872}#home-space .stat strong{font-size:58px;letter-spacing:-1px;line-height:72px}#home-space .divider{height:48px;width:1px;background:#CAD1CA}#home-space .house strong{color:#286CDA}
#home-space .counter{display:inline-block;vertical-align:bottom;position:relative;width:39px;height:72px}#home-space .counter span{position:absolute;left:0;top:0;height:72px;line-height:72px}#home-space .status{position:absolute;right:81px;top:837px;font-size:25px;color:#526872}#home-space .status b{color:#286CDA}
</style>
<div id="home-space" data-composition-id="home-space" data-duration="20" data-width="1920" data-height="1080">
<div class="brand">데이터로 보는 부동산</div><div class="series">근거로 읽는 집값</div><div class="rule"></div><div class="kicker">01 · 인구와 가구</div>
<div class="headline">같은 세 사람,<br>사는 집은 <b>두 곳으로.</b></div><div class="concept">가구 분리 과정 · 가상 예시</div>
<div id="world"><svg viewBox="0 0 1920 1080" role="img" aria-label="한 집에서 함께 살던 세 사람이 두 집에서 따로 거주하게 되는 설명용 예시">
<g id="family-home">FAMILY
<text id="family-label-before" class="room-label" x="535" y="330" text-anchor="middle">부모와 성인 자녀 · 함께 거주</text>
<text id="family-label-after" class="room-label" x="535" y="330" text-anchor="middle">부모 · 기존 집에서 계속 거주</text>
<text class="room-note" x="535" y="781" text-anchor="middle">기존 집</text></g>
<g id="studio-home">STUDIO
<text class="room-label" x="1417" y="330" text-anchor="middle">성인 자녀 · 다른 집으로 독립</text>
<text class="room-note" x="1417" y="781" text-anchor="middle">자녀가 따로 마련한 집</text></g>
</svg></div>
<div class="numbers"><div class="stat"><span class="label">인구</span><strong>3명</strong></div><div class="divider"></div><div class="stat house"><span class="label">가구</span><strong><span class="counter"><span id="house-number">1</span></span>가구</strong></div></div>
<div id="end-status" class="status">사람 수는 그대로, <b>가구 수는 증가</b></div>
</div>
<script>(()=>{const tl=gsap.timeline({paused:true});
tl.fromTo('.headline',{opacity:0,y:10},{opacity:1,y:0,duration:.65,ease:'power2.out'},0);
tl.fromTo('#world',{scale:1.12,x:361,y:-52},{scale:1,x:0,y:0,duration:3.2,ease:'sine.inOut'},4.6);
tl.fromTo('#studio-home',{opacity:0},{opacity:1,duration:1.5,ease:'sine.inOut'},6);
tl.fromTo('#family-label-before',{opacity:1},{opacity:0,duration:.65,ease:'sine.inOut'},6);
tl.fromTo('#family-label-after',{opacity:0},{opacity:1,duration:.8,ease:'sine.inOut'},6.55);
tl.fromTo('#child-cup-old',{opacity:1},{opacity:0,duration:.7,ease:'sine.inOut'},6.1);
tl.fromTo('#child-cup-new',{opacity:0},{opacity:1,duration:.8,ease:'sine.inOut'},7.1);
const clock={t:0};tl.to(clock,{t:20,duration:20,ease:'none',onUpdate:()=>{document.getElementById('house-number').textContent=clock.t<8.2?'1':'2';}},0);
tl.fromTo('#end-status',{opacity:0},{opacity:1,duration:1.0,ease:'sine.inOut'},11.3);
window.__timelines['home-space']=tl;})();</script>
</template></body></html>'''.replace('FAMILY',family).replace('STUDIO',studio)
(P/'compositions/home-space.html').write_text(scene,'utf-8')
captions=[{'at':0,'text':'부모와 성인 자녀, 세 사람이 한 집에 살고 있다고 하겠습니다.'},{'at':5,'text':'자녀가 독립해서 따로 살면 사람은 여전히 세 명입니다.'},{'at':10.3,'text':'하지만 사는 집은 한 곳에서 두 곳으로 늘어납니다.'},{'at':15.2,'text':'이것은 가구가 나뉘는 과정을 설명하는 예시입니다.'}]
cap='''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template>
<style>#home-captions{position:absolute;inset:0}#home-captions .caption{position:absolute;left:96px;right:96px;top:932px;height:80px;border-radius:14px;background:#FFF;display:flex;align-items:center;justify-content:center;color:#173348;font-size:34px;letter-spacing:-.5px}#home-captions .source{position:absolute;left:96px;bottom:24px;font-size:18px;color:#526872}</style>
<div id="home-captions" data-composition-id="home-captions" data-duration="20" data-width="1920" data-height="1080"><div class="caption"><span id="caption-text">부모와 성인 자녀, 세 사람이 한 집에 살고 있다고 하겠습니다.</span></div><div class="source">구조 설명용 가상 예시 · 실제 지역의 인구·가구 통계가 아닙니다.</div></div>
<script>(()=>{const cues=CUES;const clock={t:0};const tl=gsap.timeline({paused:true});tl.to(clock,{t:20,duration:20,ease:'none',onUpdate:()=>{let cue=cues[0];for(const c of cues){if(c.at<=clock.t)cue=c;}document.getElementById('caption-text').textContent=cue.text;}},0);window.__timelines['home-captions']=tl;})();</script></template></body></html>'''.replace('CUES',json.dumps(captions,ensure_ascii=False))
(P/'compositions/captions.html').write_text(cap,'utf-8')
index='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>집 공간으로 설명하는 가구 분리</title><script src="assets/gsap.min.js"></script><style>
@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2');font-weight:400}@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}body{margin:0;background:#F6F4EF;font-family:Pretendard,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden;background:#F6F4EF}.clip{position:absolute;inset:0}
</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="20" data-fps="30">
<div id="space-scene" class="clip" data-composition-id="home-space" data-composition-src="compositions/home-space.html" data-width="1920" data-height="1080" data-start="0" data-duration="20" data-track-index="1"></div>
<div id="caption-scene" class="clip" data-composition-id="home-captions" data-composition-src="compositions/captions.html" data-width="1920" data-height="1080" data-start="0" data-duration="20" data-track-index="2"></div>
</div><script>window.__timelines['main']=gsap.timeline({paused:true});</script></body></html>'''
(P/'index.html').write_text(index,'utf-8')
(P/'hyperframes.json').write_text(json.dumps({'authoringSkill':'general-video','paths':{'assets':'assets','blocks':'compositions','components':'components'}},indent=2),'utf-8')
(P/'BRIEF.md').write_text('''---
workflow: general-video
flow: automation
storyboard: no
aspect: 1920x1080
language: ko
length: 20s
---
## Accepted change
2026-10-25 사용자: 기존 시안은 마음에 들지 않는다. 집을 보여주는 방식은 좋으나 걷기가 이상하다. 집 단면 구도는 계승하고 보행 인물은 제거한다. 기존 대본의 동일한 가구 분리 예시로 공간 중심 교체 시안을 제작한다.
## Constraints
새 유료 생성·음성·외부 전송·업로드 없음. 기존 모든 본편/시안과 승인 대본 보존. 실제 단지나 통계로 제시하지 않는다. 본편 전체 반영은 아직 수행하지 않는다.
''','utf-8')
(P/'STORYBOARD.md').write_text('''# 집 공간 중심 수정 시안

## 최신 피드백과 선택
집을 보여주는 방식은 유지한다. 인물 원화를 조금 바꾸며 같은 보행을 반복하는 대신, 캐릭터의 관절/발 미끄러짐 문제가 생기지 않도록 이 장면에서 인물을 제거한다.

- 0–4.6초: 가족의 거실을 조금 가까이 보여준다. 세 개의 잔과 함께 거주 라벨. 인구 3명, 1가구.
- 4.6–7.8초: 카메라가 완만하게 물러나며 별도 원룸을 제시한다. 물리적으로 한 집을 쪼개거나 현관을 관통하는 표현을 쓰지 않는다.
- 6–8초: 기존 집의 부모/자녀 함께 거주 라벨이 부모 거주 라벨로 바뀐다. 자녀의 잔은 사라지고 별도 집의 같은 색 잔이 나타난다. 거실과 원룸은 서로 다른 가구 배치로 구분한다.
- 8.2초: 두 번째 집이 나타난 상태에 맞춰 인구 3명은 유지한 채 1가구에서 2가구로 전환한다. 10.3초 자막에서 이를 다시 설명한다.
- 15.2–20초: 예시라는 기존 대본 문장으로 정리하며 두 공간과 결과를 유지한다.

## 검수
보행 캐릭터와 움직이는 사람/가구/이사 상자는 없다. 가구 분리 가정·원문 자막·1→2가구·독립된 집 라벨·카메라와 자막 경계·이미지 잘림을 실제 출력에서 확인한다. 표본 프레임과 연속 재생은 별도로 기록한다.
''','utf-8')
(P/'assets/provenance.json').write_text(json.dumps({'rooms':'Original code-native SVG conceptual interiors. Not a real property, not an actual floor plan.','assets_reused':['Existing local Pretendard fonts','Existing local GSAP'], 'new_paid_media_calls':0,'human_animation':False,'script_text_unchanged':True,'captions':captions,'source_script_sha256':hashlib.sha256((EP/'outputs/literature-video-v1/내레이션_초안.md').read_bytes()).hexdigest(),'catalog_query':{'query':'architectural cutaway room interior camera reveal','result':[]}},ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'project':str(P),'duration':20,'characters':0,'new_paid_media_calls':0}))
