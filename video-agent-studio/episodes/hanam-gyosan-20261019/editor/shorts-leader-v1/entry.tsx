import React from 'C:/projects/realestate_reco/video/node_modules/react';
import {AbsoluteFill,Audio,Composition,registerRoot,staticFile,useCurrentFrame,interpolate} from 'C:/projects/realestate_reco/video/node_modules/remotion';
import D from './data.json';
const ink='#132d43',blue='#367cda',ivory='#f5f1e8',colors:any={home:'#ead7a0',commercial:'#dfb8c8',park:'#bdd3ae',jobs:'#b9c9e8',school:'#aac8ce',other:'#dce0dd'};
const txt=(id:string,text:string,x:number,y:number,size:number,color=ink,width=700,kind='key_value')=><div data-critical={id} data-kind={kind} style={{position:'absolute',left:x,top:y,width,fontSize:size,fontWeight:kind==='condition_source'?400:700,color,lineHeight:1.15,whiteSpace:'pre-wrap',wordBreak:'keep-all'}}>{text}</div>;
export const Short=()=>{const f=useCurrentFrame(),t=f/30,c=D.clips.find(x=>t>=x.start&&t<x.end+.12),n=c?.mode??10,caption=D.captions.find(x=>t>=x.start&&t<x.end);const active=n<5?'C2':'B2',det=(D.details as any)[active],v=det.view,p=interpolate(f-(c?.start??0)*30,[0,24],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),cta=n===10,overall=n<2||n>=7;const view=overall?[120,350,550,450]:v;
return <AbsoluteFill style={{background:ivory,fontFamily:'Malgun Gothic'}}><Audio src={staticFile('voice.wav')}/>
<img src={staticFile('map-'+(overall?'all':active)+'.png')} style={{position:'absolute',top:435,width:1080,height:770}}/><svg width={1080} height={770} viewBox={view.join(' ')} preserveAspectRatio="xMidYMid slice" style={{position:'absolute',top:435}}>{D.features.filter(a=>['공동주택 (C2)','공동주택 (B2)'].includes(a.name)).map((a,i)=><path key={i} d={a.d} fill={a.name===`공동주택 (${active})`?blue:'#e3a33b'} fillOpacity={.6+.25*p} stroke={a.name===`공동주택 (${active})`?blue:'#ad741e'} strokeWidth={2.4}/>)}</svg>
<div style={{position:'absolute',inset:'0 0 auto',height:435,background:ivory}}/>
{txt('title','3기 신도시 하남 교산의\n대장단지는 어디가 될까?',140,270,58,ink,700,'title')}
<div style={{position:'absolute',top:920,height:1000,width:1080,background:ivory}}/>
{!cta&&<><div style={{position:'absolute',left:140,top:470,padding:'10px 20px',background:'#f5f1e8ef',borderRadius:10}}>{null}<span data-critical="candidate" style={{fontSize:64,fontWeight:800,color:blue}}>{overall?'교산 중앙 권역':active+' · 민간분양 계획'}</span></div>
{!overall&&<svg width={220} height={220} viewBox="0 0 1000 1000" style={{position:'absolute',left:620,top:650,background:'#f5f1e8ed',border:'3px solid white',borderRadius:12}}><image href={staticFile('map-locator.png')} width={1000} height={1000} preserveAspectRatio="none"/><rect x={v[0]} y={v[1]} width={v[2]} height={v[3]} fill="#367cda30" stroke={blue} strokeWidth={18}/></svg>}
{txt('facts',n<2?'새 철도 +\n상업·생활시설':n<5?'C2 · 전용 85㎡ 초과\n786호 계획':n<7?'B2 · 전용 60~85㎡\n281호 계획':'분양가·역 출입구\n공개 후 비교',140,930,52,ink,700)}
{overall&&<>{txt('c2-label','C2',328,805,62,blue,170)}{txt('b2-label','B2',738,660,62,'#8b5c15',170)}<svg width={1080} height={770} viewBox={view.join(' ')} preserveAspectRatio="xMidYMid slice" style={{position:'absolute',top:435,pointerEvents:'none'}}>{['C2','B2'].map(id=>{const q=(D.details as any)[id].block_point;return <circle key={id} cx={q[0]} cy={q[1]} r={4} fill={id==='C2'?blue:'#8b5c15'} stroke={ivory} strokeWidth={2}/>})}</svg></>}
</>}
{cta&&<><div style={{position:'absolute',top:435,width:1080,height:595,background:'#f5f1e8da'}}/>{txt('cta-candidates','C2 · B2',140,550,100,blue)}{txt('cta','지도·교통·분양가\n전체 비교는 본편에서',140,760,58)}</>}
{caption&&txt('caption',caption.text,140,1080,54,ink,700,'caption')}
{txt('source','국토교통부 고시 2026-535호 · 2026.10.08\nLH 공개 토지이용계획 재구성 · 조회 10.18\n계획 후보 · 분양가·역 출입구 추후 확인',140,1265,26,'#526575',700,'condition_source')}
</AbsoluteFill>};
registerRoot(()=> <Composition id="GyosanLeaderShortV1" component={Short} width={1080} height={1920} fps={30} durationInFrames={Math.ceil(D.duration*30)}/>);
