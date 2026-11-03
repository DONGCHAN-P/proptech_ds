from pathlib import Path
import json,re
root=Path('video/public/pilot-v8');plan=json.loads((root/'plan.json').read_text(encoding='utf8'))
p=Path('video/src/PilotV7.tsx').read_text(encoding='utf-8-sig')
p="import longPlan from '../public/pilot-v8/plan.json';\nimport {Expanded,TradeVolume} from './ExpandedV8';\n"+p
p=p.replace("./ContinuationV6","./ContinuationV8").replace("./MediaV7","./MediaV8").replace("pilot-v5/plan.json","pilot-v8/base-extra.json").replace("pilot-v5/leaders.json","pilot-v8/representatives.json").replace("pilot-v2/metrics.json","pilot-v8/regional.json").replace('2,779','2,787')
p=re.sub(r'const total=introLength[^;]+;', 'const total=18000;',p)
p=p.replace("function Pilot(){let cursor=0;", "function Pilot(){let cursor=0;const additions=(key:string)=>longPlan.segments.filter(s=>s.after===key).map(s=>{const from=cursor;cursor+=s.frames;return <Sequence key={s.id} from={from} durationInFrames={s.frames}><Expanded id={s.id}/><Sequence from={6}><Audio src={staticFile('pilot-v8/'+s.file)}/></Sequence></Sequence>});")
old="<Sequence key={'extra'+i} from={from} durationInFrames={s.frames}><ExtraScene index={i}/><Sequence from={6}><Audio src={staticFile(((s as any).folder||'pilot-v2')+'/'+s.file)}/></Sequence></Sequence>"
assert old in p;p=p.replace(old,"<React.Fragment key={'extra'+i}>"+old+"{additions('extra-'+i)}</React.Fragment>")
old="<Sequence key={'after'+i} from={from} durationInFrames={s.frames+(i===after.segments.length-1?60:0)}><Continuation index={i}/><Sequence from={6}><Audio src={staticFile('pilot-v6/'+s.file)}/></Sequence></Sequence>"
assert old in p;p=p.replace(old,"<React.Fragment key={'after'+i}>"+old+"{additions('after-'+i)}</React.Fragment>")
p=p.replace("const f=useCurrentFrame();const {fps}=useVideoConfig();if(index===1", "const f=useCurrentFrame();const {fps}=useVideoConfig();if(index===3)return <TradeVolume/>;if(index===1")
p=p.replace("const f=useCurrentFrame();const elapsed=f+(index===2", "const f=useCurrentFrame();const focus=index===2?Math.min(4,Math.floor(f/(extension.segments[2].frames/5))):-1;const elapsed=f+(index===2")
p=p.replace("{leaders.towns.map((t,i)=><g key={t.apt_id}>","{leaders.towns.map((t,i)=><g key={t.apt_id} opacity={focus<0||focus===i?1:.18}>")
p=p.replace('>전용 84㎡ 안팎으로 비교 · 입주 전과 거래 없는 해는 비워 둡니다.</div>', ">{focus>=0?'지금 보는 단지 · '+shortNames[leaders.towns[focus].town]:'전용 84㎡ 안팎으로 비교 · 입주 전과 거래 없는 해는 비워 둡니다.'}</div>")
p=p.replace('id="NewtownV7"','id="NewtownV8"');Path('video/src/PilotV8.tsx').write_text(p,encoding='utf8')
s=Path('video/src/ExpandedV8.tsx').read_text(encoding='utf8').replace('x="100" y="0" width={1435*visible}','x="0" y="0" width={1630*visible}')
Path('video/src/ExpandedV8.tsx').write_text(s,encoding='utf8')
intro=json.loads(Path('video/public/pilot-v1/plan.json').read_text(encoding='utf8'))['segments'];extra=json.loads(Path('video/public/pilot-v8/base-extra.json').read_text(encoding='utf8'))['segments'];after=json.loads(Path('video/public/pilot-v6/plan.json').read_text(encoding='utf8'))['segments']
rows=[];at=0
def put(s,key,frames):
 global at
 rows.append(dict(key=key,start=at/30,end=(at+frames)/30,text=s['text'],title=s.get('title',key)));at+=frames
for i,s in enumerate(intro):put(s,'intro-'+str(i),int(__import__('math').ceil((s['duration']+1.2)*30)))
for group,segments in [('extra',extra),('after',after)]:
 for i,s in enumerate(segments):
  key=group+'-'+str(i);put(s,key,s['frames'])
  for new in plan['segments']:
   if new['after']==key:put(new,new['id'],new['frames'])
rows[-1]['end']+=2;at+=60
assert at==18000,(at,18000)
Path('video/out/newtown-v8-timing.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
def fmt(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
Path('video/out/newtown-v8.srt').write_text('\n\n'.join(f'{i+1}\n{fmt(r["start"]+.2)} --> {fmt(r["end"]-.1)}\n{r["text"]}' for i,r in enumerate(rows)),encoding='utf8')
print(json.dumps([dict(key=r['key'],start=round(r['start'],2)) for r in rows],ensure_ascii=False))
points=''.join(f'<circle cx="{7+(i%60)*12}" cy="{7+(i//60)*12}" r="3.8" fill="#2F6FED"/>' for i in range(2787))
(root/'trade-dots.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="728" height="576" viewBox="0 0 728 576">'+points+'</svg>',encoding='utf8')
