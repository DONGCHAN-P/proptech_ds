const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const dir=path.join(out,'preview-visual-v4-delta');fs.mkdirSync(dir,{recursive:true});
 const edl=read(path.join(out,'assembly_edl.json')),cut=edl.hook_cut_s,frames=[],checks=[];
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
  for(const ch of [7,9]){
   await page.goto(pathToFileURL(path.join(out,`ch${String(ch).padStart(2,'0')}/index.html`)).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
   const targets=read(path.join(out,`ch${String(ch).padStart(2,'0')}/anchor_audit.json`)).beats.filter(b=>b.scene_id===(ch===7?'S031':'S040'));
   for(const beat of targets){
    const time=(beat.start_s+beat.end_s)/2;await page.evaluate(t=>window.__sourceSeek(t),time);
    const actual=await page.evaluate(sid=>{
     const visible=e=>+getComputedStyle(e).opacity>.1&&getComputedStyle(e).visibility!=='hidden';
     const scene=document.getElementById(sid),rings=[...scene.querySelectorAll('.native-word-focus')].filter(visible);
     const textIDs=[...scene.querySelectorAll('text')].filter(e=>{const b=e.getBoundingClientRect();return rings.some(r=>{const q=r.getBoundingClientRect();return Math.abs(q.left-(b.left-6))<1&&Math.abs(q.top-(b.top-4))<1&&Math.abs(q.width-(b.width+12))<1;})}).map(e=>e.id);
     const groupIDs=[...scene.querySelectorAll('.semantic-part')].filter(g=>visible(g.querySelector(':scope > .focus-ring'))).map(e=>e.id);
     return {textIDs,groupIDs};
    },beat.scene_id);
    const sorted=x=>JSON.stringify([...x].sort());if(sorted(actual.textIDs)!==sorted(beat.text_target_ids)||sorted(actual.groupIDs)!==sorted(beat.target_ids))throw Error('Actual focus drift '+beat.cue_id+' '+JSON.stringify(actual));
    const file=path.join(dir,beat.cue_id+'.png');await page.screenshot({path:file});
    const offset=edl.offset_map.find(o=>o.chapter===ch&&o.local_start_s<=time&&time<o.local_end_s).global_offset_s;
    frames.push({chapter:ch,scene_id:beat.scene_id,cue_id:beat.cue_id,role:'actual_native_cue_focus',local_time_s:time,global_time_s:time+offset,file:path.relative(out,file).replaceAll('\\','/'),sha256:sha(file)});checks.push({cue_id:beat.cue_id,expected:{textIDs:beat.text_target_ids,groupIDs:beat.target_ids},actual,status:'pass'});
   }
  }
  await page.goto(pathToFileURL(path.join(out,'ch01/index.html')).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
  const native=read(path.join(out,'ch01/timing.json')).cues.find(c=>c.scene_id==='S002');
  for(const [time,global,role,expected] of [[cut-1/30,cut-1/30,'before_intro_hook_last_frame','S001'],[cut,cut+5,'after_intro_first_body_frame','S002'],[native.start_s-.01,native.start_s+4.99,'before_S002_actual_voice_caption_blank','S002']]){
   await page.evaluate(t=>window.__sourceSeek(t),time);const state=await page.evaluate(()=>({scenes:[...document.querySelectorAll('.scene-panel')].filter(e=>getComputedStyle(e).visibility!=='hidden').map(e=>e.id),cues:[...document.querySelectorAll('.cue')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.5).map(e=>e.textContent)}));
   if(JSON.stringify(state.scenes)!==JSON.stringify([expected])||(expected==='S002'&&state.cues.length))throw Error('Brand resume or native caption drift '+JSON.stringify(state));
   const file=path.join(dir,role+'.png');await page.screenshot({path:file});frames.push({chapter:1,scene_id:expected,role,local_time_s:time,global_time_s:global,file:path.relative(out,file).replaceAll('\\','/'),sha256:sha(file)});checks.push({role,status:'pass',...state});
  }
 }finally{await browser.close();}
 const provision=read(path.join(root,'video-agent-studio/episodes/housing-choice-networth-20261020/director/two-episode-production-v1/ffmpeg_receipt.json')),ffmpeg=path.join(root,provision.binary);if(sha(ffmpeg)!==provision.binary_sha256)throw Error('FFmpeg SHA');
 const intro=edl.segments.find(s=>s.id==='clean_brand_intro').asset;const media=path.join(root,intro.path);if(sha(media)!==intro.sha256)throw Error('Brand SHA');
 for(const [time,global,role] of [[0,cut,'intro_first_frame'],[149/30,cut+149/30,'intro_last_frame']]){
  const file=path.join(dir,role+'.png');cp.execFileSync(ffmpeg,['-v','error','-ss',String(time),'-i',media,'-frames:v','1','-y',file]);frames.push({chapter:null,scene_id:'clean_brand_intro',role,local_time_s:time,global_time_s:global,file:path.relative(out,file).replaceAll('\\','/'),sha256:sha(file),scope:'frame from unchanged approved brand MP4; final assembly not encoded yet'});
 }
 const report={status:'pass_targeted_visual_v4_source_checks_independent_closure_pending',issues:['SOURCE-FOCUS-003','SOURCE-BRAND-004'],script_audio_captions_EDL_unchanged:true,canonical_carve_rerun:false,actual_encoded_film_frames:false,chapters:[1,7,9].map(ch=>({chapter:ch,html_sha256:sha(path.join(out,`ch${String(ch).padStart(2,'0')}/index.html`))})),checks,frames};
 fs.writeFileSync(path.join(__dirname,'visual_v4_targeted_handoff.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,frames:frames.length,focus_cues:8}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
