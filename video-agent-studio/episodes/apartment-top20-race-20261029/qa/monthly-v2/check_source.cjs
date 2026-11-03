const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());
 await page.goto(pathToFileURL(path.join(ep,'editor/monthly-v2/project/index.html')).href);await page.evaluate(()=>document.fonts.ready);
 const timing=await page.evaluate(()=>window.__raceData.timing),issues=[],rankIssues=[],partialEntry=[];
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 const knots=await page.evaluate(()=>{const t=window.__raceData.timing;return Array.from({length:t.period_count},(_,i)=>t.first_hold+i*t.month_step)});
 // All monthly data knots, not just a few evenly sampled frames.
 for(const t of knots){const result=await page.evaluate(t=>{window.__sourceSeek(t);const s=window.__frameState,bad=[];
  const live=s.active.filter(a=>a.alpha>.999&&a.pos<19.01);if(live.length!==20)bad.push({reason:'not20',count:live.length});
  for(const r of s.expected){const a=live.find(a=>a.id===r.id);if(!a||Math.abs(a.pos-r.r)>1e-6||Math.abs(a.value-r.v)>1e-6||a.quote_asof_month!==r.asof)bad.push({reason:'knot_mismatch',id:r.id});}
  return bad;},t);if(result.length)rankIssues.push({time:t,bad:result});}
 const curvature=await page.evaluate(()=>{const issues=[],sample=window.__sample,tracks=window.__tracks,n=window.__raceData.frames.length;
  let flat=0,c1=0,maxJump=0;
  for(const [id,tr] of Object.entries(tracks))for(const key of ['value','position','alpha']){const a=tr[key];
   for(let i=0;i<n-1;i++){const low=Math.min(a.y[i],a.y[i+1]),hi=Math.max(a.y[i],a.y[i+1]);for(const u of [.1,.25,.5,.75,.9]){const v=sample(a,i+u);if(v<low-1e-8||v>hi+1e-8)issues.push({id,key,i,reason:'overshoot'});if(low===hi){flat++;if(Math.abs(v-low)>1e-8)issues.push({id,key,i,reason:'changed_flat_interval'});}}}
   for(let i=1;i<n-1;i++){const h=1e-5,left=(sample(a,i)-sample(a,i-h))/h,right=(sample(a,i+h)-sample(a,i))/h,jump=Math.abs(left-right);maxJump=Math.max(maxJump,jump);c1++;if(jump>.02)issues.push({id,key,i,reason:'velocity_jump',jump});}
  }return {issues,flat_samples:flat,c1_knots:c1,max_numeric_derivative_jump:maxJump};});
 const frames=Math.round(timing.duration*timing.fps);
 for(let f=0;f<frames;f++){
  const result=await page.evaluate(t=>{window.__sourceSeek(t);const s=window.__frameState,bad=[],partial=[];
   const visible=e=>{for(let p=e;p;p=p.parentElement){const c=getComputedStyle(p);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<.02)return false;}return true;};
   const plot=document.getElementById('plot').getBoundingClientRect();
   for(const e of document.querySelectorAll('.measure')){if(!visible(e))continue;const row=e.closest('.racerow'),range=document.createRange();range.selectNodeContents(e);const b=range.getBoundingClientRect();
    if(row&&(b.bottom<plot.top||b.top>plot.bottom))continue;
    if(row&&(b.top<plot.top-.5||b.bottom>plot.bottom+.5))partial.push({text:e.textContent,top:b.top,bottom:b.bottom});
    if(b.left<139||b.top<259||b.right>841||b.bottom>1361)bad.push({text:e.textContent,l:b.left,t:b.top,r:b.right,b:b.bottom});
   }return {bad,partial};
  },f/timing.fps);
  if(result.bad.length)issues.push({frame:f,bad:result.bad});if(result.partial.length)partialEntry.push({frame:f,partial:result.partial});
 }
 const snapshotTimes=[0,2.2,10,20,30,40,48.8,52.8,56.8-1/60];
 for(const t of snapshotTimes){await page.evaluate(t=>window.__sourceSeek(t),t);await page.screenshot({path:path.join(__dirname,'source_'+t.toFixed(3)+'.png')});}
 const report={frames_checked:frames,monthly_knots_checked:knots.length,source_safe_area:[140,260,840,1360],safe_area_issue_frames:issues.length,monthly_knot_issues:rankIssues.length,partial_entry_label_frames:partialEntry.length,curve:curvature,runtime_errors:errors,issues:issues.slice(0,20),rankIssues,partial_entry_examples:partialEntry.slice(0,3),snapshot_times:snapshotTimes,continuous_playback_performed:false,actual_listening_performed:false};
 fs.writeFileSync(path.join(__dirname,'source_validation.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({...report,issues:report.issues.slice(0,2),curve:{...curvature,issues:curvature.issues.slice(0,2)}}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
