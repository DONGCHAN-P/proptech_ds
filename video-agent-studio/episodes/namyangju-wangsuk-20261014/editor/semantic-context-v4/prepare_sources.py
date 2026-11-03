from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
proof=(ROOT/'video/src/NamyangjuRailRouteProofV3.tsx').read_text(encoding='utf-8')
proof=proof[:proof.index('function Movie()')]
proof=proof.replace("import {AbsoluteFill,Audio,Composition,interpolate,registerRoot,staticFile,useCurrentFrame} from 'remotion';","import {AbsoluteFill,useCurrentFrame} from 'remotion';")
proof=proof.replace("'../public/namyangju-rail-route-proof-v2/proof_data.json'","'../../public/namyangju-rail-route-proof-v2/proof_data.json'")
proof+='''export function RailRouteVisuals(){const t=useCurrentFrame()/30;return <AbsoluteFill style={{background:cream,color:ink}}><div style={{position:'absolute',left:80,right:80,top:28,display:'flex',justifyContent:'space-between',fontSize:23,color:'#6e6e6e'}}><b>｜ 데이터로 보는 부동산</b><span>남양주 · 왕숙 / 기존 생활권</span></div>{t<30?<Rail t={t}/>:t<40.3?<Commute t={t}/>:t<61?<Dasan/>:<Commute t={t} replay/>}<div style={{position:'absolute',left:80,right:80,top:870,fontSize:19,color:'#676b6d',lineHeight:1.45}}>© OpenStreetMap contributors · {D.sourceNote}<br/>{t>=30&&!(t>=40.3&&t<61)?'속도 비교 연출 · 실제시간 아님 | 단지 대표 진입도로점·출입구 미확인 | 역 4번출구 인근·보도/횡단보도 통행 미확인':t>=40.3&&t<61?D.dasanContext.source_note:'지리 위치를 바탕으로 노선 표시 · 4호선 진접선은 같은 노선의 연장 구간'}</div></AbsoluteFill>}
'''
(ROOT/'video/src/namyangju-v4/RailRouteVisuals.tsx').write_text(proof,encoding='utf-8')
source=(ROOT/'video/src/NamyangjuV3.tsx').read_text(encoding='utf-8')
source=source.replace("import project from './namyangju-v2/project.json';","import project from './namyangju-v4/project.json';\nimport {RailRouteVisuals} from './namyangju-v4/RailRouteVisuals';\nimport {RegionComparison} from './namyangju-v4/RegionComparison';")
start=source.index('function Captions()')
end=source.index('function Movie()',start)
source=source[:start]+'''function Captions({sceneId}:{sceneId:string}){const t=useCurrentFrame()/30;const cap=D.captions[sceneId].find((c:any)=>t>=c.start_s&&t<c.end_s);return cap?<div style={{position:'absolute',left:96,right:96,bottom:28,minHeight:110,padding:'14px 35px',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',background:'white',borderRadius:13,fontSize:39,fontWeight:500,lineHeight:1.25,textAlign:'center',whiteSpace:'pre',zIndex:99}}>{cap.lines.map((line:string,i:number)=><div key={i} style={{whiteSpace:'nowrap',wordBreak:'keep-all'}}>{line}</div>)}</div>:null}
''' +source[end:]
source=source.replace('{D.chapters.map((c:any)=>','<Sequence from={2820} durationInFrames={2400} name="생활권 · 철도 · 접근 동선" style={{zIndex:20}}><RailRouteVisuals/></Sequence>{D.chapters.map((c:any)=>')
source=source.replace('<Audio src={staticFile(c.audio)} volume={1}/></Sequence>','<Audio src={staticFile(c.audio)} volume={1}/><Captions sceneId={c.scene_id}/></Sequence>')
source=source.replace('<Captions/></AbsoluteFill>','</AbsoluteFill>')
source=source.replace('function BoundShot({shot}:{shot:any}){','function BoundShot({shot}:{shot:any}){if(shot.shot_id===\'V2-054\')return <RegionComparison shot={shot}/>;')
source=source.replace('id="NamyangjuV2"','id="NamyangjuV4"').replace('id="StoryproofV2"','id="StoryproofV4"')
(ROOT/'video/src/NamyangjuV4.tsx').write_text(source,encoding='utf-8')
print('v4 sources prepared; semantic cues and regional context pending')
