import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {ProductionFrame} from '../changneung-v5/ProductionScenes';
import D from '../changneung-v5/data.json';
const c:any=(D as any).cues.find((x:any)=>x.cue_id==='M005_C10');
registerRoot(()=><Composition id="ChangneungV6Detail" component={ProductionFrame} defaultProps={{cueId:c.cue_id,globalFrame:c.end_frame-1,motionFrame:40,caption:'S4는 입주 예정월과 같은 2030년 3월이 초등학교 개교 목표입니다.'}} durationInFrames={120} fps={30} width={1920} height={1080}/>);
