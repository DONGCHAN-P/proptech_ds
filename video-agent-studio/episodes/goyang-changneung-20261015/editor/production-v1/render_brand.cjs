const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../../../../..');
const nm=path.join(root,'video/node_modules');
const out=path.resolve(__dirname,'../../outputs/editor-preflight-v1');
const {bundle}=require(path.join(nm,'@remotion/bundler'));
const {selectComposition,renderMedia}=require(path.join(nm,'@remotion/renderer'));
async function main(){
  fs.mkdirSync(out,{recursive:true});
  // Preserve the approved design and sources; change only its geography-specific label.
  const original=fs.readFileSync(path.join(root,'video/src/namyangju-landuse-v8/BrandReuse.tsx'),'utf8');
  const old='기존 채널 브랜딩용 AI 개념 도시 · 왕숙 실제 모습 아님';
  if(!original.includes(old))throw new Error('Original brand label changed: review before regenerating');
  fs.writeFileSync(path.join(__dirname,'BrandGeneric.tsx'),original.replace(old,'기존 채널 브랜딩용 AI 개념 도시 · 특정 지역의 실제 모습 아님'));
  const serveUrl=await bundle({entryPoint:path.join(__dirname,'brand_entry.tsx'),outDir:path.join(__dirname,'brand-bundle'),publicDir:path.join(root,'video/public'),webpackOverride:c=>({...c,resolve:{...c.resolve,modules:[nm,...(c.resolve.modules||['node_modules'])]}})});
  const browserExecutable=path.join(nm,'.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
  for(const [id,file] of [['GenericBrandIntro','brand_intro_generic_v1.mp4'],['GenericBrandOutro','brand_outro_generic_v1.mp4']]){
    const composition=await selectComposition({serveUrl,browserExecutable,id});
    await renderMedia({serveUrl,browserExecutable,composition,codec:'h264',crf:18,concurrency:2,outputLocation:path.join(out,file)});
    console.log(file);
  }
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
