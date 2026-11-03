const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const selected=process.argv.length>2?new Set(process.argv.slice(2).map(Number)):new Set([1,2,3,4,5,6,7,8,9,10]);
 const previous=selected.size<10?read(path.join(__dirname,'bbox_measured_v4.json')):null;
 const report={status:'pass',timing_revision:'production-injoon-v3',chapters:[],failures:[],text_checks:0,caption_cues_checked:0,actual_encoded_frames:false};
 const dir=path.join(out,'preview-measured-v4');fs.mkdirSync(dir,{recursive:true});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
  for(let chapter=1;chapter<=10;chapter++){
   const folder=path.join(out,'ch'+String(chapter).padStart(2,'0')),file=path.join(folder,'index.html'),timing=read(path.join(folder,'timing.json'));
   if(!selected.has(chapter)){
    const old=previous.chapters.find(c=>c.chapter===chapter);if(old.html_sha256!==sha(file))throw Error('Cannot reuse changed chapter BBox');
    report.chapters.push(old);report.text_checks+=old.times.reduce((n,s)=>n+s.checked,0);report.caption_cues_checked+=timing.cues.length;report.failures.push(...previous.failures.filter(f=>f.chapter===chapter));continue;
   }
   const errors=[],listener=e=>errors.push(e.message);page.on('pageerror',listener);
   await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
   const scenes=read(path.join(out,'snapshot_times.json')).samples.filter(s=>s.chapter===chapter),times=new Set([.1,timing.leading_silence_s-.01,timing.last_speech_end_s+.05,timing.total_seconds-.04]);
   for(const s of scenes)for(const t of [s.representative_s,s.after_start_s,s.before_end_s,...s.cue_sample_times_s])times.add(t);
   for(const cue of timing.cues){times.add(Math.max(0,cue.start_s-.01));times.add(Math.min(timing.total_seconds-.01,cue.end_s+.01));}
   const row={chapter,html_sha256:sha(file),times:[],frames:[],seek_pixel_identical:true};
   const seek=async t=>page.evaluate(t=>window.__sourceSeek(t),t);
   for(const t of [...times].filter(t=>t>=0&&t<timing.total_seconds).sort((a,b)=>a-b)){
    await seek(t);
    const metric=await page.evaluate(()=>{
     const findings=[],labels=[];for(const el of document.querySelectorAll('.scene-panel path,.scene-panel polyline')){if(!el.hasAttribute('fill'))findings.push({type:'implicit_path_fill',scene:el.closest('.scene-panel').id,tag:el.outerHTML});}let count=0,maxCaptionWidth=0;const bounds=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
     for(const el of document.querySelectorAll('svg text,.scene-source,.scene-topic,#brand,#tag,.cue')){
      const st=getComputedStyle(el);if(st.visibility==='hidden'||+st.opacity<.01)continue;
      const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),rects=[];let node;
      while(node=walker.nextNode()){const range=document.createRange();range.selectNodeContents(node);rects.push(...[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1));}
      const panel=el.closest('.scene-panel');let box={left:72,right:1848,top:0,bottom:1060};
      if(panel){box=bounds(panel.getBoundingClientRect());if(el.matches('text'))rects.push(el.getBoundingClientRect());}if(el.matches('.cue'))box={left:140,right:1780,top:876,bottom:1000};
      for(const r of rects)if(r.left<box.left-.6||r.right>box.right+.6||r.top<box.top-.6||r.bottom>box.bottom+.6)findings.push({type:'glyph_clipping',text:el.textContent,box,glyph:bounds(r)});
      if(el.matches('.cue')){const lines=rects.filter((r,i)=>!rects.slice(0,i).some(q=>Math.abs(q.top-r.top)<.5));maxCaptionWidth=Math.max(0,...lines.map(r=>r.width));if(lines.length>2||maxCaptionWidth>1600.5||st.fontSize!=='40px'||st.lineHeight!=='50px')findings.push({type:'caption_contract',text:el.textContent,font:st.fontSize,lineHeight:st.lineHeight,lines:lines.length,width:maxCaptionWidth});}
      if(panel&&el.matches('text'))labels.push({text:el.textContent,panel:panel.id,box:bounds(el.getBoundingClientRect())});count++;
     }
     for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){
      const a=labels[i],b=labels[j];if(a.panel!==b.panel)continue;
      const w=Math.min(a.box.right,b.box.right)-Math.max(a.box.left,b.box.left),h=Math.min(a.box.bottom,b.box.bottom)-Math.max(a.box.top,b.box.top);
      if(w>2&&h>2)findings.push({type:'label_overlap',texts:[a.text,b.text],width:w,height:h});
     }
     const visible=[...document.querySelectorAll('.cue')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.5).map(e=>e.textContent);
     const capbox=getComputedStyle(document.getElementById('capbox')).visibility!=='hidden';return {count,findings,visible,capbox,maxCaptionWidth};
    });
    const expected=timing.cues.filter(c=>c.start_s<=t&&t<c.end_s).map(c=>c.display_lines.join('\n'));
    if(JSON.stringify(expected)!==JSON.stringify(metric.visible))metric.findings.push({type:'caption_lifecycle',expected,visible:metric.visible});
    const expectedBox=chapter!==10||t<timing.last_speech_end_s;
    if(metric.capbox!==expectedBox)metric.findings.push({type:'white_box_lifecycle',expected:expectedBox,actual:metric.capbox});
    report.text_checks+=metric.count;if(metric.findings.length)report.failures.push({chapter,time_s:t,findings:metric.findings});row.times.push({time_s:t,checked:metric.count,max_caption_width_px:metric.maxCaptionWidth,findings:metric.findings.length});
   }
   report.caption_cues_checked+=timing.cues.length;
   for(const s of scenes){await seek(s.representative_s);const target=path.join(dir,`ch${String(chapter).padStart(2,'0')}_${s.scene_id}.png`);await page.screenshot({path:target});row.frames.push({scene_id:s.scene_id,time_s:s.representative_s,file:path.relative(out,target).replaceAll('\\','/'),sha256:sha(target)});}
   const mid=scenes[Math.floor(scenes.length/2)].representative_s;await seek(mid);const forward=crypto.createHash('sha256').update(await page.screenshot()).digest('hex');await seek(.1);await seek(mid);row.seek_pixel_identical=forward===crypto.createHash('sha256').update(await page.screenshot()).digest('hex');if(!row.seek_pixel_identical)report.failures.push({chapter,type:'backward_seek_pixel_drift'});
   if(chapter>1){await seek(timing.leading_silence_s/2);const target=path.join(dir,`ch${String(chapter).padStart(2,'0')}_title.png`);await page.screenshot({path:target});row.frames.push({scene_id:`CH${chapter}_TITLE`,time_s:timing.leading_silence_s/2,file:path.relative(out,target).replaceAll('\\','/'),sha256:sha(target)});}
   row.runtime_errors=errors;if(errors.length)report.failures.push({chapter,type:'runtime',errors});page.off('pageerror',listener);report.chapters.push(row);
   console.log(JSON.stringify({chapter,samples:row.times.length,frames:row.frames.length,findings:report.failures.filter(f=>f.chapter===chapter).length}));
  }
  report.status=report.failures.length?'findings':'pass';fs.writeFileSync(path.join(__dirname,'bbox_measured_v4.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,text_checks:report.text_checks,cues:report.caption_cues_checked,findings:report.failures.length}));if(report.failures.length)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
