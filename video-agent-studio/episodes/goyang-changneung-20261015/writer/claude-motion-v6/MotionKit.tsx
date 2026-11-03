import React from 'react';
import { interpolate } from 'remotion';

const INK='#173348',BLUE='#286cda',GREEN='#4f8970',CREAM='#f6f4ef',FF='Pretendard,sans-serif';
const ei=(f:number,s=18,e=30)=>interpolate(f,[s,e],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

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
  const op=ei(frame);const cols=['S1','S4','S5'];
  return<div style={{position:'absolute',left:80,top:190,width:760,fontFamily:FF,opacity:op}}>
    <div style={{display:'flex',borderBottom:`2px solid ${INK}`,paddingBottom:8,marginBottom:8}}>
      <div style={{width:160}}/>
      {cols.map(c=><div key={c} style={{flex:1,textAlign:'center',fontSize:26,fontWeight:700,color:active==='all'||active===c?BLUE:'#aaa'}}>{c}</div>)}
    </div>
    {rows.map(r=>{const hl=active==='all'||active===r.label;return(
      <div key={r.label} style={{display:'flex',alignItems:'center',marginBottom:12,opacity:hl?1:0.35}}>
        <div style={{width:160,fontSize:26,color:INK,fontWeight:600}}>{r.label}</div>
        {r.values.map((v,i)=><div key={i} style={{flex:1,textAlign:'center',fontSize:34,fontWeight:800,color:active===cols[i]?BLUE:INK}}>{v}<span style={{fontSize:20}}>분</span></div>)}
      </div>);})}
  </div>;
}

export function PriceComparison({frame,rows,active}:{frame:number;rows:{label:string;value:number;note?:string}[];active?:string}){
  const op=ei(frame);const mx=Math.max(...rows.map(r=>r.value));
  return<div style={{position:'absolute',left:80,top:190,width:800,fontFamily:FF,opacity:op}}>
    {rows.map((r,i)=>{const hl=!active||active==='all'||active===r.label;
      const w=interpolate(frame,[18+i*3,30+i*3],[0,(r.value/mx)*600],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
      return<div key={r.label} style={{marginBottom:28,opacity:hl?1:0.35}}>
        <div style={{fontSize:26,color:INK,fontWeight:600,marginBottom:6}}>{r.label}</div>
        <div style={{display:'flex',alignItems:'center',gap:16}}>
          <div style={{width:w,height:44,background:hl?BLUE:'#aaa',borderRadius:4,minWidth:4,transition:'none'}}/>
          <span style={{fontSize:34,fontWeight:800,color:INK}}>{r.value.toLocaleString()}<span style={{fontSize:22}}>만원</span></span>
          {r.note&&<span style={{fontSize:20,color:GREEN}}>{r.note}</span>}
        </div>
      </div>;})}
  </div>;
}

export function CalendarReveal({frame,events,startYear=2027,endYear=2032,active}:{frame:number;events:{label:string;year:number;month?:number;kind?:'move'|'school'|'rail';status?:string}[];startYear?:number;endYear?:number;active?:string}){
  const op=ei(frame);const span=endYear-startYear+1;const W=1760/span;
  const clrs:{[k:string]:string}={move:BLUE,school:GREEN,rail:'#c07a2b'};
  const years=Array.from({length:span},(_,i)=>startYear+i);
  return<div style={{position:'absolute',left:80,top:190,width:1760,fontFamily:FF,opacity:op}}>
    <div style={{display:'flex',borderBottom:`2px solid ${INK}`,paddingBottom:8,marginBottom:12}}>
      {years.map(y=><div key={y} style={{flex:1,textAlign:'center',fontSize:26,fontWeight:700,color:INK}}>{y}</div>)}
    </div>
    {(['move','school','rail'] as const).map(lane=>(
      <div key={lane} style={{position:'relative',height:60,marginBottom:12}}>
        {events.filter(e=>(e.kind??'move')===lane).map((e,idx)=>{
          const hl=!active||active==='all'||active===e.label;
          const xp=((e.year-startYear)+(e.month?(e.month-1)/12:0))/span*1760;
          const bw=e.month?W/6:W*0.8;
          return<div key={idx} style={{position:'absolute',left:xp,top:8,width:Math.max(bw,10),height:40,background:hl?clrs[lane]:'#ccc',borderRadius:4,opacity:hl?1:0.3}}>
            <div style={{position:'absolute',top:-26,left:0,fontSize:20,color:clrs[lane],fontWeight:600,whiteSpace:'nowrap'}}>{e.label}{e.status?` (${e.status})`:''}</div>
          </div>;})}
      </div>))}
  </div>;
}

export function DecisionHighlight({frame,active,rows}:{frame:number;active?:string;rows:{label:string;reason:string}[]}){
  const op=ei(frame);
  return<div style={{position:'absolute',left:80,top:190,width:1760,display:'flex',gap:40,fontFamily:FF,opacity:op}}>
    {rows.map((r,i)=>{const hl=!active||active==='all'||active===r.label;
      const p=interpolate(frame,[18+i*4,30+i*4],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
      return<div key={r.label} style={{flex:1,background:hl?BLUE:CREAM,borderRadius:12,padding:'28px 32px',opacity:hl?p:p*0.35}}>
        <div style={{fontSize:34,fontWeight:800,color:hl?CREAM:INK,marginBottom:12}}>{r.label}</div>
        <div style={{fontSize:26,color:hl?CREAM:INK,lineHeight:1.55}}>{r.reason}</div>
      </div>;})}
  </div>;
}