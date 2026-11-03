const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const root=path.resolve(__dirname,'../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{
 const dir=fs.readdirSync(path.join(root,'reports')).find(n=>n.endsWith('20261029'));
 const file=path.join(root,'reports',dir,'보고서.html');
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const results=[];
 try{
  for(const [name,width,height] of [['desktop',1440,1100],['mobile',390,844]]){
   const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
   await page.route(/^https?:\/\//,r=>r.abort());await page.goto(pathToFileURL(file).href);await page.evaluate(()=>document.fonts.ready);
   const check=await page.evaluate(()=>({page_width:document.documentElement.clientWidth,scroll_width:document.documentElement.scrollWidth,section_count:document.querySelectorAll('section').length,svg_count:document.querySelectorAll('svg').length,unloaded_images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length}));
   await page.screenshot({path:path.join(__dirname,'report_'+name+'.png'),fullPage:false});results.push({name,...check});await page.close();
  }
 }finally{await browser.close()}
 fs.writeFileSync(path.join(__dirname,'report_layout_check.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
})().catch(e=>{console.error(e.message);process.exitCode=1});
