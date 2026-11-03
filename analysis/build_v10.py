from pathlib import Path
import json,re
src=Path('video/src')
media=(src/'MediaV8.tsx').read_text(encoding='utf8').replace("./ContinuationV8","./ContinuationV10")
media=media.replace('</svg></AbsoluteFill>}','''</svg>{m.pins.filter(pin=>pin.name.startsWith('삼성전자')).map(pin=><div key={pin.name} style={{position:'absolute',left:65+pin.x-110,top:240+pin.y-135,width:220,height:124}}><Img src={staticFile('ci-v10/samsung-official.png')} style={{width:220,height:124,objectFit:'contain'}}/></div>)}</AbsoluteFill>}''',1)
(src/'MediaV10.tsx').write_text(media,encoding='utf8')
c=(src/'ContinuationV8.tsx').read_text(encoding='utf8');c="import {QuarterPlot} from './QuarterChartsV10';\n"+c
c=re.sub(r'function Trend\(.*?\n',"function Trend({dip=false}:{dip?:boolean}){return <QuarterPlot index={0} from={dip?2020:2012}/>;}\n",c,count=1)
c=c.replace('연도별 중위가격','분기별 중위가격')
(src/'ContinuationV10.tsx').write_text(c,encoding='utf8')
e=(src/'ExpandedV8.tsx').read_text(encoding='utf8');e="import {QuarterPlot} from './QuarterChartsV10';\n"+e
e=re.sub(r'function Trend\(.*?\n',"function Trend({index,from=2012}:{index:number;from?:number}){return <><div style={{fontSize:26,color:'#777'}}>{names[index]} · 전용83~85㎡ · 분기 중위가격</div><QuarterPlot index={index} from={from}/></>;}\n",e,count=1)
e=e.replace("./MediaV7","./MediaV10").replace("f<300?'gwanggyo-life':'dongtan-jobs'","f<480?'gwanggyo-life':'dongtan-jobs'").replace('offset={f<300?0:300}','offset={f<480?0:480}')
e=e.replace('2021년은2건 · 이후 충분히 쌓인 표본과 함께','분기별 가격과 거래 건수를 함께 읽습니다.').replace('초기 표본6건·3건 → 2026년27건','빈 분기는 비우고, 소수 표본은 빈 점으로 표시합니다.').replace('같은 조정, 달라진 회복 경로','연간 요약으로 확인하는 회복 경로').replace('2021년 중위가격을100으로 놓고 비교합니다.','보조 비교 · 2021년 연간 중위가격=100')
(src/'ExpandedV10.tsx').write_text(e,encoding='utf8')
p=(src/'PilotV9.tsx').read_text(encoding='utf8');p="import {QuarterOverview} from './QuarterChartsV10';\n"+p
p=p.replace("./ExpandedV8","./ExpandedV10").replace("./MediaV8","./MediaV10").replace("./ContinuationV8","./ContinuationV10").replace("./AssetCutsV9","./AssetCutsV10").replace("pilot-v8/plan.json","pilot-v10/plan.json")
p=p.replace("const f=useCurrentFrame();const {fps}=useVideoConfig();if(index===3)","const f=useCurrentFrame();const {fps}=useVideoConfig();if(index===1||index===2)return <QuarterOverview focus={index===2?Math.min(4,Math.floor(f/(extension.segments[2].frames/5))):-1}/>;if(index===3)")
p=p.replace("staticFile('pilot-v8/'+s.file)","staticFile(((s as any).folder||'pilot-v8')+'/'+s.file)").replace('id="NewtownV9"','id="NewtownV10"')
(src/'PilotV10.tsx').write_text(p,encoding='utf8')
cuts=(src/'AssetCutsV9.tsx').read_text(encoding='utf-8-sig').replace('start:199,end:204.47','start:198,end:202')
(src/'AssetCutsV10.tsx').write_text(cuts,encoding='utf8')
plan=json.loads(Path('video/public/pilot-v8/plan.json').read_text(encoding='utf8'))
current_file=Path('video/public/pilot-v10/plan.json')
current={s['id']:s for s in json.loads(current_file.read_text(encoding='utf8'))['segments']} if current_file.exists() else {}
texts={
'gwanggyo-growth':'광교의 흐름을 이번에는 분기별로 보겠습니다. 전용 팔십사 제곱미터 안팎의 거래를 같은 분기 안에서 모아 가운데 가격을 계산했습니다. 이천십육년 사분기는 육억 팔천만 원, 이천이십삼년 일분기는 십이억 원입니다. 이천이십육년 삼분기에는 이십억 오천만 원으로 올라왔습니다. 연간 요약에서는 한 덩어리로 보였던 상승과 조정이 더 세밀하게 드러납니다. 오른쪽 라벨은 마지막 거래 분기와 거래 건수입니다.',
'unjeong':'운정 아이파크도 분기별로 따라가 보겠습니다. 이천이십삼년 일분기 중위가격은 육억 육천오백만 원, 그해 사분기는 칠억 오천오백만 원입니다. 최근 이천이십육년 삼분기는 칠억 이천칠백오십만 원이고 거래는 쉰네 건입니다. 가격과 함께 표본 수를 보면 선을 읽는 근거가 더 분명해집니다. 한두 건뿐인 분기는 빈 점으로 표시하고, 거래가 없는 분기는 선을 이어 채우지 않았습니다.',
'gimpo':'김포 한강센트럴자이 일단지의 분기 차트입니다. 이천이십일년 사분기에는 칠억 원, 이천이십삼년 일분기에는 사억 팔천오백만 원으로 내려왔습니다. 이천이십육년 삼분기는 사억 구천만 원, 표본은 스물다섯 건입니다. 이 단지도 한 번도 오르지 않은 곳은 아닙니다. 상승했던 시기와 조정 이후의 흐름을 함께 보고, 지금의 가격이 어느 구간에 있는지 확인하는 게 더 정확합니다.',
'okjeong':'옥정 제일풍경채 레이크시티 일단지는 관측 기간이 짧습니다. 분기로 나누면 거래가 없는 구간과 한두 건뿐인 구간도 드러납니다. 없는 가격을 선으로 채우면 실제보다 연속적인 흐름처럼 보일 수 있습니다. 그래서 빈 구간은 비우고, 소수 거래는 빈 점으로 구분했습니다. 최근 이천이십육년 삼분기의 중위가격은 사억 육천만 원, 거래는 일곱 건입니다. 가격 옆의 기간과 표본을 함께 읽겠습니다.'}
for s in plan['segments']:
 if s['id'] in texts:
  prior=current.get(s['id'],{});s.update(text=prior.get('text',texts[s['id']]),file=s['id']+'.mp3',folder='pilot-v10',duration=prior.get('duration',s['duration']))
Path('video/public/pilot-v10/plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
