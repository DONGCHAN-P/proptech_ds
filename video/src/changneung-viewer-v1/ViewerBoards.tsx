import React from 'react';
import {interpolate,useCurrentFrame} from 'remotion';
import {Shell} from '../changneung-v4/Representative';
import DATA from '../changneung-v6/data.json';
const blue='#286cda',ink='#173348',muted='#637580',green='#4f8970',cream='#f6f4ef';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const prices=['S5','S1','S4'].map(id=>(DATA as any).prices.find((x:any)=>x.price?.scope?.startsWith(id)));
const panel:React.CSSProperties={position:'absolute',background:'#fffdf8',borderRadius:12};
function Price({active='all'}:{active?:string}){return <>
 <div style={{position:'absolute',left:100,top:190,fontSize:27,color:muted}}>본청약 공고 사례 · 현재 신규 접수 안내 아님</div>
 <div style={{position:'absolute',left:100,top:232,fontSize:26}}>특정 84㎡대 · 5층 이상 · 기본가+발코니 확장 · 다른 유상옵션·세금 별도</div>
 {prices.map((x:any,i:number)=>{const p=x.price,id=p.scope.split(' ')[0],hl=active==='all'||active===id;return <div key={id} style={{...panel,left:100+i*580,top:290,width:550,height:395,padding:'24px 28px',borderTop:`6px solid ${hl?blue:'#bdcbd5'}`,background:active===id?'#e8eef9':'#fffdf8'}}>
  <div style={{fontSize:38,fontWeight:700,color:hl?blue:ink}}>{id}</div>
  <div style={{fontSize:79,fontWeight:700,letterSpacing:-2,color:hl?blue:ink,marginTop:12}}>약 {(p.basic_plus_balcony_krw/1e8).toFixed(2)}<span style={{fontSize:50,marginLeft:4}}>억</span></div>
  <div style={{fontSize:28,marginTop:13}}>{p.basic_plus_balcony_krw.toLocaleString('ko-KR')}원</div>
  <div style={{fontSize:26,color:muted,marginTop:21}}>{p.scope} · {p.exclusive_area_sqm}㎡ · 5층 이상</div>
  <div style={{fontSize:23,marginTop:14,lineHeight:1.55}}>기본가 {p.amount_krw.toLocaleString('ko-KR')}원<br/>확장 {p.balcony_extension_krw.toLocaleString('ko-KR')}원</div>
  <div style={{fontSize:21,color:muted,marginTop:10}}>공고 {x.published_on}</div>
 </div>})}
 <div style={{position:'absolute',left:130,top:735,width:1660,textAlign:'center',fontSize:active==='S4'?52:35,fontWeight:700,color:active==='S4'?blue:ink}}>{active==='S4'?'S4 · 약 9,700만원 추가 (S5 대비)':'가격표에서 먼저 읽을 것은, 내 예산과 추가 부담'}</div>
 {active==='S4'?<div style={{position:'absolute',left:130,top:805,width:1660,textAlign:'center',fontSize:25,color:muted}}>공고가 사례의 차이 · 생활권 가치의 원인이나 미래 차익을 뜻하지 않음</div>:null}
 </>}
const supply=[{id:'S6',n:430,year:2027,month:12},{id:'S5',n:759,year:2028,month:1},{id:'S1',n:494,year:2029,month:5},{id:'S4',n:1024,year:2030,month:3}];
const cum:{[k:string]:number}={S6:0,S5:759,S1:1253,S4:2277};
function Supply({active='S4',frame=40}:{active?:string;frame?:number}){const target=supply.find(x=>x.id===active)!;const x=(v:number)=>660+(v-2027)/5*500;const op=interpolate(frame,[0,15],[.65,1],clamp);return <>
 <div style={{position:'absolute',left:100,top:190,fontSize:26,color:'#94682a'}}>별도: S6 430세대 · 2027.12 예정 · 비교 3후보 합계에서 제외</div>
 <svg width={1120} height={490} style={{position:'absolute',left:80,top:245,fontFamily:'Pretendard'}}>
  <line x1={580} y1={45} x2={1080} y2={45} stroke="#aab9c0" strokeWidth={2}/>
  {[2027,2028,2029,2030,2031,2032].map(y=><g key={y}><line x1={x(y)-80} x2={x(y)-80} y1={38} y2={52} stroke={muted}/><text x={x(y)-80} y={23} textAnchor="middle" fontSize={24} fill={ink}>{y}</text></g>)}
  {supply.map((e,i)=>{const yes=e.id===active,y=115+i*91,c=e.id==='S6'?'#94682a':blue;return <g key={e.id} opacity={yes?1:.55}>
   {yes?<rect x={10} y={y-39} width={1090} height={75} fill="#e7edf8" rx={6}/>:null}
   <text x={30} y={y+6} fontSize={30} fontWeight={700} fill={c}>{e.id}{e.id==='S6'?' · 별도':''}</text>
   <text x={205} y={y+6} fontSize={29} fill={ink}>{e.year}.{String(e.month).padStart(2,'0')} 예정</text>
   <text x={445} y={y+6} fontSize={29} fontWeight={700} fill={c}>{e.n.toLocaleString()}세대</text>
   <line x1={580} y1={y} x2={1080} y2={y} stroke="#d3dfe3"/><circle cx={x(e.year+(e.month-1)/12)-80} cy={y} r={yes?9:6} fill={c}/>
  </g>})}
 </svg>
 <div style={{...panel,left:1240,top:275,width:580,height:390,padding:'30px 38px',opacity:op,borderLeft:`7px solid ${active==='S6'?'#94682a':blue}`}}>
  <div style={{fontSize:40,fontWeight:700,color:blue}}>지금 설명하는 {target.id}</div>
  <div style={{fontSize:97,fontWeight:700,color:ink,marginTop:32}}>{target.n.toLocaleString()}<span style={{fontSize:40}}>세대</span></div>
  <div style={{fontSize:31,marginTop:27}}>{target.year}.{String(target.month).padStart(2,'0')} 입주 예정</div>
  <div style={{fontSize:25,color:muted,marginTop:19}}>{active==='S6'?'별도 참고행 · 아래 누적에서 제외':'확인된 해당 공고 규모'}</div>
 </div>
 <div style={{position:'absolute',left:125,top:735,fontSize:29,color:muted}}>비교 후보 누적 <span style={{fontSize:active==='S6'?42:57,color:blue,fontWeight:700,marginLeft:25}}>{active==='S6'?'S6 합계 제외':cum[active].toLocaleString()+'세대'}</span></div>
 <div style={{position:'absolute',left:750,top:753,fontSize:36,fontWeight:700,color:ink}}><span style={{color:active==='S6'?'#a7b0b5':blue}}>759</span> + <span style={{color:['S1','S4'].includes(active)?blue:'#a7b0b5'}}>494</span> + <span style={{color:active==='S4'?blue:'#a7b0b5'}}>1,024</span> = <span style={{color:active==='S4'?blue:'#a7b0b5'}}>2,277</span></div>
 <div style={{position:'absolute',left:125,top:817,fontSize:25,color:muted}}>세 후보의 공고 규모 · 창릉과 주변 지역의 전체 공급량 아님</div>
 </>}
