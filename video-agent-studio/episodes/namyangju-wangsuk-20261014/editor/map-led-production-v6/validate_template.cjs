const fs=require('fs'),path=require('path');
const repo=path.resolve(__dirname,'../../../../..');
const {bundle}=require(path.join(repo,'video/node_modules/@remotion/bundler'));
const {getCompositions}=require(path.join(repo,'video/node_modules/@remotion/renderer'));
const browserExecutable=path.join(repo,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
(async()=>{
 const project=JSON.parse(fs.readFileSync(path.join(repo,'video/src/namyangju-map-led-v6/project.json'),'utf8'));
 if(project.timing_locked!==false||project.narration.length||project.duration_frames!==null)throw Error('Template phase must remain untimed with no narration');
 for(const asset of project.assets)if(asset.file&&!fs.existsSync(path.join(repo,'video/public',asset.file)))throw Error('Missing asset '+asset.asset_id);
 const serveUrl=await bundle({entryPoint:path.join(repo,'video/src/NamyangjuMapLedV6.tsx'),outDir:path.join(__dirname,'bundle-template-check'),publicDir:path.join(repo,'video/public')});
 const compositions=await getCompositions(serveUrl,{browserExecutable});
 if(compositions.some(c=>c.id==='NamyangjuMapLedV6'))throw Error('Full composition must remain unavailable before voice lock');
 const report={status:'template_checked',compositions:compositions.map(c=>({id:c.id,width:c.width,height:c.height,fps:c.fps,durationInFrames:c.durationInFrames})),full_render_started:false,renderMedia_called:false,new_voice_generated:false,new_images_generated:false,paid_api_called:false,timing_locked:false,existing_music_asset_ready:true};
 fs.writeFileSync(path.join(__dirname,'template_validation.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.message);process.exitCode=1});
