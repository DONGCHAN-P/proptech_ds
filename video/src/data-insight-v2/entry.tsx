import React from 'react';
import {AbsoluteFill,Audio,Composition,Img,OffthreadVideo,Sequence,interpolate,registerRoot,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {ScreenSurface} from './ScreenSurface';
import D from './data.json';
import T from './tracking.json';
import type {TrackKey} from './homography';
const sf=(name:string)=>staticFile('data-insight-v2/'+name);
const shotStarts:Record<string,number>={'V2-S1':0,'V2-S2':1.5,'V2-S3a':.7,'V2-S3b':.3,'V2-S3c':1.2,'V2-S3d':1.5,'V2-S4':0,'V2-S5':.4,'V2-S6':1};
const reframes:Record<string,number>={'V2-S1':1,'V2-S2':1.07,'V2-S3a':1.14,'V2-S3b':1,'V2-S3c':1.09,'V2-S3d':1.12,'V2-S4':1,'V2-S5':1.03,'V2-S6':1};
const DeviceScene=({s}:{s:any})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),start=shotStarts[s.scene_id];
 let id=s.asset_ids[0],file='';
 if(s.scene_id==='V2-S2'&&f>=60)id='A13';
 if(s.scene_id==='V2-S3b'&&f>=45)id='A09';
 if(s.scene_id==='V2-S3c'&&f>=69)id='A12';
 if(s.scene_id==='V2-S5'&&f>=45)id='A08';
 file=(D.assets as any)[id];
 if(id==='A05')file=`A05_${Math.min(6,Math.floor(f/69*7))}.png`;
 if(s.shot==='phone')file=f<75?'A01_mobile_spike.png':'A01_mobile_drop.png';
 if(s.scene_id==='V2-S3d'&&f>=45)file='A10_dashboard_crop.png';
 const enter=interpolate(f,[0,10],[0,1],{extrapolateRight:'clamp'}),accent=s.color==='rose'?'#ea7ba4':s.color==='gray'?'#d3ced7':'#d7c1ff';
 return <AbsoluteFill>
  <AbsoluteFill style={{transform:`scale(${reframes[s.scene_id]})`,transformOrigin:s.shot==='laptop'?'66% 58%':s.shot==='monitor'?'66% 48%':'60% 50%',filter:s.color==='gray'?'grayscale(1)':undefined}}>
   <OffthreadVideo src={sf(s.shot+'.mp4')} trimBefore={Math.round(start*fps)} muted style={{width:1920,height:1080,objectFit:'cover'}}/>
   <ScreenSurface src={sf(file)} track={(T as any)[s.shot] as TrackKey[]} sourceStart={start}
    width={s.shot==='phone'?430:1600} height={s.shot==='phone'?932:s.shot==='monitor'?900:1000}
    phone={s.shot==='phone'} matte={id==='A03'||id==='A09'?'#170d29':'white'} reflection={.055}/>
  </AbsoluteFill>
  <AbsoluteFill style={{pointerEvents:'none',background:'linear-gradient(180deg,rgba(22,10,34,.67),transparent 27%,transparent 80%,rgba(22,10,34,.77))'}}/>
  <div style={{position:'absolute',left:70,top:44,color:'white',fontSize:25,fontWeight:700,letterSpacing:4}}>DATA INSIGHT</div>
  <div style={{position:'absolute',right:70,top:44,color:'white',fontSize:21,background:'#241332a8',padding:'8px 14px',borderRadius:6}}>AI 재현 · 화면 합성</div>
  <div style={{position:'absolute',left:70,top:112,color:'white',fontSize:s.title.length>23?49:57,fontWeight:700,lineHeight:1.17,letterSpacing:-1.3,opacity:enter,transform:`translateY(${(1-enter)*10}px)`}}><span style={{display:'inline-block',width:6,height:53,background:accent,marginRight:20,verticalAlign:'middle'}}/>{s.title}</div>
  {s.scene_id==='V2-S3c'&&<div style={{position:'absolute',left:76,top:202,color:'white',fontSize:23}}>입력·요건서 정리 과정 · 빠르게 재생</div>}
  {s.scene_id==='V2-S3d'&&f>=45&&<div style={{position:'absolute',left:76,top:202,color:'white',fontSize:23}}>원본 자료의 대시보드 예시</div>}
  {s.scene_id==='V2-S4'&&<><div style={{position:'absolute',left:76,top:208,color:accent,fontSize:30,fontWeight:700}}>매시 10분 · 야간·주말 이상 알림</div><div style={{position:'absolute',left:76,bottom:48,color:'white',fontSize:20}}>제공 화면 기반 모바일 재구성</div></>}
  {s.scene_id==='V2-S5'&&<><div style={{position:'absolute',left:76,top:208,color:accent,fontSize:30,fontWeight:700}}>Weekly 7회　/　2~3시간 → 5분</div><div style={{position:'absolute',left:76,bottom:48,color:'white',fontSize:20}}>수치: 사용자 제공 구성안</div></>}
  <div style={{position:'absolute',left:70,right:70,bottom:82,height:85,display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:36,fontWeight:700,background:'#1c0d30a8',borderRadius:5}}>{s.caption}</div>
 </AbsoluteFill>;
};
const Film=()=>{const {fps}=useVideoConfig();return <AbsoluteFill style={{fontFamily:'DeviceInsight'}}>
 <style>{`@font-face{font-family:DeviceInsight;src:url('${sf('regular.woff2')}');font-weight:400}@font-face{font-family:DeviceInsight;src:url('${sf('bold.woff2')}');font-weight:700}`}</style>
 <Audio src={sf('bgm.wav')}/>
 {D.scenes.map(s=><Sequence key={s.scene_id} from={s.start*fps} durationInFrames={(s.end-s.start)*fps} premountFor={fps}><DeviceScene s={s}/></Sequence>)}
 </AbsoluteFill>};
registerRoot(()=> <Composition id="DataInsightV2" component={Film} width={1920} height={1080} fps={30} durationInFrames={900}/>);
