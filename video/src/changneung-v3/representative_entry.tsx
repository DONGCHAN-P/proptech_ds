import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {TransportRep,PriceRep,LifeRep} from './Representative';
registerRoot(()=><><Composition id="ChangneungTransportRepV3" component={TransportRep} durationInFrames={300} fps={30} width={1920} height={1080}/><Composition id="ChangneungPriceRepV3" component={PriceRep} durationInFrames={300} fps={30} width={1920} height={1080}/><Composition id="ChangneungLifeRepV3" component={LifeRep} durationInFrames={300} fps={30} width={1920} height={1080}/></>);
