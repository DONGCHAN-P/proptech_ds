import React from 'react';
import {registerRoot,Composition,Sequence,staticFile,useCurrentFrame} from 'remotion';
import {JobsTimeline} from './JobsTimeline';
import {FocusVisuals} from './FocusVisuals';
import {OutsideLocator} from './OutsideTimeline';
import {PriceComparison} from './OutsidePrice';
import {PersistentCaptions} from '../namyangju-landuse-v8/PersistentCaptions';
import P from '../namyangju-landuse-v8/project_final.json';
function Outside(){const f=useCurrentFrame(),s=P.scenes.find(x=>f>=x.from_frame&&f<x.from_frame+x.duration_frames)!;return s.kind==='outside_price_comparison'?<Sequence from={s.from_frame}><PriceComparison project={P as any} scene={s as any}/></Sequence>:<Sequence from={s.from_frame}><OutsideLocator project={P as any} scene={s as any}/></Sequence>}
function Clip({start,kind}:{start:number;kind:string}){return <><style>{`@font-face{font-family:Pretendard;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')}')}@font-face{font-family:Pretendard;font-weight:700;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')}')}`}</style><div style={{fontFamily:'Pretendard'}}><Sequence from={-start}>{kind==='jobs'?<JobsTimeline/>:kind==='rail'?<FocusVisuals/>:<Outside/>}<PersistentCaptions project={P as any}/></Sequence></div></>}
registerRoot(()=> <>{[{id:'JobsDatesV14',start:2407,end:4942,kind:'jobs'},{id:'RailDatesV14',start:4942,end:8190,kind:'rail'},{id:'OutsideDatesV14',start:18648,end:21636,kind:'outside'}].map(x=><Composition key={x.id} id={x.id} component={Clip} defaultProps={{start:x.start,kind:x.kind}} durationInFrames={x.end-x.start} fps={30} width={1920} height={1080}/>)}</>);
