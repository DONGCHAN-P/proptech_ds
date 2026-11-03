const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const ep=path.resolve(__dirname,'../..'),root=path.resolve(ep,'../../..'),out=path.join(ep,'outputs/thumbnail-rework-20261030');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});await page.route(/^https?:\/\//,r=>r.abort());await page.goto(pathToFileURL(path.join(ep,'visual/thumbnail-rework-20261030/thumbnail.html')).href);await page.evaluate(()=>document.fonts.ready);
 const boxes=await page.evaluate(()=>[...document.querySelectorAll('.copy')].map(e=>{let r=document.createRange();r.selectNodeContents(e);let b=r.getBoundingClientRect(),c=getComputedStyle(e),stroke=parseFloat(c.webkitTextStrokeWidth)||0;return {text:e.textContent,font:c.fontFamily,fontSize:c.fontSize,left:b.left-stroke,top:b.top-stroke,right:b.right+stroke,bottom:b.bottom+stroke};}));
 const issues=boxes.filter(b=>b.left<32||b.top<32||b.right>1248||b.bottom>672);if(issues.length)throw Error(JSON.stringify(issues));
 await page.screenshot({path:path.join(out,'TH001_affordable_photo_v1.png')});
 fs.writeFileSync(path.join(__dirname,'source_qa.json'),JSON.stringify({canvas:[1280,720],fontLoaded:await page.evaluate(()=>document.fonts.check('800 114px Series')),boxes,clippingIssues:issues.length,thumbnailOnly:true},null,2));console.log(JSON.stringify({rendered:true,clippingIssues:issues.length,boxes}));
 }finally{await browser.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1});
