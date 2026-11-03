import React from 'react';
import {AbsoluteFill} from 'remotion';
import w2 from '../../public/namyangju-landuse-v7/w2_board.json';
import raw from './project.json';
import type {MapLedProject} from './types';
import {LanduseBoard,LanduseLegend,Board} from './LanduseBoard';
import {PersistentCaptions} from './PersistentCaptions';
export function BoardAudit(){const board=w2 as unknown as Board;return <AbsoluteFill style={{background:'#f6f4ef',color:'#173348',fontFamily:'Pretendard,sans-serif'}}><div style={{position:'absolute',left:80,top:35,fontSize:23}}>｜ 데이터로 보는 부동산</div><div style={{position:'absolute',left:80,top:100,fontSize:47,fontWeight:700}}>왕숙2 · A1과 A3 사이의 학교와 공원</div><div style={{position:'absolute',left:80,top:190}}><LanduseBoard board={board} camera={board.cameras.a1_a3_school} highlight={['a1','a3','school_e','school_m','park_w']} labelIds={['a1','a3','school_e','school_m','park_w','c1','c2','commerce1','public_w']}/></div><div style={{position:'absolute',left:1550,top:240,width:300,fontSize:27,lineHeight:1.6,wordBreak:'keep-all'}}><b>A1 동쪽</b><div>초등학교·중학교<br/>유치원 계획</div><div style={{marginTop:35}}><b>A3 서쪽</b><div>공원과 학교 배치</div></div><div style={{fontSize:22,color:'#67746e',marginTop:40}}>같은 보드에서 생활시설과 입주 시점을 함께 봅니다.</div></div><div style={{position:'absolute',left:85,top:850}}><LanduseLegend/></div><div style={{position:'absolute',left:80,right:80,top:885,fontSize:18,color:'#6b7477'}}>LH A3 공고 팸플릿 p5의 계획 배치를 자체 도해 · 원도면 내부 상대좌표 기준 / 측량·지적 경계 아님</div><PersistentCaptions project={raw as unknown as MapLedProject} frame={10790}/></AbsoluteFill>}
