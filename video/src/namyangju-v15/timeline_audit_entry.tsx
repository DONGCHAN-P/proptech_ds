import React from 'react';
import {eventsFor} from './FocusVisuals';
import {closingDateCases} from './ClosingVisuals';
import {registerRoot,Composition,useCurrentFrame,delayRender,continueRender,staticFile} from 'remotion';
import {DateTimeline,DateEvent} from './DateTimeline';
import {jobsDates,railDates,changneungDates,gyosanDates} from './TimelineEvents';
const cases:DateEvent[][]=[jobsDates,railDates,changneungDates,gyosanDates,eventsFor(10370,'north'),eventsFor(12050,'south'),eventsFor(12400,'w2'),eventsFor(12700,'w2'),...closingDateCases];
function Audit(){const f=useCurrentFrame(),[h]=React.useState(()=>delayRender('timeline font bbox'));React.useEffect(()=>{document.fonts.ready.then(()=>{const nodes=[...document.querySelectorAll('svg text')] as SVGTextElement[];const boxes=nodes.map(el=>{const b=el.getBBox(),stroke=Number(el.getAttribute('stroke-width')||0)/2;return {text:el.textContent,x:b.x-stroke,y:b.y-stroke,width:b.width+stroke*2,height:b.height+stroke*2}});const outside=boxes.filter(b=>b.x<0||b.y<0||b.x+b.width>1740||b.y+b.height>95);console.log('TIMELINE_BBOX '+JSON.stringify({case:f,boxes,outside}));continueRender(h)})},[f]);return <div style={{fontFamily:'Pretendard'}}><style>{`@font-face{font-family:Pretendard;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')}')}@font-face{font-family:Pretendard;font-weight:700;src:url('${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')}')}`}</style><DateTimeline events={cases[f]}/></div>}
registerRoot(()=> <Composition id="TimelineAuditV15" component={Audit} durationInFrames={12} fps={30} width={1920} height={1080}/>);
