/* Local DOM/geometry/seek check. Does not encode or claim audio listening. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),repo=path.resolve(ep,'../../..'),output=path.join(ep,'outputs/rebuild-v2');
const {chromium}=require(path.join(repo,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const within=(child,parent)=>{const r=path.relative(parent,child);return r!==''&&!r.startsWith('..')&&!path.isAbsolute(r);};
(async()=>{
  const run=path.resolve(process.argv[2]||'');
  if(!within(run,output))throw Error('QA writes must stay within outputs/rebuild-v2/<run>');
  const manifest=path.join(run,'preparation_manifest.json');
  const ordered=fs.existsSync(manifest)?read(manifest).scene_order:fs.readdirSync(path.join(run,'scenes')).sort();
  const selected=process.argv.slice(3),scenes=selected.length?ordered.filter(s=>selected.includes(s)):ordered;
  console.log(JSON.stringify({phase:'browser_launch',run}));
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,timeout:10000});
  console.log(JSON.stringify({phase:'browser_ready'}));
  const report={status:'pass',actual_encoded_frames:false,actual_listening:false,continuous_playback:false,scenes:[],failures:[]};
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
    page.setDefaultTimeout(10000);page.setDefaultNavigationTimeout(10000);
    await page.route(/^https?:\/\//,r=>r.abort());
    for(const sid of scenes){
      const folder=path.join(run,'scenes',sid),model=read(path.join(folder,'scene.json')),errors=[];
      console.log(JSON.stringify({phase:'scene_start',scene_id:sid}));
      const listener=e=>errors.push(e.message);page.on('pageerror',listener);
      await page.goto(pathToFileURL(path.join(folder,'index.html')).href);
      await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
      console.log(JSON.stringify({phase:'fonts_timeline_ready',scene_id:sid}));
      const times=new Set([0,model.duration_s-1/30]);
      if(model.opening_context){times.add(model.beats[0].start_s/2);times.add(Math.max(0,model.opening_context.end_s-1/300));}
      for(const b of model.beats){times.add(Math.max(0,b.start_s-1/30));times.add(b.start_s+.12);times.add(b.start_s+Math.min(.45,b.end_s-b.start_s)+.02);}
      for(const c of model.cues){times.add(Math.max(0,c.start_s-1/300));times.add((c.start_s+c.end_s)/2);times.add(Math.min(model.duration_s-1/30,c.end_s+1/300));}
      const samples=[];
      for(const t of [...times].filter(t=>t>=0&&t<model.duration_s).sort((a,b)=>a-b)){
        await page.evaluate(t=>window.__sourceSeek(t),t);
        const metric=await page.evaluate(({t,beats,cues,opening})=>{
          const findings=[],texts=[],shapes=[];
          const rect=r=>({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height});
          const opacity=e=>{let a=1;for(let p=e;p;p=p.parentElement){const c=getComputedStyle(p);if(c.visibility==='hidden'||c.display==='none')return 0;a*=Number(c.opacity);}return a;};
          const intersects=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
          for(const el of document.querySelectorAll('[data-object="shape"]')){
            if(opacity(el)<.01)continue;const b=rect(el.getBoundingClientRect());if(b.width>.5&&b.height>.5)shapes.push({id:el.id,box:b});
          }
          const visibleCues=[];
          for(const el of document.querySelectorAll('[data-object="text"],#message,#source,.caption-lines')){
            if(opacity(el)<.01)continue;
            const st=getComputedStyle(el),range=document.createRange();range.selectNodeContents(el);
            const glyphs=[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1).map(rect);
            const inGraphic=!!el.closest('#graphic'),caption=!!el.closest('.cue');
            const allowed=caption?{left:140,top:876,right:1780,bottom:1000}:el.id==='source'?{left:96,top:1020,right:1824,bottom:1050}:inGraphic?{left:80,top:225,right:1820,bottom:810}:{left:80,top:125,right:1820,bottom:215};
            for(const g of glyphs){
              if(g.left<allowed.left-.6||g.right>allowed.right+.6||g.top<allowed.top-.6||g.bottom>allowed.bottom+.6)findings.push({type:'glyph_out_of_region',id:el.id,text:el.textContent,box:g,allowed});
              if(inGraphic)texts.push({id:el.id,text:el.textContent,box:g});
            }
            if(inGraphic&&parseFloat(st.fontSize)<28)findings.push({type:'small_graphic_label',id:el.id,size:st.fontSize});
            if(/^conclusion(?:-\d+)?$/.test(el.id)&&parseFloat(st.fontSize)<64)findings.push({type:'small_conclusion',size:st.fontSize});
            if(caption){const distinct=[...new Set(glyphs.map(g=>Math.round(g.top)))];if(st.fontSize!=='40px'||st.lineHeight!=='50px'||distinct.length>2)findings.push({type:'caption_size_lines',size:st.fontSize,lineHeight:st.lineHeight,lines:distinct.length});visibleCues.push(el.closest('.cue').id.slice(4));}
          }
          for(let i=0;i<texts.length;i++){
            for(let j=i+1;j<texts.length;j++)if(texts[i].id!==texts[j].id&&intersects(texts[i].box,texts[j].box))findings.push({type:'text_text_collision',a:texts[i],b:texts[j]});
            for(const s of shapes)if(intersects(texts[i].box,s.box))findings.push({type:'text_graphic_collision',text:texts[i],shape:s});
          }
          for(const b of beats)for(const id of b.reveal){
            if(t<b.start_s-1e-5&&opacity(document.getElementById(id))>.001)findings.push({type:'premature_information',id,t,anchor:b.start_s});
          }
          const expected=cues.filter(c=>c.start_s<=t&&t<c.end_s).map(c=>c.id);
          if(JSON.stringify(visibleCues)!==JSON.stringify(expected))findings.push({type:'caption_lifecycle',expected,actual:visibleCues});
          if(opening){
            const el=document.getElementById(opening.id),a=el?opacity(el):0;
            const inputs=[...document.querySelectorAll('[id^="opening-node-"]')].filter(e=>opacity(e)>.99);
            if(t<opening.end_s-1e-5&&(a<.99||inputs.length!==3))findings.push({type:'opening_context_missing',opacity:a,visible_inputs:inputs.length,t});
            if(t>=opening.end_s+1/30+1e-5&&a>.001)findings.push({type:'opening_context_not_hidden',opacity:a,t});
          }
          return {t,findings,texts,shapes};
        },{t,beats:model.beats,cues:model.cues,opening:model.opening_context});
        if(metric.findings.length)report.failures.push({scene_id:sid,...metric});
        samples.push({time_s:t,text_count:metric.texts.length,shape_count:metric.shapes.length,findings:metric.findings.length});
      }
      const evidence=[];
      for(const [i,b] of model.beats.entries()){
        const t=Math.min(model.duration_s-1/30,b.start_s+.7);await page.evaluate(t=>window.__sourceSeek(t),t);
        const file=path.join(folder,`template-stage-${String(i).padStart(2,'0')}.png`),buffer=await page.screenshot({path:file});
        evidence.push({time_s:t,file,sha256:sha(buffer),basis:model.template_only?'synthetic_template_clock':'actual_anchor_source_preview',manual_viewed:false});
      }
      const t=model.beats.at(-1).start_s+.7;await page.evaluate(t=>window.__sourceSeek(t),t);const first=sha(await page.screenshot());
      await page.evaluate(()=>window.__sourceSeek(0));await page.evaluate(t=>window.__sourceSeek(t),t);const repeated=sha(await page.screenshot());
      if(first!==repeated)report.failures.push({scene_id:sid,type:'backward_seek_pixel_drift'});
      if(model.opening_context){
        for(const t0 of [0,model.opening_context.end_s/2]){
          await page.evaluate(t=>window.__sourceSeek(t),t0);
          const a=await page.evaluate(id=>Number(getComputedStyle(document.getElementById(id)).opacity),model.opening_context.id);
          if(a<.99)report.failures.push({scene_id:sid,type:'opening_missing_after_backward_seek',time_s:t0,opacity:a});
        }
      }
      if(model.read_hold_s<1.2-1e-6)report.failures.push({scene_id:sid,type:'insufficient_read_hold',hold:model.read_hold_s});
      if(errors.length)report.failures.push({scene_id:sid,type:'runtime',errors});
      report.scenes.push({scene_id:sid,html_sha256:sha(fs.readFileSync(path.join(folder,'index.html'))),template_only:model.template_only,read_hold_s:model.read_hold_s,samples,evidence,seek_pixel_identical:first===repeated});
      page.off('pageerror',listener);
    }
  }finally{await browser.close();}
  report.status=report.failures.length?'findings':'pass';fs.writeFileSync(path.join(run,'geometry_receipt.json'),JSON.stringify(report,null,2)+'\n','utf8');
  console.log(JSON.stringify({status:report.status,scenes:report.scenes.length,findings:report.failures.length,mp4_rendered:false}));
  if(report.failures.length)process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
