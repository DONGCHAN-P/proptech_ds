from pathlib import Path
import json, shutil, copy, math

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/character-quality-v1'
P=OUT/'project'
OLD=ROOT/'outputs/literature-visual-v1/project'
for directory in (P/'assets/fonts',OUT/'checks'):
    directory.mkdir(parents=True,exist_ok=True)
for name in ('Pretendard-Regular.woff2','Pretendard-Bold.woff2'):
    shutil.copy2(OLD/'assets/fonts'/name,P/'assets/fonts'/name)
shutil.copy2(OLD/'assets/gsap.min.js',P/'assets/gsap.min.js')
base=json.loads((OUT/'checks/mascot-original.json').read_text('utf-8'))

def prop(v): return {'a':0,'k':v}
def col(h): return [int(h[n:n+2],16)/255 for n in (1,3,5)]+[1]
def tr(): return {'ty':'tr','p':prop([0,0]),'a':prop([0,0]),'s':prop([100,100]),'r':prop(0),'o':prop(100),'sk':prop(0),'sa':prop(0)}
def shape(ty,p,s,color,r=0,name='detail'):
    geo={'ty':ty,'d':1,'p':prop(p),'s':prop(s)}
    if ty=='rc':geo['r']=prop(r)
    return {'ty':'gr','nm':name,'it':[geo,{'ty':'fl','c':prop(col(color)),'o':prop(100),'r':1},tr()]}
def polygon(pts,color,name):
    geo={'ty':'sh','ks':prop({'i':[[0,0]]*len(pts),'o':[[0,0]]*len(pts),'v':pts,'c':True})}
    return {'ty':'gr','nm':name,'it':[geo,{'ty':'fl','c':prop(col(color)),'o':prop(100),'r':1},tr()]}

def value(p,t):
    if not p.get('a'):return p['k']
    keys=p['k']; prev=keys[0]
    for nxt in keys[1:]:
        if t<nxt['t']:
            f=max(0,min(1,(t-prev['t'])/(nxt['t']-prev['t'])))
            a=prev['s'];b=nxt['s'];v=[x+(y-x)*f for x,y in zip(a,b)]
            return v[0] if len(v)==1 else v
        prev=nxt
    v=prev['s'];return v[0] if len(v)==1 else v

def sample_prop(p,mode):
    if p.get('s') is True:
        return {'s':True,**{key:sample_prop(p.get(key,prop(0)),mode) for key in ('x','y','z')}}
    if not p.get('a'):return copy.deepcopy(p)
    if mode=='idle':return prop(value(p,146))
    keys=[]
    for f in range(601):
        src=146 if f<150 else min(225,f-150)
        v=value(p,src)
        if isinstance(v,(float,int)):v=[v]
        keys.append({'t':f,'s':v,'i':{'x':[1],'y':[1]},'o':{'x':[0],'y':[0]}})
    return {'a':1,'k':keys}

