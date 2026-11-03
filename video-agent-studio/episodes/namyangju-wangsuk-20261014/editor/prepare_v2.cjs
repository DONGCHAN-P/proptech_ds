const fs=require('fs'),path=require('path');
const repo=path.resolve(__dirname,'../../../..'),episode=path.resolve(__dirname,'..');
const pub=path.join(repo,'video/public/namyangju-v2'),src=path.join(repo,'video/src/namyangju-v2');
fs.mkdirSync(pub,{recursive:true});fs.mkdirSync(src,{recursive:true});
const read=p=>JSON.parse(fs.readFileSync(path.join(episode,p),'utf8'));
const timing=read('editor/render_v1/timing_actual.json'), shots=read('writer/shot_plan_video_v2.json').shots, captions=read('editor/render_v1/caption_estimates.json');
const meta=read('visual/regional_meta_v3.json'),raw=read('visual/regional_osm_v3.json');
const copy=(from,name)=>{if(!fs.existsSync(from))return null;fs.copyFileSync(from,path.join(pub,name));return 'namyangju-v2/'+name;};
const chapters=timing.map(t=>({...t,from:Math.round(t.start_s*30),frames:t.encoded_frames,audio:copy(path.join(episode,'narration/audio-v1/'+t.scene_id+'.mp3'),t.scene_id+'.mp3')}));
const durations=read('narration/timing_proposals_v1.json').scenes;
const edited=shots.map(s=>{const t=chapters.find(t=>t.scene_id===s.chapter_id),d=durations.find(d=>d.scene_id===s.chapter_id).duration_s;return {...s,from:t.from+Math.round(s.chapter_local_start_s/d*t.frames),frames:Math.max(1,Math.round(s.chapter_local_end_s/d*t.frames)-Math.round(s.chapter_local_start_s/d*t.frames))};});
const paths=raw.elements.filter(e=>e.type==='way'&&e.geometry?.length>1).map(e=>({kind:e.tags?.waterway?'water':e.tags?.railway?'rail':'road',points:e.geometry.filter((_,i)=>i%3===0||i===e.geometry.length-1).map(g=>[g.lon,g.lat])}));
const media={ai:[],photos:[],plans:[],previous:'namyangju-v2/previous-v14-4s.mp4',bgm:copy(path.join(repo,'assets/music/data_city_ambient_v1.wav'),'data-city-ambient.wav')};
for(const f of fs.readdirSync(path.join(episode,'visual/gpt-generated-v1'))){if(/\.png$/i.test(f)){media.ai.push({file:copy(path.join(episode,'visual/gpt-generated-v1',f),f),title:'AI 개념 이미지 · 실제 왕숙 모습 아님'});}}
for(const [n,label]of [[1,'왕숙1'],[2,'왕숙2']]){media.plans.push({file:copy(path.join(episode,`visual/outputs/S003_wangsuk${n}_official_plan.jpg`),`official-plan-${n}.jpg`),title:label,credit:'남양주시 제공 계획도 · 공공누리 제3유형 · 전체 원본',condition:'페이지 최종수정 2026.3.4 · 최신 변경차수 전수대조 미완료'});}
const photoManifest=path.join(episode,'visual/photos_verified_v4.json');
if(fs.existsSync(photoManifest)){const m=JSON.parse(fs.readFileSync(photoManifest,'utf8'));for(const p of m.assets||m.photos||m){const f=p.actual_file||p.file||p.local_path;if(!f)continue;const full=path.isAbsolute(f)?f:path.join(episode,f);if(!fs.existsSync(full))continue;media.photos.push({...p,file:copy(full,'photo-'+path.basename(full))});}}
const va=path.join(episode,'visual/assets_v4.json');if(fs.existsSync(va))for(const a of JSON.parse(fs.readFileSync(va,'utf8')).assets.filter(a=>a.type==='ai_concept')){const f=path.join(episode,a.actual_file);if(fs.existsSync(f))media.ai.push({file:copy(f,path.basename(f)),title:'AI 개념 이미지 · 실제 왕숙 모습 아님'});}
// Existing licensed source imagery is used only for comparative previous-episode shots.
copy(path.join(repo,'video/public/fonts/Pretendard-Regular.woff2'),'Pretendard-Regular.woff2');copy(path.join(repo,'video/public/fonts/Pretendard-Bold.woff2'),'Pretendard-Bold.woff2');
const bindings=read('visual/shot_asset_binding_v2.json').bindings;
const canonical=read('visual/assets_v5.json').assets;
media.assets={};for(const a of canonical){const f=a.actual_file;if(!f)continue;const from=path.isAbsolute(f)?f:path.join(episode,f);if(a.asset_id==='PREV_V14'){media.assets[a.asset_id]={...a,file:media.previous};continue;}if(!fs.existsSync(from))throw Error('asset missing: '+a.asset_id);media.assets[a.asset_id]={...a,file:copy(from,'asset-'+a.asset_id+path.extname(f))};}
for(const s of edited){s.binding=bindings.find(b=>b.shot_id===s.shot_id);if(!s.binding)throw Error('exact binding missing '+s.shot_id);}
const data={revision:'editor-remotion-v2',fps:30,durationInFrames:chapters.reduce((s,t)=>s+t.frames,0),chapters,shots:edited,captions,places:meta.place_points,paths,media};
fs.writeFileSync(path.join(src,'project.json'),JSON.stringify(data));fs.writeFileSync(path.join(__dirname,'project_manifest_v2.json'),JSON.stringify({revision:data.revision,shots:edited.length,chapters:chapters.length,frames:data.durationInFrames,media,caption_basis:'existing character-weight estimates scaled within each decoded audio scene'},null,2));
console.log(JSON.stringify({shots:edited.length,frames:data.durationInFrames,photos:media.photos.length,ai:media.ai.length}));
