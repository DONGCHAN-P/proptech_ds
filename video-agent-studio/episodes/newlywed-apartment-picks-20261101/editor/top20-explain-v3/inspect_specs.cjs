/* HyperFrames의 검증된 브라우저 경로로 원본 PNG를 캡처합니다. MP4 렌더가 아닙니다. */
const fs=require('fs'),path=require('path'),cp=require('child_process');
const H=__dirname,read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const timeline=read(path.join(H,'timeline_resolved.json')),phases=read(path.join(H,'phase_audit.json'));
const evidence=path.join(H,'evidence'),pngdir=path.join(evidence,'대표PNG');fs.mkdirSync(pngdir,{recursive:true});
const samples=[];
for(const s of timeline.scenes){
 const p=phases.find(v=>v.scene_id===s.scene_id);
 if(!p){samples.push({scene_id:s.scene_id,phase:'intro',global_s:s.start_s+12});continue;}
 const ts=s.sentence_times.filter(t=>!t.is_pending&&!p.price_sentence_ids.includes(t.sentence_id)),last=ts.at(-1);
 samples.push({scene_id:s.scene_id,phase:'feature',global_s:s.start_s+(last.start_s+last.end_s)/2});
 samples.push({scene_id:s.scene_id,phase:'price',global_s:s.start_s+(p.switch_s+s.duration_s)/2});
}
let version=1,raw;do{raw=path.join(evidence,'snapshots-spec-v'+version++);}while(fs.existsSync(raw));
const cli=process.env.HYPERFRAMES_CLI_FILE||'C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/dist/cli.js';
const argv=[cli,'snapshot',path.join(H,'spec'),'--at',samples.map(v=>v.global_s.toFixed(6)).join(','),'--no-end','--describe','false','--output',raw,'--timeout','20000'];
const stdout=fs.openSync(path.join(evidence,'snapshot.log'),'w'),stderr=fs.openSync(path.join(evidence,'snapshot.stderr.log'),'w');
const result=cp.spawnSync(process.execPath,argv,{env:{...process.env,DO_NOT_TRACK:'1',HYPERFRAMES_NO_UPDATE_CHECK:'1',HYPERFRAMES_NO_AUTO_INSTALL:'1'},stdio:['ignore',stdout,stderr],timeout:180000});fs.closeSync(stdout);fs.closeSync(stderr);
if(result.status!==0)throw new Error('PNG 캡처 실패. evidence/snapshot.stderr.log 확인');
const files=fs.readdirSync(raw).filter(f=>/^frame.*\.png$/i.test(f)).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
if(files.length!==samples.length)throw new Error(`PNG 수량 불일치 ${files.length}/${samples.length}`);
for(let i=0;i<samples.length;i++){const target=path.join(pngdir,samples[i].scene_id+'_'+samples[i].phase+'.png');fs.copyFileSync(path.join(raw,files[i]),target);samples[i].png=target;}
const check=read(path.join(evidence,'check-spec.json'));
const receipt={status:check.ok&&!check.browserSkipped&&check.layout.totalIssueCount===0?'passed':'failed',검수범위:'실제 브라우저 DOM 글자 경계·캡션 영역·전환 직전/직후13표본은 HyperFrames check의 layout audit로 검사했습니다. PNG는 별도13표본입니다.',timing_locked:false,실제음성청취:false,MP4생성:false,vision_API:false,layout_report:'evidence/check-spec.json',layout_samples:check.layout.samples,layout_findings:check.layout.findings,PNG_samples:samples,command:[process.execPath,...argv],snapshot_exit_code:result.status};
fs.writeFileSync(path.join(evidence,'text_bounds.json'),JSON.stringify(receipt,null,2)+'\n');
process.stdout.write(JSON.stringify({상태:receipt.status,경계검사:check.layout.samples.length,PNG:samples.length,문제:check.layout.totalIssueCount})+'\n');
if(receipt.status!=='passed')process.exitCode=1;
