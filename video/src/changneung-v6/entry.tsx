import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Board} from './Boards';
registerRoot(()=><Composition id="ChangneungV6Frame" component={Board} defaultProps={{board:'commute',focus:'all',caption:'현재 교통으로 실제 목적지까지의 길을 비교합니다.',motionFrame:40}} durationInFrames={120} fps={30} width={1920} height={1080}/>);
