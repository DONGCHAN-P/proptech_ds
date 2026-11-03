from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
p=ROOT/'video/src/NamyangjuRailRouteProofV2.tsx'
s=(ROOT/'video/src/NamyangjuRailRouteProofV1.tsx').read_text(encoding='utf-8').replace("../public/namyangju-rail-route-proof-v1/proof_data.json","../public/namyangju-rail-route-proof-v2/proof_data.json").replace('NamyangjuRailRouteProofV1','NamyangjuRailRouteProofV2')
start=s.index('function Dasan()')
end=s.index('function Movie()',start)
s=s[:start]+'''const landColors:any={housing:'#edc873',commerce:'#ee9aa8',park:'#7db28b'};
function Dasan(){
 const f=useCurrentFrame(),t=f/30-40.3,ctx=D.dasanContext;
 const phase=t<3?0:t<8?1:t<13?2:3;
 const kind=['station','housing','commerce','park'][phase];
 const marker=D.stations.find((p:any)=>p.id==='dasan');
 const pr=projection(ctx.bounds);
 const selected=ctx.display_labels.filter((a:any)=>a.kind===kind);
 const categoryNames:any={station:'다산역 · 8호선',housing:'주거 단지',commerce:'상권 · 쇼핑시설',park:'공원 · 녹지'};
 return <>
 <div style={{position:'absolute',left:80,top:100,fontSize:50,fontWeight:700}}>다산역 주변 배치, 주거·상권·공원을 함께 보기</div>
 <div style={{position:'absolute',left:80,top:200,width:1320,height:650,overflow:'hidden',background:'#eeece5',borderRadius:18}}>
 <svg width="1320" height="650">
 {ctx.features.map((feature:any,i:number)=>{
    const focused=feature.kind===kind;
    return <g key={feature.id}>
    {feature.points?<path d={path(feature.points,pr)+' Z'} fill={landColors[feature.kind]} fillOpacity={focused?.9:.55} stroke={focused?'#2f5964':landColors[feature.kind]} strokeWidth={focused?4:2}/>:null}
    </g>;
 })}
 {ctx.water.map((g:any,i:number)=><path key={'water'+i} d={path(g.points,pr)} stroke="#9fc8d6" strokeWidth={8} fill="none"/>)}
 {ctx.roads.map((g:any,i:number)=><path key={'road'+i} d={path(g.points,pr)} stroke={['primary','secondary','tertiary'].includes(g.highway)?'#fff':'#cbc7bc'} strokeWidth={['primary','secondary','tertiary'].includes(g.highway)?4:1.5} fill="none"/>)}
 {ctx.buildings.map((g:any,i:number)=><path key={'building'+i} d={path(g.points,pr)+' Z'} stroke="#7e7d78" strokeWidth={1} fill="#f4f2e8" fillOpacity={.35}/>)}
 {ctx.display_labels.map((a:any)=>{const [x,y]=pr([a.lon,a.lat]);const tx=x+a.dx,ty=y+a.dy;return <g key={a.id}><path d={`M${x} ${y}L${tx} ${ty}`} stroke={landColors[a.kind]} strokeWidth={2}/><circle cx={x} cy={y} r={6} stroke="white" strokeWidth={2} fill={landColors[a.kind]}/><text x={tx+(a.dx<0?-8:8)} y={ty} textAnchor={a.dx<0?'end':'start'} fontSize={24} fontWeight={700} fill={ink} stroke={cream} strokeWidth={6} paintOrder="stroke">{a.name.replace('아파트','').replace('현대프리미엄아울렛 ','')}</text></g>})}
 <Place p={marker} pr={pr} color={pink}/>
 {phase===0?<circle cx={pr([marker.lon,marker.lat])[0]} cy={pr([marker.lon,marker.lat])[1]} r={17+3*Math.sin(t*4)} stroke={pink} strokeWidth={3} fill="none"/>:null}
 </svg></div>
 <div style={{position:'absolute',left:1440,top:225,width:395}}>
 <div style={{fontSize:24,color:'#6e6e6e'}}>주변 배치 · 공개지도 기준</div>
 <div style={{marginTop:25,fontSize:36,fontWeight:700,color:kind==='station'?pink:'#253840'}}>{categoryNames[kind]}</div>
 <div style={{marginTop:32}}>{[['housing','주거 단지'],['commerce','상권 · 쇼핑시설'],['park','공원 · 녹지']].map(([id,name])=><div key={id} style={{marginBottom:22,fontSize:26,opacity:id===kind?1:.65}}><span style={{display:'inline-block',width:22,height:22,background:landColors[id],verticalAlign:'middle',marginRight:14}}/>{name}</div>)}</div>
 <div style={{borderTop:'2px solid #d3d2c8',paddingTop:25,fontSize:27,lineHeight:1.6}}>{selected.length?selected.map((a:any)=><div key={a.id}>{a.name}</div>):<>운영 중인 다산역에서<br/>주변의 실제 시설을 확인</>}</div>
 <div style={{marginTop:30,fontSize:24,lineHeight:1.6,color:'#6e6e6e'}}>역이 있다는 사실에서<br/>내 생활 동선까지 연결하기</div>
 </div>
 </>;
}
''' +s[end:]
s=s.replace("'지리 위치를 바탕으로 노선 표시 · 4호선 진접선은 같은 노선의 연장 구간'", "t>=40.3&&t<61?D.dasanContext.source_note:'지리 위치를 바탕으로 노선 표시 · 4호선 진접선은 같은 노선의 연장 구간'")
p.write_text(s,encoding='utf-8')
print('source ready')