def character(offset,mode,stage_x,stage_y,scale,shirt,hair):
    layers=copy.deepcopy(base['layers'])
    for layer in layers:
        layer['ind']+=offset
        if 'parent' in layer: layer['parent']+=offset
        else:layer['parent']=offset+100
        layer['ip']=0;layer['op']=600;layer['st']=0
        nm=layer['nm'];layer['nm']=f'{offset}.{nm}'
        layer['ks']={k:sample_prop(v,mode) for k,v in layer['ks'].items()}
        if mode=='walk' and nm not in ('hip','shadow','eye'):
            rotation=layer['ks'].get('r',{})
            if rotation.get('a'):
                first=value(next(x for x in base['layers'] if x['nm']==nm)['ks']['r'],0)
                for k in rotation['k']:
                    f=k['t']
                    if f<150:
                        a=max(0,min(1,(f-144)/6)); k['s']=[first*a*a*(3-2*a)]
                    elif nm.startswith('leg.') and f>=296:
                        a=max(0,min(1,(f-296)/24));k['s']=[k['s'][0]*(1-a*a*(3-2*a))]
                    elif f>=354:
                        a=max(0,min(1,(f-354)/36));k['s']=[k['s'][0]*(1-a*a*(3-2*a))]
        if nm=='hip':
            if mode=='walk':
                # Retain the reference walk's travel/stride relationship; only add a 5 s standing pre-roll.
                x=layer['ks']['p']['x']
                for k in x['k']:
                    if k['t']<150:k['s']=[-140]
            else:layer['ks']['p']={'s':True,'x':prop(764),'y':prop(736),'z':prop(0)}
        if nm=='shadow':layer['ks']['o']=prop(10)
        if nm=='shadow' and mode=='walk':
            for k in layer['ks']['p']['x']['k']:
                if k['t']<150:k['s']=[-140]
        skin='#D9A681'; dark='#173348'; trousers='#233C51'
        for group in layer.get('shapes',[]):
            group['it']=[item for item in group['it'] if item.get('ty')!='st']
            for item in group['it']:
                if item.get('ty')=='fl':
                    color=shirt if nm=='torso' or nm.endswith('upper') else trousers if nm.startswith('leg.') else skin
                    if nm=='eye':color=dark
                    if nm=='shadow':color=dark
                    if nm.endswith('foot'):color=dark
                    item['c']=prop(col(color))
        if nm=='head':
            layer['shapes']=[
                shape('el',[-17,-112],[89,44],hair,name='side swept hair'),
                shape('rc',[-35,-68],[30,69],hair,13,'side hair'),
                shape('rc',[42,-44],[12,3],'#8D5D44',1,'mouth'),
                shape('el',[52,-62],[12,20],skin,name='nose'),
                shape('el',[-14,-64],[18,25],skin,name='ear'),
                shape('el',[4,-70],[100,112],skin,name='face'),
                shape('el',[1,-100],[108,64],hair,name='hair back'),
                shape('rc',[0,-28],[30,40],skin,10,'neck'),
            ]
            if offset==400:
                layer['shapes'].insert(0,shape('el',[-42,-80],[38,70],hair,name='tied hair'))
        if nm=='eye':layer['ks']['p']=prop([42,-75,0]);layer['shapes']=[shape('el',[0,0],[7,9],dark,name='eye')]
        if nm=='torso':
            layer['shapes']=[
                shape('rc',[30,-102],[26,31], '#4C80B5' if mode=='walk' else '#AE9470',3,'pocket'),
                polygon([[-22,-167],[0,-139],[21,-167]],'#F6F4EF','collar'),
                shape('rc',[0,2],[112,14],trousers,4,'belt'),
                shape('rc',[0,-78],[116,178],shirt,25,'tailored shirt')]
        if nm.startswith('arm.') and nm.endswith('upper'):
            for group in layer['shapes']:
                for item in group['it']:
                    if item.get('ty')=='rc':item['s']=prop([40,86]);item['r']=prop(18)
        if nm.startswith('arm.') and nm.endswith('fore'):
            layer['shapes']=[shape('rc',[0,26],[28,65],skin,13,'forearm'),shape('el',[0,65],[31,38],skin,name='hand')]
        if nm.endswith('foot'):
            layer['shapes']=[shape('rc',[16,11],[67,7],'#F6F4EF',3,'sole'),shape('rc',[14,0],[66,27],dark,10,'shoe')]
        if mode=='idle' and nm.startswith('leg.'):
            layer['ks']['r']=prop(0)
    parent={'ddd':0,'ind':offset+100,'ty':3,'nm':f'{offset}.stage','sr':1,'ks':{'o':prop(100),'r':prop(0),'p':prop([stage_x,stage_y,0]),'a':prop([0,0,0]),'s':prop([scale,scale,100])},'ip':0,'op':600,'st':0,'bm':0}
    return layers+[parent]

layers=[]
# Standing parents use the stopped reference pose; the adult child uses a delayed walk, settle and gesture.
layers+=character(0,'walk',777,165.3,62,'#326EC5','#173348')
layers+=character(200,'idle',104,219.7,56,'#AD8C60','#6B7477')
layers+=character(400,'idle',-60,219.7,56,'#7B8E87','#3E4E56')
asset={'v':'5.7.4','fr':30,'ip':0,'op':600,'w':1920,'h':1080,'nm':'Household formation — redesigned characters','ddd':0,'assets':[],'layers':layers,'markers':[{'tm':150,'cm':'adult child begins walking','dr':0},{'tm':296,'cm':'arrival','dr':0},{'tm':313,'cm':'gesture','dr':0}]}
(P/'assets/household-characters.json').write_text(json.dumps(asset,separators=(',',':')),'utf-8')

