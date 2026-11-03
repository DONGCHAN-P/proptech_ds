import React from 'react';
import {Audio,Sequence,staticFile} from 'remotion';
import type {MusicRegion} from './types';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const v=clamp(x);return v*v*(3-2*v)};
export function musicEnvelope(frame:number,r:MusicRegion){
 const attack=smooth(frame/Math.max(1,r.fade_in_frames)),release=smooth((r.duration_frames-1-frame)/Math.max(1,r.fade_out_frames));
 let voiceWeight=0;
 for(const [a,b] of r.voice_ranges){const before=smooth((frame-a+6)/12),after=smooth((b+12-frame)/18);voiceWeight=Math.max(voiceWeight,Math.min(before,after));}
 return (r.gain+(r.duck_gain-r.gain)*voiceWeight)*attack*release;
}
export function MusicBed({regions}:{regions:MusicRegion[]}){return <>{regions.map(r=><Sequence key={r.id} from={r.from_frame} durationInFrames={r.duration_frames} name={r.id}><Audio src={staticFile('namyangju-map-led-v6/data_city_ambient_v1.wav')} trimBefore={r.source_offset_frames} volume={f=>musicEnvelope(f,r)}/></Sequence>)}</>}
