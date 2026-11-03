"""Build a 20-complex, seek-safe rank race from actual eligible snapshots."""
import hashlib,html,json,math,re,shutil,uuid,wave
from pathlib import Path
import numpy as np
from PIL import ImageFont

EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2];PROJECT=EP/'editor/project';ASSETS=PROJECT/'assets'
data=json.loads((EP/'research/data.json').read_text(encoding='utf-8'))
frames=data['frames'];complexes=data['complexes'];ASSETS.mkdir(parents=True,exist_ok=True)
def district(v):
 parts=v['location'].split()
 candidates=[s[:-1] for s in parts[1:-1] if s.endswith('구')]
 return candidates[-1] if candidates else (parts[1].removesuffix('시') if len(parts)>1 else v['region'])
fontpath=ASSETS/'Pretendard-Bold.ttf'
labels={}
for cid,v in complexes.items():
 label=v['display_name'];size=31
 while size>25 and ImageFont.truetype(str(fontpath),size).getlength(label)>408:size-=1
 assert ImageFont.truetype(str(fontpath),size).getlength(label)<=408,(label,size)
 labels[cid]={'name':label,'full_name':v['name'],'location':v['location'],'district':district(v),'font_size':size,'color':['#168A91','#C37835','#667CA6','#8876A5','#6A8A74','#9C736C','#7C8C50','#887D62'][int(hashlib.sha256(cid.encode()).hexdigest()[:8],16)%8]}
compact=[]
for frame in frames:
 compact.append({'p':frame['period'],'w':frame['window_start']+'–'+frame['window_end'],'rows':[{'id':r['id'],'v':r['median_manwon']/10000,'n':r['n'],'r':r['rank']-1} for r in frame['top']], 'entries':[r['id'] for r in frame.get('entries',[]) if r['event']!='initial'],'leader':frame['top'][0]['id'],'eligible':frame['eligible_complexes']})
highlights={'2010Q4':.9,'2016Q3':1.,'2023Q3':1.1,'2025Q4':1.1}
segments=[];cursor=1.8
for i in range(1,len(frames)):
 start=cursor;transition=.34;end=start+.55+highlights.get(frames[i]['period'],0)
 segments.append({'i':i,'start':round(start,6),'transition_end':round(start+transition,6),'end':round(end,6),'highlight':frames[i]['period'] in highlights})
 cursor=end
