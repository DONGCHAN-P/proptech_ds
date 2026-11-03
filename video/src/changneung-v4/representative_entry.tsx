import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {PlanFrame} from './PlanFrame';
registerRoot(()=><Composition id="ChangneungPlanV4" component={PlanFrame} defaultProps={{focus:'S-5',overview:false,caption:''}} durationInFrames={1} fps={30} width={1920} height={1080}/>);
