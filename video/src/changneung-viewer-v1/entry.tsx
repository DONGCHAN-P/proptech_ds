import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {ViewerBoard,SupplyMotion} from './ViewerBoards';
registerRoot(()=><><Composition id="ViewerImprovementStill" component={ViewerBoard} defaultProps={{kind:'price',active:'all',stageFrame:40,caption:'가격표에서 먼저 읽을 것은 내 예산과 추가 부담입니다.'}} durationInFrames={180} fps={30} width={1920} height={1080}/><Composition id="SupplyImprovementMotion" component={SupplyMotion} durationInFrames={180} fps={30} width={1920} height={1080}/></>);
