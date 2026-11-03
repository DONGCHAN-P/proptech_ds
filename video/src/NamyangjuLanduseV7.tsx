import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,registerRoot,staticFile} from 'remotion';
import raw from './namyangju-landuse-v7/project.json';
import type {MapLedProject} from './namyangju-landuse-v7/types';
import {PersistentCaptions} from './namyangju-landuse-v7/PersistentCaptions';
import {MusicBed} from './namyangju-landuse-v7/MusicBed';
import {FrontVisuals} from './namyangju-landuse-v7/FrontVisuals';
import {BoardAudit} from './namyangju-landuse-v7/BoardAudit';
const P=raw as unknown as MapLedProject;
const END=13087;
function Font(){return <style>{`@font-face{font-family:Pretendard;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Regular.woff2')})}@font-face{font-family:Pretendard;font-weight:700;src:url(${staticFile('namyangju-map-led-v6/Pretendard-Bold.woff2')})}*{box-sizing:border-box}`}</style>}
export function CaptionAudit(){return <AbsoluteFill style={{background:'#eae7df',fontFamily:'Pretendard,sans-serif'}}><Font/><div style={{position:'absolute',top:100,left:100,fontSize:40}}>v7 고정 자막 바 검증 · 지도 자산 연결 전 템플릿</div><PersistentCaptions project={P}/></AbsoluteFill>}
function FrontMovie(){return <AbsoluteFill style={{fontFamily:'Pretendard,sans-serif'}}><Font/><FrontVisuals project={P}/><PersistentCaptions project={P}/>{P.narration.filter(n=>n.from_frame<END).map(n=><Sequence key={n.scene_id} from={n.from_frame} durationInFrames={Math.min(n.duration_frames,END-n.from_frame)}><Audio src={staticFile(n.file)} volume={.9}/></Sequence>)}<MusicBed regions={P.music_regions.filter(r=>r.from_frame<END)}/></AbsoluteFill>}
function BoardAuditPreview(){return <><Font/><BoardAudit/></>}
function Root(){return <><Composition id="LanduseV7BoardAudit" component={BoardAuditPreview} durationInFrames={1} width={1920} height={1080} fps={30}/><Composition id="LanduseV7CaptionAudit" component={CaptionAudit} durationInFrames={END} width={1920} height={1080} fps={30}/>{(raw as any).board_assets_ready?<Composition id="NamyangjuLanduseFrontV7" component={FrontMovie} durationInFrames={END} width={1920} height={1080} fps={30}/>:null}</>}
registerRoot(Root);
