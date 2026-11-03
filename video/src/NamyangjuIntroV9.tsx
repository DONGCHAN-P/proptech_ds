import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,registerRoot,staticFile} from 'remotion';
import raw from './namyangju-intro-v9/project.json';
import {IntroVisuals} from './namyangju-intro-v9/IntroVisuals';
import {BrandReuse} from './namyangju-landuse-v8/BrandReuse';
import {PersistentCaptions} from './namyangju-landuse-v8/PersistentCaptions';
import {MusicBed} from './namyangju-landuse-v8/MusicBed';
import type {MapLedProject} from './namyangju-landuse-v8/types';
const P=raw as unknown as MapLedProject;
function Movie(){return <AbsoluteFill style={{fontFamily:'Pretendard,sans-serif',color:'#173348'}}><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}*{box-sizing:border-box}`}</style><Sequence durationInFrames={917}><IntroVisuals/></Sequence><Sequence from={917} durationInFrames={150}><BrandReuse/></Sequence><Sequence from={45} durationInFrames={872}><Audio src={staticFile('namyangju-intro-v9/M000.mp3')} volume={.9}/></Sequence><MusicBed regions={P.music_regions}/><PersistentCaptions project={P}/></AbsoluteFill>}
registerRoot(()=> <Composition id="NamyangjuIntroV9" component={Movie} durationInFrames={1067} fps={30} width={1920} height={1080}/>);
