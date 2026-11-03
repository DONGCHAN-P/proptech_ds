const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const qa=__dirname,ep=path.resolve(qa,'../..'),root=path.resolve(qa,'../../../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const metrics=JSON.parse(fs.readFileSync(path.join(qa,'actual_source_metrics_v2.json'),'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});const frames=[];
try{const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
for(const [chapter,time,scene,kind] of [[1,23.033333333333335,'S001','brand_resume_source'],[1,23.066666666666666,'S001','brand_resume_plus1'],[7,152.947208,'S031','one_month_focus']]){
const file=path.join(out,'ch'+String(chapter).padStart(2,'0'),'index.html'),hash=sha(file),old=metrics.chapters.find(c=>c.chapter===chapter);
if(hash!==old.html_sha256){frames.push({chapter,time_s:time,status:'source_changed_capture_skipped',expected:old.html_sha256,actual:hash});continue;}
await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__sourceSeek&&document.fonts.status==='loaded');await page.evaluate(async()=>{for(const w of [400,600,700,800])await document.fonts.load(w+' 40px Pretendard');await document.fonts.ready});await page.evaluate(t=>window.__sourceSeek(t),time);
const actual=await page.evaluate(()=>({scenes:[...document.querySelectorAll('.scene-panel')].filter(e=>getComputedStyle(e).visibility!=='hidden').map(e=>e.id),cue:[...document.querySelectorAll('.cue')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.5).map(e=>e.textContent)}));
const p=path.join(qa,'actual-source-v2-frames',`ch${String(chapter).padStart(2,'0')}_${scene}_${kind}.png`);await page.screenshot({path:p});frames.push({chapter,time_s:time,scene_id:scene,kind,path:p,sha256:sha(p),html_sha256:hash,...actual});}
fs.writeFileSync(path.join(qa,'candidate_source_frames_v2.json'),JSON.stringify({frames},null,2)+'\n');console.log(JSON.stringify(frames));
}finally{await browser.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
