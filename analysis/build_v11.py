from pathlib import Path
import json,re
src=Path('video/src');out=Path('video/public/pilot-v11');out.mkdir(exist_ok=True)
q=(src/'QuarterChartsV10.tsx').read_text(encoding='utf8').replace("'#777E87','#9AA0A6','#B4A8A0'","'#167A89','#D07812','#8658B4'")
q=q.replace('y%2===0||y===2026','y%2===0||y===from||y===2026').replace('!compact||y%2===0','y%2===0')
q=q.replace('fontSize="25" fill={colors[actual]}','fontSize="30" fill={colors[actual]} stroke="#F6F4EF" strokeWidth="7" paintOrder="stroke" fontWeight="700"')
q=q.replace('fontSize="21" fill="#777"','fontSize="25" fill="#555" stroke="#F6F4EF" strokeWidth="6" paintOrder="stroke"')
q=q.replace('fontSize="30" fontWeight="700" fill={colors[actual]}','fontSize="36" fontWeight="700" fill={colors[actual]} stroke="#F6F4EF" strokeWidth="7" paintOrder="stroke"')
q=q.replace('fontSize="22" fill="#777"','fontSize="26" fill="#555" stroke="#F6F4EF" strokeWidth="6" paintOrder="stroke"')
q=q.replace('(r.median_manwon/10000).toFixed(2)','(Math.round(r.median_manwon/100)/100).toFixed(2)').replace('(last.median_manwon/10000).toFixed(2)','(Math.round(last.median_manwon/100)/100).toFixed(2)')
(src/'QuarterChartsV11.tsx').write_text(q,encoding='utf8')
c=(src/'ContinuationV10.tsx').read_text(encoding='utf8').replace('./QuarterChartsV10','./QuarterChartsV11');(src/'ContinuationV11.tsx').write_text(c,encoding='utf8')
m=(src/'MediaV10.tsx').read_text(encoding='utf8').replace('./ContinuationV10','./ContinuationV11')
m="import {MapPanel as NewMap} from './MapsV11';\n"+m
m=m.replace('export function MapPanel({id,offset=0}', 'function OldMapPanel({id,offset=0}')
m+= "\nexport function MapPanel({id}:{id:keyof typeof maps;offset?:number}){return <NewMap id={id}/>;}\n"
m=m.replace('if(index===1&&f<150)','if(index===1)').replace("if(index===3)return f<120?<MapPanel id=\"dongtan-jobs\"/>:<MapPanel id=\"dongtan-core\" offset={120}/>;","if(index===3)return <MapPanel id=\"dongtan-core\"/>;")
(src/'MediaV11.tsx').write_text(m,encoding='utf8')
e=(src/'ExpandedV10.tsx').read_text(encoding='utf8').replace('./QuarterChartsV10','./QuarterChartsV11').replace('./MediaV10','./MediaV11')
e="import {Teaser,Application} from './EndingV11';\n"+e
e=e.replace("id={f<480?'gwanggyo-life':'dongtan-jobs'} offset={f<480?0:480}","id=\"dongtan-jobs\"")
e=e.replace("if(id==='return')return <Return/>;return <Timing/>;","if(id==='return')return <Teaser/>;return <Application/>;")
e=e.replace("const grey='#777E87'","const grey='#D07812'").replace("grey='#777E87'","grey='#D07812'")
e=e.replace('{r.rows.map(s=><circle key={s.year} cx={x(s.year)} cy={y(s.value)} r="7" fill={i===0?blue:grey}/>)}','''{r.rows.map(s=><g key={s.year}><circle cx={x(s.year)} cy={y(s.value)} r="7" fill={i===0?blue:grey}/><text x={x(s.year)} y={y(s.value)+(i===0?-22:44)} textAnchor="middle" fontSize="28" fontWeight="700" fill={i===0?blue:grey} stroke="#F6F4EF" strokeWidth="7" paintOrder="stroke">{(s.median_manwon/10000).toFixed(2)}억</text></g>)}''')
e=e.replace('<text x="1300" y={y(122.2)-25} fontSize="32" fill={blue}>122.2</text><text x="1300" y={y(75.0)-25} fontSize="32" fill={grey}>75.0</text>','')
e=e.replace('● 광교 자연앤힐스테이트','● 광교 자연앤힐스테이트 · 2026 지수122.2').replace('● 김포 한강센트럴자이1단지','● 김포 한강센트럴자이1단지 · 2026 지수75.0')
(src/'ExpandedV11.tsx').write_text(e,encoding='utf8')
rows=json.loads(Path('video/out/newtown-v10-timing.json').read_text(encoding='utf8'))
original={s['id']:s for s in json.loads(Path('video/public/pilot-v10/plan.json').read_text(encoding='utf8'))['segments']}
intro=json.loads(Path('video/public/pilot-v1/plan.json').read_text(encoding='utf8'))['segments'];extra=json.loads(Path('video/public/pilot-v8/base-extra.json').read_text(encoding='utf8'))['segments'];after=json.loads(Path('video/public/pilot-v6/plan.json').read_text(encoding='utf8'))['segments']
for r in rows:
 key=r['key'];r['frames']=round((r['end']-r['start'])*30)
 if key.startswith('intro-'):s=intro[int(key.split('-')[1])];r.update(file=s['file'],folder='pilot-v1',kind='intro',index=int(key.split('-')[1]))
 elif key.startswith('extra-'):s=extra[int(key.split('-')[1])];r.update(file=s['file'],folder=s.get('folder','pilot-v2'),kind='extra',index=int(key.split('-')[1]))
 elif key.startswith('after-'):s=after[int(key.split('-')[1])];r.update(file=s['file'],folder='pilot-v6',kind='after',index=int(key.split('-')[1]))
 else:s=original[key];r.update(file=s['file'],folder=s.get('folder','pilot-v8'),kind='expanded',index=0)
 # Stable, single-pass scene tails: no overlay return to earlier screen.
