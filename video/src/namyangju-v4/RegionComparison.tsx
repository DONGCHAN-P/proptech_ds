import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import contextsData from '../../public/namyangju-v4/comparison_contexts.json';
const D:any=contextsData,cream='#F6F4EF',ink='#17191e',colors:any={housing:'#edc873',commerce:'#ee9aa8',park:'#7db28b'};
function projection(b:number[]){const [w,s,e,n]=b,scale=Math.min(1320/((e-w)*Math.cos(37.7*Math.PI/180)),650/(n-s));return (p:number[])=>[660+(p[0]-(w+e)/2)*Math.cos(37.7*Math.PI/180)*scale,325+((s+n)/2-p[1])*scale]}
const path=(points:number[][],pr:any)=>points.map((p,i)=>{const q=pr(p);return `${i?'L':'M'}${q[0]},${q[1]}`}).join(' ');
export function RegionComparison({shot}:{shot:any}){
 const f=useCurrentFrame(),ctx=D.contexts[f<shot.frames/2?0:1],pr=projection(ctx.bounds),focus=Math.min(2,Math.floor(f/(shot.frames/3)));
 return <AbsoluteFill style={{background:cream,color:ink}}><div style={{position:'absolute',left:80,right:80,top:28,display:'flex',justifyContent:'space-between',fontSize:23,color:'#6e6e6e'}}><b>｜ 데이터로 보는 부동산</b><span>남양주 · 왕숙 / 가격 비교의 조건</span></div><div style={{position:'absolute',left:80,top:100,fontSize:50,fontWeight:700}}>주변 단지와 비교할 때, 같은 조건부터</div>
 <div style={{position:'absolute',left:80,top:200,width:1320,height:650,overflow:'hidden',background:'#eeece5',borderRadius:18}}><svg width="1320" height="650">
 {ctx.features.map((a:any)=><path key={a.id} d={path(a.points,pr)+' Z'} fill={colors[a.kind]} fillOpacity={.62} stroke={colors[a.kind]} strokeWidth={2}/>)}
 {ctx.water.map((a:any,i:number)=><path key={'w'+i} d={path(a.points,pr)} stroke="#9fc8d6" strokeWidth={8} fill="none"/>)}
 {ctx.roads.map((a:any,i:number)=><path key={'r'+i} d={path(a.points,pr)} stroke={['primary','secondary','tertiary'].includes(a.highway)?'#fff':'#cbc7bc'} strokeWidth={['primary','secondary','tertiary'].includes(a.highway)?4:1.5} fill="none"/>)}
 {ctx.buildings.map((a:any,i:number)=><path key={'b'+i} d={path(a.points,pr)+' Z'} fill="#f4f2e8" fillOpacity={.35} stroke="#7e7d78" strokeWidth={1}/>)}
 {ctx.display_labels.map((a:any)=>{const [x,y]=pr([a.lon,a.lat]),tx=x+a.dx,ty=y+a.dy;return <g key={a.id}><path d={`M${x} ${y}L${tx} ${ty}`} stroke={colors[a.kind]} strokeWidth={2}/><circle cx={x} cy={y} r={6} fill={colors[a.kind]} stroke="white" strokeWidth={2}/><text x={tx+(a.dx<0?-8:8)} y={ty} textAnchor={a.dx<0?'end':'start'} fontSize={24} fontWeight={700} fill={ink} stroke={cream} strokeWidth={6} paintOrder="stroke">{a.name.replace('아파트','').replace('현대프리미엄아울렛 ','')}</text></g>})}
 {(()=>{const [x,y]=pr([ctx.station.lon,ctx.station.lat]);return <g><circle cx={x} cy={y} r={8} fill="white" stroke="#E6186C" strokeWidth={4}/><text x={x+15} y={y-10} fontSize={28} fontWeight={700} fill={ink} stroke={cream} strokeWidth={6} paintOrder="stroke">{ctx.station.name}</text></g>})()}
 </svg></div>
 <div style={{position:'absolute',left:1440,top:225,width:395}}><div style={{fontSize:24,color:'#6e6e6e'}}>기존 지역의 배치 예시</div><div style={{fontSize:42,fontWeight:700,marginTop:22}}>{ctx.region_title}</div><div style={{display:'flex',gap:15,fontSize:20,color:'#6e6e6e',marginTop:25}}>{[['housing','주거'],['commerce','상업'],['park','공원']].map(([id,name])=><span key={id}><i style={{display:'inline-block',width:15,height:15,background:colors[id],marginRight:6}}/>{name}</span>)}</div><div style={{marginTop:38}}>{['같은 전용면적 · 거래 시점','준공연도 · 역 접근성','취소 거래 · 거래 건수'].map((s,i)=><div key={s} style={{fontSize:27,lineHeight:1.6,padding:'18px 15px',marginBottom:20,background:focus===i?'#fff0bd':'#ffffffa0',borderLeft:focus===i?'5px solid #d8ac2d':'5px solid transparent'}}>{s}</div>)}</div><div style={{marginTop:26,fontSize:24,lineHeight:1.65,color:'#6e6e6e'}}>입주한 단지의 실거래와<br/>입주 전 공고가격을<br/>같은 뜻으로 빼지 않습니다.</div></div>
 <div style={{position:'absolute',left:80,right:80,top:870,fontSize:19,lineHeight:1.45,color:'#676b6d'}}>© OpenStreetMap contributors · NCUC · GH · 시설 공식 안내 | 조회 2026.10.15<br/>공개지도 기반 주변 배치 · 단지별 가격·수익 계산 아님 · 모든 표시 시설이 역 도보권이라는 의미 아님</div>
 </AbsoluteFill>;
}
