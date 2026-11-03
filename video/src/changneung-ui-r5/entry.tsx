import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {R5Board} from './R5Boards';
registerRoot(()=><Composition id="ChangneungUIR5" component={R5Board} defaultProps={{mode:'plan',focus:'S4',phase:'',motionFrame:44,caption:'기존 생활권과 학교 목표월을 함께 비교합니다.',baseProps:{}}} durationInFrames={120} fps={30} width={1920} height={1080}/>);
