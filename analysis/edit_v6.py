from pathlib import Path
p=Path('video/src/PilotV5.tsx').read_text(encoding='utf-8-sig')
p="import {Apartment,Continuation} from './ContinuationV6';\nimport after from '../public/pilot-v6/plan.json';\n"+p
p=p.replace("+60;","+after.segments.reduce((n,s)=>n+s.frames,0)+60;")
start=p.index('<div style={{width:750}}><div style={{borderLeft:')
end=p.index('</div></div></div>}',start)+len('</div></div></div>}')
p=p[:start]+"<div style={{width:650,textAlign:'center'}}><Apartment width={520}/><div style={{fontSize:30,fontWeight:700}}>동탄역 롯데캐슬</div><div style={{fontSize:24,color:muted,marginTop:12}}>주거 · 백화점 · SRT</div></div></div>}"+p[end:]
start=p.index('{index===1&&<>')
end=p.index('{index===2&&<>',start)
p=p[:start]+'''{index===1&&<><div style={{fontSize:30,color:muted}}>2017 분양가 → 2026.06.04 거래가 · 전용 84㎡</div><div style={{display:'flex',alignItems:'flex-end',gap:60,marginTop:30,height:510}}><div style={{width:390,textAlign:'center'}}><Apartment width={215} color="#9AA0A6"/><div style={{fontSize:43,fontWeight:800}}>4억 8,200만</div><div style={{fontSize:25,color:muted,marginTop:10}}>2017 분양가</div></div><div style={{fontSize:70,color:muted,paddingBottom:190}}>→</div><div style={{width:960,display:'flex',alignItems:'end',gap:40}}><div style={{width:490,height:480,position:'relative'}}><div style={{position:'absolute',bottom:0,left:15,transformOrigin:'bottom left',transform:'scale('+interpolate(f,[10,65],[1,Math.sqrt(22.25/4.82)],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})+')'}}><Apartment width={215}/></div></div><div style={{paddingBottom:30}}><div style={{fontSize:68,fontWeight:800,color:'#2F6FED'}}>22억 2,500만</div><div style={{fontSize:28,color:muted,marginTop:18}}>2026 거래가</div><div style={{fontSize:58,fontWeight:800,marginTop:22}}>4.6배</div></div></div></div></>}
'''+p[end:]
start=p.index('<OffthreadVideo src=')
end=p.index('/><div style={{position:',start)+2
p=p[:start]+'''<svg width="950" height="850" style={{position:'absolute',right:30,top:120,opacity:.30}}>{Array.from({length:120},(_,i)=><g key={i} transform={'translate('+(50+(i%12)*72)+','+(40+Math.floor(i/12)*72)+')'}><circle r="12" fill="#e8f0ff"/><path d="M-18 42V26Q0 4 18 26V42Z" fill="#e8f0ff"/></g>)}</svg>'''+p[end:]
p=p.replace('<div style={{fontSize:25,color:\'#b3c1c6\',marginTop:35}}>AI 생성 개념 영상 · 실제 단지 모습 아님</div>','')
p=p.replace('[15,span-30],[2012,2026]','[8,68],[2012,2026]')
p=p.replace("s.frames+(i===4?60:0)","s.frames")
needle='})}</div></div></AbsoluteFill>}'
replacement="})}{after.segments.map((s,i)=>{const from=cursor;cursor+=s.frames;return <Sequence key={'after'+i} from={from} durationInFrames={s.frames+(i===after.segments.length-1?60:0)}><Continuation index={i}/><Sequence from={6}><Audio src={staticFile('pilot-v6/'+s.file)}/></Sequence></Sequence>})}</div></div></AbsoluteFill>}"
assert needle in p
p=p.replace(needle,replacement,1)
old="<div key={r.name} style={{display:'flex',justifyContent:'space-between',margin:'28px 0',fontSize:34}}><span>{r.name}</span><b>{(r.median_manwon/10000).toFixed(2)}억</b></div>"
new="<div style={{display:'flex',alignItems:'center',gap:14,margin:'28px 0',fontSize:30}}><span style={{width:175}}>{r.name}</span><div style={{width:375,height:28,background:'#e4e7df'}}><div style={{height:28,width:interpolate(f,[0,45],[0,r.median_manwon/150000*100],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})+'%',background:r.name==='광교'?'#E5484D':'#2F6FED'}}/></div><b>{(r.median_manwon/10000).toFixed(2)}억</b></div>"
assert old in p
p=p.replace(old,new).replace('id="NewtownV5"','id="NewtownV6"')
Path('video/src/PilotV6.tsx').write_text(p,encoding='utf-8')
