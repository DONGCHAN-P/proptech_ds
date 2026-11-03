const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const puppeteer = require('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/node_modules/puppeteer-core');
const visual = __dirname;
const episode = path.resolve(visual, '../..');
const root = path.resolve(episode, '../../..');
const out = path.join(episode, 'outputs/top20-production-v1/thumbnail');
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const json = (p, v) => fs.writeFileSync(p, JSON.stringify(v, null, 2) + '\n');
const pngSize = p => {const b=fs.readFileSync(p);if(b.toString('hex',0,8)!=='89504e470d0a1a0a')throw Error('Invalid PNG');return [b.readUInt32BE(16),b.readUInt32BE(20)];};
const manifestFile = path.join(visual,'../top20-8min-v2/photo_assets_v2.json');
const manifest = JSON.parse(fs.readFileSync(manifestFile,'utf8'));
const photos = ['R03','R02'].map(id=>manifest.assets.find(a=>a.region_id===id));
const inputs = [
  ['photo_assets_v2',manifestFile],
  ['brief',path.join(episode,'brief.json')],
  ['state_at_start',path.join(episode,'state.json')],
  ['channel_style',path.join(root,'config/channel_style_tokens.json')],
  ['current_video',path.join(root,'config/current_video.json')],
  ['master_guide',path.join(root,'video-agent-studio/guides/영상제작_마스터가이드.md')],
  ['font',path.join(root,'assets/fonts/Pretendard-ExtraBold.woff2')],
  ['approved_affordable_thumbnail',path.join(root,'video-agent-studio/episodes/affordable-home-price-20261026/outputs/thumbnail-rework-20261030/TH001_affordable_photo_v1.png')],
  ['approved_housing_thumbnail',path.join(root,'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/launch-proposal-v2/TH003_housing_modes_1280x720.png')],
  ['html',path.join(visual,'thumbnail.html')],['renderer',__filename],
].map(([name,p])=>({name,path:p.replaceAll('\\','/'),sha256:sha(p)}));
const inputSnapshot=path.join(visual,'input_snapshot.json');
if(!fs.existsSync(inputSnapshot))json(inputSnapshot,{task_id:'top20-thumbnail-v1',captured_utc:new Date().toISOString(),inputs});
for(const a of photos){if(sha(a.absolute_file)!==a.sha256)throw Error('Source hash mismatch: '+a.asset_id);}
fs.mkdirSync(out,{recursive:true});
(async()=>{
  const browser=await puppeteer.launch({executablePath:'C:/Users/e2ken/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe',headless:true,args:['--no-sandbox','--allow-file-access-from-files']});
  try{
    const page=await browser.newPage();const networkRequests=[];
    await page.setRequestInterception(true);
    page.on('request',req=>{if(/^(file|data|about):/.test(req.url()))req.continue();else{networkRequests.push(req.url());req.abort();}});
    await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(visual,'thumbnail.html')).href,{waitUntil:'load'});
    await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));});
    const checks=await page.evaluate(()=>({
      fontReady:document.fonts.check('800 103px Channel'),
      texts:[...document.querySelectorAll('[data-check]')].map(el=>{const r=document.createRange();r.selectNodeContents(el);const b=r.getBoundingClientRect();const cs=getComputedStyle(el);return {text:el.textContent,rect:{x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom},font_px:parseFloat(cs.fontSize),mobile_font_px:parseFloat(cs.fontSize)/4,inside_canvas:b.x>=10&&b.y>=10&&b.right<=1270&&b.bottom<=710};}),
      photos:[...document.querySelectorAll('.photo')].map(el=>{const img=el.querySelector('img');const b=el.getBoundingClientRect();const s=getComputedStyle(img);return {asset_id:el.dataset.source,frame:{x:b.x,y:b.y,width:b.width,height:b.height},natural:[img.naturalWidth,img.naturalHeight],object_fit:s.objectFit,object_position:s.objectPosition,filter:s.filter,opacity:s.opacity,loaded:img.complete&&img.naturalWidth>0};})
    }));
    if(!checks.fontReady||checks.texts.some(x=>!x.inside_canvas)||checks.photos.some(x=>!x.loaded||x.filter!=='none'))throw Error('Layout failure '+JSON.stringify(checks));
    const full=path.join(out,'TH001_신혼부부_수도권TOP20_1280x720.png');
    await page.screenshot({path:full,type:'png',clip:{x:0,y:0,width:1280,height:720}});
    const mobile=path.join(out,'TH001_신혼부부_수도권TOP20_mobile_320.png');
    const png='data:image/png;base64,'+fs.readFileSync(full).toString('base64');
    const mobileData=await page.evaluate(async(data)=>{const im=new Image();im.src=data;await im.decode();const c=document.createElement('canvas');c.width=320;c.height=180;const ctx=c.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(im,0,0,320,180);return c.toDataURL('image/png').split(',')[1];},png);
    fs.writeFileSync(mobile,Buffer.from(mobileData,'base64'));
    if(pngSize(full).join('x')!=='1280x720'||pngSize(mobile).join('x')!=='320x180')throw Error('Wrong dimensions');
    if(fs.statSync(full).size>=2*1024*1024)throw Error('Thumbnail exceeds 2MiB');
    if(networkRequests.length)throw Error('Unexpected network request');
    for(const a of photos){if(sha(a.absolute_file)!==a.sha256)throw Error('Source changed');}
    const outputs=[full,mobile].map(p=>({path:p.replaceAll('\\','/'),sha256:sha(p),dimensions:pngSize(p),bytes:fs.statSync(p).size}));
    const report={task_id:'top20-thumbnail-v1',rendered_utc:new Date().toISOString(),engine:'local Chromium via HyperFrames-installed puppeteer-core; native static HTML/CSS',browser_version:await browser.version(),puppeteer_version:require('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/node_modules/puppeteer-core/package.json').version,external_network_requests:networkRequests,technical_status:'passed',checks,source_hashes_unchanged:true,inputs,outputs,visual_review:'pending_actual_view'};
    json(path.join(visual,'technical_checks.json'),report);
    console.log(JSON.stringify({outputs,technical_status:report.technical_status,text_bounds:checks.texts,photo_frames:checks.photos},null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
