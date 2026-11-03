import React from 'react';import {Composition,registerRoot} from 'remotion';import {Board} from './Board';
registerRoot(()=><Composition id="GyosanReviewV2" component={Board} durationInFrames={60} fps={30} width={1920} height={1080} defaultProps={{mode:'plan'}}/>);
