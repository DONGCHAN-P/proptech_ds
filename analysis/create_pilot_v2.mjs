import fs from 'node:fs';
let s=fs.readFileSync('video/src/PilotV1.tsx','utf8');
s=s.replace('spring,registerRoot','spring,registerRoot,Img,useVideoConfig,Easing');
s=s.replace("const total=durations.reduce((a,b)=>a+b,0)+90;","const introLength=durations.reduce((a,b)=>a+b,0);const total=introLength+extension.segments.reduce((n,s)=>n+s.frames,0)+60;");
s=s.replace("import plan from '../public/pilot-v1/plan.json';","import plan from '../public/pilot-v1/plan.json';\nimport extension from '../public/pilot-v2/plan.json';\nimport metrics from '../public/pilot-v2/metrics.json';\nconst extraCaptions=['実際の地図で光教・東灘と比較地域を確認します。','同じ面積帯の年別中位価格を比較します。','代表団地5件。地域全体の成果とは区別します。','東灘1・2の標本合計2,779件を地域別に比較します。','10億超取引の割合と地域中位価格を並べます。'];");
s=s.replace('const extraCaptions=[', 'const extraCaptions=[');
s=s.replace("實際","実際");
s=s.replace("実際の地図で光教・東灘と比較地域を確認します。","실제 지도에서 광교·동탄의 위치를 확인합니다.").replace("同じ面積帯の年別中位価格を比較します。","같은 면적대의 연도별 중위가격을 비교합니다.").replace("代表団地5件。地域全体の成果とは区別します。","대표 단지 5곳의 흐름. 지역 전체 성과와는 구분합니다.").replace("東灘1・2の標本合計2,779件を地域別に比較します。","동탄1·2 표본 합계 2,779건을 다른 지역과 비교합니다.").replace("10億超取引の割合と地域中位価格を並べます。","10억 초과 거래 비율과 지역 중위가격을 나란히 봅니다.");
s=s.replace("return <AbsoluteFill style={{background:bg", "if(index===3)return <AbsoluteFill style={{background:cream}}><Img src={staticFile('pilot-v2/map.png')} style={{width:1920,height:1080}}/></AbsoluteFill>;return <AbsoluteFill style={{background:bg");
s=s.replace("i===5?d+90:d","d");
s=s.replace("})}</AbsoluteFill>}","})}{extension.segments.map((s,i)=>{const from=cursor;cursor+=s.frames;return <Sequence key={'extra'+i} from={from} durationInFrames={s.frames+(i===4?60:0)}><ExtraScene index={i}/><Sequence from={6}><Audio src={staticFile('pilot-v2/'+s.file)}/></Sequence></Sequence>})}</AbsoluteFill>}");
s=s.replace('id="NewtownPilotV1"','id="NewtownV2"');
s=s.replace('registerRoot(()=>',fs.readFileSync('analysis/extra_scene.txt','utf8')+'\nregisterRoot(()=>');
fs.writeFileSync('video/src/PilotV2.tsx',s);fs.copyFileSync('output/metrics_newtown_v2_20261013.json','video/public/pilot-v2/metrics.json');
console.log('V2 composition created');

