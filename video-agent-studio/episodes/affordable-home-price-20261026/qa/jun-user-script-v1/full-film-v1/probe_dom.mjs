import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const OWN=path.dirname(fileURLToPath(import.meta.url));
const EP=path.resolve(OWN,'../../..');
const PROJECT=path.join(EP,'editor/jun-user-script-v1/full-film-v1/project');
const require=createRequire('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/package.json');
const puppeteer=require('puppeteer-core');
const {bundleToSingleHtml}=await import('file:///C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/dist/compiler-U3W6CJW7.js');
const compiled=await bundleToSingleHtml(PROJECT);
if(typeof compiled!=='string')throw Error('Unexpected compiled HTML type');
await fs.writeFile(path.join(OWN,'compiled.html'),compiled);
const server=http.createServer(async(req,res)=>{
 try{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const target=pathname==='/'?path.join(OWN,'compiled.html'):path.resolve(PROJECT,'.'+pathname);
  if(pathname!=='/'&&!target.startsWith(PROJECT+path.sep)){res.writeHead(403).end();return;}
  const b=await fs.readFile(target);const ext=path.extname(target);
  const type={'.html':'text/html','.js':'text/javascript','.woff2':'font/woff2','.png':'image/png','.mp4':'video/mp4','.m4a':'audio/mp4'}[ext]??'application/octet-stream';
  res.writeHead(200,{'Content-Type':type,'Content-Length':b.length});res.end(b);
 }catch(e){res.writeHead(404).end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const port=server.address().port;
const browser=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-extensions','--no-first-run','--no-sandbox','--mute-audio']});
console.log('QA_BROWSER_LAUNCHED');
try{
 const page=await browser.newPage();await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});
 await page.setRequestInterception(true);page.on('request',r=>{const u=r.url();if(u.startsWith(`http://127.0.0.1:${port}/`)||u.startsWith('data:')||u.startsWith('blob:'))r.continue();else r.abort();});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'domcontentloaded',timeout:30000});
 console.log('QA_DOM_LOADED');await page.evaluate(()=>document.fonts.ready);console.log('QA_FONTS_READY');
 const data=await page.evaluate(()=>({playerKeys:Object.keys(window.__player??{}),playerFunctions:Object.fromEntries(Object.entries(window.__player??{}).filter(([k,v])=>typeof v==='function').map(([k,v])=>[k,String(v).slice(0,500)])),timelines:Object.keys(window.__timelines??{}),fonts:document.fonts.status,bodyBox:document.body.getBoundingClientRect().toJSON()}));
 console.log(JSON.stringify({port,compiledBytes:Buffer.byteLength(compiled),...data,errors}));
 await fs.writeFile(path.join(OWN,'probe.json'),JSON.stringify({port,...data,errors},null,2));
}finally{await browser.close();await new Promise(r=>server.close(r));}
