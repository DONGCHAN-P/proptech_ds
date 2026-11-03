const path=require('path'),R=path.resolve(__dirname,'../../../../..');
const {bundle}=require(path.join(R,'video/node_modules/@remotion/bundler'));
const {selectComposition,renderStill}=require(path.join(R,'video/node_modules/@remotion/renderer'));
const browserExecutable=path.join(R,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
(async()=>{const serveUrl=await bundle({entryPoint:path.join(R,'video/src/NamyangjuLanduseV7.tsx'),outDir:path.join(__dirname,'bundle-board'),publicDir:path.join(R,'video/public')});const composition=await selectComposition({serveUrl,browserExecutable,id:'LanduseV7BoardAudit'});await renderStill({serveUrl,browserExecutable,composition,frame:0,imageFormat:'png',output:path.join(__dirname,'w2_composed_audit.png')});console.log('W2 native board composed audit; no audio/final render');})().catch(e=>{console.error(e);process.exitCode=1});
