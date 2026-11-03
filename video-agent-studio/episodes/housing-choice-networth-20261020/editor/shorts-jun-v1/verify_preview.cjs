/* Offline native-portrait source inspection; not encoded-MP4 or listening approval. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

async function seek(page,time){
 return page.evaluate(time=>{
  window.__timelines.main.pause().time(time,false);
  for(const el of document.querySelectorAll('.clip')){
   const start=+el.dataset.start,end=start+(+el.dataset.duration);
   el.style.visibility=time>=start-1e-7&&time<end-1e-7?'visible':'hidden';
  }
  const visible=e=>{for(let n=e;n&&n.nodeType===1;n=n.parentElement){let c=getComputedStyle(n);if(c.visibility==='hidden'||c.display==='none'||+c.opacity<.1)return false;}return true;};
  const elements=[],failures=[];
  const walker=document.createTreeWalker(document.getElementById('root'),NodeFilter.SHOW_TEXT);
  let node;
  while(node=walker.nextNode()){
   if(!node.textContent.trim()||!visible(node.parentElement)||node.parentElement.closest('script,style'))continue;
   const parent=node.parentElement,owner=parent.closest('[data-kind]');
   if(!owner)continue;
   const range=document.createRange();range.selectNodeContents(node);
   const size=parseFloat(getComputedStyle(parent).fontSize),kind=owner.dataset.kind;
   for(const r of range.getClientRects()){
    if(!r.width||!r.height)continue;
    const row={kind,text:node.textContent.trim(),font_px:size,bbox:[r.left,r.top,r.right,r.bottom].map(x=>+x.toFixed(4)),time_s:time};elements.push(row);
    if(r.left<139.5||r.top<259.5||r.right>840.5||r.bottom>1360.5)failures.push({...row,reason:'critical_text_outside_safe_rect'});
    for(let p=parent;p&&p.id!=='root';p=p.parentElement){
     const c=getComputedStyle(p),b=p.getBoundingClientRect();
     if(['hidden','clip'].includes(c.overflowX)||['hidden','clip'].includes(c.overflowY)){
      if(r.left<b.left-.5||r.top<b.top-.5||r.right>b.right+.5||r.bottom>b.bottom+.5)failures.push({...row,reason:'clipping_ancestor',ancestor:p.className});
     }
    }
   }
  }
  return {elements,failures,visibleScene:document.querySelector('.scene[style*="visible"]')?.id};
 },time);
}

(async()=>{
 let browser;
 try{
  browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--allow-file-access-from-files','--disable-background-networking']});
  const results=[];
  for(const ident of ['funnel','analysis']){
   const dest=path.join(ep,'outputs/shorts-jun-v1',ident),pre=path.join(dest,'preview');fs.mkdirSync(pre,{recursive:true});
   const timing=read(path.join(dest,'timing.json')),scenes=read(path.join(dest,'scenes.json')).scenes,anchors=read(path.join(dest,'anchor_audit.json')).anchors;
   const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1}),errors=[],external=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route(/^https?:\/\//,r=>{external.push(r.request().url());return r.abort();});
   await page.goto(pathToFileURL(path.join(dest,'index.html')).href);
   await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
   await page.evaluate(async()=>{await Promise.all([400,700,800].map(w=>document.fonts.load(`${w} 54px Pretendard`)));await document.fonts.ready;});
   const fonts=await page.evaluate(()=>[...document.fonts].map(f=>({family:f.family,weight:f.weight,status:f.status})));
   if(fonts.some(f=>f.status!=='loaded'))errors.push('font not loaded');
   const times=new Set();
   for(const s of scenes){times.add((s.start_s+s.end_s)/2);times.add(Math.min(s.end_s-1/30,s.start_s+.8));times.add(s.end_s-1/30);}
   for(const q of timing.cues){times.add((q.start_s+q.end_s)/2);times.add(Math.min(timing.duration_s-1/30,q.end_s+1/30));}
   for(const a of anchors)times.add(a.time_s+.6);
   const elements=[],failures=[];
   for(const time of [...times].sort((a,b)=>a-b)){const r=await seek(page,time);elements.push(...r.elements);failures.push(...r.failures);}
   const shots=[];
   for(const s of scenes){const time=(s.start_s+s.end_s)/2;await seek(page,time);const file=path.join(pre,`${s.id}.png`);await page.screenshot({path:file});shots.push({scene_id:s.id,time_s:time,file:path.relative(ep,file),sha256:hash(file)});}
   const mid=timing.duration_s*.52;
   await seek(page,mid);const a=await page.screenshot();await seek(page,1);await seek(page,timing.duration_s-1/30);await seek(page,mid);const b=await page.screenshot();
   const seekSafe=crypto.createHash('sha256').update(a).digest('hex')===crypto.createHash('sha256').update(b).digest('hex');
   if(!seekSafe)errors.push('backward seek differs');
   // Platform UI simulation for inspection; no claim of actual mobile playback.
   await seek(page,scenes[Math.floor(scenes.length/2)].start_s+.8);
   await page.evaluate(()=>{for(const [left,top,width,height,label] of [[0,0,1080,240,'HEADER'],[0,1400,1080,520,'FOOTER'],[900,240,180,1160,'ACTIONS']]){const x=document.createElement('div');x.style.cssText=`position:absolute;z-index:100;left:${left}px;top:${top}px;width:${width}px;height:${height}px;background:#17334899;color:#f6f4ef;font-size:36px;`;x.textContent=label;document.getElementById('root').appendChild(x);}});
   await page.screenshot({path:path.join(pre,'modeled_youtube_ui.png')});
   const report={status:failures.length||errors.length?'failed':'source_preview_bbox_pass',scope:'source samples and modeled UI; no final MP4/no actual listening',profile:'youtube_portrait_full_frame_v2',safe_rect:[140,260,840,1360],html_sha256:hash(path.join(dest,'index.html')),audio_sha256:hash(path.join(dest,'assets/narration.wav')),fonts,sample_times:[...times],elements,failures,errors,external_requests:external,backward_seek_pixel_identical:seekSafe,snapshots:shots};
   fs.writeFileSync(path.join(pre,'bbox_report.json'),JSON.stringify(report,null,2)+'\n');
   results.push({id:ident,status:report.status,text_checks:elements.length,failures:failures.length,errors,shots:shots.length,examples:failures.slice(0,16)});await page.close();
  }
  fs.writeFileSync(path.join(__dirname,'preview_receipt.json'),JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results));
  if(results.some(r=>r.status==='failed'))process.exitCode=1;
 }finally{if(browser)await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
