import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import original from './namyangju-landuse-v8/project.json';
import raw from './namyangju-landuse-v8/project_final.json';
import {IntroVisuals} from './namyangju-intro-v9/IntroVisuals';
import {BrandReuse} from './namyangju-landuse-v8/BrandReuse';
import type {MapLedProject} from './namyangju-landuse-v8/types';
import {RearVisuals} from './namyangju-landuse-v8/RearVisuals';
import {FrontVisuals} from './namyangju-landuse-v8/FrontVisuals';
import {PersistentCaptions} from './namyangju-landuse-v8/PersistentCaptions';
import {MusicBed} from './namyangju-landuse-v8/MusicBed';
const P=raw as unknown as MapLedProject,Original=original as unknown as MapLedProject;
function BodyVisuals(){const f=useCurrentFrame();return f<13087?<FrontVisuals project={Original}/>:<RearVisuals project={Original}/>}
function Movie(){return <AbsoluteFill style={{fontFamily:'Pretendard,sans-serif',color:'#173348'}}><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}*{box-sizing:border-box}`}</style><Sequence durationInFrames={917}><IntroVisuals/></Sequence><Sequence from={917} durationInFrames={150}><BrandReuse/></Sequence><Sequence from={1067} durationInFrames={25353}><Sequence from={-669}><BodyVisuals/></Sequence></Sequence><Sequence from={26420} durationInFrames={300}><BrandReuse outro/></Sequence><PersistentCaptions project={P}/>{P.narration.map(n=><Sequence key={n.scene_id} from={n.from_frame} durationInFrames={n.duration_frames}><Audio src={staticFile(n.file)} volume={.9}/></Sequence>)}<MusicBed regions={P.music_regions}/></AbsoluteFill>}
function Root(){return <Composition id="NamyangjuLanduseFullV8" component={Movie} durationInFrames={26720} fps={30} width={1920} height={1080}/>}
registerRoot(Root);
