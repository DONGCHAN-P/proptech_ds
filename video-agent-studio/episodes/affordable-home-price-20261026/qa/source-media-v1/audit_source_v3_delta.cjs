const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const qa=__dirname,ep=path.resolve(qa,'../..'),root=path.resolve(qa,'../../../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const timingFile=path.join(ep,'narration/production-injoon-v3/final_timing.json'),timing=read(timingFile),receipt=read(path.join(ep,'editor/measured_build_receipt.json')),packet=read(path.join(qa,'caption_packet.json')),edlFile=path.join(out,'assembly_edl.json'),edl=read(edlFile);
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const report={timing_sha256:sha(timingFile),edl_sha256:sha(edlFile),script_sha256:timing.script_sha256,chapters:[],anchor_failures:[],caption_failures:[],focus_presence_failures:[],geometry_candidates:[],frames:[],actual_listening:false,actual_encoded_frames:false,continuous_playback:false};
fs.mkdirSync(path.join(qa,'actual-source-v3-delta-frames'),{recursive:true});
try{const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
for(const item of receipt.chapters){const file=path.join(out,item.project,'index.html'),hash=sha(file);if(hash!==item.html_sha256)throw Error('source hash drift '+item.chapter);
await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__sourceSeek&&document.fonts.status==='loaded');await page.evaluate(async()=>{for(const w of [400,600,700,800])await document.fonts.load(w+' 40px Pretendard');await document.fonts.ready});
const meta=await page.evaluate(()=>({scenes:SCENES,cues:CUES,beats:BEATS})),native=timing.chapters.find(c=>c.chapter===item.chapter),row={chapter:item.chapter,html_sha256:hash,scenes:meta.scenes,cue_checks:0,focus_checks:[]};
for(const s of meta.scenes){const cues=native.cues.filter(c=>c.scene_id===s.scene_id);if(Math.abs(s.start_s-Math.min(...cues.map(c=>c.start_s)))>1e-6||Math.abs(s.end_s-Math.max(...cues.map(c=>c.end_s)))>1e-6)report.anchor_failures.push({chapter:item.chapter,scene_id:s.scene_id});}
for(const cue of meta.cues){const n=native.cues.find(c=>c.id===cue.id),frozen=packet.cues.find(c=>c.id===cue.id),beat=meta.beats.find(b=>b.cue_id===cue.id);
if(!n||!frozen||cue.text!==frozen.text||JSON.stringify(cue.display_lines)!==JSON.stringify(frozen.display_lines)||Math.abs(cue.start_s-n.start_s)>1e-6||Math.abs(cue.end_s-n.end_s)>1e-6||Math.abs(beat.start_s-n.start_s)>1e-6||Math.abs(beat.end_s-n.end_s)>1e-6)report.anchor_failures.push({chapter:item.chapter,cue_id:cue.id});
const t=(cue.start_s+cue.end_s)/2;await page.evaluate(t=>window.__sourceSeek(t),t);
const actual=await page.evaluate(beat=>{const vis=e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.01;return {active_scenes:[...document.querySelectorAll('.scene-panel')].filter(vis).map(e=>e.id),cues:[...document.querySelectorAll('.cue')].filter(vis).map(e=>({text:e.textContent,font:getComputedStyle(e).fontSize,lineHeight:getComputedStyle(e).lineHeight})),labels:beat.text_target_ids.map(id=>document.getElementById(id)?.textContent),target_ids:beat.target_ids,text_ids:beat.text_target_ids,visible_focus:[...document.querySelectorAll('#'+beat.scene_id+' .focus-ring,#'+beat.scene_id+' .native-word-focus')].filter(vis).length}},beat);
if(actual.cues.length!==1||actual.cues[0].text!==cue.display_lines.join('\n')||actual.cues[0].font!=='40px'||actual.cues[0].lineHeight!=='50px')report.caption_failures.push({chapter:item.chapter,cue_id:cue.id,actual});
if(!actual.active_scenes.includes(cue.scene_id)||!actual.visible_focus)report.focus_presence_failures.push({chapter:item.chapter,cue_id:cue.id,actual});
row.focus_checks.push({cue_id:cue.id,scene_id:cue.scene_id,time_s:t,display_text:cue.text,...actual});row.cue_checks++;
}
const save=async(scene,t,kind)=>{await page.evaluate(t=>window.__sourceSeek(t),t);const p=path.join(qa,'actual-source-v3-delta-frames',`ch${String(item.chapter).padStart(2,'0')}_${scene}_${kind}.png`);await page.screenshot({path:p});const actual=await page.evaluate(()=>({active_scenes:[...document.querySelectorAll('.scene-panel')].filter(e=>getComputedStyle(e).visibility!=='hidden').map(e=>e.id),caption:[...document.querySelectorAll('.cue')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.5).map(e=>e.textContent)}));report.frames.push({chapter:item.chapter,scene_id:scene,time_s:t,kind,path:p,sha256:sha(p),html_sha256:hash,...actual});};
const targetScenes=new Set(['S014','S016','S018','S019','S024','S030','S032','S031','S040']);
for(const s of meta.scenes){if(!targetScenes.has(s.scene_id))continue;
await save(s.scene_id,(s.start_s+s.end_s)/2,'changed_or_fix');
if(s.scene_id==='S040')for(const d of [0,.1,.35]){const t=s.clip_start_s+d;await save(s.scene_id,t,'entrance_'+d);const bad=await page.evaluate(()=>{const panel=document.getElementById('S040'),limit=panel.getBoundingClientRect(),el=document.getElementById('S040_text011'),r=el.getBoundingClientRect();return {text:el.textContent,bottom:r.bottom,limit:limit.bottom,top:r.top,font:el.getAttribute('font-size')}});if(bad.bottom>bad.limit+.5)report.geometry_candidates.push({scene_id:s.scene_id,time_s:t,...bad});}
}
if(item.chapter===1){await save('brand_resume',edl.hook_cut_s,'source_at_cut');const active=report.frames[report.frames.length-1].active_scenes;report.brand_resume={chapter_local_s:edl.hook_cut_s,global_s:edl.segments.find(s=>s.id==='clean_brand_intro').global_end_s,active_scenes:active,expected_scene:'S002',passed:active.length===1&&active[0]==='S002'};}
row.html_unchanged=sha(file)===hash;report.chapters.push(row);
}
report.anchor_scene_count=report.chapters.reduce((n,c)=>n+c.scenes.length,0);report.cues=report.chapters.reduce((n,c)=>n+c.cue_checks,0);
fs.writeFileSync(path.join(qa,'source_delta_metrics_v3.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({scenes:report.anchor_scene_count,cues:report.cues,anchors_failed:report.anchor_failures.length,captions_failed:report.caption_failures.length,focus_presence_failed:report.focus_presence_failures.length,geometry_candidates:report.geometry_candidates.length,brand_resume:report.brand_resume,frames:report.frames.length}));
}finally{await browser.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
