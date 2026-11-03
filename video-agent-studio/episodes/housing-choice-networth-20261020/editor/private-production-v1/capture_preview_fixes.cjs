/* Only the three changed scenes and their exact measured cue anchors. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const destination=path.join(out,'preview_fixes');fs.mkdirSync(destination,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
 const wanted=[[2,'PVQA-003','s2g','2016년 2분기부터',1],[5,'PVQA-001','s5b','10년 동안 갚은 원금',.8],
 [8,'PVQA-002','s8h','집값 상승률만 바꿉니다',.5],[8,'PVQA-002','s8h','집값이 연 2%',.5],[8,'PVQA-002','s8h','연 4%로 바꾸면',.5],[8,'PVQA-002','s8h','연 6%라면',.5]];
 const report={status:'editor_fixes_ready_for_independent_recheck',timing_basis:'measured_audio_units',script_sha256:read(path.join(out,'render_plan.json')).script_sha256,frames:[],note:'0% overview focus is cued to the spoken instruction that only house growth changes; no new 0% narration is claimed.'};
 for(const [chapter,issue,scene,literal,off] of wanted){
  const project='ch'+String(chapter).padStart(2,'0'),f=path.join(out,project,'index.html'),a=read(path.join(out,project,'anchor_audit.json')).anchors;
  const anchor=a.find(r=>r.literal===literal);if(!anchor)throw new Error('Missing measured snapshot anchor '+literal);const t=anchor.time_s+off;
  await page.goto(pathToFileURL(f).href);await page.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
  await page.evaluate(t=>{window.__timelines.main.pause().time(t,false);for(const e of document.querySelectorAll('.clip'))e.style.visibility=t>=+e.dataset.start&&t<+e.dataset.start+(+e.dataset.duration)?'visible':'hidden';},t);
  const dest=path.join(destination,`${issue}_${project}_${scene}_${t.toFixed(2)}s.png`);await page.screenshot({path:dest});
  report.frames.push({issue_id:issue,chapter,scene_id:scene,anchor:literal,time_s:t,file:path.relative(out,dest).replaceAll('\\','/'),sha256:sha(dest),html_sha256:sha(f),cue_id:anchor.cue_id,cue_text:anchor.cue_text});
 }
 fs.writeFileSync(path.join(destination,'handoff.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({fix_frames:report.frames.length,path:path.join(destination,'handoff.json')}));
}finally{await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
