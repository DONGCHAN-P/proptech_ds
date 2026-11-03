import React from 'react';
import { interpolate } from 'remotion';

const INK='#173348',BLUE='#286cda',GREEN='#4f8970',CREAM='#f6f4ef',FF='Pretendard,sans-serif';
const ei=(f:number,s=0,e=24)=>interpolate(f,[s,e],[0.65,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

export function FocusOverlay({x,y,width,height,frame,active=true,label}:{x:number;y:number;width:number;height:number;frame:number;active?:boolean;label:string}){
  if(!active)return null;const op=ei(frame);
  return<svg style={{position:'absolute',left:0,top:0,width:1920,height:1080,pointerEvents:'none'}}>
    <rect x={x} y={y} width={width} height={height} fill="none" stroke={BLUE} strokeWidth={3} opacity={op} rx={4}/>
    <rect x={x} y={y-38} width={label.length*15+24} height={34} fill={BLUE} opacity={op} rx={3}/>
    <text x={x+10} y={y-14} fill={CREAM} fontSize={20} fontFamily={FF} opacity={op}>{label}</text>
  </svg>;
}

export function RouteReveal({d,frame,color=BLUE,label,x,y}:{d:string;frame:number;color?:string;label:string;x:number;y:number}){
  const p=interpolate(frame,[0,30],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return<svg style={{position:'absolute',left:0,top:0,width:1920,height:1080,pointerEvents:'none'}}>
    <path d={d} fill="none" stroke={color} strokeWidth={4} pathLength={1} strokeDasharray={1} strokeDashoffset={1-p}/>
    <text x={x} y={y} fill={color} fontSize={26} fontFamily={FF} fontWeight={700} opacity={p}>{label}</text>
  </svg>;
}

export function CommuteComparison({frame,active='all',rows}:{frame:number;active?:string;rows:{label:string;values:number[]}[]}){
 const cols=['S1','S4','S5'];return <div style={{position:'absolute',left:1260,top:275,width:580,fontFamily:FF,opacity:ei(frame)}}><div style={{display:'flex',borderBottom:'2px solid '+INK,paddingBottom:15}}><div style={{width:250,fontSize:23}}>도착 지점</div>{cols.map(c=><b key={c} style={{width:105,textAlign:'center',fontSize:28,color:BLUE}}>{c}</b>)}</div>{rows.map(r=><div key={r.label} style={{display:'flex',alignItems:'center',height:86,borderBottom:'1px solid #dbe2e3',opacity:active==='all'||active===r.label?1:.65,background:active===r.label?'#e6edf8':'transparent'}}><div style={{width:250,fontSize:26,fontWeight:700}}>{r.label}</div>{r.values.map((v,i)=><b key={i} style={{width:105,textAlign:'center',fontSize:34,color:active===r.label?BLUE:INK}}>{v}</b>)}</div>)}</div>
}

export function PriceComparison({frame,rows,active='all'}:{frame:number;rows:{label:string;value:number;note?:string}[];active?:string}){
 const mx=Math.max(...rows.map(r=>r.value));return <div style={{position:'absolute',left:150,top:300,width:1620,fontFamily:FF,opacity:ei(frame)}}>{rows.map((r,i)=>{const hl=active==='all'||active===r.label;const target=r.value/mx*860;const w=interpolate(frame,[0,30],[target*.7,target],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});return <div key={r.label} style={{marginBottom:42,opacity:hl?1:.65}}><div style={{display:'flex',alignItems:'center',gap:24}}><b style={{fontSize:34,width:90}}>{r.label}</b><div style={{width:900}}><div style={{width:w,height:48,background:hl?BLUE:'#a5b7c9'}}/></div><b style={{fontSize:38,color:hl?BLUE:INK}}>{Math.round(r.value*10000).toLocaleString()}원</b></div><div style={{fontSize:23,color:GREEN,marginLeft:115,marginTop:10}}>{r.note}</div></div>})}</div>
}

export function CalendarReveal({frame,events,startYear=2027,endYear=2032,active='all'}:{frame:number;events:{label:string;year:number;month?:number;kind?:'move'|'school'|'rail';status?:string}[];startYear?:number;endYear?:number;active?:string}){
 const x=(v:number)=>580+(v-startYear)/(endYear-startYear)*1090;const clrs:any={move:BLUE,school:GREEN,rail:'#a57837'};return <svg width={1760} height={530} style={{position:'absolute',left:80,top:220,fontFamily:FF,opacity:ei(frame)}}><line x1={580} y1={55} x2={1670} y2={55} stroke="#aab9c0" strokeWidth={2}/>{Array.from({length:endYear-startYear+1},(_,i)=>startYear+i).map(y=><g key={y}><line x1={x(y)} y1={48} x2={x(y)} y2={62} stroke="#71848e"/><text x={x(y)} y={32} textAnchor="middle" fontSize={25} fill={INK}>{y}</text></g>)}{events.map((e,i)=>{const y=120+i*72,c=clrs[e.kind||'move'],pos=x(e.year+(e.month?(e.month-1)/12:0)),hl=active==='all'||active===e.label;return <g key={i} opacity={hl?1:.65}><text x={30} y={y+8} fontSize={26} fill={c} fontWeight={700}>{e.label}</text><text x={290} y={y+8} fontSize={22} fill={INK}>{e.year}{e.month?'.'+String(e.month).padStart(2,'0'):'년'} · {e.status}</text><line x1={580} y1={y} x2={1670} y2={y} stroke="#dce3e5"/>{e.month?<circle cx={pos} cy={y} r={8} fill={c}/>:<line x1={pos} y1={y} x2={x(e.year+1)} y2={y} stroke={c} strokeWidth={7} strokeDasharray="10 6"/>}</g>})}</svg>
}

export function DecisionHighlight({frame,active='all',rows}:{frame:number;active?:string;rows:{label:string;reason:string}[]}){
 return <div style={{position:'absolute',left:850,top:245,width:960,fontFamily:FF,opacity:ei(frame)}}>{rows.map((r,i)=>{const hl=active==='all'||active===r.label;return <div key={r.label} style={{borderLeft:'6px solid '+(hl?BLUE:'#b4c1ca'),padding:'23px 24px',marginBottom:30,background:hl?'#e7edf6':'transparent',opacity:hl?1:.65}}><b style={{fontSize:38,color:BLUE}}>{r.label}</b><div style={{fontSize:29,color:INK,lineHeight:1.6,marginTop:12}}>{r.reason}</div></div>})}</div>
}
