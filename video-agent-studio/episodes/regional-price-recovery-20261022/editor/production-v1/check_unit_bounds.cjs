// Local DOM geometry audit of the actual authored SVGs. No provider/network assets.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const ED=__dirname,EP=path.resolve(ED,'../..'),REPO=path.resolve(EP,'../../..');
const P=path.join(EP,'outputs/production-v1-jun/project'),C=path.join(EP,'outputs/production-v1-jun/checks/fix_req01');
const {chromium}=require(path.join(REPO,'tools/rea/node_modules/playwright-core'));
const findings=JSON.parse(fs.readFileSync(path.join(EP,'qa/production-v1/findings.json'),'utf8'));
const targets=findings.findings.find(f=>f.issue_id==='RPR-P1-REQ-01').evidence.affected_authored_beats;
const bm=JSON.parse(fs.readFileSync(path.join(P,'beat_manifest.json'),'utf8')).beats;
const host=fs.readFileSync(path.join(P,'index.html'),'utf8'),css=host.match(/<style>([\s\S]*?)<\/style>/)[1].replaceAll('url(assets/','url(/assets/');
const server=http.createServer((req,res)=>{
 try{const url=new URL(req.url,'http://127.0.0.1');
 if(url.pathname.startsWith('/fixture/')){
   const id=path.basename(url.pathname,'.html');if(!/^S\d{3}$/.test(id))throw Error('invalid scene');
   const src=fs.readFileSync(path.join(P,'compositions',id+'.html'),'utf8').match(/<template>([\s\S]*?)<\/template>/)[1];
   res.setHeader('content-type','text/html; charset=utf-8');res.end('<html><head><script>window.__timelines={}</script><script src="/assets/gsap.min.js"></script><style>'+css+'</style></head><body>'+src+'</body></html>');return;
 }
 const file=path.resolve(P,'.'+decodeURIComponent(url.pathname));if(!file.startsWith(P+path.sep))throw Error('outside project');
 res.setHeader('content-type',file.endsWith('.woff2')?'font/woff2':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');res.end(fs.readFileSync(file));
 }catch(e){res.statusCode=404;res.end(String(e.message))}
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-background-networking']});
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});const consoleErrors=[];
 await page.addInitScript(()=>{window.__timelines={}});
 page.on('pageerror',e=>consoleErrors.push(e.message));await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
 const results=[];
 try{
 for(const scene of [...new Set(targets.map(x=>x.split('-')[0]))]){
  await page.goto(origin+'/fixture/'+scene+'.html');await page.evaluate(async()=>{await document.fonts.load('400 21px Pretendard');await document.fonts.load('700 28px Pretendard');await document.fonts.ready});
  const sceneStart=bm.find(b=>b.scene_id===scene).start;
  for(const id of targets.filter(x=>x.startsWith(scene+'-'))){const beat=bm.find(x=>x.beat_id===id);
   for(const f of [.25,.5,.9]){
    const data=await page.evaluate(({id,scene,time})=>{
      for(const s of document.querySelectorAll('.rpr-beat'))s.style.display=s.id===id?'block':'none';
      window.__timelines[scene].seek(time,false);
      const svg=document.querySelector('#'+id+' svg'),texts=[...svg.querySelectorAll('text')].filter(x=>x.textContent.trim());
      const boxes=texts.map(el=>{const b=el.getBBox(),ctm=el.getScreenCTM(),stroke=getComputedStyle(el).stroke==='none'?0:parseFloat(getComputedStyle(el).strokeWidth)/2;const a=new DOMPoint(b.x-stroke,b.y-stroke).matrixTransform(ctm),z=new DOMPoint(b.x+b.width+stroke,b.y+b.height+stroke).matrixTransform(ctm);return {text:el.textContent,left:a.x,top:a.y,right:z.x,bottom:z.y,font:getComputedStyle(el).fontFamily}});
      const unit=boxes.find(b=>/^\d{4}Q\d=100$/.test(b.text));
      const overlaps=unit?boxes.filter(b=>b!==unit&&Math.min(b.right,unit.right)-Math.max(b.left,unit.left)>.5&&Math.min(b.bottom,unit.bottom)-Math.max(b.top,unit.top)>.5):[];
      return {unit,svg_text_count:boxes.length,outside:boxes.filter(b=>b.left<-.5||b.top<-.5||b.right>1920.5||b.bottom>1080.5),unit_overlaps:overlaps,title_has_index:boxes.some(b=>b.text.includes('자체 지수'))};
    },{id,scene,time:beat.start-sceneStart+(beat.end-beat.start)*f});
    if(!data.unit||!data.title_has_index||data.outside.length||data.unit_overlaps.length)throw Error(id+' '+JSON.stringify(data));
    results.push({beat_id:id,local_fraction:f,...data});
   }
  }
 }
 await page.goto(origin+'/preview/incheon2008-2016recovery.html');await page.evaluate(()=>document.fonts.ready);
 for(const t of [2,4,7]){
  const r=await page.evaluate(t=>{window.__timelines['incheon2008-2016recovery'].seek(t,false);const texts=[...document.querySelectorAll('svg text')].filter(e=>e.textContent.trim());const b=texts.map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent,left:r.left,top:r.top,right:r.right,bottom:r.bottom}});return {unit:b.find(e=>e.text==='2006Q1=100'),outside:b.filter(r=>r.left<-.5||r.top<-.5||r.right>1920.5||r.bottom>1080.5)}},t);
  if(!r.unit||r.outside.length)throw Error('preview bounds '+JSON.stringify(r));results.push({preview_seconds:t,...r});
 }
 const report={ok:true,method:'fonts-ready actual authored SVG getBBox + half stroke in 1920x1080 local Chrome; preview DOM at encoded sample times. Full-body fixture explicitly isolates each beat; not a new body render.',affected_beats:targets,scope:'12 episode price units and their annotation/readout boundaries; Incheon preview at2,4,7s',console_errors:consoleErrors,checks:results};
 if(consoleErrors.length)throw Error(consoleErrors.join('\n'));
 fs.writeFileSync(path.join(C,'text_bounds.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,affected_beats:targets.length,measurements:results.length,unit_bounds:results.at(-1).unit}));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
