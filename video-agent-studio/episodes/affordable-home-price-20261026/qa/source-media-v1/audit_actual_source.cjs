const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const qa=__dirname,ep=path.resolve(qa,'../..'),root=path.resolve(qa,'../../../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const packet=read(path.join(qa,'caption_packet.json')),receipt=read(path.join(ep,'editor/measured_build_receipt.json'));
const snapshots=read(path.join(out,'snapshot_times.json'));
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const report={status:'review_in_progress',timing_revision:'production-injoon-v2_provisional_v3_pending',script_sha256:receipt.script_sha256,timing_sha256:receipt.timing_sha256,chapters:[],geometry_candidates:[],runtime_errors:[],caption_failures:[],focus_failures:[],source_frames:[],actual_encoded_frames:false,actual_listening:false,continuous_playback:false};
 const frameDir=path.join(qa,'actual-source-v2-frames');fs.mkdirSync(frameDir,{recursive:true});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
  for(const item of receipt.chapters){
   const file=path.join(out,item.project,'index.html'),errors=[];const onError=e=>errors.push(e.message);page.on('pageerror',onError);
   const hash=sha(file);if(hash!==item.html_sha256)throw Error('Source revision changed before review: '+item.project);
   await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__sourceSeek&&document.fonts.status==='loaded');
   await page.evaluate(async()=>{for(const w of [400,600,700,800])await document.fonts.load(w+' 40px Pretendard');await document.fonts.ready});
   const meta=await page.evaluate(()=>({scenes:SCENES,cues:CUES,beats:BEATS}));
   const row={chapter:item.chapter,html_sha256:hash,scenes:meta.scenes,cues_checked:0,beats:[],samples:[],dependencies:[]};
   for(const cue of meta.cues){
    const expected=packet.cues.find(c=>c.id===cue.id);
    if(!expected||JSON.stringify(cue.display_lines)!==JSON.stringify(expected.display_lines)||cue.text!==expected.text)report.caption_failures.push({chapter:item.chapter,cue_id:cue.id,type:'source_caption_text_drift'});
   }
   const times=new Map();
   const add=(t,reason)=>{if(t>=0&&t<item.total_seconds){const key=t.toFixed(6);if(!times.has(key))times.set(key,{time_s:t,reasons:[]});times.get(key).reasons.push(reason)}};
   add(.1,'chapter_start');add(item.leading_silence_s/2,'chapter_title');add(item.last_speech_end_s+.04,'last_voice_after');add(item.total_seconds-.04,'chapter_end');
   for(const scene of meta.scenes){add((scene.start_s+scene.end_s)/2,scene.scene_id+'/representative');for(const delta of [-1/30,0,.1,.35])add(scene.clip_start_s+delta,scene.scene_id+'/entrance'+delta);add(scene.clip_end_s-1/30,scene.scene_id+'/exit');}
   for(const cue of meta.cues){add((cue.start_s+cue.end_s)/2,cue.id+'/native_focus');add(cue.start_s-.001,cue.id+'/before');add(cue.end_s+.001,cue.id+'/after');}
   const measure=async sample=>{
    await page.evaluate(t=>window.__sourceSeek(t),sample.time_s);
    const metric=await page.evaluate(()=>{
     const b=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
     const visible=e=>{const s=getComputedStyle(e);return s.visibility!=='hidden'&&+s.opacity>.01;};
     const candidates=[],labels=[],activeScenes=[...document.querySelectorAll('section.scene-panel')].filter(visible).map(e=>e.id);
     let textChecks=0;
     for(const el of document.querySelectorAll('svg text,.scene-source,.scene-topic,#brand,#tag,.cue')){
      if(!visible(el))continue;
      const panel=el.closest('.scene-panel'),range=document.createRange();range.selectNodeContents(el);
      const rects=[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1).map(b);
      let limit={left:72,right:1848,top:0,bottom:1060};if(panel)limit=b(panel.getBoundingClientRect());
      if(el.matches('.cue'))limit={left:140,right:1780,top:876,bottom:1000};
      for(const r of rects)if(r.left<limit.left-.5||r.right>limit.right+.5||r.top<limit.top-.5||r.bottom>limit.bottom+.5)candidates.push({type:'glyph_outside',scene_id:panel?.id,text:el.textContent,element_id:el.id,glyph:r,limit});
      if(el.matches('.scene-topic')&&rects.some(r=>r.bottom>215))candidates.push({type:'title_hits_panel',text:el.textContent,rects});
      if(el.matches('.scene-source')&&rects.some(r=>r.right>1824||r.top<1018||r.bottom>1060))candidates.push({type:'source_footer',text:el.textContent,rects});
      if(panel&&el.matches('text'))labels.push({scene_id:panel.id,text:el.textContent,rect:b(el.getBoundingClientRect()),id:el.id});
      textChecks++;
     }
     for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){
      const a=labels[i],z=labels[j];if(a.scene_id!==z.scene_id)continue;
      const w=Math.min(a.rect.right,z.rect.right)-Math.max(a.rect.left,z.rect.left),h=Math.min(a.rect.bottom,z.rect.bottom)-Math.max(a.rect.top,z.rect.top);
      if(w>2&&h>2)candidates.push({type:'label_overlap',scene_id:a.scene_id,texts:[a.text,z.text],width:w,height:h});
     }
     const activeCues=[...document.querySelectorAll('.cue')].filter(visible).map(e=>({id:e.id,text:e.textContent,font:getComputedStyle(e).fontSize,lineHeight:getComputedStyle(e).lineHeight}));
     const rings=[...document.querySelectorAll('.focus-ring,.native-word-focus')].filter(visible).filter(e=>e.closest('section')&&activeScenes.includes(e.closest('section').id)).map(e=>({scene_id:e.closest('section').id,parent_id:e.parentElement.id,rect:b(e.getBoundingClientRect()),opacity:getComputedStyle(e).opacity}));
     return {textChecks,activeScenes,activeCues,rings,candidates,capbox_visible:visible(document.getElementById('capbox'))};
    });
    const expected=meta.cues.filter(c=>c.start_s<=sample.time_s&&sample.time_s<c.end_s);
    if(JSON.stringify(expected.map(c=>c.display_lines.join('\n')))!==JSON.stringify(metric.activeCues.map(c=>c.text)))report.caption_failures.push({chapter:item.chapter,time_s:sample.time_s,type:'actual_caption_lifecycle',expected:expected.map(c=>c.id),actual:metric.activeCues});
    if(metric.activeCues.some(c=>c.font!=='40px'||c.lineHeight!=='50px'))report.caption_failures.push({chapter:item.chapter,time_s:sample.time_s,type:'actual_caption_font'});
    const expectedBox=item.chapter!==10||sample.time_s<item.last_speech_end_s;
    if(metric.capbox_visible!==expectedBox)report.caption_failures.push({chapter:item.chapter,time_s:sample.time_s,type:'actual_white_box_lifecycle',expected:expectedBox});
    for(const c of metric.candidates)report.geometry_candidates.push({chapter:item.chapter,time_s:sample.time_s,...c});
    row.samples.push({time_s:sample.time_s,reasons:sample.reasons,text_checks:metric.textChecks,scene_ids:metric.activeScenes,candidates:metric.candidates.length});
    for(const cue of expected){if(!sample.reasons.includes(cue.id+'/native_focus'))continue;
     const beat=meta.beats.find(b=>b.cue_id===cue.id);
     const focus=await page.evaluate(beat=>({target_ids:beat.target_ids,text_ids:beat.text_target_ids,text_labels:beat.text_target_ids.map(id=>document.getElementById(id)?.textContent),missing:beat.target_ids.concat(beat.text_target_ids).filter(id=>!document.getElementById(id)),source_text:document.querySelector('#'+beat.scene_id)?.parentElement?.querySelector('.scene-source')?.textContent}),beat);
     row.beats.push({cue_id:cue.id,scene_id:cue.scene_id,time_s:sample.time_s,spoken_display_text:cue.text,...focus,visible_ring_count:metric.rings.length});
     if(focus.missing.length||!metric.rings.length||!metric.activeScenes.includes(cue.scene_id))report.focus_failures.push({chapter:item.chapter,cue_id:cue.id,time_s:sample.time_s,focus,activeScenes:metric.activeScenes,rings:metric.rings.length});row.cues_checked++;
    }
   };
   for(const sample of [...times.values()].sort((a,b)=>a.time_s-b.time_s))await measure(sample);
   const save=async(t,sid,kind)=>{await page.evaluate(t=>window.__sourceSeek(t),t);const target=path.join(frameDir,`ch${String(item.chapter).padStart(2,'0')}_${sid}_${kind}.png`);await page.screenshot({path:target});report.source_frames.push({chapter:item.chapter,scene_id:sid,time_s:t,kind,path:target,sha256:sha(target),html_sha256:hash});};
   for(const scene of meta.scenes)await save((scene.start_s+scene.end_s)/2,scene.scene_id,'representative');
   if(item.chapter>1)await save(item.leading_silence_s/2,'CH'+item.chapter,'title');
   // 후보 경계는 직접 프레임으로 확인할 수 있게 별도로 보존한다.
   for(const c of report.geometry_candidates.filter(c=>c.chapter===item.chapter).slice(0,3))await save(c.time_s,c.scene_id||'candidate','bbox_candidate');
   const mid=meta.scenes[Math.floor(meta.scenes.length/2)].start_s+1;
   await page.evaluate(t=>window.__sourceSeek(t),mid);const forward=crypto.createHash('sha256').update(await page.screenshot()).digest('hex');await page.evaluate(()=>window.__sourceSeek(.01));await page.evaluate(t=>window.__sourceSeek(t),mid);row.backward_seek_pixel_identical=forward===crypto.createHash('sha256').update(await page.screenshot()).digest('hex');
   row.html_unchanged=sha(file)===hash;row.runtime_errors=errors;if(errors.length)report.runtime_errors.push({chapter:item.chapter,errors});
   report.chapters.push(row);page.off('pageerror',onError);console.log(JSON.stringify({chapter:item.chapter,samples:row.samples.length,cues:row.cues_checked,geometry_candidates:report.geometry_candidates.filter(c=>c.chapter===item.chapter).length}));
  }
  report.status=report.runtime_errors.length||report.caption_failures.length||report.focus_failures.length?'findings':'geometry_candidates_need_visual_review';
  report.total_text_checks=report.chapters.reduce((n,c)=>n+c.samples.reduce((s,t)=>s+t.text_checks,0),0);report.total_native_focus_cues=report.chapters.reduce((n,c)=>n+c.cues_checked,0);
  fs.writeFileSync(path.join(qa,'actual_source_metrics_v2.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,scenes:report.chapters.reduce((n,c)=>n+c.scenes.length,0),cues:report.total_native_focus_cues,text_checks:report.total_text_checks,candidates:report.geometry_candidates.length,caption_failures:report.caption_failures.length,focus_failures:report.focus_failures.length}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