tails={'method':('01m30s_최고가와_중위가격_개념.png',6),'jobs':('03m43s_반도체_일자리_AI.png',5),'after-2':('03m34s_수변_생활권_AI.png',4.5),'after-4':('04m05s_철도_연결_AI.png',6),'after-5':('05m00s_대표단지와_생활권_AI.png',5.5),'recovery':('08m30s_회복경로_비교원칙.png',6),'return':('09m00s_근거를_확인하는_책상_AI.png',5),'timing':('09m30s_세개의_시간표_개념.png',6)}
for r in rows:
 if r['key'] in tails:r.update(tail=tails[r['key']][0],tail_seconds=tails[r['key']][1])
# Finish Gwanggyo before the extended Dongtan employment segment.
jobs=next(r for r in rows if r['key']=='jobs');rows.remove(jobs);rows.insert(next(i for i,r in enumerate(rows) if r['key']=='after-2')+1,jobs)
texts={
'intro-5':'오늘은 광교와 동탄에서 성공 조건을 찾고, 그 기준으로 앞으로의 신도시를 미리 살펴보겠습니다.',
'after-1':'광교를 설명하는 조건은 일자리, 철도, 그리고 출발 가격입니다. 지도에서 위치를 조금 더 살펴보겠습니다. 남쪽의 삼성전자 디지털시티는 수원 매탄동에 있습니다. 광교 안에는 경기도청과 법원 같은 행정 기능이 모이고, 서쪽에는 경기남부경찰청이 자리합니다. 기관 이름만 모아놓기보다, 주거지와 일터가 어디에 있는지 먼저 확인하는 겁니다. 여기에 신분당선과 공원이 생활의 연결을 더합니다.',
'jobs':'동탄의 일자리도 삼성 한 곳으로만 설명하지 않겠습니다. 북쪽에는 삼성전자 기흥과 화성 캠퍼스가 있습니다. 램리서치도 동탄지성로에 사무소를 두고 있고, 동탄 송동에는 에이에스엠엘 한국본사가 있습니다. 반도체를 만드는 기업뿐 아니라 장비와 기술 서비스를 담당하는 기업까지 함께 보는 이유입니다. 다만 회사 이름이 많다고 수요가 자동으로 늘어나는 것은 아닙니다. 실제 사업장 위치와 출퇴근 동선, 어느 직장과 연결되는 생활권인지를 확인해야 합니다.',
'return':'이제 이 기준을 입주 전의 신도시에 적용해 보겠습니다. 다음에는 남양주 왕숙 에이 일과 에이 이 블록, 하남 교산 에이 이 블록, 고양 창릉 에이 사 블록을 살펴보려 합니다. 어느 곳이 오를지 먼저 찍는 대신, 일자리와 철도, 분양가와 생활시설, 주변 공급을 같은 질문으로 비교하겠습니다. 완성된 도시에서 찾은 조건을 새 도시의 계획과 대조해 보는 겁니다.',
'timing':'먼저 단지에서 실제 사업장까지의 이동을 보겠습니다. 철도는 노선 이름보다 입주할 때 이용할 수 있는 구간을 확인합니다. 분양가는 주변 기존 주택과 비교하고, 학교와 상업시설, 공원의 운영 시점을 함께 보겠습니다. 주택이 들어오는 시기와 이동, 생활 기능이 갖춰지는 시기가 얼마나 맞물리는지, 그 차이를 단지별로 확인하겠습니다.',
'after-9':'광교와 동탄의 사례를 분석한 이유는 과거의 성공을 되풀이해 말하려는 게 아닙니다. 다음 신도시를 볼 때 사용할 기준을 만들기 위해서입니다. 왕숙과 교산, 창릉의 단지들을 같은 기준으로 살펴보겠습니다. 성공한 도시에서 배운 질문으로, 앞으로의 도시를 미리 읽어보겠습니다.'}
for r in rows:
 if r['key'] in texts:r.update(text=texts[r['key']],file=r['key']+'.mp3',folder='pilot-v11',regenerate=True)
