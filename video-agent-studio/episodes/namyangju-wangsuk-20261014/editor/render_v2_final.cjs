const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../../../..');
const {bundle}=require(path.join(repo,'video/node_modules/@remotion/bundler'));
const {selectComposition,renderMedia,renderStill}=require(path.join(repo,'video/node_modules/@remotion/renderer'));
const out=path.join(__dirname,'render_v2');fs.mkdirSync(out,{recursive:true});
const browserExecutable=path.join(repo,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
(async()=>{
 const full=process.argv.includes('--full'),still=process.argv.includes('--stills');
 const publicDir=path.join(__dirname,'public_v2');fs.mkdirSync(publicDir,{recursive:true});fs.cpSync(path.join(repo,'video/public/namyangju-v2'),path.join(publicDir,'namyangju-v2'),{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(repo,'video/src/NamyangjuV2.tsx'),outDir:path.join(out,'bundle-final'),publicDir,onProgress:p=>{if(p===100)console.log('bundled')}});
 const composition=await selectComposition({browserExecutable,serveUrl,id:full?'NamyangjuV2':'StoryproofV2'});
 if(still){const frames=full?[6030,8070,11370,14430,18000,20730,21090,21900,25350,27000]:[0,150,270,750,1700,2050,2500];for(const frame of frames){await renderStill({browserExecutable,serveUrl,composition,output:path.join(out,`bound_${frame}.png`),frame,imageFormat:'png'});}console.log('stills_done');return;}
 const output=path.join(out,full?'namyangju-wangsuk_v2.mp4':'storyproof_v2c.mp4');
 let last=-1;await renderMedia({browserExecutable,serveUrl,composition,outputLocation:output,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',crf:18,concurrency:4,onProgress:p=>{const n=Math.floor(p.progress*100);if(n%5===0&&n!==last){last=n;console.log(`render ${n}%`);}}});
 const source=fs.readFileSync(path.join(repo,'video/src/NamyangjuV2.tsx'));const data=fs.readFileSync(path.join(repo,'video/src/namyangju-v2/project.json'));
 fs.writeFileSync(path.join(out,full?'full_render_manifest.json':'proof_c_render_manifest.json'),JSON.stringify({composition,output,rendered:true,bytes:fs.statSync(output).size,source_sha256:crypto.createHash('sha256').update(source).digest('hex'),data_sha256:crypto.createHash('sha256').update(data).digest('hex'),continuous_playback:false,audio_listened:false},null,2));
 console.log(output);
})().catch(e=>{console.error(e.message);process.exitCode=1});
