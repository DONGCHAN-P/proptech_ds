import React from 'react';
import {AbsoluteFill,Composition,registerRoot,staticFile} from 'remotion';
import {ScreenSurface} from './ScreenSurface';
import type {TrackKey} from './homography';
const track:TrackKey[]=[{time:0,quad:[[350,210],[1500,150],[1440,825],[410,785]]}];
const Calibration=()=> <AbsoluteFill style={{background:'#b9b5ad'}}>
 <svg width={1920} height={1080}>
  <defs><linearGradient id="desk" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#b8b6b0"/><stop offset="1" stopColor="#867e72"/></linearGradient></defs>
  <path d="M0 680 L1920 600 L1920 1080 L0 1080Z" fill="url(#desk)"/>
  <polygon points="326,186 1525,125 1465,853 389,813" fill="#1b1d22" stroke="#111" strokeWidth={9}/>
  <path d="M865 826 L1000 826 L1010 920 L840 920Z" fill="#35373b"/>
  <path d="M760 924 L1100 924 L1160 948 L710 948Z" fill="#25262b"/>
  <polygon points="450,960 1300,948 1410,1045 410,1060" fill="#37383c"/>
  {Array.from({length:5},(_,i)=><path key={i} d={`M${450-i*6} ${975+i*16} L${1315+i*18} ${963+i*18}`} stroke="#727478" strokeWidth={3}/>)}
 </svg>
 <ScreenSurface src={staticFile('data-insight-v2/A03.jpg')} track={track} width={1600} height={1000} diagnostic/>
 <div style={{position:'absolute',left:35,bottom:25,color:'white',background:'#111b',fontSize:22,padding:12}}>TECHNICAL CALIBRATION ONLY · synthetic device plate · not final footage</div>
 </AbsoluteFill>;
registerRoot(()=> <Composition id="ScreenReplaceCalibration" component={Calibration} width={1920} height={1080} fps={30} durationInFrames={30}/>);
