const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v2');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const norm=s=>s.replace(/\s/g,'');
(async()=>{
 const dest=path.join(out,'preview_delta');fs.mkdirSync(dest,{recursive:true});
 const report={status:'ready_for_independent_v6_delta_source_QA',script_sha256:read(path.join(out,'render_plan.json')).script_sha256,frames:[],
  input_revisions:{CLI_summary_sha256:sha(path.join(__dirname,'checks/summary.json')),BBox_report_sha256:sha(path.join(out,'preview/bbox_report.json')),mix_receipt_sha256:sha(path.join(__dirname,'mix_receipt.json'))},
  unchanged_visual_proof:'editor/private-production-v2/unchanged_visual_proof.json',scope:'two terminology changes; chapter 5/6 caption and timing. Prior three fixes retained. Remaining visual HTML/timing/assets invariant proof supplied.'};
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
  for(const [chapter,text] of [[5,'원금 상환의 효과는'],[6,'한국 돈으로 환산한 자산은']]){
   const ch='ch'+String(chapter).padStart(2,'0'),file=path.join(out,ch,'index.html'),timing=read(path.join(out,ch,'timing.json'));
   const cue=timing.cues.find(c=>norm(c.text).includes(norm(text)));if(!cue)throw new Error('No exact changed cue '+text);
   const time=(cue.start_s+cue.end_s)/2,scene=timing.scenes.find(s=>time>=s.start_s&&time<s.end_s);
   await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
   await page.evaluate(t=>{window.__timelines.main.pause().time(t,false);for(const el of document.querySelectorAll('.clip'))el.style.visibility=t>=+el.dataset.start&&t<+el.dataset.start+(+el.dataset.duration)?'visible':'hidden';},time);
   const target=path.join(dest,`${ch}_${scene.scene_id}_${time.toFixed(2)}s.png`);await page.screenshot({path:target});
   report.frames.push({chapter,scene_id:scene.scene_id,time_s:time,file:path.relative(out,target).replaceAll('\\','/'),sha256:sha(target),html_sha256:sha(file),cue_id:cue.id,cue_text:cue.text});
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(dest,'handoff.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1});
