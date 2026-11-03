const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../../../../..');
const {bundle}=require(path.join(repo,'video/node_modules/@remotion/bundler'));
const {selectComposition,renderMedia,renderStill}=require(path.join(repo,'video/node_modules/@remotion/renderer'));
const out=path.join(repo,'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/video-review-v4');
const browserExecutable=path.join(repo,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(repo,'video/src/NamyangjuV4.tsx'),outDir:path.join(__dirname,'bundle'),publicDir:path.join(repo,'video/public'),onProgress:p=>{if(p===100)console.log('bundled')}});
 const composition=await selectComposition({browserExecutable,serveUrl,id:'NamyangjuV4'});
 if(process.argv.includes('--stills')){
  const keys=JSON.parse(fs.readFileSync(path.join(out,'semantic_caption_keyframes.json'),'utf8'));
  const data=JSON.parse(fs.readFileSync(path.join(repo,'video/src/namyangju-v4/project.json'),'utf8'));
  const long=data.chapters.flatMap(c=>data.captions[c.scene_id].filter(x=>x.lines.length===2).map(x=>Math.round((c.start_s+(x.start_s+x.end_s)/2)*30)));
  const frames=[...new Set([120,2835,4050,4920,6570,22670,22980,23280,...keys.map(x=>x.frame),...long])];
  for(const frame of frames)await renderStill({browserExecutable,serveUrl,composition,output:path.join(out,`source_${frame}.png`),frame,imageFormat:'png'});console.log('source stills done',frames.length);return;
 }
 const output=path.join(out,'namyangju-wangsuk_v4.mp4');let last=-1;
 await renderMedia({browserExecutable,serveUrl,composition,outputLocation:output,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',crf:18,concurrency:4,onProgress:p=>{const n=Math.floor(p.progress*100);if(n%5===0&&n!==last){last=n;console.log(`render ${n}% ${p.renderedFrames||0}/${composition.durationInFrames}`)}}});
 const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 fs.writeFileSync(path.join(out,'render_manifest.json'),JSON.stringify({output,bytes:fs.statSync(output).size,sha256:hash(output),composition,semantic_cue_count:302,source_sha256:hash(path.join(repo,'video/src/NamyangjuV4.tsx')),data_sha256:hash(path.join(repo,'video/src/namyangju-v4/project.json')),live_proof_window_s:[94,174],region_comparison_shot:'V2-054',prior_full_master_preserved:true,new_paid_generation:false,actual_listening:false,continuous_playback:false},null,2));console.log(output);
})().catch(e=>{console.error(e.message);process.exitCode=1});
