import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import data from '../../public/namyangju-rail-route-proof-v2/proof_data.json';
const D:any=data;
const cream='#F6F4EF',ink='#17191e',blue='#00A5DE',pink='#E6186C',green='#0C8E72',amber='#e6a419';
const cap=(v:number)=>Math.max(0,Math.min(1,v));
const ease=(v:number)=>{const p=cap(v);return p*p*(3-2*p)};
const mix=(a:number,b:number,p:number)=>a+(b-a)*p;
function projection(bounds:number[],w=1320,h=650){const [west,south,east,north]=bounds;const scale=Math.min(w/((east-west)*Math.cos(37.7*Math.PI/180)),h/(north-south));return (p:number[])=>[w/2+(p[0]-(west+east)/2)*Math.cos(37.7*Math.PI/180)*scale,h/2+((south+north)/2-p[1])*scale]}
const path=(pts:number[][],pr:any)=>pts.map((p,i)=>{const q=pr(p);return `${i?'L':'M'}${q[0].toFixed(2)},${q[1].toFixed(2)}`}).join(' ');
function pointAlong(pts:number[][],p:number,pr:any){const points=pts.map(pr),lengths=points.slice(1).map((q:number[],i:number)=>Math.hypot(q[0]-points[i][0],q[1]-points[i][1]));let remain=lengths.reduce((a:number,b:number)=>a+b,0)*cap(p);for(let i=0;i<lengths.length;i++){if(remain<=lengths[i])return [mix(points[i][0],points[i+1][0],remain/Math.max(.001,lengths[i])),mix(points[i][1],points[i+1][1],remain/Math.max(.001,lengths[i]))];remain-=lengths[i]}return points[points.length-1]||[0,0]}
function Place({p,pr,color=ink,align='right'}:any){const [x,y]=pr([p.lon,p.lat]);return <g><circle cx={x} cy={y} r={7} fill="white" stroke={color} strokeWidth={4}/><text x={x+(align==='left'?-15:15)} y={y-10} textAnchor={align==='left'?'end':'start'} fontSize={28} fontWeight={700} stroke={cream} strokeWidth={7} paintOrder="stroke" fill={ink}>{p.name}</text></g>}
function Base({pr}:any){return <g>{D.background.map((p:any,i:number)=><path key={i} d={path(p.points,pr)} fill={p.kind==='park'?'#dce7d5':p.kind==='building'?'#e0ded5':'none'} stroke={p.kind==='water'?'#a2cfdd':p.kind==='rail'?'#c4c4c4':p.kind==='building'?'#cac7bd':'#d3c9b6'} strokeWidth={p.kind==='water'?5:p.kind==='building'?1:2} opacity={.85}/>)}<g transform="translate(35 30)"><path d="M0 42L14 0L28 42L14 32Z" fill="#4d585c"/><text x={14} y={-8} textAnchor="middle" fontSize={20} fill="#4d585c">N</text></g></g>}
function Rail({t}:any){const phase=t<15?0:t<28?1:2;const base=D.railBounds;const target=phase===0?D.byeollaeBounds:D.railBounds;const tween=ease((t-(phase===0?0:15))/1.4);const bounds=base.map((v:number,i:number)=>phase===0?mix(v,target[i],ease(t/1.2)):mix(D.byeollaeBounds[i],v,tween));const pr=projection(bounds);const highlight=phase===0?'byeollae':phase===1?'byeolgaram':'all';return <><div style={{position:'absolute',left:80,top:100,fontSize:50,fontWeight:700}}>별내역과 별내별가람역, 서로 다른 역</div><div style={{position:'absolute',left:80,top:200,width:1320,height:650,borderRadius:18,overflow:'hidden',background:'#eeece5'}}><svg width="1320" height="650"><Base pr={pr}/>{D.lines.map((line:any,i:number)=>{const start=line.id==='eight'?3:line.id==='gyeongchun'?7:line.id==='four'?15:18;return <g key={line.id} opacity={cap((t-start+.7)/.7)}><path d={(line.segments||[line.points]).map((pts:number[][])=>path(pts,pr)).join(' ')} fill="none" stroke="white" strokeWidth={13}/><path d={(line.segments||[line.points]).map((pts:number[][])=>path(pts,pr)).join(' ')} fill="none" stroke={line.color} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-ease((t-start)/2.5)}/></g>})}{D.stations.filter((p:any)=>p.id!=='dasan').map((p:any)=><Place key={p.id} p={p} pr={pr} color={p.id==='byeollae'?pink:blue} align={p.id==='onnam'?'left':'right'}/>)}{D.stations.filter((p:any)=>p.id===highlight).map((p:any)=>{const [x,y]=pr([p.lon,p.lat]);return <circle key={p.id} cx={x} cy={y} r={18+3*Math.sin(t*3)} fill="none" stroke={amber} strokeWidth={5}/>})}</svg></div><div style={{position:'absolute',left:1440,top:230,width:395}}><div style={{fontSize:25,color:'#6e6e6e'}}>현재 운영 노선</div>{[['8호선 · 별내선',pink],['경춘선',green],['4호선',blue]].map(([name,c],i)=><div key={name} style={{marginTop:35,fontSize:31,fontWeight:700,opacity:cap((t-[3,7,15][i]+.7)/.7)}}><span style={{display:'inline-block',width:40,height:8,background:c,verticalAlign:'middle',marginRight:15}}/>{name}</div>)}<div style={{marginTop:42,fontSize:26,lineHeight:1.65}}>진접선은<br/><b style={{color:blue}}>4호선의 연장 구간</b><br/>별내별가람 → 오남 → 진접</div><div style={{marginTop:35,padding:20,background:'#fff4c9',fontSize:25,lineHeight:1.6}}>별내역 ↔ 별내별가람역<br/>동일 역 내 환승 아님</div></div></>}
function walkFacing(points:number[][],progress:number,pr:any){const a=pointAlong(points,Math.max(0,progress-.025),pr),b=pointAlong(points,Math.min(1,progress+.025),pr);return b[0]-a[0]<-2?-1:1}
function Walker({x,y,moving=false,color=amber,facing=1}:any){
 const f=useCurrentFrame(),cycle=moving?f*.26:0,stride=moving?Math.sin(cycle):0;
 const bounce=moving?Math.abs(Math.sin(cycle))*.8:0;
 const jacket=color===amber?'#b77e15':'#0786b4',pants='#2b3d47';
 const leg=(side:number)=>{const swing=stride*side*23,knee=Math.max(0,-stride*side)*24;return <g key={side} transform={`translate(${side*1.3} -19) rotate(${swing})`}><path d="M-2.6 0L2.5 0L2.8 10L-2.6 10Z" fill={pants}/><g transform={`translate(0 10) rotate(${knee})`}><path d="M-2.6 -1L2.8 -1L2.6 8L-2.1 8Z" fill={pants}/><path d="M-2.2 6.5L2.8 6.5L7.4 8.5L7.4 10L-2.8 10Z" fill="#17262e"/></g></g>};
 const arm=(side:number)=>{const swing=-stride*side*22;return <g key={side} transform={`translate(${side*4} -36) rotate(${swing})`}><path d="M-2.2 0L2.2 0L2.4 10L-1.8 11Z" fill={jacket}/><path d="M-1.8 9L2.4 9L4.2 16L.7 17Z" fill={jacket}/><ellipse cx={2.1} cy={17.2} rx={2} ry={2.4} fill="#e5b891"/></g>};
 return <g transform={`translate(${x} ${y})`}><circle cx={0} cy={-12} r={16} fill="#fffdf5" stroke={color} strokeWidth={1.25}/><g transform={`translate(0 ${-bounce*.48}) scale(${facing*.48} .48)`}>
 {leg(-1)}{arm(-1)}
 <path d="M-7 -36Q-12 -35 -11 -25L-7 -24Z" fill="#43535c"/>
 <path d="M-5.2 -38Q0 -41 5.7 -37L6.3 -26L4.8 -19L-5 -19L-6.4 -29Z" fill={jacket}/>
 <path d="M-1.5 -42L2.8 -42L3.3 -37L-1.9 -37Z" fill="#e5b891"/>
 <ellipse cx={1.3} cy={-47} rx={4.9} ry={5.5} fill="#e5b891"/>
 <path d="M-3.6 -47Q-4 -53 1.4 -53Q6.4 -53 6.2 -48L2.4 -49L-2 -46Z" fill="#263740"/>
 <path d="M5 -48L7.1 -46L5 -45Z" fill="#e5b891"/>
 {leg(1)}{arm(1)}
 </g></g>;
}
function Bus({x,y}:any){return <g transform={`translate(${x} ${y})`}><rect x={-28} y={-21} width={56} height={39} rx={8} fill={blue} stroke="white" strokeWidth={4}/><rect x={-20} y={-14} width={40} height={15} rx={3} fill="white"/><circle cx={-16} cy={19} r={6} fill={ink}/><circle cx={16} cy={19} r={6} fill={ink}/></g>}
function Commute({t,replay=false}:any){
 const c=D.commute,pr=projection(c.bounds),tt=replay?t-61:t-30;
 const walk=cap((tt-1)/8),access=cap((tt-1)/1.5),bus=cap((tt-3.5)/3),egress=cap((tt-6.5)/1.5);
 const wp=pointAlong(c.walkPoints,walk,pr),bp=pointAlong(c.busPoints,bus,pr);
 const accessActive=tt<2.5,waiting=tt>=2.5&&tt<3.5,busActive=tt>=3.5&&tt<6.5;
 const legPoints=accessActive||waiting?c.accessPoints:c.egressPoints;
 const lp=pointAlong(legPoints,accessActive||waiting?access:egress,pr);
 const stage=accessActive?'① 정류장까지 걷기':waiting?'② 버스 기다리기':busActive?'③ 버스 탑승':'④ 하차 후 역까지 걷기';
 return <>
 <div style={{position:'absolute',left:80,top:100,fontSize:50,fontWeight:700}}>같은 단지, 역까지 가는 방법을 확인</div>
 <div style={{position:'absolute',left:80,top:200,width:1320,height:650,overflow:'hidden',background:'#eeece5',borderRadius:18}}>
 <svg width="1320" height="650"><Base pr={pr}/>
 <path d={path(c.apartmentBoundary,pr)} fill="#ffe9a855" stroke={amber} strokeWidth={3}/>
 <path d={path(c.busPoints,pr)} fill="none" stroke="white" strokeWidth={13}/>
 <path d={path(c.busPoints,pr)} fill="none" stroke={blue} strokeWidth={7} opacity={.3}/>
 <path d={path(c.busPoints,pr)} fill="none" stroke={blue} strokeWidth={7} pathLength={1} strokeDasharray={1} strokeDashoffset={1-bus}/>
 <path d={path(c.walkPoints,pr)} fill="none" stroke={amber} strokeWidth={6} strokeDasharray="9 8"/>
 {[c.accessPoints,c.egressPoints].map((points:any,i:number)=><path key={i} d={path(points,pr)} fill="none" stroke={blue} strokeWidth={6} strokeDasharray="5 7" opacity={i===0?Math.max(.3,access):Math.max(.3,egress)}/>)}
 <Place p={c.apartment} pr={pr}/><Place p={c.station} pr={pr} color={pink} align="left"/>
 {(c.busStops||[]).map((p:any,i:number)=>{const [x,y]=pr([p.lon,p.lat]);return <g key={i}><rect x={x-5} y={y-5} width={10} height={10} fill={blue}/><text x={x-15} y={y+23} textAnchor="end" fontSize={20} fill={blue} stroke={cream} strokeWidth={5} paintOrder="stroke">{p.name}</text></g>})}
 <Walker x={wp[0]} y={wp[1]} moving={walk>0&&walk<1} facing={walkFacing(c.walkPoints,walk,pr)}/>
 {busActive?<Bus x={bp[0]} y={bp[1]}/>:<Walker x={lp[0]} y={lp[1]} color={blue} moving={(accessActive&&access>0&&access<1)||(!accessActive&&!waiting&&egress>0&&egress<1)} facing={walkFacing(legPoints,accessActive||waiting?access:egress,pr)}/>}
 </svg></div>
 <div style={{position:'absolute',left:1440,top:220,width:395}}>
 <div style={{fontSize:25,color:'#6e6e6e'}}>실제 단지를 지정한 동선 예시</div>
 <div style={{fontSize:31,fontWeight:700,marginTop:25,lineHeight:1.5}}>{c.apartment.name}<br/>↓<br/>{c.station.name}</div>
 <div style={{marginTop:30,fontSize:27,color:'#8e6200'}}>● 전 구간 도보 · 느린 이동</div>
 <div style={{marginTop:20,fontSize:27,color:blue}}>■ {c.busRoute}번 버스 · 빠른 이동</div>
 <div style={{marginTop:28,fontSize:28,lineHeight:1.55,padding:'15px 18px',background:'#def1fa',color:'#167296'}}>{stage}</div>
 <div style={{marginTop:38,fontSize:29,lineHeight:1.7,color:'#61666a'}}>도보 → 48번 → 도보</div>
 </div></>;
}
const landColors:any={housing:'#edc873',commerce:'#ee9aa8',park:'#7db28b'};
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
export function RailRouteVisuals(){const t=useCurrentFrame()/30;return <AbsoluteFill style={{background:cream,color:ink}}><div style={{position:'absolute',left:80,right:80,top:28,display:'flex',justifyContent:'space-between',fontSize:23,color:'#6e6e6e'}}><b>｜ 데이터로 보는 부동산</b><span>남양주 · 왕숙 / 기존 생활권</span></div>{t<30?<Rail t={t}/>:t<40.3?<Commute t={t}/>:t<61?<Dasan/>:<Commute t={t} replay/>}<div style={{position:'absolute',left:80,right:80,top:870,fontSize:19,color:'#676b6d',lineHeight:1.45}}>© OpenStreetMap contributors · {D.sourceNote}<br/>{t>=30&&!(t>=40.3&&t<61)?'속도 비교 연출 · 실제시간 아님 | 단지 대표 진입도로점·출입구 미확인 | 역 4번출구 인근·보도/횡단보도 통행 미확인':t>=40.3&&t<61?D.dasanContext.source_note:'지리 위치를 바탕으로 노선 표시 · 4호선 진접선은 같은 노선의 연장 구간'}</div></AbsoluteFill>}
