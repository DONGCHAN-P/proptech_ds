/* Native headless source QA. Source frames are distinguished from encoded frames. */
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const puppeteer=require('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/node_modules/puppeteer-core');
const here=__dirname,ep=path.resolve(here,'../..'),out=path.join(ep,'outputs/jun-user-script-v1/representatives');
const plan=JSON.parse(fs.readFileSync(path.join(here,'preview_plan.json'),'utf8'));
(async()=>{
 fs.mkdirSync(path.join(out,'source_frames'),{recursive:true});
 console.log(JSON.stringify({phase:'browser_launch_pipe'}));
 const browser=await puppeteer.launch({executablePath:process.env.REVIEW_CHROME||'C:/Users/e2ken/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe',headless:true,pipe:true,timeout:10000,args:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--no-zygote','--no-first-run','--disable-background-networking']});
 const results=[];
 for(const p of plan.projects){
  console.log(JSON.stringify({phase:'checking',id:p.id}));
  const page=await browser.newPage();await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});page.setDefaultTimeout(10000);const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(pathToFileURL(path.join(p.project,'index.html')).href);await page.waitForFunction(()=>window.__ready===true);
  const samples=[];
  for(const t of p.samples){
   await page.evaluate(t=>window.__sourceSeek(t),t);
   const result=await page.evaluate(()=>{
    const issues=[],texts=[],opacity=e=>{let a=1;for(let p=e;p;p=p.parentElement){let s=getComputedStyle(p);a*=Number(s.opacity);if(s.display==='none'||s.visibility==='hidden')return 0;}return a;};
    const region=e=>e.closest('.caption')?{left:140,top:876,right:1780,bottom:1000}:e.id==='source'?{left:96,top:1015,right:1824,bottom:1055}:e.id==='brand'||e.id==='preview'?{left:80,top:20,right:1840,bottom:80}:e.id==='message'?{left:80,top:130,right:1840,bottom:207}:e.id==='condition'?{left:96,top:210,right:1824,bottom:265}:{left:96,top:265,right:1824,bottom:835};
    for(const e of document.querySelectorAll('[data-text]')){if(opacity(e)<.02)continue;
     const r=document.createRange();r.selectNodeContents(e);const allowed=region(e);
     for(const b of r.getClientRects()){if(b.width<.01||b.height<.01)continue;const box={left:b.left,top:b.top,right:b.right,bottom:b.bottom};texts.push({id:e.id||e.parentElement.id,text:e.textContent,box});
      if(b.left<allowed.left-.6||b.right>allowed.right+.6||b.top<allowed.top-.6||b.bottom>allowed.bottom+.6)issues.push({kind:'text_out_of_region',id:e.id||e.parentElement.id,box,allowed});
      for(let parent=e.parentElement;parent&&parent.id!=='root';parent=parent.parentElement){const s=getComputedStyle(parent);if(s.overflow==='hidden'){const a=parent.getBoundingClientRect();if(b.left<a.left-.5||b.right>a.right+.5||b.top<a.top-.5||b.bottom>a.bottom+.5)issues.push({kind:'parent_clip',id:e.id,parent:parent.id});}}
     }
    }
    const shapes=[...document.querySelectorAll('[data-money-won]')].filter(e=>opacity(e)>.02).map(e=>{const w=e.getBoundingClientRect().width,expected=Number(e.dataset.moneyWon)*Number(e.dataset.pxPerWon);return{id:e.id,actual_width:w,expected_width:expected,settled:Math.abs(w-expected)<.1};});
    return{issues,texts,shapes,fonts_loaded:document.fonts.check('700 40px Pretendard')&&document.fonts.check('400 40px Pretendard')};
   });
   const file=path.join(out,'source_frames',`${p.id}_${String(t).replace('.','p')}s.png`);await page.screenshot({path:file});
   samples.push({time_s:t,file,...result});
  }
  // Every supplied caption line is measured at the actual 40px Pretendard caption style.
  const all=JSON.parse(fs.readFileSync(path.join(ep,'narration/jun-user-script-v1/caption_plan.json'),'utf8'));
  const captionWidths=await page.evaluate(cues=>{const c=document.createElement('canvas').getContext('2d');c.font='400 40px Pretendard';return cues.map(q=>({cue_id:q.cue_id,scene_id:q.scene_id,widths:q.display_lines.map(x=>c.measureText(x).width),fits:q.display_lines.every(x=>c.measureText(x).width<=1640)}));},all.cues);
  // Backward seek must reproduce the same PNG as a fresh forward seek.
  await page.evaluate(t=>window.__sourceSeek(t),p.samples[2]);const first=await page.screenshot();
  await page.evaluate(t=>window.__sourceSeek(t),p.duration_s-.1);await page.evaluate(t=>window.__sourceSeek(t),p.samples[2]);const back=await page.screenshot();
  results.push({id:p.id,errors,samples,all_156_caption_width_checks:captionWidths,backward_seek_equal:Buffer.from(first).equals(Buffer.from(back))});await page.close();
 }
 await browser.close();
 const receipt={scope:'source DOM/range boxes/font widths and sampled source PNGs; not encoded media, independent review, audio sync, continuous playback, or listening',results};
 fs.writeFileSync(path.join(out,'source_qa.json'),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(results.map(r=>({id:r.id,runtime_errors:r.errors.length,geometry_findings:r.samples.flatMap(s=>s.issues).length,caption_width_failures:r.all_156_caption_width_checks.filter(c=>!c.fits).length,backward_seek_equal:r.backward_seek_equal}))));
})().catch(e=>{console.error(e);process.exit(1)});
