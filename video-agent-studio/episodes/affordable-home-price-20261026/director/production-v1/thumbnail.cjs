const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const crypto=require('node:crypto');
const puppeteer=require('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/node_modules/puppeteer-core');
const root='C:/projects/realestate_reco';
const ep=path.join(root,'video-agent-studio/episodes/affordable-home-price-20261026');
const out=path.join(ep,'outputs/private-release-v1');
const assets=path.join(out,'assets'); fs.mkdirSync(assets,{recursive:true});
for(const name of ['Pretendard-Bold.woff2','Pretendard-ExtraBold.woff2'])
 fs.copyFileSync(path.join(root,'assets/fonts',name),path.join(assets,name));
fs.copyFileSync(path.join(ep,'visual/hero-budget-v1.png'),path.join(assets,'hero-budget-v1.png'));
(async()=>{
 const browser=await puppeteer.launch({executablePath:'C:/Users/e2ken/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe',headless:true,args:['--no-sandbox','--allow-file-access-from-files']});
 try{
  const page=await browser.newPage(); await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
  await page.goto(pathToFileURL(path.join(out,'thumbnail.html')).href); await page.evaluate(()=>document.fonts.ready);
  const checks=await page.evaluate(()=>[...document.querySelectorAll('.kicker,.line1,.line2,.note,.brand')].map(el=>{
   const range=document.createRange();range.selectNodeContents(el);const rect=range.getBoundingClientRect();
   return {text:el.textContent,x:rect.x,y:rect.y,width:rect.width,height:rect.height,pass:rect.x>=42&&rect.y>=38&&rect.right<=1238&&rect.bottom<=688};
  }));
  if(checks.some(x=>!x.pass)) throw new Error('Thumbnail text safe margin failure: '+JSON.stringify(checks));
  const target=path.join(out,'thumbnail.png'); if(fs.existsSync(target))throw new Error('Preserve existing thumbnail; version any change'); await page.screenshot({path:target});
  const bytes=fs.readFileSync(target); if(bytes.length>=2*1024*1024) throw new Error('Thumbnail exceeds platform size limit');
  fs.writeFileSync(path.join(out,'thumbnail_checks.json'),JSON.stringify({resolution:[1280,720],checks,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,visual_review:'pending'},null,2));
  process.stdout.write(JSON.stringify({thumbnail:'outputs/private-release-v1/thumbnail.png',text_bounds:'pass',bytes:bytes.length}));
 } finally{await browser.close();}
})().catch(e=>{process.stderr.write(String(e));process.exit(1)});
