const fs=require('fs'),path=require('path'),crypto=require('crypto');const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v3');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
 const report={status:'pass',caption_timing_sha256:read(path.join(out,'render_plan.json')).caption_timing_sha256,cues:[],target_frames:[],failures:[]};
 const seek=async time=>page.evaluate(t=>{window.__timelines.main.pause().time(t,false);for(const el of document.querySelectorAll('.clip'))el.style.visibility=t>=+el.dataset.start&&t<+el.dataset.start+(+el.dataset.duration)?'visible':'hidden';},time);
 for(let chapter=1;chapter<=10;chapter++){
  const project='ch'+String(chapter).padStart(2,'0'),file=path.join(out,project,'index.html'),timing=read(path.join(out,project,'timing.json'));
  await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
  await page.evaluate(async()=>{await document.fonts.load('400 40px Pretendard');await document.fonts.ready;});
  for(let i=0;i<timing.cues.length;i++){
   const cue=timing.cues[i],time=(cue.start_s+cue.end_s)/2;await seek(time);
   const metric=await page.evaluate(i=>{const el=document.getElementById('cue'+String(i).padStart(3,'0'));const style=getComputedStyle(el),rects=[];
    const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n;while(n=walker.nextNode()){const range=document.createRange();range.selectNodeContents(n);for(const r of range.getClientRects())if(r.width>.1&&r.height>.1)rects.push({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height});}
    const lines=[];for(const r of rects){let line=lines.find(l=>Math.abs(l.top-r.top)<.5);if(!line)lines.push({...r});else{line.left=Math.min(line.left,r.left);line.right=Math.max(line.right,r.right);line.bottom=Math.max(line.bottom,r.bottom);line.width=line.right-line.left;}}
    return {font_size:style.fontSize,line_height:style.lineHeight,font_family:style.fontFamily,font_weight:style.fontWeight,lines};},i);
   const row={chapter,cue_id:cue.id,text:cue.text,display_lines:cue.display_lines||[cue.text],time_s:time,html_sha256:sha(file),...metric};report.cues.push(row);
   if(metric.font_size!=='40px'||metric.line_height!=='50px'||metric.lines.length!==row.display_lines.length||metric.lines.length>2||metric.lines.some(r=>r.width>1600.5||r.left<139.5||r.right>1780.5||r.top<875.5||r.bottom>1000.5))report.failures.push(row);
  }
 }
 report.max_line_width_px=Math.max(...report.cues.flatMap(c=>c.lines.map(r=>r.width)));
 report.min_glyph_top_px=Math.min(...report.cues.flatMap(c=>c.lines.map(r=>r.top)));report.max_glyph_bottom_px=Math.max(...report.cues.flatMap(c=>c.lines.map(r=>r.bottom)));
 const widest=report.cues.filter(r=>r.display_lines.length===2).sort((a,b)=>Math.max(...b.lines.map(l=>l.width))-Math.max(...a.lines.map(l=>l.width)))[0];
 const edl=read(path.join(out,'assembly_edl.json'));const globalToLocal=(chapter,time)=>time-edl.offset_map.find(o=>o.chapter===chapter&&time>=o.local_start_s+o.global_offset_s&&time<o.local_end_s+o.global_offset_s).global_offset_s;
 const targets=[{id:'C01_context',chapter:1,time:7.2},{id:'CH09_old_orphan_time',chapter:9,time:globalToLocal(9,1352.2)},{id:'CH10_old_orphan_time',chapter:10,time:globalToLocal(10,1467.4333333333334)},{id:'widest_two_line',chapter:widest.chapter,time:widest.time_s}];
 for(const target of targets){
  const project='ch'+String(target.chapter).padStart(2,'0'),file=path.join(out,project,'index.html'),timing=read(path.join(out,project,'timing.json'));
  await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');await seek(target.time);
  const cue=timing.cues.find(c=>target.time>=c.start_s&&target.time<c.end_s);const dest=path.join(out,'preview_captions',target.id+'.png');await page.screenshot({path:dest});
  report.target_frames.push({...target,cue_id:cue?.id,cue_text:cue?.text,file:path.relative(out,dest).replaceAll('\\','/'),sha256:sha(dest),html_sha256:sha(file)});
 }
 report.status=report.failures.length?'fail':'pass';fs.writeFileSync(path.join(__dirname,'caption_fit_metrics.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,cues:report.cues.length,max_line_width_px:report.max_line_width_px,min_glyph_top_px:report.min_glyph_top_px,max_glyph_bottom_px:report.max_glyph_bottom_px,target_frames:report.target_frames.length}));if(report.failures.length)process.exitCode=1;
}finally{await browser.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1});
