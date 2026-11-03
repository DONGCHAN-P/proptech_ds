from pathlib import Path
p=Path(__file__).resolve().parents[5]/'video/src/NamyangjuRailRouteProofV1.tsx'
s=p.read_text(encoding='utf-8')
start=s.index('function Commute(')
end=s.index('function Dasan()',start)
s=s[:start]+'''function Commute({t,replay=false}:any){
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
 <Place p={c.apartment} pr={pr}/><Place p={c.station} pr={pr} color={pink}/>
 {(c.busStops||[]).map((p:any,i:number)=>{const [x,y]=pr([p.lon,p.lat]);return <g key={i}><rect x={x-5} y={y-5} width={10} height={10} fill={blue}/><text x={x-15} y={y+23} textAnchor="end" fontSize={20} fill={blue} stroke={cream} strokeWidth={5} paintOrder="stroke">{p.name}</text></g>})}
 <Walker x={wp[0]} y={wp[1]}/>
 {busActive?<Bus x={bp[0]} y={bp[1]}/>:<g style={{opacity:.9}}><g transform={`translate(${lp[0]} ${lp[1]})`} stroke={blue} strokeWidth={5} fill="none" strokeLinecap="round"><circle cy={-26} r={8} fill="white"/><path d="M0 -15V7M0 -8L-14 5M0 -8L15 -1M0 7L-12 25M0 7L13 25"/></g></g>}
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
''' +s[end:]
p.write_text(s,encoding='utf-8')
