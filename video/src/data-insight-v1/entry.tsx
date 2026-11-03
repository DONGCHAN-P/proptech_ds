import React from 'react';
import {AbsoluteFill,Audio,Composition,Img,OffthreadVideo,Sequence,interpolate,registerRoot,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import D from './data.json';
const base='data-insight-v1/';
const purple='#5125a8',rose='#d83d78',ink='#24183b';
const sf=(s:string)=>staticFile(base+s);
const Panel=({id,style={}}:{id:string;style?:React.CSSProperties})=>{
 const f=useCurrentFrame();let file=(D.assets as any)[id];
 if(id==='A05'){const ds=D.gif_durations;let t=f/90*ds.reduce((a,b)=>a+b,0),i=0;while(t>=ds[i]&&i<ds.length-1){t-=ds[i];i++;}file=`A05_${i}.png`;}
 return <div style={{background:'white',borderRadius:18,overflow:'hidden',boxShadow:'0 18px 50px #2b145322',border:'1px solid #e7e1ef',...style}}><Img src={sf(file)} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div>;
};
const Hero=({s}:{s:any})=>{const {fps}=useVideoConfig();const start=Math.round(.5*fps);return <AbsoluteFill>
 <OffthreadVideo src={sf(s.video)} trimBefore={start} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>
 {s.scene_id==='S1'&&<div style={{position:'absolute',left:0,top:0,width:'43%',height:'100%',overflow:'hidden'}}><OffthreadVideo src={sf(s.video)} trimBefore={start} muted style={{width:1920,height:1080,objectFit:'cover',filter:'grayscale(1) brightness(.65)'}}/></div>}
 <AbsoluteFill style={{background:'linear-gradient(90deg,rgba(20,8,38,.83),rgba(23,11,43,.13) 56%,rgba(23,11,43,.48))'}}/>
 <div style={{position:'absolute',left:80,top:53,color:'white',fontSize:25,letterSpacing:4,fontWeight:700}}>DATA INSIGHT</div>
 <div style={{position:'absolute',right:76,top:53,color:'white',background:'#21103588',padding:'7px 16px',borderRadius:8,fontSize:21}}>AI 재현</div>
 <div style={{position:'absolute',left:80,top:200,width:1050,color:'white',fontSize:s.scene_id==='S5'?60:72,fontWeight:700,lineHeight:1.2,letterSpacing:-2}}>{s.title}</div>
 <div style={{position:'absolute',left:84,top:375,width:900,color:'#e4cfff',fontSize:31,fontWeight:700}}>{s.scene_id==='S1'?'월요일 Before/After':s.message}</div>
 {s.scene_id==='S5'&&<div style={{position:'absolute',left:84,top:470,color:'white',fontSize:83,fontWeight:700}}>30명 · 7개 본부<div style={{fontSize:38,color:'#efb8d3',marginTop:25}}>2~3시간 → 5분</div></div>}
 <div style={{position:'absolute',right:75,top:s.scene_id==='S5'?470:390,width:570,display:'grid',gridTemplateColumns:'1fr 1fr',gap:15}}>{s.assets.map((id:string,i:number)=><div key={id} style={{height:s.assets.length>3?165:200,gridColumn:s.assets.length===3&&i===0?'span 2':undefined}}><Panel id={id} style={{width:'100%',height:'100%',borderRadius:11,boxShadow:'0 10px 35px #0005'}}/></div>)}</div>
 </AbsoluteFill>};
const Scene=({s}:{s:any})=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig();const dur=(s.end-s.start)*fps;const enter=interpolate(f,[0,12],[0,1],{extrapolateRight:'clamp'});const color=s.color==='gray'?'#85828c':s.color==='rose'?rose:purple;
 const hero=!!s.video,ending=s.scene_id==='S6';
 const ids=s.assets as string[];
 return <AbsoluteFill style={{background:ending?ink:'#f7f5fb',color:ending?'white':ink}}>
 <div style={{position:'absolute',width:1000,height:1000,borderRadius:'50%',right:-350,top:-600,background:`radial-gradient(circle,${color}22,transparent 68%)`}}/>
 <div style={{position:'absolute',left:70,top:40,fontSize:25,fontWeight:700,letterSpacing:4,color:ending?'#d5b8ff':purple}}>DATA INSIGHT</div>
 <div style={{position:'absolute',right:70,top:42,fontSize:22,color:ending?'#c1b4d5':'#8b8299'}}>2026 → 2027</div>
 <div style={{position:'absolute',left:70,top:105,width:1780,display:'flex',alignItems:'center',gap:24,opacity:enter,transform:`translateY(${(1-enter)*16}px)`}}><div style={{width:7,height:66,borderRadius:9,background:ending?rose:color}}/><div style={{fontSize:s.title.length>19?54:62,fontWeight:700,lineHeight:1.15,letterSpacing:-2}}>{s.title}</div></div>
 {!hero&&!ending&&<>
 <div style={{position:'absolute',left:74,top:216,color,fontSize:26,fontWeight:700}}>{s.message}</div>
 {s.scene_id==='S3a'&&<div style={{position:'absolute',right:75,top:219,fontSize:21,color:'#82798d'}}>시그널룸 알림 예시 / 프로모션 브리핑 예시</div>}
 {s.scene_id==='S3c'&&<div style={{position:'absolute',right:75,top:219,fontSize:23,color:'#82798d'}}>입력·요건서 정리 과정 · 빠르게 재생</div>}
 {s.scene_id==='S2'?<><Panel id="A04" style={{position:'absolute',left:70,top:280,width:720,height:610,filter:'grayscale(1)',opacity:.75}}/><div style={{position:'absolute',left:875,top:330,width:890}}>{['이슈 인지','요청 부서 찾기','검토·재질문'].map((x,i)=><div key={x} style={{fontSize:40,padding:'24px 30px',marginBottom:25,borderRadius:15,background:'#e8e6ec',opacity:interpolate(f,[i*14,i*14+10],[.2,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}>{String(i+1).padStart(2,'0')}　{x}{i<2?'　↓':''}</div>)}</div></>:
 <div style={{position:'absolute',left:70,top:275,width:1780,height:615,display:'flex',gap:30}}>{ids.map((id,i)=><Panel key={id} id={id} style={{height:'100%',width:ids.length===1?'100%':i===0?'62%':'38%'}}/>)}</div>}
 </>}
 {ending&&<><div style={{position:'absolute',left:82,top:290,width:820,fontSize:65,fontWeight:700,lineHeight:1.35}}>보안·정합성을<br/>걱정하지 않는 환경</div><Panel id="A06" style={{position:'absolute',left:970,top:265,width:880,height:520}}/><div style={{position:'absolute',left:84,top:650,width:770,height:4,background:'linear-gradient(90deg,#df548a,#8350d8)'}}/></>}
 {hero&&<Hero s={s}/>}
 <div style={{position:'absolute',left:70,right:70,bottom:83,height:95,background:hero?'#1d0d30b8':ending?'#ffffff0d':'white',borderRadius:hero?5:18,display:'flex',alignItems:'center',justifyContent:'center',fontSize:36,fontWeight:700,color:ending||hero?'white':ink,boxShadow:'0 4px 20px #24183b08'}}>{s.caption}</div>
 <div style={{position:'absolute',left:75,bottom:35,fontSize:18,color:ending||hero?'#d0c1e0':'#8e859a'}}>제공 자료 기반 · UI 원본 사용{s.scene_id==='S5'?' · 수치: 사용자 제공 구성안':''}</div>
 <div style={{position:'absolute',right:74,bottom:35,fontSize:18,color:ending?'#bfb1d0':'#8e859a'}}>{s.scene_id} / 30s</div>
 </AbsoluteFill>
};
const Film=()=>{const {fps}=useVideoConfig();return <AbsoluteFill style={{fontFamily:'Insight'}}><style>{`@font-face{font-family:Insight;src:url('${sf('regular.woff2')}');font-weight:400}@font-face{font-family:Insight;src:url('${sf('bold.woff2')}');font-weight:700}`}</style><Audio src={sf('bgm.wav')}/>{D.scenes.map(s=><Sequence key={s.scene_id} from={s.start*fps} durationInFrames={(s.end-s.start)*fps} premountFor={fps}><Scene s={s}/></Sequence>)}<div style={{position:'absolute',bottom:0,left:0,height:6,width:`${useCurrentFrame()/899*100}%`,background:'linear-gradient(90deg,#d83d78,#5125a8)'}}/></AbsoluteFill>};
registerRoot(()=> <Composition id="DataInsightV1" component={Film} width={1920} height={1080} fps={30} durationInFrames={900}/>);
