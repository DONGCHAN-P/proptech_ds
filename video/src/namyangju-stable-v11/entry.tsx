import React from 'react';
import {Composition,registerRoot,staticFile} from 'remotion';
import {NativePlate,RailPlate} from './StaticPlates';
function Plate({kind}:{kind:string}){return <div style={{fontFamily:'Pretendard,sans-serif'}}><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}*{box-sizing:border-box}`}</style>{kind==='rail'?<RailPlate/>:<NativePlate kind={kind}/>}</div>}
registerRoot(()=> <Composition id="StablePlateV11" component={Plate} defaultProps={{kind:'rail'}} durationInFrames={300} fps={30} width={1920} height={1080}/>);
