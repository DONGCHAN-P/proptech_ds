import React from 'react';
import {AbsoluteFill,Composition,OffthreadVideo,registerRoot,staticFile} from 'remotion';
import {ScreenSurface} from './ScreenSurface';
import T from './tracking.json';
import type {TrackKey} from './homography';
const sf=(n:string)=>staticFile('data-insight-v2/'+n);
const Proof=({shot}:{shot:string})=><AbsoluteFill>
 <OffthreadVideo src={sf(shot+'.mp4')} muted style={{width:1920,height:1080}}/>
 <ScreenSurface src={sf(shot==='phone'?'A01_mobile_spike.png':shot==='monitor'?'A01.png':'A03.jpg')}
 track={(T as any)[shot] as TrackKey[]} width={shot==='phone'?430:1600} height={shot==='phone'?932:shot==='monitor'?900:1000}
 phone={shot==='phone'} matte={shot==='laptop'?'#170d29':'white'}/>
 </AbsoluteFill>;
registerRoot(()=> <>{['monitor','laptop','phone'].map(shot=><Composition key={shot} id={'Proof-'+shot} component={Proof} defaultProps={{shot}} width={1920} height={1080} fps={30} durationInFrames={150}/>)}</>);
