import React from 'react';
import {Img,staticFile,useCurrentFrame} from 'remotion';
import {Shell} from './Visuals';
import type {MapLedProject,TimelineScene} from './types';
const colors={school:'#c4d9f4',park:'#cfe4cc',commerce:'#efd0d9',housing:'#eee0b1'};
const concise:Record<string,string[]>={
'W1-A1':['왕숙1 북부 · 자족용지와 주거','입주 2028.08 / 개교목표 2028.03','남쪽의 예정 철도와는 위치가 다릅니다'],
'W1-A2':['학교·공원이 배치된 신혼희망타운','46·55㎡ / 입주 2028.08','자격·금융 조건을 함께 확인합니다'],
'W1-A24':['학교·공원과 남부 생활권의 접점','입주 2028.12 / 개교목표 2029.03','입주 직후의 통학 공백을 확인합니다'],
'W1-B17':['왕숙1 남부 · 74·84㎡ 선택지','입주예정 2028.12','예정 교통의 완성 시점이 변수입니다'],
'W2-A1':['학교 배치와 가격을 함께 보는 대안','입주 2029.02 / 개교목표 2029.03','A3보다 이른 입주와 비용을 비교합니다'],
'W2-A3':['공원·복합 기능이 만나는 남부 후보','입주예정 2030.05','늦은 입주 · 높은 분양가 비교']};
export function CandidateContext({scene,project}:{scene:TimelineScene;project:MapLedProject}){
 const f=useCurrentFrame(),id=scene.focus_ids?.[0],b=project.atlas.blocks.find((x:any)=>x.candidate_id===id);
 if(!b)return null;
 const w2=id?.startsWith('W2'),asset=project.assets.find(a=>a.asset_id===(w2?'PLAN_W2_ORIGINAL':'PLAN_W1_ORIGINAL'));
 const slots:any={north:[480,20],south:[480,360],west:[30,175],east:[930,175]};
 const entries=Object.entries(b.neighbors||{}).slice(0,4),info=concise[id||'']||[];
 const scale=135/.024,pr=(pt:number[])=>[170+(pt[0]-b.coordinates.lon)*.791*scale,78+(b.coordinates.lat-pt[1])*scale];
 return <Shell title={`${b.district} ${b.block_id} · ${scene.map_theme==='life'?'학교와 생활 배치':'입지의 장점과 기다릴 조건'}`} label="남양주시 원본 계획도 전체 무편집 · LH 공고의 주변 배치 설명을 별도 관계도로 재구성 / 관계도는 축척·정밀경계·보행 동선 아님">
 <div style={{position:'absolute',left:80,top:182,width:510,height:660,background:'white',borderRadius:12,padding:8}}><Img src={staticFile(asset!.file!)} style={{width:'100%',height:'100%',objectFit:'contain'}}/><div style={{position:'absolute',left:0,right:0,bottom:-27,fontSize:18,textAlign:'center'}}>공식 전체 계획도 · 공공누리 제3유형</div></div>
 <div style={{position:'absolute',left:625,top:190,width:1210,height:510,background:'#eeece5',borderRadius:18}}><div style={{position:'absolute',left:25,top:15,fontSize:20,color:'#646a6d'}}>계획도 기반 배치 관계 · 축척·정밀경계 아님</div><svg viewBox="0 0 1210 510" width="1210" height="510">
 {entries.map(([k,v],i)=>{const [x,y]=slots[k],s=String(v),color=/학교|유치원|초등|중학/.test(s)?colors.school:/공원|녹지/.test(s)?colors.park:/상업|근린|복합/.test(s)?colors.commerce:colors.housing;return <g key={k} opacity={Math.max(.18,Math.min(1,(f-i*7)/20))}><path d={`M605 260L${x+120} ${y+48}`} stroke="#a6aaa3" strokeWidth={2} strokeDasharray="6 5"/><rect x={x} y={y+34} width={240} height={104} rx={12} fill={color}/><foreignObject x={x+10} y={y+43} width={220} height={90}><div style={{fontSize:22,lineHeight:1.38,textAlign:'center',display:'flex',alignItems:'center',justifyContent:'center',height:'100%',wordBreak:'keep-all'}}>{s}</div></foreignObject><text x={x+120} y={y+24} textAnchor="middle" fontSize={19} fill="#747873">{({north:'북쪽',south:'남쪽',east:'동쪽',west:'서쪽'} as any)[k]}</text></g>})}
 <rect x={475} y={215} width={260} height={100} rx={16} fill="#2f6fed"/><text x={605} y={258} textAnchor="middle" fill="white" fontSize={32} fontWeight={700}>{b.district} {b.block_id}</text><text x={605} y={290} textAnchor="middle" fill="white" fontSize={20}>해당 블록 중심의 배치 설명</text>
 <svg x={850} y={10} width={340} height={165} viewBox="0 0 340 165"><rect width={340} height={165} rx={9} fill="#f8f9f5"/>{project.map.paths.map((p,i)=><path key={i} d={p.points.map((pt,j)=>{const q=pr(pt);return `${j?'L':'M'}${q[0]},${q[1]}`}).join(' ')} fill="none" stroke={p.kind==='water'?'#b2d4df':'#d3d0c5'} strokeWidth={p.kind==='water'?2:1}/>)}{project.map.block_points.map(p=>{const q=pr([p.lon,p.lat]),active=p.id===id;return <g key={p.id}><circle cx={q[0]} cy={q[1]} r={active?6:2.5} fill={active?'#2f6fed':'#adb4b7'}/>{active?<text x={q[0]+9} y={q[1]-5} fill="#17191e" fontSize={17} fontWeight={700} stroke="white" strokeWidth={4} paintOrder="stroke">{p.name}</text>:null}</g>})}<text x={8} y={158} fontSize={13} fill="#646a6d">실제 안내점 위치 · © OSM contributors</text></svg>
 </svg></div>
 <div style={{position:'absolute',left:640,top:725,right:85,display:'flex',gap:32}}>{info.map((s,i)=><div key={i} style={{flex:1,fontSize:i===0?27:24,lineHeight:1.5,color:i===0?'#17191e':'#626965',borderTop:'3px solid '+(i===0?'#2f6fed':'#c9cdc6'),paddingTop:14,fontWeight:i===0?700:400}}>{s}</div>)}</div>
 </Shell>
}
