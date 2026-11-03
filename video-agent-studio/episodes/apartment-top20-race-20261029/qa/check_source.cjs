const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'..'),root=path.resolve(ep,'../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{fs.mkdirSync(__dirname,{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const issues=[],rankIssues=[],collisionIssues=[],motion=[];let checked=0;
 try{const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());await page.goto(pathToFileURL(path.join(ep,'editor/project/index.html')).href);await page.evaluate(()=>document.fonts.ready);
 const timing=await page.evaluate(()=>window.__raceData.timing),totalFrames=Math.round(timing.duration*30);
 for(let f=0;f<totalFrames;f++){
  const result=await page.evaluate(t=>{window.__sourceSeek(t);const s=window.__frameState;const visible=e=>{let p=e;while(p){const c=getComputedStyle(p);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<.02)return false;p=p.parentElement;}return true;};const bad=[];for(const e of document.querySelectorAll('.measure')){if(!visible(e))continue;const r=document.createRange();r.selectNodeContents(e);const b=r.getBoundingClientRect();if(b.left<139||b.top<259||b.right>841||b.bottom>1361)bad.push({text:e.textContent,left:b.left,top:b.top,right:b.right,bottom:b.bottom});}
    let rankBad=[];if(s.stable){const vis=s.active.filter(q=>q.labelsVisible&&q.alpha>.99);if(vis.length!==20)rankBad.push({reason:'not_20_stable_labels',count:vis.length});for(const e of s.expected){const a=s.active.find(x=>x.id===e.id);if(!a||Math.abs(a.pos-e.r)>1e-7||Math.abs(a.value-e.v)>1e-7)rankBad.push({reason:'wrong_stable_value_or_position',id:e.id});}}
    const labels=[...document.querySelectorAll('.name')].filter(visible).map(e=>{const r=document.createRange();r.selectNodeContents(e);const b=r.getBoundingClientRect();return {text:e.textContent,l:b.left,t:b.top,r:b.right,b:b.bottom}});const overlaps=[];for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];if(Math.min(a.r,b.r)-Math.max(a.l,b.l)>2&&Math.min(a.b,b.b)-Math.max(a.t,b.t)>1)overlaps.push([a.text,b.text]);}
    return {time:t,stable:s.stable,bad,rankBad,overlaps,active:s.active};
  },f/30);checked++;
  if(result.bad.length)issues.push({frame:f,...result});if(result.rankBad.length)rankIssues.push({frame:f,...result});if(result.overlaps.length)collisionIssues.push({frame:f,overlaps:result.overlaps});
 }
 for(const seg of timing.segments){const t=seg.start+(seg.transition_end-seg.start)*.5;await page.evaluate(t=>window.__sourceSeek(t),t);const s=await page.evaluate(()=>window.__frameState);motion.push({i:seg.i,time:t,moving_rows:s.active.filter(r=>Math.abs(r.pos-Math.round(r.pos))>.01).length});}
 const snapshotPlan=[0,2,10,20,30,timing.race_end,timing.duration-1/30];
 for(const p of ['2010Q4','2016Q3','2023Q3','2025Q4']){const i=await page.evaluate(p=>window.__raceData.frames.findIndex(f=>f.p===p),p);const seg=timing.segments.find(s=>s.i===i);snapshotPlan.push(seg.start+.12,seg.transition_end+.1);}
 for(const t of snapshotPlan){await page.evaluate(t=>window.__sourceSeek(t),t);await page.screenshot({path:path.join(__dirname,'source_'+t.toFixed(3)+'.png')});}
 const report={frames_checked:checked,source_safe_area:[140,260,840,1360],safe_area_issue_frames:issues.length,stable_state_issue_frames:rankIssues.length,name_collision_frames:collisionIssues.length,issues,rankIssues,collisionIssues,motion,actual_position_change_segments:motion.filter(m=>m.moving_rows>0).length,total_segments:motion.length,snapshot_times:snapshotPlan,continuous_playback_performed:false,actual_listening_performed:false};
 fs.writeFileSync(path.join(__dirname,'source_validation.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({frames_checked:checked,safe_area_issue_frames:issues.length,stable_state_issue_frames:rankIssues.length,name_collision_frames:collisionIssues.length,moving_segments:report.actual_position_change_segments,first_issues:issues.slice(0,1),first_collision:collisionIssues.slice(0,1)}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
