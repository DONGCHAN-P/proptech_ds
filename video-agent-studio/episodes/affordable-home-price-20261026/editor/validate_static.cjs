const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const report={status:'pass',timing:'PROVISIONAL',scenes:[],failures:[],actual_encoded_frames:false,actual_listening:false};
 const dir=path.join(out,'preview-v2');fs.mkdirSync(dir,{recursive:true});
 try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.route(/^https?:\/\//,r=>r.abort());
 for(const name of ['cash','fees_cases','reset_budget']){
  const file=path.join(out,name,'index.html'),errors=[];const listener=e=>errors.push(e.message);page.on('pageerror',listener);
  await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>Object.keys(window.__timelines||{}).length&&document.fonts.status==='loaded');
  await page.evaluate(async()=>{for(const weight of [400,600,700,800])await document.fonts.load(weight+' 40px Pretendard');await document.fonts.ready});
  const row={scene:name,html_sha256:sha(file),samples:[],max_label_width_px:0};
  for(const t of [0,.4,2,4.399,4.4,4.7,5,6,10.899,10.9,11.93,6,2]){
   await page.evaluate(t=>window.__sourcePreviewSeek(t),t);
   const metric=await page.evaluate(()=>{
    const bad=[],labels=[];let checked=0;
    const bounds=el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
    for(const el of document.querySelectorAll('svg text,.source,.title,#brand,#tag,.cue')){
     const st=getComputedStyle(el);if(st.visibility==='hidden'||+st.opacity<.01)continue;
     const rs=[],walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let node;
     while(node=walker.nextNode()){const range=document.createRange();range.selectNodeContents(node);rs.push(...[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1));}checked++;
     let b;if(el.matches('svg text'))b=bounds(document.getElementById('panel'));else if(el.matches('.cue'))b={left:140,right:1780,top:876,bottom:1000};else b={left:70,right:1840,top:0,bottom:1060};
     for(const r of rs)if(r.left<b.left-.5||r.right>b.right+.5||r.top<b.top-.5||r.bottom>b.bottom+.5)bad.push({text:el.textContent,bounds:b,glyph:{left:r.left,right:r.right,top:r.top,bottom:r.bottom}});
     if(el.matches('svg text'))labels.push({text:el.textContent,...bounds(el)});
     if(el.matches('.cue')){const lines=rs.filter((r,i)=>!rs.slice(0,i).some(q=>Math.abs(q.top-r.top)<.5));if(lines.length>2||lines.some(r=>r.width>1600.5)||st.fontSize!=='40px'||st.lineHeight!=='50px')bad.push({caption:el.textContent,font:st.fontSize,lineHeight:st.lineHeight,lineCount:lines.length});}
    }
    const visible=[...document.querySelectorAll('.cue')].filter(el=>getComputedStyle(el).visibility!=='hidden'&&+getComputedStyle(el).opacity>.5).map(el=>el.textContent);
    // Check inter-label overlaps, including long max-value labels on the SVG.
    for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){
      const a=labels[i],b=labels[j],w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
      if(w>2&&h>2)bad.push({overlap:[a.text,b.text],width:w,height:h});
    }
    return {checked,bad,visible,capbox_visible:getComputedStyle(document.getElementById('capbox')).visibility!=='hidden',max_label_width:Math.max(...labels.map(l=>l.width))};
   });
   const timing=JSON.parse(fs.readFileSync(path.join(out,name,'timing.json'),'utf8'));
   const expected=timing.cues.filter(c=>c.start_s<=t&&t<c.end_s).map(c=>c.display_lines.join('\n'));
   if(JSON.stringify(expected)!==JSON.stringify(metric.visible)||!metric.capbox_visible)metric.bad.push({caption_lifecycle:{t,expected,actual:metric.visible,box:metric.capbox_visible}});
   row.samples.push({time_s:t,...metric});row.max_label_width_px=Math.max(row.max_label_width_px,metric.max_label_width);
   if(metric.bad.length)report.failures.push({scene:name,time_s:t,findings:metric.bad});
  }
  await page.evaluate(()=>window.__sourcePreviewSeek(6));const target=path.join(dir,name+'.png');await page.screenshot({path:target});
  const forward=crypto.createHash('sha256').update(await page.screenshot()).digest('hex');
  await page.evaluate(()=>window.__sourcePreviewSeek(2));await page.evaluate(()=>window.__sourcePreviewSeek(6));
  const backward=crypto.createHash('sha256').update(await page.screenshot()).digest('hex');
  row.seek_pixel_identical=forward===backward;if(!row.seek_pixel_identical)report.failures.push({scene:name,reason:'backward seek pixel drift'});
  row.preview={file:path.relative(out,target).replaceAll('\\','/'),sha256:sha(target),width:1920,height:1080,at_s:6,time_status:'PROVISIONAL'};
  row.runtime_errors=errors;if(errors.length)report.failures.push({scene:name,errors});page.off('pageerror',listener);report.scenes.push(row);
 }
 report.status=report.failures.length?'fail':'pass';
 fs.writeFileSync(path.join(__dirname,'bbox_preflight_v2.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,scenes:report.scenes.length,text_checks:report.scenes.reduce((s,r)=>s+r.samples.reduce((n,x)=>n+x.checked,0),0),findings:report.failures.length}));if(report.failures.length)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