end_race=round(cursor,6);duration=math.ceil((end_race+8)*30)/30
timing={'duration':duration,'fps':30,'first_hold':1.8,'race_end':end_race,'final_hold':duration-end_race,'CTA_start':duration-4,'segments':segments,'highlight_periods':highlights,'label_collision_policy':'labels hidden only when approaching glyph-box collision; bar bodies retain continuous identity and motion','transition_label':'adjacent report quarters shown as a range; steady states show actual report quarter'}
(EP/'editor/timing.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding='utf-8')
(EP/'editor/labels.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2),encoding='utf-8')
(ASSETS/'race_data.json').write_text(json.dumps({'frames':compact,'labels':labels,'timing':timing},ensure_ascii=False),encoding='utf-8')

# Extend our own original music motif, preserving a smooth ending without a cut loop.
rate=48000;audio=np.zeros((int(round(duration*rate)),2),np.float64)
def note(start,length,freq,gain,pan=0):
 n=min(int(length*rate),len(audio)-int(start*rate))
 if n<=0:return
 t=np.arange(n)/rate;env=(1-np.exp(-t/.016))*np.exp(-t/1.1)*np.minimum(1,(length-t)/.15)
 tone=(np.sin(2*np.pi*freq*t)+.19*np.sin(4*np.pi*freq*t)+.07*np.sin(6*np.pi*freq*t))*env*gain
 off=int(start*rate);audio[off:off+n,0]+=tone*np.sqrt((1-pan)/2);audio[off:off+n,1]+=tone*np.sqrt((1+pan)/2)
chords=[[146.832,174.614,220],[130.813,164.814,196],[116.541,146.832,174.614],[130.813,164.814,220]]
for b in range(int((duration-2)/.6)):
 start=b*.6;chord=chords[(b//8)%4];note(start,1.2,chord[b%3]*2,.08,.2 if b%2 else -.2)
 if b%4==0:note(start,2.3,chord[0]/2,.16)
 if b%8==0:
  for freq in chord:note(start,2.5,freq,.05)
for freq in [146.832,174.614,220,293.665]:note(duration-2,2,freq,.075)
fade=np.minimum(1,np.arange(len(audio))/(rate*.35))*np.minimum(1,(len(audio)-np.arange(len(audio)))/(rate*1.0));audio*=fade[:,None];audio*=.36/max(np.abs(audio).max(),1e-9)
with wave.open(str(ASSETS/'original_race_pulse.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes((audio*32767).astype('<i2').tobytes())

doc='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920"><title>84㎡대 아파트 중위가 TOP20</title><script src="assets/gsap.min.js"></script><style>
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.ttf');font-weight:400}@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.ttf');font-weight:700}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#F4F1E9;color:#17313F;font-family:Pretendard,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden}.clip{position:absolute;inset:0}.ground{position:absolute;inset:0;background:#F4F1E9}.stripe{position:absolute;top:0;left:0;width:100%;height:18px;background:#168A91}.cityscape{position:absolute;bottom:0;width:1080px;height:370px;opacity:.18}.brand{position:absolute;left:140px;top:266px;font-size:26px;font-weight:700;color:#3C6974;letter-spacing:1px}.title{position:absolute;left:140px;top:308px;width:700px;font-size:53px;font-weight:700;letter-spacing:-1.7px;line-height:1.1;white-space:nowrap}.subtitle{position:absolute;left:140px;top:373px;font-size:28px;color:#496371;white-space:nowrap}.period{position:absolute;left:140px;top:412px;font-size:33px;font-weight:700;line-height:1.2;font-variant-numeric:tabular-nums;white-space:nowrap}.unit{position:absolute;right:240px;top:420px;font-size:27px;color:#496371}.axis{position:absolute;left:280px;top:454px;width:372px;height:23px;font-size:23px;color:#496371}.axis span{position:absolute;white-space:nowrap;transform:translateX(-50%)}.tableplate{position:absolute;left:127px;top:479px;width:725px;height:753px;border-radius:15px;background:#FFFEFA;border:1px solid #D6E0DA}.plot{position:absolute;left:0;top:480px;width:1080px;height:750px;overflow:hidden}.rank{position:absolute;left:139px;width:39px;height:37.5px;text-align:right;font-size:27px;font-weight:700;line-height:37.5px;color:#7C8B8E}.rank:first-child{color:#168A91}.racerow{position:absolute;left:0;top:0;width:1080px;height:37.5px;will-change:transform,opacity}.rowbar{position:absolute;left:280px;top:6px;width:372px;height:26px;background:var(--color);opacity:.21;transform-origin:left;border-radius:3px}.rowtip{position:absolute;left:280px;top:6px;width:3px;height:26px;background:var(--color)}.location{position:absolute;left:188px;top:0;width:84px;font-size:24px;font-weight:400;line-height:37.5px;white-space:nowrap;color:#4F6874}.name{position:absolute;left:286px;top:0;width:409px;font-weight:700;line-height:37.5px;letter-spacing:-.5px;white-space:nowrap}.count{position:absolute;left:660px;top:0;width:54px;text-align:right;font-size:24px;line-height:37.5px;color:#496371;font-variant-numeric:tabular-nums;white-space:nowrap}.count-head{position:absolute;left:679px;top:453px;width:35px;text-align:right;font-size:23px;font-weight:700;color:#496371}.value{position:absolute;left:724px;top:0;width:116px;font-size:32px;font-weight:700;line-height:37.5px;text-align:right;font-variant-numeric:tabular-nums;letter-spacing:-.5px;white-space:nowrap}.entrydot{position:absolute;left:181px;top:14px;width:4px;height:10px;background:#C37835;border-radius:3px}.event{position:absolute;left:140px;top:1248px;width:700px;font-size:29px;font-weight:700;line-height:1.2;color:#A35F26;white-space:nowrap}.source{position:absolute;left:140px;top:1291px;width:700px;font-size:25px;line-height:1.38;color:#496371;white-space:nowrap}.source div{white-space:nowrap}.cta{position:absolute;left:630px;top:262px;width:210px;height:36px;border-radius:8px;background:#168A91;color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700}.progress{position:absolute;left:140px;top:239px;width:700px;height:3px;background:#D1DDDA}.progress i{display:block;width:100%;height:3px;background:#168A91;transform-origin:left}.period em{font-size:26px;font-style:normal;color:#496371}
</style></head><body><div id="root" data-composition-id="apt-top20-race" data-start="0" data-duration="__DURATION__" data-width="1080" data-height="1920">
<section id="race-scene" class="clip" data-start="0" data-duration="__DURATION__" data-track-index="0"><div class="ground"></div><div class="stripe"></div><svg class="cityscape" viewBox="0 0 1080 370" aria-hidden="true"><g fill="#BCCDC9"><path d="M0 370V190H105V120H225V370Z"/><path d="M245 370V210H370V60H475V370Z"/><path d="M495 370V155H640V250H742V370Z"/><path d="M770 370V95H895V175H1010V370Z"/></g><g stroke="#F4F1E9" stroke-width="9"><path d="M30 220H195M30 270H195M400 100H445M400 150H445M400 200H445M525 190H610M525 240H610M800 135H865M800 185H865M800 235H865"/></g></svg><div class="progress"><i id="progress"></i></div><div class="brand measure">데이터로보는부동산</div><div class="title measure">84㎡대 아파트 중위가 TOP20</div><div class="subtitle measure">20년, 누가 올라왔을까? · 최근 1년 집계</div><div id="period" class="period measure"></div><div class="unit measure">단위: 억원</div><div class="axis"><span class="measure" style="left:0">0</span><span id="axis-mid" class="measure" style="left:186px"></span><span id="axis-max" class="measure" style="left:372px"></span></div><div class="count-head measure">?</div><div class="tableplate"></div><div class="plot" id="plot"><div id="rank-column"></div><div id="rows"></div></div><div id="event" class="event measure"></div><div class="source"><div class="measure">7개 수집 지역 · 최근 1년 5건 이상 거래 단지</div><div class="measure">국토교통부 실거래가 · 자료 종점 2026-06-30</div></div><div class="cta measure" id="cta">구독 · 좋아요</div></section>
<audio id="music" class="clip" data-start="0" data-duration="__DURATION__" data-track-index="1" src="assets/original_race_pulse.wav" data-volume="0.70"></audio>
</div><script>
const FRAMES=__FRAMES__,LABELS=__LABELS__,TIMING=__TIMING__,TOTAL=TIMING.duration,PITCH=37.5;const KEYS=Object.keys(LABELS).sort(),EL={};
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}function smooth(v){return v*v*(3-2*v);}function money(v){return (Math.round((v+1e-9)*100)/100).toFixed(2);}function maxScale(frame){return Math.max(5,Math.ceil(Math.max(...frame.rows.map(r=>r.v))/5)*5);}
for(let i=0;i<20;i++){const e=document.createElement('div');e.className='rank measure';e.textContent=i+1;e.style.top=(i*PITCH)+'px';document.getElementById('rank-column').appendChild(e);}
for(let k=0;k<KEYS.length;k++){const id=KEYS[k],l=LABELS[id],e=document.createElement('div');e.className='racerow';e.id='complex-'+k;e.dataset.cid=id;e.style.setProperty('--color',l.color);e.innerHTML='<div class="rowbar"></div><div class="rowtip"></div><span class="location measure"></span><span class="name measure"></span><span class="count measure"></span><span class="value measure"></span><span class="entrydot"></span>';e.querySelector('.location').textContent=l.district;e.querySelector('.name').textContent=l.name;e.querySelector('.name').style.fontSize=l.font_size+'px';document.getElementById('rows').appendChild(e);EL[id]={root:e,bar:e.querySelector('.rowbar'),tip:e.querySelector('.rowtip'),labels:[e.querySelector('.location'),e.querySelector('.name'),e.querySelector('.count'),e.querySelector('.value')],value:e.querySelector('.value'),count:e.querySelector('.count'),dot:e.querySelector('.entrydot')};}
function frameAt(t){if(t<1.8)return {a:0,b:0,u:1,moving:false};let s=TIMING.segments.find(s=>t<s.end);if(!s)return {a:FRAMES.length-1,b:FRAMES.length-1,u:1,moving:false};let u=clamp((t-s.start)/(s.transition_end-s.start),0,1);return {a:s.i-1,b:s.i,u:smooth(u),moving:u<1,segment:s};}
function eventText(i){const b=FRAMES[i],a=FRAMES[Math.max(0,i-1)],leader=LABELS[b.leader];if(i===0)return '출발 2006년 · 20년 뒤에는 누가 남을까?';if(b.leader!==a.leader)return '1위 교체 · '+leader.district+' '+leader.name;if(b.entries.length){const id=b.entries.slice().sort((x,y)=>b.rows.find(r=>r.id===x).r-b.rows.find(r=>r.id===y).r)[0];return '랭킹 진입 · '+LABELS[id].name+'  '+(b.rows.find(r=>r.id===id).r+1)+'위';}return '1위 · '+leader.district+' '+leader.name;}
function render(t){const st=frameAt(t),a=FRAMES[st.a],b=FRAMES[st.b],u=st.u;const am=new Map(a.rows.map(r=>[r.id,r])),bm=new Map(b.rows.map(r=>[r.id,r])),ids=[...new Set([...am.keys(),...bm.keys()])];const scale=maxScale(a)+(maxScale(b)-maxScale(a))*u;const active=[];
for(const id of KEYS)EL[id].root.style.opacity='0';
for(const id of ids){const ar=am.get(id),br=bm.get(id),entry=!ar&&!!br,exit=!!ar&&!br;let r0=ar?ar.r:20.6,r1=br?br.r:20.6;let pos=r0+(r1-r0)*u,value=ar&&br?ar.v+(br.v-ar.v)*u:(br?br.v:ar.v);let alpha=entry?u:exit?1-u:1;if(pos>20.2||alpha<.015)continue;active.push({id,pos,value,alpha,entry,exit,rank:br?br.r:ar.r});}
for(const q of active){const el=EL[q.id];const minDistance=active.filter(v=>v.id!==q.id&&v.alpha>.12).reduce((m,v)=>Math.min(m,Math.abs(v.pos-q.pos)*PITCH),1000);const labelsVisible=minDistance>=36.8&&q.pos>=0&&q.pos<=19.04&&q.alpha>.8;el.root.style.opacity=q.alpha;el.root.style.transform='translateY('+(q.pos*PITCH)+'px)';el.bar.style.transform='scaleX('+clamp(q.value/scale,0,1)+')';el.tip.style.transform='translateX('+(372*clamp(q.value/scale,0,1))+'px)';el.value.textContent=money(q.value);el.count.textContent=st.moving?'?':String(bm.get(q.id)?.n??am.get(q.id)?.n??'');for(const label of el.labels)label.style.opacity=labelsVisible?'1':'0';el.dot.style.opacity=b.entries.includes(q.id)&&!q.exit?'1':'0';el.root.style.zIndex=String(100-Math.round(q.pos));q.labelsVisible=labelsVisible;}
document.getElementById('period').textContent=st.moving?a.p+' → '+b.p:b.p;document.getElementById('period').style.fontSize=st.moving?'29px':'36px';document.getElementById('axis-mid').textContent=money(scale/2).replace(/\.00$/,'');document.getElementById('axis-max').textContent=money(scale).replace(/\.00$/,'');document.getElementById('event').textContent=t>=TIMING.CTA_start?'?? ??? ????? ?? ? ???':eventText(st.moving?st.a:st.b);document.getElementById('cta').style.opacity='0';document.getElementById('progress').style.transform='scaleX('+Math.max(.01,Math.min(1,t/TIMING.race_end))+')';window.__frameState={time:t,...st,period:st.moving?a.p+' → '+b.p:b.p,scale,active,expected:b.rows,stable:!st.moving,window:b.w};}
const driver={t:0},tl=gsap.timeline({paused:true});tl.to(driver,{t:TOTAL,duration:TOTAL,ease:'none',onUpdate:()=>render(driver.t)},0);window.__timelines=window.__timelines||{};window.__timelines['apt-top20-race']=tl;window.__sourceSeek=t=>{tl.seek(t,false);render(t);};window.__raceData={frames:FRAMES,labels:LABELS,timing:TIMING};render(0);
</script></body></html>'''
doc=doc.replace('__DURATION__',str(duration)).replace('__FRAMES__',json.dumps(compact,ensure_ascii=False)).replace('__LABELS__',json.dumps(labels,ensure_ascii=False)).replace('__TIMING__',json.dumps(timing,ensure_ascii=False))
# Apply Korean copy in this UTF-8 file, never via Windows legacy-encoded stdin.
doc=doc.replace('데이터로보는부동산</div><div class="title measure">84㎡대 아파트 중위가 TOP20</div><div class="subtitle measure">20년, 누가 올라왔을까? · 최근 1년 집계',
 '데이터로보는부동산 · 7개 수집 지역</div><div class="title measure">1위가 13번 바뀌었다</div><div class="subtitle measure">단지 TOP20 · 전용 84㎡대 · 최근 1년 중위가')
doc=doc.replace('<div class="count-head measure">?</div>','<div class="count-head measure">건</div>')
doc=doc.replace("el.count.textContent=st.moving?'?':", "el.count.textContent=st.moving?'—':")
doc=re.sub(r"document\.getElementById\('event'\)\.textContent=.*?;", "document.getElementById('event').textContent=t>=TIMING.CTA_start?'다음 비교도 궁금하다면 구독 · 좋아요':eventText(st.b);",doc)
doc=doc.replace("if(i===0)return '출발 2006년 · 20년 뒤에는 누가 남을까?';", "if(i===0)return '2006 → 2026, 어떤 단지가 올라올까?';")
doc=doc.replace("el.bar.style.transform='scaleX('","el.bar.style.opacity=b.entries.includes(q.id)&&!q.exit?'.40':'.21';el.bar.style.transform='scaleX('")
assert '1위가 13번 바뀌었다' in doc and '구독 · 좋아요' in doc and 'count-head measure">건' in doc
(PROJECT/'index.html').write_text(doc,encoding='utf-8');shutil.copyfile(EP/'BRIEF.md',PROJECT/'BRIEF.md')
config=json.loads((PROJECT/'hyperframes.json').read_text(encoding='utf-8'));config['authoringSkill']='general-video';(PROJECT/'hyperframes.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
meta=json.loads((PROJECT/'meta.json').read_text(encoding='utf-8'));meta['id']='apartment-top20-race-20261029';meta['name']='아파트 단지 중위가 TOP20';(PROJECT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
ledger={'source_data_sha256':hashlib.sha256((EP/'research/data.json').read_bytes()).hexdigest(),'frames':len(frames),'unique_top20_ids':len(labels),'duration':duration,'actual_ranking_change':True,'registry_adapted':'bar-chart-race (rank-driven rows, axis rescaling); original registry file preserved; missing data not held or zero-filled','label_font_sizes':sorted(set(v['font_size'] for v in labels.values())),'new_paid_calls':0,'voice':None,'music':'original deterministic synthesis with earlier channel Short music motif','source_html_sha256':hashlib.sha256((PROJECT/'index.html').read_bytes()).hexdigest()}
(EP/'editor/build_manifest.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(ledger,ensure_ascii=False))
