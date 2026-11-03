/* 실제 채널 WOFF2와 CSS로 150개 의미큐의 전량 글리프 기하를 검사한다.
   검수 harness이며 본편 source-frame/encoded-frame 통과 근거로 사용하지 않는다. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const qa=__dirname,root=path.resolve(qa,'../../../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const packet=JSON.parse(fs.readFileSync(path.join(qa,'caption_packet.json'),'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
  await page.route(/^https?:\/\//,r=>r.abort());
  const cssURL=pathToFileURL(packet.css_path).href;
  const html='<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="'+cssURL+'"><div id="root"><div id="capbox" class="abs"></div><div class="cue" style="opacity:1"><span class="caption-lines"></span></div></div>';
  const harness=path.join(qa,'caption_harness.html');fs.writeFileSync(harness,html);
  await page.goto(pathToFileURL(harness).href);
  await page.evaluate(async()=>{await document.fonts.load('400 40px Pretendard');await document.fonts.ready});
  const rows=[];
  for(const cue of packet.cues){
   const row=await page.evaluate(cue=>{
    const el=document.querySelector('.cue'),span=document.querySelector('.caption-lines');span.textContent=cue.display_lines.join('\n');
    const style=getComputedStyle(el),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=style.fontWeight+' '+style.fontSize+' '+style.fontFamily;
    const r=span.getBoundingClientRect(),rect={left:r.left,right:r.right,top:r.top,bottom:r.bottom};
    const range=document.createRange();range.selectNodeContents(span);const rects=[...range.getClientRects()].filter(r=>r.width>.1&&r.height>.1).map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}));
    const lines=cue.display_lines.map(text=>{const m=ctx.measureText(text);return {text,width:m.width,actualBoundingBoxLeft:m.actualBoundingBoxLeft,actualBoundingBoxRight:m.actualBoundingBoxRight,inkAscent:m.actualBoundingBoxAscent,inkDescent:m.actualBoundingBoxDescent}});
    const bad=[];
    if(!document.fonts.check('400 40px Pretendard'))bad.push('font_not_loaded');
    if(style.fontSize!=='40px'||style.lineHeight!=='50px'||style.fontWeight!=='400')bad.push('font_contract');
    if(cue.display_lines.length>2||lines.some(l=>l.width>1600.5))bad.push('line_limit');
    if(rects.some(b=>b.left<139.5||b.right>1780.5||b.top<875.5||b.bottom>1000.5))bad.push('glyph_container_clipped');
    if(lines.some(l=>l.inkAscent+l.inkDescent>50.5))bad.push('ink_exceeds_lineheight');
    return {cue_id:cue.id,scene_id:cue.scene_id,chapter:cue.chapter,start_s:cue.start_s,end_s:cue.end_s,lines,range_rects:rects,span_rect:rect,font:style.font,computed_font_family:style.fontFamily,font_loaded:document.fonts.check('400 40px Pretendard'),bad};
   },cue);rows.push(row);
  }
  const longest=[...rows].sort((a,b)=>Math.max(...b.lines.map(l=>l.width))-Math.max(...a.lines.map(l=>l.width))).slice(0,4);
  fs.mkdirSync(path.join(qa,'caption-harness-frames'),{recursive:true});
  const frames=[];
  for(const row of longest){const cue=packet.cues.find(c=>c.id===row.cue_id);await page.evaluate(c=>document.querySelector('.caption-lines').textContent=c.display_lines.join('\n'),cue);const p=path.join(qa,'caption-harness-frames',cue.id+'.png');await page.screenshot({path:p});frames.push({cue_id:cue.id,path:p,sha256:sha(p),kind:'isolated_font_harness_not_source_or_encoded_frame'});}
  const report={status:rows.some(r=>r.bad.length)?'fail':'pass',scope:'150큐 실제CSS/WOFF2격리harness 글리프기하검사.본문45소스/MP4프레임검수아님.',script_sha256:packet.script_sha256,timing_sha256:packet.timing_sha256,css_sha256:packet.css_sha256,css_unchanged:sha(packet.css_path)===packet.css_sha256,cues:rows.length,failures:rows.filter(r=>r.bad.length),max_line_width_px:Math.max(...rows.flatMap(r=>r.lines.map(l=>l.width))),rows,frames,actual_listening:false,continuous_playback:false};
  fs.writeFileSync(path.join(qa,'caption_glyph_review.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,cues:report.cues,failed:report.failures.length,max_line_width_px:report.max_line_width_px,css_unchanged:report.css_unchanged}));
  if(report.status!=='pass'||!report.css_unchanged)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
