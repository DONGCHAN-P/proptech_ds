/* 독립 소스 DOM 검사. 실제 MP4 육안 판정·청취·연속재생을 대신하지 않는다. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url');
const here=fs.realpathSync(__dirname),root=path.resolve(here,'../../../../../..');
const {chromium}=require(path.join(root,'tools/rea/node_modules/playwright-core'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const rawOutput=path.resolve(process.argv[3]||'');
const output=path.join(fs.realpathSync(path.dirname(rawOutput)),path.basename(rawOutput));
const outputRelative=path.relative(here,output);
if(!outputRelative||outputRelative.startsWith('..')||path.isAbsolute(outputRelative))throw Error('QA 소유범위 밖 출력');
const input=read(process.argv[2]);
(async()=>{
  const report={status:'unchecked',basis:'font-loaded per-character DOM Range rectangles, not raster ink bounds',actual_encoded_frames:false,actual_listening:false,continuous_playback:false,samples:[],findings:[]};
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-background-networking'],timeout:10000});
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
    page.setDefaultTimeout(10000);page.setDefaultNavigationTimeout(10000);
    await page.route(/^https?:\/\//,r=>r.abort());
    for(const project of input.projects){
      for(const key of ['html','model'])if(hash(project[key].path)!==project[key].sha256)throw Error('Source SHA mismatch '+project.scene_id);
      const model=read(project.model.path);
      if(model.template_only!==false)throw Error('실제 음성 기반 소스 model 필요');
      const errors=[];const listener=e=>errors.push(e.message);page.on('pageerror',listener);
      await page.goto(pathToFileURL(project.html.path).href);
      await page.waitForFunction(()=>document.fonts.status==='loaded'&&typeof window.__sourceSeek==='function');
      for(const time of project.times_s){
        await page.evaluate(t=>window.__sourceSeek(t),time);
        const metric=await page.evaluate(({time,allowedPairs,beats})=>{
          const findings=[],texts=[],shapes=[];
          const box=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom});
          const intersects=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
          const visible=e=>{let v=1;for(let p=e;p;p=p.parentElement){const c=getComputedStyle(p);if(c.display==='none'||c.visibility==='hidden')return false;v*=Number(c.opacity);}return v>.01;};
          for(const el of document.querySelectorAll('[data-object="shape"]'))if(visible(el)){const r=el.getBoundingClientRect();if(r.width>.5&&r.height>.5)shapes.push({id:el.id,box:box(r)});}
          for(const [i,el] of [...document.querySelectorAll('[data-object="text"],#message,#source,.caption-lines')].entries()){
            if(!visible(el))continue;
            const id=el.id||el.closest('.cue')?.id||'text-'+i,style=getComputedStyle(el),graphic=!!el.closest('#graphic'),caption=!!el.closest('.cue');
            const allowed=caption?[140,876,1780,1000]:el.id==='source'?[96,1020,1824,1050]:graphic?[80,225,1820,810]:[80,125,1820,215];
            const glyphs=[],walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let node;
            while(node=walker.nextNode()){let offset=0;for(const c of node.textContent){const next=offset+c.length;if(c.trim()){const range=document.createRange();range.setStart(node,offset);range.setEnd(node,next);for(const r of range.getClientRects())if(r.width>.1&&r.height>.1)glyphs.push(box(r));}offset=next;}}
            for(const g of glyphs)if(g.left<allowed[0]-.6||g.top<allowed[1]-.6||g.right>allowed[2]+.6||g.bottom>allowed[3]+.6)findings.push({type:'glyph_out_of_region',id,glyph:g,allowed});
            const size=parseFloat(style.fontSize);
            if(graphic&&size<28)findings.push({type:'small_label',id,size});
            if(id==='conclusion'&&size<64)findings.push({type:'small_conclusion',id,size});
            if(caption&&(size!==40||parseFloat(style.lineHeight)!==50||new Set(glyphs.map(g=>Math.round(g.top))).size>2))findings.push({type:'caption_size_lines',id});
            texts.push({id,text:el.textContent,font_size:size,graphic,glyphs});
          }
          const graphical=texts.filter(t=>t.graphic);
          for(let i=0;i<graphical.length;i++){
            const t=graphical[i];
            for(const s of shapes){if(allowedPairs.some(p=>p.text_id===t.id&&p.shape_id===s.id))continue;const g=t.glyphs.find(g=>intersects(g,s.box));if(g)findings.push({type:'text_shape_collision',text_id:t.id,shape_id:s.id,glyph:g,shape:s.box});}
            for(const other of graphical.slice(i+1))if(other.id!==t.id&&t.glyphs.some(g=>other.glyphs.some(h=>intersects(g,h))))findings.push({type:'text_text_collision',a:t.id,b:other.id});
          }
          for(const b of beats)if(time<b.start_s-1e-5)for(const id of b.reveal||[]){const el=document.getElementById(id);if(!el||visible(el))findings.push({type:'premature_or_missing_information',id,anchor_s:b.start_s});}
          return {time_s:time,fonts_status:document.fonts.status,glyph_count:texts.reduce((n,t)=>n+t.glyphs.length,0),text_count:texts.length,shape_count:shapes.length,findings};
        },{time,allowedPairs:project.allowed_text_shapes||[],beats:model.beats||[]});
        report.samples.push({scene_id:project.scene_id,...metric});
        for(const f of metric.findings)report.findings.push({scene_id:project.scene_id,time_s:time,...f});
      }
      if(errors.length)report.findings.push({scene_id:project.scene_id,type:'runtime',errors});
      page.off('pageerror',listener);
      for(const key of ['html','model'])if(hash(project[key].path)!==project[key].sha256)throw Error('Source changed during geometry');
    }
    report.status=report.findings.length?'findings':'pass';
  }finally{await browser.close();}
  fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n','utf8');
  console.log(JSON.stringify({status:report.status,samples:report.samples.length,findings:report.findings.length,actual_encoded_frames:false}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
