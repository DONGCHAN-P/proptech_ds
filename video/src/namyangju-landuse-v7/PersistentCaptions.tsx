import React from 'react';
import {useCurrentFrame} from 'remotion';
import type {MapLedProject} from './types';
export function cueAt(project:MapLedProject,frame:number){const n=project.narration.find(n=>frame>=n.from_frame&&frame<n.from_frame+n.duration_frames);if(!n)return null;const f=frame-n.from_frame;return project.captions[n.scene_id]?.find(c=>f>=c.start_frame&&f<c.end_frame)||null}
export function PersistentCaptions({project,frame}:{project:MapLedProject;frame?:number}){const now=useCurrentFrame(),c=cueAt(project,frame??now);return <div data-persistent-caption="true" style={{position:'absolute',left:96,right:96,bottom:28,height:130,padding:'12px 35px',background:'#fff',borderRadius:13,fontSize:39,lineHeight:1.25,textAlign:'center',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',zIndex:99}}>{c?.lines.map((line,i)=><div key={i} style={{whiteSpace:'nowrap'}}>{line}</div>)}</div>}
