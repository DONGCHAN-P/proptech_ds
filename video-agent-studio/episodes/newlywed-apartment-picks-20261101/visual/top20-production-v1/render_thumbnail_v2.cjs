const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const work=__dirname,ep=path.resolve(work,'../..'),out=path.join(ep,'outputs/top20-production-v1/thumbnail');
const slash=p=>p.replaceAll('\\','/');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const save=(p,o)=>fs.writeFileSync(p,JSON.stringify(o,null,2)+'\n');
const oldManifestPath=path.join(out,'artifact_manifest.json');
const oldManifest=JSON.parse(fs.readFileSync(oldManifestPath,'utf8'));
const oldHtml=path.join(work,'thumbnail.html'),htmlV2=path.join(work,'thumbnail_v2.html');
const issuePath=path.join(ep,'qa/top20-production-v1/findings.json');
const label='2024년 · 수도권 53개 구 기준';
const full=path.join(out,'TH001_신혼부부_수도권TOP20_v2_1280x720.png');
const mobile=path.join(out,'TH001_신혼부부_수도권TOP20_v2_mobile_320.png');
const technicalPath=path.join(work,'technical_checks_v2.json');
const record=p=>({path:slash(p),sha256:sha(p),bytes:fs.statSync(p).size});
const size=p=>{const b=fs.readFileSync(p);if(b.toString('hex',0,8)!=='89504e470d0a1a0a')throw Error('Not PNG');return [b.readUInt32BE(16),b.readUInt32BE(20)];};
const verifyPrevious=()=>{
 for(const a of oldManifest.artifacts)if(sha(a.path)!==a.sha256)throw Error('v1 PNG changed');
 for(const a of oldManifest.records)if(sha(a.path)!==a.sha256)throw Error('v1 record changed: '+a.path);
 for(const p of oldManifest.source_photo_hashes){const source=JSON.parse(fs.readFileSync(path.join(work,'source_ledger.json'),'utf8')).sources.find(a=>a.asset_id===p.asset_id);if(sha(source.absolute_file)!==p.source_sha256)throw Error('Photo changed');}
};
verifyPrevious();
async function render(){
 if(fs.existsSync(full)||fs.existsSync(mobile))throw Error('Preserve existing v2; choose a new version');
 const source=fs.readFileSync(oldHtml,'utf8');
 if(!source.includes('font-size:27px;letter-spacing:-.6px')||!source.includes('2024년 신혼부부 수 기준'))throw Error('Unexpected v1 HTML');
 const html=source.replaceAll('2024년 신혼부부 수 기준',label).replace('font-size:27px;letter-spacing:-.6px','font-size:38px;letter-spacing:-.6px');
 fs.writeFileSync(htmlV2,html);
 const puppeteer=require('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/node_modules/puppeteer-core');
 const browser=await puppeteer.launch({executablePath:'C:/Users/e2ken/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe',headless:true,args:['--no-sandbox','--allow-file-access-from-files']});
 try{
  const page=await browser.newPage(),blocked=[];
  await page.setRequestInterception(true);
  page.on('request',r=>{if(/^(file|data|about):/.test(r.url()))r.continue();else{blocked.push(r.url());r.abort();}});
  await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
  await page.goto(pathToFileURL(htmlV2).href,{waitUntil:'load'});
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));});
  const fit=await page.evaluate(()=>[...document.querySelectorAll('[data-check]')].map(el=>{const range=document.createRange();range.selectNodeContents(el);const b=range.getBoundingClientRect(),s=getComputedStyle(el);return {text:el.textContent,x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom,font_px:parseFloat(s.fontSize),mobile_px:parseFloat(s.fontSize)/4,inside_canvas:b.x>=10&&b.y>=10&&b.right<=1270&&b.bottom<=710,inside_text_column:!el.classList.contains('copy')||b.right<680};}));
  if(fit.some(r=>!r.inside_canvas||!r.inside_text_column))throw Error('Fit bounds failure: '+JSON.stringify(fit));
  const copy=fit.filter(r=>!r.text.includes('촬영'));
  for(let i=0;i<copy.length;i++)for(let j=i+1;j<copy.length;j++){const a=copy[i],b=copy[j];if(a.x<b.right&&a.right>b.x&&a.y<b.bottom&&a.bottom>b.y)throw Error('Text overlap');}
  await page.screenshot({path:full,type:'png',clip:{x:0,y:0,width:1280,height:720}});
  const dataUrl=p=>'data:image/png;base64,'+fs.readFileSync(p).toString('base64');
  const result=await page.evaluate(async(v1,v2)=>{
   async function load(src){const im=new Image();im.src=src;await im.decode();return im;}
   const [a,b]=await Promise.all([load(v1),load(v2)]);
   const ca=document.createElement('canvas'),cb=document.createElement('canvas');ca.width=cb.width=1280;ca.height=cb.height=720;
   const xa=ca.getContext('2d'),xb=cb.getContext('2d');xa.drawImage(a,0,0);xb.drawImage(b,0,0);
   const da=xa.getImageData(0,0,1280,720).data,db=xb.getImageData(0,0,1280,720).data;
   let changed=0,outside=0,minX=1280,minY=720,maxX=0,maxY=0;
   for(let y=0;y<720;y++)for(let x=0;x<1280;x++){const k=(y*1280+x)*4;if(da[k]!==db[k]||da[k+1]!==db[k+1]||da[k+2]!==db[k+2]||da[k+3]!==db[k+3]){changed++;if(x<55||x>=665||y<590||y>=665)outside++;minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}}
   const cm=document.createElement('canvas');cm.width=320;cm.height=180;const xm=cm.getContext('2d');xm.imageSmoothingEnabled=true;xm.imageSmoothingQuality='high';xm.drawImage(b,0,0,320,180);
   return {changed_pixels:changed,outside_footer_changed_pixels:outside,changed_bbox:[minX,minY,maxX+1,maxY+1],mobile_base64:cm.toDataURL('image/png').split(',')[1]};
  },dataUrl(oldManifest.artifacts[0].path),dataUrl(full));
  if(result.outside_footer_changed_pixels!==0)throw Error('Changes extend outside footer: '+JSON.stringify({...result,mobile_base64:undefined}));
  fs.writeFileSync(mobile,Buffer.from(result.mobile_base64,'base64'));delete result.mobile_base64;
  if(size(full).join('x')!=='1280x720'||size(mobile).join('x')!=='320x180'||blocked.length)throw Error('Output check failed');
  if(fs.statSync(full).size>=2097152)throw Error('PNG too large');
  verifyPrevious();
  const report={task_id:'top20-thumbnail-v2-scope-fix',issue_id:'QA-T20P-TH-SCOPE-01',created_utc:new Date().toISOString(),status:'rendered_pending_actual_view',label,fit,overlap_count:0,pixel_difference_from_v1:result,original_v1_manifest:record(oldManifestPath),previous_artifacts:oldManifest.artifacts,source_photo_hashes:oldManifest.source_photo_hashes,html_v1:record(oldHtml),html_v2:record(htmlV2),renderer:record(__filename),qa_input:record(issuePath),source_ledger:record(path.join(work,'source_ledger.json')),artifacts:[full,mobile].map(p=>({...record(p),dimensions:size(p)})),v1_preserved:true,source_photos_preserved:true,paid_calls:0,network_requests:blocked,browser:await browser.version()};
  save(technicalPath,report);
  console.log(JSON.stringify({artifacts:report.artifacts,footer:fit.find(x=>x.text===label),pixel_difference:result,v1_preserved:true},null,2));
 }finally{await browser.close();}
}
function finalize(){
 const technical=JSON.parse(fs.readFileSync(technicalPath,'utf8'));
 verifyPrevious();if(sha(oldManifestPath)!==technical.original_v1_manifest.sha256)throw Error('v1 manifest changed');
 for(const a of technical.artifacts)if(sha(a.path)!==a.sha256)throw Error('v2 PNG changed');
 const reviewPath=path.join(work,'visual_review_v2.json');
 save(reviewPath,{task_id:technical.task_id,issue_id:technical.issue_id,reviewed_utc:new Date().toISOString(),status:'self_checked_pending_independent_reQA',actual_viewed_files:technical.artifacts,view_method:'최종 1280×720 PNG와 320×180 PNG를 view_image로 각각 직접 열람',observation:'320px에서도 2024년 · 수도권 53개 구 기준의 53개 구가 식별됨. 하단 라벨만 문구·가독성을 위한 글자 크기 27→38px(모바일9.5px) 변경. 제목·사진·색·사진 배치 동일.',fit_bounds:'글자 모두 캔버스/텍스트열 안, 겹침0. 기술 좌표는 technical_checks_v2.json.',scope_confirmation:'2024년 수도권 53개 구 가운데 신혼부부 전체 수 TOP20. 시·군을 포함한 수도권 전체 순위로 확장하지 않음.',independent_QA:false,real_phone_device_test:false,previous_sha256:technical.previous_artifacts.map(a=>a.sha256),v2_sha256:technical.artifacts.map(a=>a.sha256)});
 const assetPath=path.join(work,'assets_v2.json');
 const oldAssets=JSON.parse(fs.readFileSync(path.join(work,'assets.json'),'utf8'));
 save(assetPath,{...oldAssets,task_id:technical.task_id,revision:'thumbnail-v2-scope-fix',issue_id:technical.issue_id,previous_assets:record(path.join(work,'assets.json')),assets:oldAssets.assets.map((a,i)=>({...a,asset_id:i?'TH001_MOBILE320_V2':'TH001_V2',scene_ids:['TH001'],actual_file:technical.artifacts[i].path,sha256:technical.artifacts[i].sha256,context:label,inspection_status:'self_checked_pending_independent_reQA',previous_sha256:technical.previous_artifacts[i].sha256,source_ledger:technical.source_ledger}))});
 const manifestPath=path.join(out,'artifact_manifest_v2.json'),handoffPath=path.join(work,'handoff_v2.json');
 const manifest={task_id:technical.task_id,issue_id:technical.issue_id,revision:'thumbnail-v2-scope-fix',created_utc:new Date().toISOString(),status:'self_checked_pending_independent_reQA',affected_scene_ids:['TH001'],title:oldManifest.title,context:label,scope_confirmation:'2024 수도권 53개 구 중 신혼부부 전체 수 TOP20',artifacts:technical.artifacts,previous_manifest:technical.original_v1_manifest,previous_artifacts:technical.previous_artifacts,previous_v1_preserved:true,changed:'하단 문구 및 해당 문구 글자 크기만 27→38px. 동일 위치·사진·주제·색·레이아웃.',pixel_difference:technical.pixel_difference_from_v1,source_photo_hashes:technical.source_photo_hashes,ranking:oldManifest.ranking,source_ledger:technical.source_ledger,credits:oldManifest.credits,records:[technicalPath,reviewPath,assetPath,htmlV2,__filename].map(record),technical:{dimensions_passed:true,fit_bounds_passed:true,text_overlap:0,only_footer_pixels_changed:true,paid_calls:0,network_requests:0},actual_view_performed:true,independent_reQA:'parent_to_assign',handoff:slash(handoffPath)};
 save(manifestPath,manifest);
 save(handoffPath,{task_id:technical.task_id,role:'visual',status:'필수 수정 반영·독립 재검수 대기',issue_id:technical.issue_id,affected_scene_ids:['TH001'],outputs:[...technical.artifacts.map(a=>a.path),slash(manifestPath)],input_revisions:{qa_findings_sha256:technical.qa_input.sha256,v1_manifest_sha256:technical.original_v1_manifest.sha256},previous_sha256:technical.previous_artifacts.map(a=>a.sha256),v2_sha256:technical.artifacts.map(a=>a.sha256),checks:[{check:'1280/320 실제 열람',result:'self_checked',evidence:'visual_review_v2.json'},{check:'경계·겹침·변경영역·원본 보존',result:'passed',evidence:'technical_checks_v2.json'}],scope_confirmation:'2024년 · 수도권 53개 구 기준',unresolved:'독립 재검수는 총괄이 재배정. QA 원본 finding 상태는 수정하지 않음.',next_role:'director → qa',note:'v1 PNG/manifest 및 기존 기록 보존. 본편·음성·공통 상태 변경, 외부 API·유료 호출 없음.'});
 const final=JSON.parse(fs.readFileSync(manifestPath,'utf8'));for(const a of [...final.artifacts,...final.records,final.previous_manifest,final.source_ledger,final.credits])if(sha(a.path)!==a.sha256)throw Error('Final manifest integrity error');
 console.log(JSON.stringify({artifacts:final.artifacts,manifest:slash(manifestPath),handoff:slash(handoffPath),v1_manifest_sha256:final.previous_manifest.sha256,scope:final.scope_confirmation,status:final.status},null,2));
}
(process.argv.includes('--finalize')?Promise.resolve().then(finalize):render()).catch(e=>{console.error(e);process.exitCode=1;});
