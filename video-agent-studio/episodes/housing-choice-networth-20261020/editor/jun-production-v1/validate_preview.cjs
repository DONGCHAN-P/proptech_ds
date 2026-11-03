/* Local browser evidence only. No TTS, network assets, full render, or external call. */
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const {pathToFileURL}=require('url');
const episode=path.resolve(__dirname,'../..');
const workspace=path.resolve(episode,'../../..');
const out=path.join(episode,'outputs/jun-production-v1');
const {chromium}=require(path.join(workspace,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const preview=path.join(out,'preview');fs.mkdirSync(preview,{recursive:true});
const selected=new Set(['1:s1','1:s4','2:s2g','2:s2p','3:s3a','4:s4d','5:s5b','6:s6a','7:s7a','8:s8h','8:s8l','9:s9d','10:s10invest','10:s10stable','10:s10life','10:s10next']);
let browser;

async function inspect(page,time,bodyStart,bodyEnd){
 return page.evaluate(({time,bodyStart,bodyEnd})=>{
  const timeline=window.__timelines.main;
  timeline.pause().time(time,false);
  // Test harness emulates framework-owned .clip visibility; production timelines never own it.
  for(const el of document.querySelectorAll('.clip')){
   const st=+el.dataset.start, en=st+(+el.dataset.duration);
   el.style.visibility=(time>=st-1e-7&&time<en-1e-7)?'visible':'hidden';
  }
  const visible=el=>{let alpha=1;for(let n=el;n&&n.nodeType===1;n=n.parentElement){const s=getComputedStyle(n);if(s.visibility==='hidden'||s.display==='none')return false;alpha*=+s.opacity;}return alpha>.18;};
  const bounds=r=>({x:+r.x.toFixed(2),y:+r.y.toFixed(2),w:+r.width.toFixed(2),h:+r.height.toFixed(2)});
  const findings=[], texts=[];
  const walker=document.createTreeWalker(document.getElementById('root'),NodeFilter.SHOW_TEXT);
  let node;
  while(node=walker.nextNode()){
   if(!node.textContent.trim()||!visible(node.parentElement)||node.parentElement.closest('.card-art'))continue;
   const range=document.createRange();range.selectNodeContents(node);
   const rects=[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1);
   if(!rects.length)continue;
   const parent=node.parentElement;
   let owner=parent.closest('[id]');
   const id=owner?owner.id:parent.tagName;
   for(const r of rects){
    texts.push({id,text:node.textContent.trim(),bbox:bounds(r)});
    if(r.left<-2||r.top<-2||r.right>1922||r.bottom>1082)findings.push({kind:'glyph_outside_canvas',id,text:node.textContent.trim(),bbox:bounds(r)});
    // Exact glyph Range rectangles against every clipping panel, including stroke allowance.
    for(let p=parent;p&&p.id!=='root';p=p.parentElement){
     const style=getComputedStyle(p),b=p.getBoundingClientRect();
     const clip=['hidden','clip','scroll','auto'].includes(style.overflowX)||['hidden','clip','scroll','auto'].includes(style.overflowY);
     const explicit=p.matches('.pnl,.panel,.box,.card,.pill,.rowpill,.frow,.cue,.source,.title,.val,.hd');
     if((clip||explicit)&&b.width>0&&b.height>0&&(r.left<b.left-2||r.right>b.right+2||r.top<b.top-2||r.bottom>b.bottom+2)){
      findings.push({kind:clip?'panel_clips_glyph':'glyph_outside_text_container',id,text:node.textContent.trim(),bbox:bounds(r),container:p.id||p.className,container_bbox:bounds(b)});break;
     }
    }
   }
  }
  // Chart path and point geometry against the clipping panel. Include half stroke width.
  for(const el of document.querySelectorAll('svg path,svg circle,svg line')){
   if(!visible(el)||el.closest('.card-art'))continue;
   const p=el.closest('.pnl,.panel');if(!p)continue;
   const b=p.getBoundingClientRect(),r=el.getBoundingClientRect(),sw=(parseFloat(getComputedStyle(el).strokeWidth)||0)/2;
   if(r.left-sw<b.left-2||r.right+sw>b.right+2||r.top-sw<b.top-2||r.bottom+sw>b.bottom+2)findings.push({kind:'panel_clips_svg_stroke',id:el.id,bbox:bounds(r),container:p.id});
  }
  const box=document.getElementById('capbox');
  for(const caption of document.querySelectorAll('.cue')){
   if(!visible(caption))continue;
   const glyphs=[],cw=document.createTreeWalker(caption,NodeFilter.SHOW_TEXT);let cn;
   while(cn=cw.nextNode()){const r=document.createRange();r.selectNodeContents(cn);glyphs.push(...[...r.getClientRects()].filter(b=>b.width>.1&&b.height>.1));}
   const ys=[];for(const g of glyphs)if(!ys.some(y=>Math.abs(y-g.top)<.5))ys.push(g.top);
   const explicit=(caption.querySelector('.caption-lines')?.textContent||'').split('\n').length;
   if(ys.length>2||ys.length>explicit)findings.push({kind:'caption_unplanned_wrap_or_excess_lines',id:caption.id,actual_lines:ys.length,explicit_lines:explicit});
   if(glyphs.some(g=>g.width>1600.5))findings.push({kind:'caption_line_exceeds_1600px',id:caption.id,width:Math.max(...glyphs.map(g=>g.width))});
  }
  if(time>=bodyStart&&time<bodyEnd&&(!box||!visible(box)))findings.push({kind:'missing_persistent_caption_box',time});
  const title=document.querySelectorAll('.title');
  for(const el of document.querySelectorAll('.source,.cue')){
   if(!visible(el))continue;
   const r=el.getBoundingClientRect();
   if(el.matches('.source')&&r.top<1008)findings.push({kind:'source_caption_separation',id:el.id});
  }
  return {findings,texts,captionVisible:box&&visible(box),timelineDuration:timeline.duration()};
 },{time,bodyStart,bodyEnd});
}

(async()=>{
 const plan=read(path.join(out,'render_plan.json'));
 const snapshots=read(path.join(out,'snapshot_times.json')).samples;
 const changes=read(path.join(out,'cue_change_groups.json')).groups;
 const captionPreview=path.join(out,'preview_captions');fs.mkdirSync(captionPreview,{recursive:true});
 const chapterFilter=process.env.PREVIEW_CHAPTERS?new Set(process.env.PREVIEW_CHAPTERS.split(',').map(Number)):null;
 const previous=chapterFilter?read(path.join(preview,'bbox_report.json')):null;
 browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--allow-file-access-from-files','--disable-background-networking']});
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const report={scope:'headless Chrome sampled DOM/glyph BBox and static PNG; no continuous playback, audio listening or encoded media review',
  timing_basis:plan.status,script_sha256:plan.script_sha256,tool:{playwright:require(path.join(workspace,'tools/rea/node_modules/playwright-core/package.json')).version,chrome:browser.version()},
  checked_chapters:[],errors:[],findings:[],snapshots:[],changed_caption_snapshots:[],external_requests:[],longest_labels:[],seek_safe_checks:[],motion_windows:[]};
 await page.route(/^https?:\/\//,r=>{report.external_requests.push(r.request().url());return r.abort();});
 let active=0;
 page.on('pageerror',e=>report.errors.push({chapter:active,error:e.message}));
 page.on('console',m=>{if(m.type()==='warning'&&/GSAP|target.*not found/i.test(m.text()))report.errors.push({chapter:active,error:m.text()});});
 for(const ch of plan.chapters){
  active=ch.chapter;
  const file=path.join(out,ch.project,'index.html');
  const timing=read(path.join(out,ch.project,'timing.json'));
  if(chapterFilter&&!chapterFilter.has(active)){
   const prior=previous.checked_chapters.find(c=>c.chapter===active);
   if(!prior||prior.html_sha256!==sha(file)||prior.timing_sha256!==sha(path.join(out,ch.project,'timing.json')))throw new Error('Cannot reuse changed chapter '+active);
   report.checked_chapters.push({...prior,evidence_reused_from_script_sha256:previous.script_sha256});
   for(const key of ['errors','findings','snapshots','longest_labels','seek_safe_checks','motion_windows'])report[key].push(...previous[key].filter(r=>r.chapter===active));
   continue;
  }
  await page.goto(pathToFileURL(file).href);
  await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded',null,{timeout:5000});
  await page.evaluate(async()=>{await Promise.all([400,600,700,800].map(w=>document.fonts.load(`${w} 32px Pretendard`)));await document.fonts.ready;});
  const data=await page.evaluate(()=>({fonts:[...document.fonts].map(f=>({family:f.family,status:f.status,weight:f.weight})),paused:window.__timelines.main.paused(),images:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)}));
  if(data.fonts.some(f=>f.status!=='loaded')||!data.paused||data.images.length)report.errors.push({chapter:active,error:'font/image/timeline readiness',data});
  const bodyStart=ch.chapter===1?0:3,bodyEnd=ch.chapter===10?ch.last_speech_end_s:ch.total_seconds;
  const rows=snapshots.filter(s=>s.chapter===active);
  const motion=await page.evaluate(()=>{
   const issues=[];
   for(const tween of window.__timelines.main.getChildren(false,true,false)){
    if(tween.duration()===0)continue; // initial states at t=0 are deliberately outside later scenes.
    for(const target of tween.targets()){
     if(!(target instanceof Element))continue;
     const scene=target.closest('.scene.clip');if(!scene)continue;
     const st=+scene.dataset.start,en=st+(+scene.dataset.duration),a=tween.startTime(),b=a+tween.totalDuration();
     if(a<st-1/30||b>en+1/30)issues.push({scene_id:scene.id,target:target.id||target.className,start_s:a,end_s:b,scene_start_s:st,scene_end_s:en});
    }
   }
   return issues;
  });
  report.motion_windows.push({chapter:active,clipped_tweens:motion});
  const seekTime=rows[Math.floor(rows.length/2)].representative_s;
  await inspect(page,seekTime,bodyStart,bodyEnd);
  const pixels1=await page.screenshot();
  await inspect(page,Math.min(ch.total_seconds-1/30,seekTime+6),bodyStart,bodyEnd);
  await inspect(page,seekTime,bodyStart,bodyEnd);
  const pixels2=await page.screenshot();
  const equal=crypto.createHash('sha256').update(pixels1).digest('hex')===crypto.createHash('sha256').update(pixels2).digest('hex');
  report.seek_safe_checks.push({chapter:active,time_s:seekTime,backward_seek_pixel_identical:equal});
  if(!equal)report.errors.push({chapter:active,error:'non-deterministic backward seek'});
  const times=new Set(rows.flatMap(s=>[s.representative_s,s.before_end_s,s.after_start_s]));
  // Every cue midpoint checks actual long captions, and both sides of each gap checks continuity.
  for(const cue of timing.cues){times.add((cue.start_s+cue.end_s)/2);times.add(Math.max(bodyStart,cue.start_s-1/30));times.add(Math.min(bodyEnd-1/30,cue.end_s+1/30));}
  const audits=read(path.join(out,ch.project,'anchor_audit.json')).anchors;
  for(const a of audits)times.add(Math.min(ch.total_seconds-1/30,a.time_s+.45));
  const samples=[];
  let textcount=0;
  for(const time of [...times].sort((a,b)=>a-b)){
   const r=await inspect(page,time,bodyStart,bodyEnd);textcount+=r.texts.length;
   for(const finding of r.findings)report.findings.push({chapter:active,time_s:+time.toFixed(6),...finding});
   samples.push({time_s:+time.toFixed(6),text_count:r.texts.length,caption_box_visible:r.captionVisible});
  }
  const labels=await page.evaluate(()=>[...document.querySelectorAll('.tx,.pill,.ml,.cardtitle,.title,.k,.s,.v')].filter(e=>!e.closest('.card-art')).map(e=>({id:e.id||e.parentElement.id,text:e.textContent.trim(),length:e.textContent.trim().length})).sort((a,b)=>b.length-a.length).slice(0,8));
  report.longest_labels.push({chapter:active,labels});
  for(const s of rows){
   // Every scene representative is captured for the new Jun clock.
   await inspect(page,s.representative_s,bodyStart,bodyEnd);
   const dest=path.join(preview,`ch${String(active).padStart(2,'0')}_${s.scene_id}_${s.representative_s.toFixed(2)}s.png`);
   await page.screenshot({path:dest});
   report.snapshots.push({chapter:active,scene_id:s.scene_id,time_s:s.representative_s,file:path.relative(out,dest).replaceAll('\\','/'),sha256:sha(dest)});
  }
  report.checked_chapters.push({chapter:active,html_sha256:sha(file),timing_sha256:sha(path.join(out,ch.project,'timing.json')),fonts:data.fonts,paused:data.paused,samples,text_checks:textcount});
  for(const group of changes.filter(g=>g.chapter===active)){
   for(const cue of group.new_cues){
    const time=(cue.start_s+cue.end_s)/2;
    await inspect(page,time,bodyStart,bodyEnd);
    const dest=path.join(captionPreview,`${group.group_id}_${cue.id}.png`);await page.screenshot({path:dest});
    report.changed_caption_snapshots.push({group_id:group.group_id,chapter:active,cue_id:cue.id,text:cue.text,display_lines:cue.display_lines||[cue.text],time_s:time,file:path.relative(out,dest).replaceAll('\\','/'),sha256:sha(dest),html_sha256:sha(file)});
   }
  }
 }
 await browser.close();
 const collapsed=new Map();
 for(const f of report.findings){const key=JSON.stringify([f.chapter,f.kind,f.id,f.text,f.container]);if(!collapsed.has(key))collapsed.set(key,{...f,observed_count:0});collapsed.get(key).observed_count++;}
 report.findings=[...collapsed.values()];
 report.status=report.errors.length||report.findings.length||report.external_requests.length?'findings_require_review':'sampled_bbox_pass';
 fs.writeFileSync(path.join(preview,'bbox_report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({status:report.status,chapters:report.checked_chapters.length,samples:report.checked_chapters.reduce((a,c)=>a+c.samples.length,0),text_checks:report.checked_chapters.reduce((a,c)=>a+c.text_checks,0),findings:report.findings.length,errors:report.errors.length,pngs:report.snapshots.length}));
 if(report.status!=='sampled_bbox_pass')process.exitCode=1;
})().catch(async e=>{if(browser)await browser.close();fs.writeFileSync(path.join(preview,'browser_failure.json'),JSON.stringify({error:e.stack},null,2));console.error(e.message);process.exitCode=1;});
