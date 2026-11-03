const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'..'),root=path.resolve(ep,'../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{
 fs.mkdirSync(__dirname,{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const issues=[],states=[];const times=[0,1,2.4,7,12,18,19,22.96,23,23.04,25.96,26,29.9667];
 try{const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
 await page.route(/^https?:\/\//,r=>r.abort());await page.goto(pathToFileURL(path.join(ep,'editor/project/index.html')).href);await page.evaluate(()=>document.fonts.ready);
 for(let frame=0;frame<900;frame++){
  const time=frame/30;
  const result=await page.evaluate(t=>{
   window.__sourceSeek(t);const visible=e=>{let p=e;while(p){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||+s.opacity<.02)return false;p=p.parentElement;}return true;};
   const errors=[];for(const e of document.querySelectorAll('.measure')){if(!visible(e))continue;const range=document.createRange();range.selectNodeContents(e);const b=range.getBoundingClientRect();if(b.left<139||b.top<259||b.right>841||b.bottom>1361)errors.push({text:e.textContent,b:{left:b.left,top:b.top,right:b.right,bottom:b.bottom}});}
   return {time:t,state:window.__frameState,errors};
  },time);
  if(result.errors.length)issues.push(result);
  if(frame%30===0||frame===899)states.push(result.state);
 }
 for(const t of times){await page.evaluate(t=>window.__sourceSeek(t),t);await page.screenshot({path:path.join(__dirname,'source_'+String(t).replace('.','_')+'.png')});}
 }finally{await browser.close();}
 const report={frames_checked:900,actual_glyph_safe_area:[140,260,840,1360],safe_area_failures:issues.length,issues,states,sample_times:times,continuous_playback_performed:false,actual_listening_performed:false};
 fs.writeFileSync(path.join(__dirname,'source_geometry.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({frames_checked:900,safe_area_failures:issues.length,first_issues:issues.slice(0,2)}));
})().catch(e=>{console.error(e.message);process.exitCode=1});
