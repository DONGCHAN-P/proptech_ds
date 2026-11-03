import React from 'react';
import {LanduseBoard} from './LanduseBoard';
import {south} from '../namyangju-landuse-v8/FrontVisuals';
export function WangsukInset(){return <div style={{position:'absolute',left:25,top:15,width:526,height:376,border:'2px solid #3971b7',borderRadius:12,background:'#fffef9',padding:12}}><div style={{fontSize:21,fontWeight:700,color:'#285b95',marginBottom:5}}>왕숙1 남측 · 주거·철도·산업 계획 배치</div><LanduseBoard board={south} camera={[100,250,1380,1030]} width={498} height={298} labelIds={['w1_a24','w1_b17','w1_rail']} labelOverrides={{w1_a24:'A24',w1_b17:'B17',w1_rail:'철도계획시설'}} fontSize={17} labelOffsets={{w1_a24:[-25,-10],w1_b17:[25,-10]}}/><div style={{fontSize:15,color:'#557084',marginTop:6}}>왕숙역: 경춘선 퇴계원~사릉 사이 신설 계획 · 역 중심 미확정</div></div>}
