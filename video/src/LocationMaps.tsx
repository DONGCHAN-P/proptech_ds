import React from 'react';
import {AbsoluteFill,Composition,Sequence,Img,staticFile,useCurrentFrame,interpolate,registerRoot} from 'remotion';
import gwCore from '../public/detail-maps/gwanggyo-core.json';
import gwLife from '../public/detail-maps/gwanggyo-life.json';
import dtCore from '../public/detail-maps/dongtan-core.json';
import dtJobs from '../public/detail-maps/dongtan-jobs.json';
const maps=[gwCore,gwLife,dtCore,dtJobs];
function MapShot({index}:{index:number}){const f=useCurrentFrame(),m=maps[index],step=150/m.pins.length,active=Math.min(m.pins.length-1,Math.floor(Math.max(0,f-10)/step));const p=m.pins[active],local=Math.max(0,f-10-active*step),radius=interpolate(local,[0,22],[24,44],{extrapolateRight:'clamp'}),opacity=interpolate(local,[0,22],[.9,0],{extrapolateRight:'clamp'});return <AbsoluteFill><Img src={staticFile('detail-maps/'+m.id+'.png')} style={{width:1920,height:1080}}/><svg width="1920" height="1080" style={{position:'absolute'}}><circle cx={65+p.x} cy={240+p.y} r={radius} stroke={m.color} strokeWidth="5" fill="none" opacity={opacity}/><circle cx={65+p.x} cy={240+p.y} r="26" stroke={m.color} strokeWidth="3" fill="none"/></svg></AbsoluteFill>}
function Preview(){return <AbsoluteFill style={{background:'#F6F4EF'}}>{maps.map((m,i)=><Sequence key={m.id} from={i*180} durationInFrames={180}><MapShot index={i}/></Sequence>)}</AbsoluteFill>}
registerRoot(()=> <Composition id="LocationMaps" component={Preview} durationInFrames={720} fps={30} width={1920} height={1080}/>);