const familyEvents=[{label:'S5 입주',date:'2028.01 예정',v:2028,c:blue},{label:'S1 입주',date:'2029.05 예정',v:2029+4/12,c:blue},{label:'S4 입주',date:'2030.03 예정',v:2030+2/12,c:blue},{label:'GTX-A 창릉역',date:'2030년 예정 · 월 미정',v:2030,range:true,c:'#a57837'},{label:'고양은평선',date:'2031.12 목표',v:2031+11/12,c:'#a57837'}];
function Family(){const x=(v:number)=>660+(v-2027)/5*1050;return <>
 {['내 계약 종료','아이 입학','희망 입주'].map((t,i)=><div key={t} style={{...panel,left:100+i*580,top:205,width:550,height:255,padding:'25px 32px',borderTop:'6px solid '+blue}}><div style={{fontSize:39,fontWeight:700}}>{i+1}. {t}</div><div style={{fontSize:70,fontWeight:700,color:blue,marginTop:35,letterSpacing:2}}>YYYY.MM</div><div style={{fontSize:24,color:muted,marginTop:15}}>내 날짜를 직접 대입</div></div>)}
 <div style={{position:'absolute',left:115,top:499,fontSize:39,fontWeight:700,color:blue}}>일시정지하고 내 날짜를 대입해보세요</div>
 <svg width={1760} height={285} style={{position:'absolute',left:80,top:570,fontFamily:'Pretendard'}}>
  <text x={25} y={28} fill={muted} fontSize={25}>그다음, 아래 일정과 나란히 비교</text>
  <line x1={580} y1={43} x2={1630} y2={43} stroke="#b5c1c7"/>
  {[2027,2028,2029,2030,2031,2032].map(y=><text key={y} x={x(y)-80} y={28} fill={muted} textAnchor="middle" fontSize={23}>{y}</text>)}
  {familyEvents.map((e,i)=>{const y=84+i*39;return <g key={e.label}><text x={25} y={y+7} fill={e.c} fontSize={25} fontWeight={700}>{e.label}</text><text x={265} y={y+7} fill={ink} fontSize={24}>{e.date}</text><line x1={580} x2={1630} y1={y} y2={y} stroke="#dce3e5"/>{e.range?<line x1={x(e.v)-80} x2={x(e.v+1)-80} y1={y} y2={y} stroke={e.c} strokeWidth={5} strokeDasharray="8 5"/>:<circle cx={x(e.v)-80} cy={y} r={6} fill={e.c}/>}</g>})}
 </svg>
 </>}
export function ViewerBoard({kind='price',active='all',stageFrame=40,caption='가격표보다 먼저, 내 예산과 선택 조건을 함께 보겠습니다.'}:{kind?:string;active?:string;stageFrame?:number;caption?:string}){return <Shell title={kind==='price'?'가격 · 내 예산과 추가 부담부터':kind==='supply'?'확인된 공고 입주달력 · 한 후보씩 비교':'내 이사 달력 · 내 날짜 세 개부터'} source={kind==='price'?'자료: 각 본청약 모집공고 · 기본가+발코니확장 특정 사례 · 옵션·세금 별도':kind==='supply'?'자료: 각 모집공고 · 입주 예정 · S6 별도 참고행 / 2,277세대는 비교 3후보 합계':'자료: 각 모집공고·철도 발표 · 입주 예정/철도 목표 구분 · 개인 날짜는 미입력'} caption={caption}>{kind==='price'?<Price active={active}/>:kind==='supply'?<Supply active={active} frame={stageFrame}/>:<Family/>}</Shell>}
export function SupplyMotion(){const f=useCurrentFrame(),active=f<30?'S6':f<80?'S5':f<130?'S1':'S4',start=f<30?0:f<80?30:f<130?80:130;return <ViewerBoard kind="supply" active={active} stageFrame={f-start} caption="6초 무음 연출 샘플 · 본편 발화 타이밍에 맞춘 영상은 아닙니다."/>}
