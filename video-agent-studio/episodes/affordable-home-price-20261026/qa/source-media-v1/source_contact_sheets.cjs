const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const qa=__dirname,root=path.resolve(qa,'../../../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const report=JSON.parse(fs.readFileSync(path.join(qa,'actual_source_metrics_v2.json'),'utf8'));
(async()=>{
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
try{const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
const groups=[];const scenes=report.source_frames.filter(f=>f.kind==='representative');for(let i=0;i<scenes.length;i+=9)groups.push({name:'scenes_'+(i/9+1),frames:scenes.slice(i,i+9)});
groups.push({name:'chapter_titles',frames:report.source_frames.filter(f=>f.kind==='title')});
for(const g of groups){const html='<!doctype html><meta charset="utf-8"><style>*{margin:0;box-sizing:border-box}body{width:1920px;height:1080px;display:grid;grid-template-columns:repeat(3,640px);grid-template-rows:repeat(3,360px);background:#222}.frame{position:relative;width:640px;height:360px}.frame img{width:640px;height:360px}.id{position:absolute;top:3px;left:3px;background:#123c;color:white;font:16px Arial;padding:4px}</style>'+g.frames.map(f=>'<div class="frame"><img src="'+pathToFileURL(f.path).href+'"><div class="id">'+f.scene_id+' · CH'+f.chapter+' · '+f.time_s.toFixed(3)+'s</div></div>').join('');
const p=path.join(qa,'actual-source-v2-frames',g.name+'.html');fs.writeFileSync(p,html);await page.goto(pathToFileURL(p).href);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));await page.screenshot({path:p.replace(/html$/,'png')});}
console.log(JSON.stringify({sheets:groups.map(g=>g.name),source_scenes:scenes.length}));
}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
