import React from 'react';
import {AbsoluteFill,Img,staticFile,useCurrentFrame,interpolate} from 'remotion';
export const assetCuts=[
 {start:0,end:5.43,file:'00m00s_신도시_야경_AI.png',title:'',caption:'',intro:true},
 {start:90,end:96,file:'01m30s_최고가와_중위가격_개념.png',title:'',caption:'최고가와 거래의 중심을 함께 봅니다.',card:true},
 {start:180.57,end:186.57,file:'03m00s_세가지_성장조건_AI.png',title:'일자리 · 이동 · 생활의 연결',caption:'시설 이름보다 위치와 연결을 함께 봅니다.'},
 {start:218,end:222.53,file:'03m34s_수변_생활권_AI.png',title:'수변에서 이어지는 생활',caption:'출퇴근뿐 아니라 주말을 보내는 공간까지.'},
 {start:198,end:202,file:'03m43s_반도체_일자리_AI.png',title:'일자리와 주거의 관계',caption:'실제 사업장의 위치는 앞의 지도에서 확인합니다.'},
 {start:245,end:251,file:'04m05s_철도_연결_AI.png',title:'철도, 실제 이용의 시작',caption:'계획 발표와 실제 개통을 나눠 봅니다.'},
 {start:298,end:303.53,file:'05m00s_대표단지와_생활권_AI.png',title:'대표 단지와 주변 생활권',caption:'도시 안에서도 단지별 가격은 다릅니다.'},
 {start:481.1,end:487.1,file:'08m30s_회복경로_비교원칙.png',title:'',caption:'같은 기준연도 · 같은 기간 · 거래 건수',card:true},
 {start:540,end:546,file:'09m00s_근거를_확인하는_책상_AI.png',title:'가격 사례를 읽는 순서',caption:'매입 시점 · 매입가격 · 보유 기간 · 비용'},
 {start:570,end:576,file:'09m30s_세개의_시간표_개념.png',title:'',caption:'입주 · 철도 이용 · 생활시설 운영',card:true},
];
export function AssetCut({cut}:{cut:typeof assetCuts[number]}){const f=useCurrentFrame(),opacity=1,src=staticFile('asset-pack-v9/01_images/'+cut.file);
 if(cut.intro)return <div style={{position:'absolute',left:1050,top:220,width:650,height:580,opacity,overflow:'hidden',borderRadius:18}}><Img src={src} style={{width:'100%',height:'100%',objectFit:'cover'}}/></div>;
 return <AbsoluteFill style={{background:'#F6F4EF',fontFamily:'Pretendard',color:'#111',opacity}}>{cut.card?<Img src={src} style={{width:1920,height:1080,objectFit:'contain'}}/>:<><div style={{position:'absolute',top:65,left:90,fontSize:24,color:'#777'}}>신도시 성공 공식 · 생활권의 구성</div><h1 style={{position:'absolute',top:100,left:90,fontSize:57}}>{cut.title}</h1><Img src={src} style={{position:'absolute',left:90,top:265,width:1740,height:580,objectFit:'cover',borderRadius:16}}/></>}<div className="caption" style={{position:'absolute',bottom:90,textAlign:'center'}}>{cut.caption}</div></AbsoluteFill>;
}

