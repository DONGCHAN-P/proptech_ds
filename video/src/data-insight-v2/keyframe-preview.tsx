import React from 'react';
import {AbsoluteFill,Composition,Img,registerRoot,staticFile} from 'remotion';
import {ScreenSurface} from './ScreenSurface';
import D from './data.json';
import type {TrackKey} from './homography';
const sf=(name:string)=>staticFile('data-insight-v2/'+name);
const Preview=({shot,id}:{shot:string;id:string})=> <AbsoluteFill>
 <Img src={sf(shot+'_reference.jpg')} style={{width:1920,height:1080}}/>
 <ScreenSurface src={sf((D.assets as any)[id])} track={(D.tracks as any)[shot] as TrackKey[]}
 width={shot==='phone'?430:1600} height={shot==='phone'?932:shot==='monitor'?900:1000}
 phone={shot==='phone'} matte={id==='A03'?'#170d29':'white'} diagnostic/>
 </AbsoluteFill>;
registerRoot(()=> <>
 <Composition id="MonitorKeyframe" component={Preview} defaultProps={{shot:'monitor',id:'A01'}} width={1920} height={1080} fps={30} durationInFrames={30}/>
 <Composition id="LaptopKeyframe" component={Preview} defaultProps={{shot:'laptop',id:'A03'}} width={1920} height={1080} fps={30} durationInFrames={30}/>
 </>);
