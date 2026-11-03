/* Render-source regression: content presence, raw timeline seeks, backward seek. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const root=path.resolve(__dirname,'../../../../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{
 const run=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
 if(!out.includes(path.join('outputs','rebuild-v2')))throw Error('Only assigned output writes');
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const report={status:'pass',cases:[],failures:[],actual_encoded_frames:false};
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});
  await page.route(/^https?:\/\//,r=>r.abort());
  for(const sid of process.argv.slice(4)){
   const folder=path.join(run,'scenes',sid),model=JSON.parse(fs.readFileSync(path.join(folder,'scene.json'),'utf8'));
   await page.goto(pathToFileURL(path.join(folder,'index.html')).href);
   await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
   const row={scene_id:sid,opening:model.opening_context,samples:[]};
   const end=model.opening_context?.end_s;
   const times=end===undefined?[0,7,15,0,7]:[0,Math.min(7,end/2),end+0.4,0,Math.min(7,end/2)];
   for(const [i,t] of times.entries()){
    await page.evaluate(t=>{window.__timelines.main.pause().time(t,true);},t);
    const metric=await page.evaluate(()=>{
     const opacity=e=>{let a=1;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);if(s.visibility==='hidden'||s.display==='none')return 0;a*=Number(s.opacity);}return a;};
     const el=document.getElementById('opening-context');
     return {time:window.__timelines.main.time(),opening_exists:!!el,opening_opacity:el?opacity(el):null,visible_inputs:[...document.querySelectorAll('[id^="opening-node-"]')].filter(e=>opacity(e)>.99).map(e=>e.textContent),visible_semantics:[...document.querySelectorAll('.semantic')].filter(e=>opacity(e)>.01).map(e=>e.id)};
    });
    const expect=end!==undefined&&t<end;
    if((expect&&(metric.opening_opacity<.99||metric.visible_inputs.length!==3))||(!expect&&metric.opening_opacity>.01))report.failures.push({scene_id:sid,requested_time_s:t,expected_opening:expect,...metric});
    const file=path.join(out,`${sid}-${i}.png`);await page.screenshot({path:file});row.samples.push({requested_time_s:t,...metric,screenshot:file});
   }
   report.cases.push(row);
  }
 }finally{await browser.close();}
 report.status=report.failures.length?'fail':'pass';fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 if(report.failures.length)process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
