const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const q=__dirname,data=JSON.parse(fs.readFileSync(path.join(q,'targeted_static_v4.json'),'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const rows=[];
const found=process.argv[2]||cp.execFileSync('where.exe',['hyperframes.cmd'],{encoding:'utf8'}).trim().split(/\r?\n/)[0];
const shim=fs.readFileSync(found,'utf8');
// cmd shim의 동일설치본 CLI JS를 직접 호출하여 셸 인용/네트워크/npx를 피한다.
const candidate=path.join(path.dirname(found),'node_modules','hyperframes','dist','cli.js');
const alternatives=[candidate,path.join(path.dirname(found),'node_modules','hyperframes','dist','index.js')];
let cli=alternatives.find(p=>fs.existsSync(p));
if(!cli){const m=shim.match(/%dp0%\\([^"\r\n]+\.(?:mjs|cjs|js))/i);if(m)cli=path.join(path.dirname(found),m[1]);}
if(!cli||!fs.existsSync(cli))throw Error('설치된 CLI 진입점 확인 불가');
const env={...process.env,DO_NOT_TRACK:'1'};
const version=cp.execFileSync(process.execPath,[cli,'--version'],{encoding:'utf8',env}).trim();if(version!=='0.8.181')throw Error('CLI pin mismatch '+version);
for(const chapter of [1,7,9]){
 const c=data.chapters.find(c=>c.chapter===chapter),dir=path.join(q,'targeted-cli-v4','ch'+String(chapter).padStart(2,'0'));
 fs.mkdirSync(dir,{recursive:true});const html=path.join(dir,'index.html');fs.copyFileSync(c.path,html);if(sha(html)!==c.postcarve_html_sha256)throw Error('shadow input changed');
 const assets=path.join(dir,'assets');if(!fs.existsSync(assets))fs.symlinkSync(path.join(path.dirname(c.path),'assets'),assets,'junction');
 const times=chapter===1?[23,23.033333333333335,24.547333]:c.cues.filter(x=>x.scene_id===(chapter===7?'S031':'S040')).map(x=>(x.start_s+x.end_s)/2);
 const args=[cli,'check','.','--json','--at',times.join(','),'--timeout','10000'];
 const res=cp.spawnSync(process.execPath,args,{cwd:dir,env,encoding:'utf8',timeout:90000,maxBuffer:8*1024*1024,windowsHide:true});
 fs.writeFileSync(path.join(dir,'check.json'),res.stdout||'');fs.writeFileSync(path.join(dir,'check.log'),res.stderr||'');
 let parsed;try{parsed=JSON.parse(res.stdout)}catch{parsed={ok:false,error:'non_json'}}
 rows.push({chapter,html_sha256:sha(html),source_html_sha256:c.postcarve_html_sha256,ok:parsed.ok===true,exit_code:res.status,result_path:path.join(dir,'check.json'),result_sha256:sha(path.join(dir,'check.json')),source_unchanged:sha(c.path)===c.postcarve_html_sha256,error:res.error?.message});
 console.log(JSON.stringify({chapter,ok:rows.at(-1).ok,exit_code:res.status}));
}
const report={status:rows.every(r=>r.ok&&r.exit_code===0&&r.source_unchanged)?'pass':'findings',version,scope:'변경CH01/07/09의동일HTML사본.자산은읽기전용참조,CLI캐시/로그는QA폴더에만저장.',chapters:rows};
fs.writeFileSync(path.join(q,'targeted_cli_v4.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,chapters:rows.length}));if(report.status!=='pass')process.exitCode=1;