(out/'plan.json').write_text(json.dumps({'segments':rows},ensure_ascii=False,indent=2),encoding='utf8')
p=(src/'PilotV10.tsx').read_text(encoding='utf8').replace('./QuarterChartsV10','./QuarterChartsV11').replace('./ExpandedV10','./ExpandedV11').replace('./ContinuationV10','./ContinuationV11').replace('./MediaV10','./MediaV11')
p="import timeline from '../public/pilot-v11/plan.json';\nimport {Checklist,Teaser} from './EndingV11';\n"+p
p=re.sub(r'const total=18000;','const total=timeline.segments.reduce((a,s)=>a+s.frames,0);',p)
start=p.index('function Pilot(){');end=p.index('function ExtraScene',start);prefix=p[:start];suffix=p[end:]
fn='''function Content({s}:{s:any}){const f=useCurrentFrame();if(s.key==='intro-5')return <Teaser/>;if(s.key==='after-8')return <Checklist/>;if(s.key==='after-9')return <Teaser/>;if(s.tail&&f>=s.frames-Math.round(s.tail_seconds*30)){const card=s.tail.includes('概念')||s.tail.includes('개념')||s.tail.includes('원칙');return <AssetCut cut={{start:0,end:1,file:s.tail,title:s.key==='jobs'?'반도체 제조와 장비·기술의 연결':s.key==='return'?'자료를 모아, 다음 도시를 비교':s.key==='after-2'?'생활 공간의 연결':s.key==='after-4'?'철도, 실제 이용의 시작':'같은 기준으로 비교하기',caption:s.key==='jobs'?'실제 위치와 동선을 확인한 뒤 생활권을 비교합니다.':'과거 사례에서 찾은 기준으로 다음 신도시를 읽습니다.',card}}/>;}return s.kind==='intro'?<Scene index={s.index}/>:s.kind==='extra'?<ExtraScene index={s.index}/>:s.kind==='after'?<Continuation index={s.index}/>:<Expanded id={s.key}/>;}
function Pilot(){let cursor=0;return <AbsoluteFill style={{background:'#15161A'}}><div style={{position:'absolute',top:16,left:98,right:98,display:'flex',justifyContent:'space-between',color:'#F6F4EF',fontFamily:'Pretendard',fontSize:22}}><b>▏ 데이터로 보는 부동산</b><span>신도시 성공 공식 · 광교·동탄</span></div><div style={{position:'absolute',left:96,top:60,width:1728,height:972,borderRadius:18,overflow:'hidden'}}><div style={{width:1920,height:1080,position:'relative',transform:'scale(.9)',transformOrigin:'top left'}}><style>{'@font-face{font-family:Pretendard;src:url('+staticFile('pilot-v1/Pretendard-Regular.woff2')+');font-weight:100 900} @font-face{font-family:Pretendard;src:url('+staticFile('pilot-v1/Pretendard-Bold.woff2')+');font-weight:700 900} .caption{color:#111!important;background:#fff;border:2px solid #e3dfb0;border-radius:10px;padding:18px 28px;box-shadow:0 4px 12px #0002;font-size:32px!important;left:300px!important;right:300px!important} '}</style>{timeline.segments.map(s=>{const from=cursor;cursor+=s.frames;return <Sequence key={s.key} from={from} durationInFrames={s.frames}><Content s={s}/><Sequence from={6}><Audio src={staticFile(s.folder+'/'+s.file)}/></Sequence>{s.key==='intro-0'&&<AssetCut cut={{start:0,end:1,file:'00m00s_신도시_야경_AI.png',title:'',caption:'',intro:true}}/>}</Sequence>})}</div></div></AbsoluteFill>}
'''
p=prefix+fn+suffix;p=p.replace('id="NewtownV10"','id="NewtownV11"')
(src/'PilotV11.tsx').write_text(p,encoding='utf8')
a=(src/'AssetCutsV10.tsx').read_text(encoding='utf-8-sig').replace('opacity=interpolate(f,[0,6],[0,1],{extrapolateRight:\'clamp\'})','opacity=1')
(src/'AssetCutsV11.tsx').write_text(a,encoding='utf8');p=(src/'PilotV11.tsx').read_text(encoding='utf8').replace('./AssetCutsV10','./AssetCutsV11');(src/'PilotV11.tsx').write_text(p,encoding='utf8')
