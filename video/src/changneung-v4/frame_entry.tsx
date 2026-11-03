import React from 'react';
import {Composition,registerRoot,useCurrentFrame} from 'remotion';
import {ProductionFrame} from './ProductionScenes';
function CTA({cues=[],holdFrom=210}:{cues?:any[];holdFrom?:number;durationFrames?:number}){const f=useCurrentFrame(),c=cues.find(x=>f>=x.start_frame&&f<x.end_frame);return <ProductionFrame shot={{kind:'cta',title:'CTA'}} caption={c?.text||''} hideCaption={f>=holdFrom} motionFrame={f}/>}
registerRoot(()=><><Composition id="ChangneungFrameV4" component={ProductionFrame} defaultProps={{shot:{kind:'official',title:'창릉 전체 계획',focus:'overview'},caption:'',hideCaption:false}} durationInFrames={1} fps={30} width={1920} height={1080}/><Composition id="ChangneungCtaV4" component={CTA} defaultProps={{cues:[],holdFrom:210,durationFrames:300}} calculateMetadata={({props})=>({durationInFrames:props.durationFrames})} durationInFrames={300} fps={30} width={1920} height={1080}/></>);
