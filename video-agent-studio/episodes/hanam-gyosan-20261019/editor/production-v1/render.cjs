const fs=require('fs'),path=require('path'),crypto=require('crypto');
const E=__dirname,EP=path.resolve(E,'../..'),R=path.resolve(EP,'../../..'),O=path.join(EP,'outputs/production-v1'),V=path.join(EP,'visual'),NM=path.join(R,'video/node_modules');
const {bundle}=require(path.join(NM,'@remotion/bundler')),{openBrowser,selectComposition,renderStill}=require(path.join(NM,'@remotion/renderer'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const tree=p=>fs.readdirSync(p,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(d=>d.isDirectory()?tree(path.join(p,d.name)):[path.join(p,d.name)]);
const representatives=[
 {mode:'plan',title:'하남 교산 · 주거와 생활의 실제 계획 배치',caption:'교산은 같은 지구 안에서도 위치에 따라 생활 조건이 달라집니다.',active:'context',items:[{label:'북부 · 기존 생활권 접속',detail:'권역은 설명을 위한 개략 구분입니다'},{label:'중앙 · 계획 시설 배치',detail:'운영 시점과 접근 동선은 별도 확인합니다'},{label:'남부 · 자족·녹지',detail:'실제 계획면을 지도에서 구분합니다'}]},
 {mode:'jobs',title:'일자리 · 자족용지와 실제 고용을 구분합니다',caption:'자족용지의 계획은 현재 직장이 들어와 있다는 뜻과 다릅니다.',items:[{label:'자족기능확보시설',detail:'LH 공개 공간정보의 실제 필지를 강조합니다'},{label:'고용과 기업 입주',detail:'계획 용지와 실제 운영을 함께 확인합니다'}]},
 {mode:'rail',title:'교통 · 입주 달력과 철도 목표를 함께 봅니다',caption:'입주 예정 시점과 철도 사업 목표 사이의 차이를 확인합니다.',active:'A2',items:[{label:'A2 입주 예정',year:2029,detail:'6월 · 공고 기준'},{label:'송파하남선 사업 목표',year:2032,detail:'개통 확정일이 아닙니다'}]},
 {mode:'life',title:'생활시설 · A-2 주변의 실제 계획면',caption:'주거와 학교, 공원은 실제 배치와 이용 가능한 시점을 함께 봅니다.',active:'A2',items:[{label:'주거·교육·녹지',detail:'A-2 주변 계획 필지 상세'},{label:'전체 위치와 연결',detail:'왼쪽 파란 범위가 상세 화면입니다'}]},
 {mode:'comparison',title:'주변 대안 · 전용 84㎡대 기존 단지의 위치와 거래',caption:'기존 단지의 면적과 현재 생활권을 함께 비교합니다.',items:[{label:'감일한라비발디',value:14.325,unit:'억',detail:'전용83~85㎡ 미만 · 8건'},{label:'미사강변푸르지오',value:15.525,unit:'억',detail:'전용83~85㎡ 미만 · 6건'},{label:'위례롯데캐슬',value:17,unit:'억',detail:'전용83~85㎡ 미만 · 7건'}]},
 {mode:'price',title:'A2 · 공고 원문과 확인된 공급금액',caption:'기본 공급금액과 발코니 확장을 합산하고 다른 비용은 구분합니다.',image:'sources/a2_p7.png',items:[{label:'59A · 기본 공급금액',value:5.7167,unit:'억',detail:'59.99㎡ · 5층 이상 · 공고 사례'}]},
 {mode:'chapter',title:'06 · 생활시설',active:'life'}
];
(async()=>{fs.mkdirSync(O,{recursive:true});const cache=path.join(E,'cache'),stills=path.join(cache,'stills'),proof=path.join(O,'preflight');for(const p of [cache,stills,proof])fs.mkdirSync(p,{recursive:true});
 const inputs=[...tree(path.join(R,'video/src/gyosan-production-v1')),...tree(path.join(V,'public')),path.join(R,'video/src/changneung-visual-v8/Guard.tsx'),__filename];const inputDigest=hash(inputs.map(p=>p+':'+hash(fs.readFileSync(p))).join('\n'));
 const serveUrl=await bundle({entryPoint:path.join(R,'video/src/gyosan-production-v1/entry.tsx'),outDir:path.join(cache,'bundle'),publicDir:path.join(V,'public')});
 const browser=await openBrowser('chrome',{browserExecutable:path.join(NM,'.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe')});let calls=0,reused=0;const checks=[];
 const receiptPath=path.join(cache,'verified_stills.json'),old=fs.existsSync(receiptPath)?JSON.parse(fs.readFileSync(receiptPath)):{};const verified=old.input_digest===inputDigest?old.files:{};
 try{const base=await selectComposition({serveUrl,puppeteerInstance:browser,id:'GyosanProduction'});
 async function still(props,dest){const rel=path.relative(E,dest);if(verified[rel]&&fs.existsSync(dest)&&verified[rel]===hash(fs.readFileSync(dest))){reused++;return;}let guard;
 await renderStill({logLevel:'error',serveUrl,puppeteerInstance:browser,composition:{...base,props},frame:0,output:dest,onBrowserLog:l=>{if(l.text.startsWith('V7_LAYOUT '))guard=JSON.parse(l.text.slice(10));}});
 if(!guard?.passed)throw Error('Missing or failed layout evidence: '+dest);checks.push({file:dest,props,...guard});verified[rel]=hash(fs.readFileSync(dest));calls++;}
 for(let i=0;i<representatives.length;i++)await still({...representatives[i],motionFrame:44},path.join(proof,`REP${i+1}_${representatives[i].mode}.png`));
 fs.writeFileSync(path.join(V,'representatives.json'),JSON.stringify(representatives,null,2));
 fs.writeFileSync(path.join(O,'representative_guard.json'),JSON.stringify({input_digest:inputDigest,passed:true,scope:'four representative stills only',checks},null,2));
 if(process.argv.includes('--representatives-only'))return;
 const project=path.join(O,'project.json');if(!fs.existsSync(project))throw Error('project.json not yet available; representatives completed');const P=JSON.parse(fs.readFileSync(project));
 const groups=new Map();for(const x of P.visual_intervals.filter(x=>['body','chapter'].includes(x.kind))){const k=JSON.stringify({...x.props,caption:undefined,motionFrame:undefined});if(!groups.has(k)||(x.props.caption||'').length>(groups.get(k).props.caption||'').length)groups.set(k,x);}
 let i=0;for(const x of groups.values())await still({...x.props,motionFrame:44},path.join(proof,`${String(i++).padStart(3,'0')}_${x.props.mode}.png`));
 fs.writeFileSync(path.join(O,'layout_guard.json'),JSON.stringify({input_digest:inputDigest,passed:true,distinct_variants:groups.size,checks},null,2));
 if(process.argv.includes('--preflight-only'))return;
 const visual=[],jobs=new Map();let lastKey='',start=0;const motionKeys=new Set(),picked=new Set();for(const x of P.visual_intervals){const k=JSON.stringify({...x.props,caption:undefined,motionFrame:undefined});const tag=x.props.mode==='decision'&&['C2','B2'].includes(x.props.active)?x.props.active:x.props.mode;if(['rail','price','comparison','supply','C2','B2'].includes(tag)&&!picked.has(tag)){picked.add(tag);motionKeys.add(k);}}
 for(const x of P.visual_intervals){if(!['body','chapter'].includes(x.kind)){visual.push(x);continue;}const key=JSON.stringify({...x.props,caption:undefined,motionFrame:undefined});if(key!==lastKey){start=x.start_frame;lastKey=key;}let f=x.start_frame;
 while(f<x.end_frame){const elapsed=Math.max(0,f-start),step=motionKeys.has(key)?Math.min(44,elapsed):44,n=Math.min(x.end_frame,step<44?start+step+1:x.end_frame),props={...x.props,motionFrame:step};if(n<=f)throw Error('Invalid interval '+x.scene_id);const dest=path.join(stills,hash(inputDigest+JSON.stringify(props)).slice(0,24)+'.png');jobs.set(dest,props);visual.push({...x,start_frame:f,end_frame:n,duration_frames:n-f,props,source_file:dest});f=n;}}
 const queue=[...jobs];let next=0;async function worker(){while(next<queue.length){const [dest,props]=queue[next++];await still(props,dest);}}await Promise.all([worker(),worker()]);
 fs.writeFileSync(path.join(O,'rendered_project.json'),JSON.stringify({...P,visual_intervals:visual},null,2));
 fs.writeFileSync(path.join(O,'render_receipt.json'),JSON.stringify({completed:true,input_digest:inputDigest,project_sha256:hash(fs.readFileSync(project)),actual_still_calls:calls,reused_verified_stills:reused,visual_intervals:visual.length,distinct_png:jobs.size,layout_guard:'layout_guard.json',motion:'six semantic states use 44 consecutive 30fps frames: rail line, price/comparison bars, calendar marker, C2/B2 parcel emphasis; fixed camera, captions and geography unchanged'},null,2));console.log('STILLS_COMPLETE '+visual.length+' intervals / '+jobs.size+' distinct PNG');
 }finally{fs.writeFileSync(receiptPath,JSON.stringify({input_digest:inputDigest,files:verified},null,2));await browser.close({silent:true});console.log('RENDER_CALLS '+calls+' REUSED '+reused);}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});

