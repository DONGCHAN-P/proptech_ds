import React from 'react';
import {registerRoot,Composition,Sequence,staticFile} from 'remotion';
import {FocusVisuals} from './FocusVisuals';
import {PersistentCaptions} from '../namyangju-landuse-v8/PersistentCaptions';
import P from '../namyangju-landuse-v8/project_final.json';
const Movie=()=> <><style>{`@font-face{font-family:Pretendard;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')}')}@font-face{font-family:Pretendard;font-weight:700;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')}')}`}</style><div style={{fontFamily:'Pretendard'}}><Sequence from={-8190}><FocusVisuals/><PersistentCaptions project={P as any}/></Sequence></div></>;
registerRoot(()=> <Composition id="LanduseLocatorV14" component={Movie} durationInFrames={7568} fps={30} width={1920} height={1080}/>);