def room(x,width,name,blue=False):
    wall='#DFE8EC' if blue else '#E4DFD5';side='#C7D7E3' if blue else '#CEC7BB'; accent='#326EC5' if blue else '#7B8E87'
    return f'''<g id="{name}">
    <path d="M{x} 352h{width}l35 25v370h-{width}l-35-25Z" fill="{side}"/>
    <path d="M{x+35} 377h{width-35}v345h-{width-35}Z" fill="{wall}"/>
    <path d="M{x} 722h{width}l35 25H{x+35}Z" fill="#C6B69D"/>
    <path d="M{x+36} 713h{width-36}v9H{x+36}Z" fill="#AD9F8A"/>
    <rect x="{x+62}" y="405" width="172" height="143" rx="3" fill="#AEC7D5"/>
    <path d="M{x+67} 409h162v134h-162Z" fill="#F5F8F5"/>
    <path d="M{x+148} 409v134M{x+67} 485h162" fill="none" stroke="#AEC7D5" stroke-width="5"/>
    <path d="M{x+72} 529l45-27 31 18 40-34 36 16v41h-152Z" fill="#DFE8E4"/>
    <path d="M{x+54} 401h29l-8 166h-34Z" fill="#EEECE3"/>
    <rect x="{x+width-165}" y="423" width="88" height="109" fill="#F5F4EE"/>
    <path d="M{x+width-148} 506l21-41 34 41Z" fill="{accent}"/>
    <ellipse cx="{x+width-114}" cy="450" rx="11" ry="11" fill="#C29A44"/>
    <rect x="{x+56}" y="632" width="202" height="67" rx="18" fill="{accent}"/>
    <rect x="{x+65}" y="584" width="182" height="72" rx="17" fill="{accent}"/>
    <path d="M{x+151} 589v54" stroke="#F6F4EF" stroke-opacity=".3" stroke-width="3"/>
    <path d="M{x+69} 693v23M{x+243} 693v23" stroke="#173348" stroke-width="9"/>
    <path d="M{x+width-55} 690v-105M{x+width-55} 638q-48-44-26-64q38 12 26 64M{x+width-55} 662q42-59 59-45q-3 38-59 45" fill="#6E8B7C"/>
    <path d="M{x+width-84} 674h58l-9 48h-40Z" fill="#B59172"/>
    </g>'''

