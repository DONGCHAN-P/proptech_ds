const fs=require('fs'),path=require('path'),crypto=require('crypto');
const e=path.resolve(__dirname,'../..'),r=path.resolve(e,'../../..'),o=path.join(e,'outputs/production-v6-preview'),nm=path.join(r,'video/node_modules'),cache=path.join(__dirname,'cache'),pub=path.join(cache,'public');
const {bundle}=require(path.join(nm,'@remotion/bundler')),{openBrowser,selectComposition,renderStill}=require(path.join(nm,'@remotion/renderer'));
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
(async()=>{
 for(const dir of ['changneung-v3','changneung-v4','changneung-v5','changneung-v6']) if(fs.existsSync(path.join(r,'video/public',dir)))fs.cpSync(path.join(r,'video/public',dir),path.join(pub,dir),{recursive:true});
 fs.mkdirSync(path.join(pub,'changneung-v4'),{recursive:true});fs.cpSync(path.join(e,'outputs/production-v4/plan_geometry'),path.join(pub,'changneung-v4/plan_geometry'),{recursive:true});
 fs.mkdirSync(path.join(o,'frames'),{recursive:true});
 const detail=process.argv.includes('--detail-proof');
 const serveUrl=await bundle({entryPoint:path.join(r,'video/src/changneung-v6',detail?'detail_entry.tsx':'entry.tsx'),outDir:path.join(cache,detail?'detail_bundle':'bundle'),publicDir:pub}),browser=await openBrowser('chrome',{browserExecutable:path.join(nm,'.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe')});
 try{
  const base=await selectComposition({serveUrl,puppeteerInstance:browser,id:detail?'ChangneungV6Detail':'ChangneungV6Frame'});
  if(detail){await renderStill({serveUrl,puppeteerInstance:browser,composition:base,frame:0,output:path.join(o,'proof_detail.png')});console.log('v6 S4 detail actual caption proof rendered');return;}
  if(process.argv.includes('--proofs')){
   const proofs=[['commute',{board:'commute',focus:'상암 MBC',caption:'상암 MBC까지 S1은 약46분, S4는 약62분, S5는 약56분입니다.'}],['price',{board:'price',focus:'S4',caption:'추가 부담을 감수하면서 S4를 먼저 볼 이유를 비교합니다.'}],['detail',{board:'legacy',cue:'M005_C10',caption:'S4는 공고상 입주와 초등학교 목표가 2030년3월입니다.'}],['calendar',{board:'calendar',variant:'rail',caption:'입주 달력 위에 새 철도의 일정을 겹쳐 보겠습니다.'}],['decision',{board:'decision',focus:'S4',caption:'생활권 접점과 학교 달력을 우선한다면 S4를 먼저 봅니다.'}]];
   proofs.push(['transit',{board:'transit',focus:'원흥',caption:'기존 원흥역 3호선 축과 새절역 6호선 연결을 비교합니다.'}],['supply',{board:'supply',caption:'2,277세대는 세 후보의 공고 규모입니다.'}],['pair',{board:'pair',pair:1,caption:'도래울과 동산동 기존 단지를 비교합니다.'}],['family',{board:'family',caption:'기다리는 개월 수에 자신의 월 주거비를 곱해 봅니다.'}],['series',{board:'series',caption:'광교·동탄에서 세운 기준을 왕숙과 창릉으로 이어갑니다.'}]);
   for(const [name,p] of proofs){const props={...p,motionFrame:40};await renderStill({serveUrl,puppeteerInstance:browser,composition:{...base,props},inputProps:props,frame:0,output:path.join(o,'proof_'+name+'.png')});console.log('proof '+name)}
   return;
  }
  const p=JSON.parse(fs.readFileSync(path.join(o,'project.json'))),sourceHash=sha(['Boards.tsx','MotionKit.tsx','data.json'].map(f=>fs.readFileSync(path.join(r,'video/src/changneung-v6',f))).join('\n'));
  const tasks=new Map(),states=[];let last='';
  for(const v of p.intervals){
   const changed=v.board_key!==last,lastBoard=last;last=v.board_key;let pos=v.start_frame;
   // Thirty deterministic in-place reveal samples at 30fps, followed by the held final state.
   const animated=changed&&!v.props.hideCaption&&v.duration_frames>=60;
   const samples=animated?Array.from({length:30},(_,i)=>({motion:i,duration:1})):[];
   samples.push({motion:40,duration:v.duration_frames-(animated?30:0)});
   for(const q of samples){const props={...v.props,motionFrame:q.motion},key=sha(JSON.stringify(props)+sourceHash).slice(0,24),file='frames/'+key+'.png';tasks.set(key,{props,file});states.push({scene_id:v.scene_id,start_frame:pos,end_frame:pos+q.duration,duration_frames:q.duration,frame_file:file,render_props:props});pos+=q.duration}
  }
  let done=0;const todo=[...tasks.values()];console.log('Unique visual states '+todo.length);
  for(let i=0;i<todo.length;i+=4){await Promise.all(todo.slice(i,i+4).map(async s=>{if(!fs.existsSync(path.join(o,s.file)))await renderStill({serveUrl,puppeteerInstance:browser,composition:{...base,props:s.props},inputProps:s.props,frame:0,output:path.join(o,s.file)});done++}));if(done%40===0||done===todo.length)console.log('rendered '+done+'/'+todo.length)}
  p.visual_intervals=states;p.source_sha256=sourceHash;fs.writeFileSync(path.join(o,'rendered_project.json'),JSON.stringify(p,null,2));fs.writeFileSync(path.join(o,'render_receipt.json'),JSON.stringify({source_sha256:sourceHash,unique_states:todo.length,animation_sampling:'30 samples x1 frame at 30fps; one second in-place reveal, final state held',frames:todo.map(s=>({file:s.file,sha256:sha(fs.readFileSync(path.join(o,s.file)))})),actual_listening:false,continuous_playback:false},null,2));
 }finally{await browser.close({silent:true})}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
