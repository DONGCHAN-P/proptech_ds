import React from 'react';
import {Img, useCurrentFrame, useVideoConfig} from 'remotion';
import {cssMatrix, homography, trackedQuad} from './homography';
import type {TrackKey} from './homography';

// The source video and this layer must share the same 1920x1080 coordinate space.
// Track the INNER display boundary, keeping physical bezel and fingers in the shot.
export const ScreenSurface = ({src, track, sourceStart=0, width=1600, height=1000,
  fit='contain', reflection=.05, diagnostic=false, phone=false, matte='#fff'}: {
  src:string; track:TrackKey[]; sourceStart?:number; width?:number; height?:number;
  fit?:'contain'|'cover'; reflection?:number; diagnostic?:boolean; phone?:boolean; matte?:string;
}) => {
  const frame=useCurrentFrame(),{fps}=useVideoConfig();
  const quad=trackedQuad(track,sourceStart+frame/fps);
  const transform=cssMatrix(homography(width,height,quad));
  return <>
    <div style={{position:'absolute',left:0,top:0,width,height,transformOrigin:'0 0',transform,
      overflow:'hidden',background:matte,backfaceVisibility:'hidden',
      clipPath:phone?'path("M44 0 H110 Q110 42 132 42 H298 Q320 42 320 0 H386 Q430 0 430 44 V888 Q430 932 386 932 H44 Q0 932 0 888 V44 Q0 0 44 0 Z")':undefined}}>
      <Img src={src} style={{width:'100%',height:'100%',objectFit:fit,display:'block'}}/>
      <div style={{position:'absolute',inset:0,pointerEvents:'none',
        background:`linear-gradient(128deg,rgba(230,240,255,${reflection}),transparent 48%,rgba(0,0,0,.06))`}}/>
    </div>
    {diagnostic&&<svg width={1920} height={1080} style={{position:'absolute',inset:0,pointerEvents:'none'}}>
      <polygon points={quad.map(p=>p.join(',')).join(' ')} fill="none" stroke="#00e5ff" strokeWidth={2}/>
      {quad.map(([x,y],i)=><g key={i}><circle cx={x} cy={y} r={5} fill="#ff276d"/><text x={x+9} y={y-9} fill="#ff276d" fontSize={18}>{i}</text></g>)}
    </svg>}
  </>;
};
