const fs=require('fs'),path=require('path');const {pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});await page.route(/^https?:\/\//,r=>r.abort());
 await page.goto(pathToFileURL(path.join(ep,'outputs/private-production-v2/ch01/index.html')).href);
 await page.evaluate(async()=>{await document.fonts.load('400 40px Pretendard');await document.fonts.ready;});
 const candidates=process.argv[2]?JSON.parse(fs.readFileSync(process.argv[2],'utf8')):[];
 const rows=Array.isArray(candidates)?candidates:candidates.lines||[];
 const report=await page.evaluate(rows=>{const ctx=document.createElement('canvas').getContext('2d');ctx.font='400 40px Pretendard';
  return {font:ctx.font,hangul_40_width_px:ctx.measureText('\uac00'.repeat(40)).width,safe_max_line_width_px:1600,
   lines:rows.map((text,index)=>({index,text,width_px:ctx.measureText(text).width,ok:ctx.measureText(text).width<=1600}))};},rows);
 fs.writeFileSync(path.join(__dirname,'renderer_metrics.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1});
