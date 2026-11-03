const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../../../../..');
const {bundle}=require(path.join(repo,'video/node_modules/@remotion/bundler'));
const {selectComposition,renderMedia,renderStill}=require(path.join(repo,'video/node_modules/@remotion/renderer'));
const out=path.join(repo,'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/rail-route-proof-v2');
const browserExecutable=path.join(repo,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(repo,'video/src/NamyangjuRailRouteProofV2.tsx'),outDir:path.join(__dirname,'bundle'),publicDir:path.join(repo,'video/public'),onProgress:p=>{if(p===100)console.log('bundled')}});
 const composition=await selectComposition({browserExecutable,serveUrl,id:'NamyangjuRailRouteProofV2'});
 if(process.argv.includes('--stills')){for(const frame of [1206,1230,1380,1560,1800,1830])await renderStill({browserExecutable,serveUrl,composition,output:path.join(out,`context_${frame}.png`),frame,imageFormat:'png'});console.log('context stills done');return;}
 const output=path.join(out,'namyangju_rail-route-proof_v2.mp4');let last=-1;
 await renderMedia({browserExecutable,serveUrl,composition,outputLocation:output,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',crf:18,concurrency:4,onProgress:p=>{const n=Math.floor(p.progress*100);if(n%10===0&&n!==last){last=n;console.log(`render ${n}%`)}}});
 const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 fs.writeFileSync(path.join(out,'render_manifest.json'),JSON.stringify({output,bytes:fs.statSync(output).size,sha256:hash(output),composition,original_timing:{start_s:94,end_s:174,duration_s:80},changed_clip_interval_s:[40.3,61],source_sha256:hash(path.join(repo,'video/src/NamyangjuRailRouteProofV2.tsx')),data_sha256:hash(path.join(repo,'video/public/namyangju-rail-route-proof-v2/proof_data.json')),audio_sha256:hash(path.join(repo,'video/public/namyangju-rail-route-proof-v1/original_audio_94_174.wav')),full_original_video_modified:false,paid_generation:false,actual_listening:false,continuous_playback:false},null,2));console.log(output);
})().catch(e=>{console.error(e.message);process.exitCode=1});
