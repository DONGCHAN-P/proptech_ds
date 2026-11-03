import React from 'react';
import {Composition,Sequence,registerRoot,staticFile} from 'remotion';
import P from '../namyangju-landuse-v8/project_final.json';
import type {MapLedProject} from '../namyangju-landuse-v8/types';
import {PersistentCaptions} from '../namyangju-landuse-v8/PersistentCaptions';
import {DualPriceMap} from './DualPriceMap';
function Clip(){return <div style={{fontFamily:'Pretendard,sans-serif'}}><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}`}</style><DualPriceMap/><Sequence from={-15758}><PersistentCaptions project={P as unknown as MapLedProject}/></Sequence></div>}
registerRoot(()=> <Composition id="DualPriceMapV14" component={Clip} durationInFrames={2890} fps={30} width={1920} height={1080}/>);
