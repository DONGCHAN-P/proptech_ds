import React from 'react';
import {registerRoot,Composition,Sequence,staticFile,useCurrentFrame} from 'remotion';
import {ClosingVisuals} from './ClosingVisuals';
import {ClosingOverview,ClosingSummary} from './ClosingSummary';
import {PersistentCaptions} from '../namyangju-landuse-v8/PersistentCaptions';
import P from './project_v14.json';
import shots from './closing_shots.json';
function Visual(){const f=useCurrentFrame(),s=shots.find(s=>f>=s.from_frame&&f<s.to_frame)!;return s.props.mode==='overview'?<ClosingOverview/>:s.props.mode==='summary'?<ClosingSummary/>:<ClosingVisuals {...s.props as any}/>}
const Movie=()=> <><style>{`@font-face{font-family:Pretendard;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')}')}@font-face{font-family:Pretendard;font-weight:700;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')}')}`}</style><div style={{fontFamily:'Pretendard'}}><Sequence from={-21636}><Visual/><PersistentCaptions project={P as any}/></Sequence></div></>;
registerRoot(()=> <Composition id="NewClosingV14" component={Movie} durationInFrames={5717} fps={30} width={1920} height={1080}/>);
