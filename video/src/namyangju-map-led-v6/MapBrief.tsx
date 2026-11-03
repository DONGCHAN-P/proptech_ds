import React from 'react';
const copy:Record<string,string[]>={
jobs:['일터와 주거의 거리','산업단지 계획 승인: 2026.10','기업시설 준공목표: 2029','산업단지는 2032까지 단계적 조성'],
transport:['환승과 입주 첫해','운영 철도와 예정 철도를 구분','GTX-B는 2031 개통 목표','역까지의 첫 이동은 따로 확인'],
life:['학교와 생활의 시작','입주예정과 개교목표를 대조','상업·공원도 완성 시점이 중요','입주 첫해의 공백을 확인'],
supply:['권역별 입주 달력','6개 블록의 계획물량 3,815세대','이 가운데 공공분양 3,409세대','2028~2030 순차 입주예정'],
price:['가격과 상품의 조건','면적·유형·공고 시점을 구분','확장비·옵션은 별도 확인','분양가 차이만으로 우열 판단 금지'],
candidates:['내 조건에 맞는 후보','왕숙1 남부 B17 / 왕숙2 A3','학교·평형·입주시점에 따라 대안','확정 대장이 아닌 조건부 후보'],
overview:['왕숙1 · 왕숙2','북쪽과 남쪽의 위치를 먼저 확인','입주와 시설의 시간을 함께 비교','내 생활의 목적지에서 선택']};
export function MapBrief({theme,block}:{theme:string;block:any}){const rows=copy[theme]||copy.overview;return <><div style={{fontSize:35,fontWeight:700,lineHeight:1.4}}>{rows[0]}</div>{block?<div style={{marginTop:22,fontSize:26,color:'#2f6fed'}}>{block.district} {block.block_id}<br/>입주예정 {block.move_in_target}</div>:null}<div style={{marginTop:25}}>{rows.slice(1).map((x,i)=><div key={i} style={{fontSize:25,lineHeight:1.55,padding:'18px 0',borderTop:'1px solid #d7d9d1',wordBreak:'keep-all'}}>{x}</div>)}</div></>}
