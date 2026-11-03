const fs=require('fs'),path=require('path');
const r=path.resolve(__dirname,'../../../../..'),o=path.resolve(__dirname,'../../outputs/production-v4'),nm=path.join(r,'video/node_modules');
const {bundle}=require(path.join(nm,'@remotion/bundler'));
const {selectComposition,renderStill,openBrowser}=require(path.join(nm,'@remotion/renderer'));
(async()=>{
 const p=JSON.parse(fs.readFileSync(path.join(o,'project_v4.json'))),serveUrl=await bundle({entryPoint:path.join(r,'video/src/changneung-v4/frame_entry.tsx'),outDir:path.join(__dirname,'cache/fullbundle'),publicDir:path.join(__dirname,'cache/public')});
 const browser=await openBrowser('chrome',{browserExecutable:path.join(nm,'.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe')});
 try{for(const cueId of ['M000_C1','M003_C10','M004_C6','M007_C11+M007_C12']){
 const c=p.captions.find(x=>x.cue_id===cueId),s=p.shots.find(x=>c.start_frame>=x.start_frame&&c.start_frame<x.end_frame);
 const props={shot:s.shot,caption:c.display_text,hideCaption:false};
 const composition=await selectComposition({serveUrl,puppeteerInstance:browser,id:'ChangneungFrameV4',inputProps:props});
 const file=path.join(o,`subtitle_proof_${cueId.replaceAll('+','_')}.png`);
 await renderStill({serveUrl,puppeteerInstance:browser,composition,inputProps:props,frame:0,output:file});console.log(file);
 }}finally{await browser.close({silent:true})}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
