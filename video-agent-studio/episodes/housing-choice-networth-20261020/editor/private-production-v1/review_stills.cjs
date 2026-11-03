/* Late settled views complement cue-midpoint checks for human numerical review. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/private-production-v1');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1}),shots=[];
 await p.route(/^https?:\/\//,r=>r.abort());
 for(const [n,sid] of [[6,'s6a'],[7,'s7a'],[9,'s9d'],[10,'s10next'],[2,'chapter_card'],[8,'chapter_card']]){
  const project='ch'+String(n).padStart(2,'0'),f=path.join(out,project,'index.html'),timing=JSON.parse(fs.readFileSync(path.join(out,project,'timing.json'),'utf8'));
  const scene=timing.scenes.find(s=>s.scene_id===sid);
  const time=sid==='chapter_card'?1.5:(sid==='s10next'||sid==='s9d'?timing.last_speech_end_s-.2:scene.end_s-.45);
  await p.goto(pathToFileURL(f).href);await p.waitForFunction(()=>window.__timelines?.main&&document.fonts.status==='loaded');
  await p.evaluate(t=>{window.__timelines.main.pause().time(t,false);for(const e of document.querySelectorAll('.clip'))e.style.visibility=t>=+e.dataset.start&&t<+e.dataset.start+(+e.dataset.duration)?'visible':'hidden';},time);
  const target=path.join(out,'preview',`${project}_${sid}_settled_${time.toFixed(2)}s.png`);await p.screenshot({path:target});
  shots.push({chapter:n,scene_id:sid,time_s:time,file:path.relative(out,target).replaceAll('\\','/'),sha256:sha(target),html_sha256:sha(f)});
 }
 fs.writeFileSync(path.join(out,'preview/review_stills.json'),JSON.stringify({scope:'late settled source preview PNG for human QA; no encoded video or listening',shots},null,2)+'\n');console.log(JSON.stringify({settled_pngs:shots.length}));
}finally{await b.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
