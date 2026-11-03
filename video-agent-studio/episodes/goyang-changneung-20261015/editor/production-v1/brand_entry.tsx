import React from 'react';
import {Composition,registerRoot,staticFile} from 'remotion';
import {BrandReuse} from './BrandGeneric';
function Brand({outro=false}:{outro?:boolean}) {return <><style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}`}</style><BrandReuse outro={outro}/></>}
registerRoot(()=><><Composition id="GenericBrandIntro" component={Brand} durationInFrames={150} fps={30} width={1920} height={1080}/><Composition id="GenericBrandOutro" component={Brand} defaultProps={{outro:true}} durationInFrames={300} fps={30} width={1920} height={1080}/></>);
