const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const q=__dirname,root=path.resolve(q,'../../../../..');const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const data=read(path.join(q,'targeted_static_v4.json')),plan=read(path.join(q,'targeted_recheck_plan.json'));
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const report={status:'in_progress',checks:[],frames:[],html_sha256:{},scope:'3개변경장·브랜드경계와S031/S040해당큐만.45대표재검사없음.',actual_encoded_frames:false,actual_listening:false,continuous_playback:false};
const check=(name,pass,details)=>{report.checks.push({check:name,passed:!!pass,details});if(!pass)throw Error(name)};
const dir=path.join(q,'targeted-visual-v4-frames');fs.mkdirSync(dir,{recursive:true});
try{const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
for(const ch of [1,7,9]){const c=data.chapters.find(c=>c.chapter===ch),file=c.path;check('검수전HTML_SHA_CH'+ch,sha(file)===c.postcarve_html_sha256);report.html_sha256['ch'+String(ch).padStart(2,'0')]=sha(file);
await page.goto(pathToFileURL(file).href);await page.waitForFunction(()=>window.__sourceSeek&&document.fonts.status==='loaded');await page.evaluate(async()=>{for(const w of [400,600,700,800])await document.fonts.load(w+' 40px Pretendard');await document.fonts.ready});
const samples=[];
if(ch===1){for(const t of plan.brand.source_frame_samples_s)samples.push({time:t,kind:'brand_boundary'});}
else for(const cue of c.cues.filter(c=>c.scene_id===(ch===7?'S031':'S040'))){samples.push({time:(cue.start_s+cue.end_s)/2,kind:'focus',cue});for(const t of [cue.start_s-.001,cue.start_s+.15,cue.end_s+.001])samples.push({time:t,kind:'cue_boundary',cue});}
for(const sample of samples){await page.evaluate(t=>window.__sourceSeek(t),sample.time);
const actual=await page.evaluate(()=>{const visible=e=>getComputedStyle(e).visibility!=='hidden'&&+getComputedStyle(e).opacity>.01;const label=e=>{let next=e.nextElementSibling;while(next&&next.tagName.toLowerCase()!=='text')next=next.nextElementSibling;return next?.textContent};return {scenes:[...document.querySelectorAll('.scene-panel')].filter(visible).map(e=>e.id),cue:[...document.querySelectorAll('.cue')].filter(visible).map(e=>e.textContent),capbox:visible(document.getElementById('capbox')),active_text_rings:[...document.querySelectorAll('.native-word-focus')].filter(visible).filter(e=>visible(e.closest('section'))).map(label),active_group_rings:[...document.querySelectorAll('.focus-ring')].filter(visible).filter(e=>visible(e.closest('section'))).map(e=>e.parentElement.id)};});
const expected=c.cues.filter(x=>x.start_s<=sample.time&&sample.time<x.end_s).map(x=>x.display_lines.join('\n'));
check('실제큐경계_CH'+ch+'_'+sample.time,JSON.stringify(actual.cue)===JSON.stringify(expected),actual);
check('본문흰박스_CH'+ch+'_'+sample.time,actual.capbox,actual);
if(ch===1)check('브랜드후장면선택_'+sample.time,JSON.stringify(actual.scenes)===JSON.stringify([sample.time<plan.brand.hook_cut_s?'S001':'S002']),actual);
if(sample.kind==='focus'){
 const exp=plan.focus_expected[sample.cue.id];
 if(exp){check('의미라벨포함_'+sample.cue.id,exp.include.every(t=>actual.active_text_rings.includes(t)),actual);check('다른측정값강조제외_'+sample.cue.id,exp.exclude.every(t=>!actual.active_text_rings.some(x=>x?.includes(t))),actual);}
 if(sample.cue.id==='C07_S031Q002')check('디딤돌그룹만',JSON.stringify(actual.active_group_rings)===JSON.stringify(['S031_didim']),actual);
 if(sample.cue.id==='C07_S031Q003')check('보금자리그룹만',JSON.stringify(actual.active_group_rings)===JSON.stringify(['S031_bogeum']),actual);
}
if(sample.kind==='focus'||(ch===1&&[plan.brand.hook_cut_s-1/30,plan.brand.hook_cut_s,plan.brand.hook_cut_s+1/30].some(t=>Math.abs(t-sample.time)<1e-7))){const name=ch===1?'brand_'+sample.time.toFixed(6):sample.cue.id;const p=path.join(dir,name+'.png');await page.screenshot({path:p});report.frames.push({chapter:ch,cue_id:sample.cue?.id,kind:sample.kind,time_s:sample.time,path:p,sha256:sha(p),html_sha256:c.postcarve_html_sha256,actual});}
}
check('검수중HTML불변_CH'+ch,sha(file)===c.postcarve_html_sha256);
}
report.status='pass';fs.writeFileSync(path.join(q,'targeted_focus_brand_v4.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,frames:report.frames.length,chapters:Object.keys(report.html_sha256)}));
}finally{await browser.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
