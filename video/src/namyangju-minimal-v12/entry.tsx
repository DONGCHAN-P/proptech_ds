import React from 'react';
import {AbsoluteFill,Audio,Composition,OffthreadVideo,Sequence,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import P from '../namyangju-landuse-v8/project_final.json';
import O from '../namyangju-landuse-v8/project.json';
import type {MapLedProject} from '../namyangju-landuse-v8/types';
import {PersistentCaptions} from '../namyangju-landuse-v8/PersistentCaptions';
import {FocusVisuals} from './FocusVisuals';
import {FrontVisuals} from './FrontVisuals';
function Movie(){const f=useCurrentFrame();return <AbsoluteFill style={{fontFamily:'Pretendard,sans-serif'}}><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}*{box-sizing:border-box}`}</style>{f>=4950?<><FocusVisuals/><PersistentCaptions project={P as unknown as MapLedProject}/></>:f>=1898&&f<2678?<><Sequence from={398}><FrontVisuals project={O as unknown as MapLedProject}/></Sequence><PersistentCaptions project={P as unknown as MapLedProject}/></>:<OffthreadVideo muted src={staticFile('namyangju-minimal-v12/base_v10.mp4')}/>}<Audio src={staticFile('namyangju-minimal-v12/base_v10.mp4')}/></AbsoluteFill>}
registerRoot(()=> <Composition id="MinimalV12Front" component={Movie} durationInFrames={15750} fps={30} width={1920} height={1080}/>);