html='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>인물 장면 교체 시안</title>
<script src="assets/gsap.min.js"></script><script src="assets/lottie.min.js"></script>
<style>
@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2');font-weight:400}@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}body{margin:0;color:#173348;background:#F6F4EF;font-family:Pretendard,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden;background:#F6F4EF}
.clip{position:absolute;inset:0}.brand{position:absolute;left:80px;top:37px;font-size:22px;letter-spacing:-.2px}.series{position:absolute;right:80px;top:40px;font-size:18px;color:#607680}.rule{position:absolute;left:80px;right:80px;top:87px;height:1px;background:#D6DCD9}
.kicker{position:absolute;left:80px;top:123px;font-size:23px;color:#607680}.headline{position:absolute;left:76px;top:165px;font-size:66px;line-height:1.1;font-weight:700;letter-spacing:-2.3px}.headline b{color:#286CDA}.illustration{position:absolute;inset:0;width:100%;height:100%}#camera{position:absolute;inset:0;transform-origin:50% 65%}#people{position:absolute;inset:0}#people svg{overflow:visible}
.tag{font-size:23px;fill:#173348;font-weight:700}.small{font-size:19px;fill:#607680}.numberline{position:absolute;left:82px;top:780px;display:flex;gap:50px;align-items:center}.stat{display:flex;gap:17px;align-items:baseline}.stat .label{font-size:24px;color:#607680}.stat strong{font-size:57px;letter-spacing:-1.5px}.divider{height:50px;width:1px;background:#C8D0CD}.stat.house strong{color:#286CDA}.caption{position:absolute;left:96px;right:96px;top:914px;height:92px;background:#FFF;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:34px;letter-spacing:-.5px}.source{position:absolute;left:96px;bottom:24px;font-size:18px;color:#607680}.concept{position:absolute;right:81px;top:128px;font-size:19px;color:#607680}.readout{display:inline-flex;height:72px;overflow:hidden;vertical-align:bottom}.digits{display:flex;flex-direction:column}.digits span{height:72px;line-height:72px}.explain{position:absolute;right:80px;top:800px;font-size:25px;line-height:1.4;text-align:right}.explain b{color:#286CDA}.stamp{position:absolute;right:80px;top:170px;font-size:16px;color:#607680}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="20" data-width="1920" data-height="1080" data-fps="30">
<section class="clip" data-start="0" data-duration="20" data-track-index="1"><div class="brand">데이터로 보는 부동산</div><div class="series">근거로 읽는 집값</div><div class="rule"></div><div class="kicker">01 · 인구와 가구</div><div class="headline">사람은 그대로,<br>필요한 집은 <b>늘어납니다.</b></div><div class="concept">가구 분리 과정 · 가상 예시</div>
<div id="camera"><svg class="illustration" viewBox="0 0 1920 1080" aria-label="한 집에서 함께 살던 세 사람이 두 가구로 나뉘는 설명용 예시"><defs><filter id="roomShadow" x="-20%" y="-20%" width="150%" height="170%"><feDropShadow dx="0" dy="15" stdDeviation="14" flood-color="#173348" flood-opacity=".09"/></filter></defs>
<path id="ground" d="M135 749H1784" stroke="#D1D8D2" stroke-width="2"/>
<g id="rooms" filter="url(#roomShadow)">ROOMS</g>
<g id="homeLabels"><text class="tag" x="540" y="783" text-anchor="middle">함께 살던 집</text><text id="newHomeLabel" class="tag" x="1445" y="783" text-anchor="middle">독립한 자녀의 집</text></g>
<g id="movingBox"><path d="M1480 670l43-15 40 16-41 17Z" fill="#D9BC86"/><path d="M1480 670l42 18v58l-42-20Z" fill="#BE9863"/><path d="M1522 688l41-17v58l-41 17Z" fill="#D1AE78"/><path d="M1504 662l41 17v20l-13 5v-20l-42-17Z" fill="#F1D9A7"/></g>
</svg><div id="people"></div></div>
<div class="numberline"><div class="stat"><span class="label">인구</span><strong>3명</strong></div><div class="divider"></div><div class="stat house"><span class="label">가구</span><strong><span class="readout"><span class="digits" id="houseCount"><span>1</span><span>2</span></span></span>가구</strong></div></div>
<div class="explain" id="conclusion">인구가 늘지 않아도<br><b>주거 수요는 달라질 수 있습니다.</b></div>
<div class="caption"><span id="captionText">부모와 성인 자녀, 세 사람이 한 집에 살고 있다고 하겠습니다.</span></div>
<div class="source">구조 설명용 가상 예시 · 실제 지역의 인구·가구 통계가 아닙니다.</div><div class="stamp">인물·동작 교체 시안</div></section></div>
<script>
const characters=lottie.loadAnimation({container:document.getElementById('people'),renderer:'svg',loop:false,autoplay:false,path:'assets/household-characters.json'});window.__hfLottie=window.__hfLottie||[];window.__hfLottie.push(characters);
const tl=gsap.timeline({paused:true});
tl.fromTo('.headline',{y:18,opacity:0},{y:0,opacity:1,duration:.7,ease:'power3.out'},0);
tl.fromTo('#camera',{scale:1.09,x:90},{scale:1,x:0,duration:5.2,ease:'power2.inOut'},3.7);
tl.fromTo('#roomB',{opacity:0,x:125},{opacity:1,x:0,duration:1.1,ease:'power3.out'},6.3);
tl.fromTo('#newHomeLabel',{opacity:0,y:8},{opacity:1,y:0,duration:.6,ease:'power2.out'},9.5);
tl.fromTo('#movingBox',{opacity:0,y:-15},{opacity:1,y:0,duration:.65,ease:'power3.out'},9.7);
tl.fromTo('#houseCount',{y:0},{y:-72,duration:.7,ease:'power3.inOut'},10.3);
tl.fromTo('#conclusion',{opacity:0,y:16},{opacity:1,y:0,duration:.7,ease:'power3.out'},13.6);
const captions=[{at:0,text:'부모와 성인 자녀, 세 사람이 한 집에 살고 있다고 하겠습니다.'},{at:5,text:'자녀가 독립해서 따로 살면 사람은 여전히 세 명입니다.'},{at:10.3,text:'하지만 사는 집은 한 곳에서 두 곳으로 늘어납니다.'},{at:15.2,text:'이것은 가구가 나뉘는 과정을 설명하는 예시입니다.'}];
const clock={t:0};tl.to(clock,{t:20,duration:20,ease:'none',onUpdate:()=>{let cue=captions[0];for(const c of captions){if(c.at<=clock.t)cue=c;}document.getElementById('captionText').textContent=cue.text;}},0);
window.__timelines['main']=tl;
</script></body></html>'''.replace('ROOMS',room(190,700,'roomA')+room(1150,590,'roomB',True)).replace('#607680','#526872').replace('<section class="clip"','<section id="household-scene" class="clip"')
html=html.replace('<div class="explain" id="conclusion">인구가 늘지 않아도<br><b>주거 수요는 달라질 수 있습니다.</b></div>','')
html=html.replace("tl.fromTo('#conclusion',{opacity:0,y:16},{opacity:1,y:0,duration:.7,ease:'power3.out'},13.6);",'')
(P/'index.html').write_text(html,'utf-8')
(P/'hyperframes.json').write_text(json.dumps({'authoringSkill':'general-video','paths':{'assets':'assets','blocks':'compositions','components':'components'}},indent=2),'utf-8')
(P/'BRIEF.md').write_text('''---
workflow: general-video
flow: automation
storyboard: no
aspect: 1920x1080
language: ko
length: 20s
---
## Intent
사용자의 졸라맨 품질 피드백에 대한 L002-P2 교체 시안. 기존 대본 문장은 유지하고 인물 원화·관절 동작·주거 공간·구도 전환을 비교한다. 전체 본편 교체 전의 로컬 시안이다. v3에서 대기·도착 자세와 결론 정보 위계를 정리했다.
## Constraints
새 유료 생성·내레이션·외부 전송 없음. 기존 본편·대본 보존. 가구 분리 가상 예시임을 표시한다.
''','utf-8')
(P/'STORYBOARD.md').write_text('''# 인물 장면 교체 시안

피드백: 가느다란 졸라맨, 도형의 미끄러짐, 같은 도식 반복으로 품질이 낮다.

- 0–5초: 같은 실내에 부모·성인 자녀. 색면 인물, 머리·옷·얼굴·신발과 가구가 있는 공간.
- 5–10초: 성인 자녀의 관절 걷기 → 정지. 다른 공간이 열리며 카메라가 물러나 전체 관계를 드러낸다.
- 10–15초: 가구 수가 1에서 2로 넘어간다. 인구 3명은 유지한다.
- 15–20초: 설명 문장과 가구 분리 결과를 읽을 시간 확보.

## 기술과 미감의 검수 구분
캐릭터는 공식 HyperFrames Apache-2.0 예제의 걷기·정지·가리키기 관절 동작을 바탕으로 원화와 시간표를 변경했다. 손수 그린 실내는 가상 공간이다. Lottie는 동작 재생 수단이며 그 자체가 디자인 품질을 보장하지 않는다. 멈춤·접지·좌우 시선 흐름을 실제 렌더에서 별도로 확인한다.
''','utf-8')
(P/'assets/provenance.json').write_text(json.dumps({'character':{'source':'https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/lottie-character-walk','license':'Apache-2.0','modifications':'new face/hair/clothing/shoes, family variants, delayed choreography; original walk kinematics retained','original':str(OUT/'checks/mascot-original.json')},'lottie_web':{'source':'https://github.com/airbnb/lottie-web','version':'5.12.2','license':'MIT'},'rooms':{'source':'Original code-native vector art, conceptual apartment interiors, not an actual property'},'fonts':'Existing locally licensed Pretendard project assets','paid_calls':0,'voice_generation':False},ensure_ascii=False,indent=2),'utf-8')
shutil.copy2(OUT/'checks/HYPERFRAMES-LICENSE',P/'assets/HYPERFRAMES-LICENSE')
print(json.dumps({'project':str(P),'duration':20,'characters':3,'paid_calls':0}))
