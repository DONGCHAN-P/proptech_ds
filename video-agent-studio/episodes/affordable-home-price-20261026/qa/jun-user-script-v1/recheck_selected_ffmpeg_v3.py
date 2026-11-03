"""DEP004 최종 선택 SHA 가드만 격리 검증하고 기존 QA에 추가한다."""
from pathlib import Path
import ast, hashlib, json, re, subprocess
from datetime import datetime, timezone
OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
put=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=read(OWN/'recommendation_recheck_v2.json')
oldhash={x['path']:x['sha256'] for x in prior['checked_file_hashes']}
code=(N/'generate.mjs').read_text('utf-8-sig')
stage=EP/'director/jun-user-script-v1/stage_generator.py'
stage_text=stage.read_text('utf-8-sig')
ready=read(N/'generation_readiness.json')
decl=re.search(r'^const DEPENDENCIES=(\[.*\]);$',code,re.M)
deps=json.loads(decl[1]);assert deps==ready['dependencies']
guard='\n'.join(line for line in code.splitlines() if line.startswith('const selectedFFmpeg=') or line.startswith('assert.equal(selectedFFmpeg.sha256,'))
assert len(guard.splitlines())==2
assert code.index(guard)<code.index('let key=')<code.index('await fetch(')
assert 'selected_ffmpeg:selectedFFmpeg,authorization_id:' in code
assert 'sha(await bytes(ff))' in stage_text and 'Selected FFmpeg differs from frozen dependency' in stage_text
assert ready['generator_sha256']==sha(N/'generate.mjs')
ast.parse(stage_text)
node='C:/Program Files/nodejs/node.exe'
syntax=subprocess.run([node,'--check',str(N/'generate.mjs')],capture_output=True,text=True)
assert syntax.returncode==0,syntax.stderr
ff=ROOT/deps[1]['path']
js="""const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const DEPENDENCIES=__DEPS__;
const actualPath=__PATH__;
(async()=>{
const realBytes=await fs.readFile(actualPath);
const cases=[];
for(const mode of ['actual_frozen_binary','different_binary_bytes','missing_selected_file']){
 const ff=mode==='actual_frozen_binary'?actualPath:'C:/QA-NOT-EXECUTED/'+mode+'.exe';
 const bytes=async p=>{if(mode==='missing_selected_file')throw Object.assign(new Error('fixture missing'),{code:'ENOENT'});return mode==='actual_frozen_binary'?realBytes:Buffer.from('QA fixture: different binary bytes; never executed');};
 try{__GUARD__
 cases.push({case:mode,accepted:true,selected_ffmpeg:selectedFFmpeg});}
 catch(e){cases.push({case:mode,accepted:false,error_code:e.code,error:e.message.split('\\n')[0]});}
}
assert.equal(cases[0].accepted,true);assert.equal(cases[1].accepted,false);assert.equal(cases[2].accepted,false);
console.log(JSON.stringify({cases,actual_bytes:realBytes.length,actual_sha256:sha(realBytes),external_requests:0,binary_execution:false,generator_entrypoint_executed:false}));
})().catch(e=>{console.error(e.message);process.exitCode=1});
""".replace('__DEPS__',json.dumps(deps)).replace('__PATH__',json.dumps(str(ff))).replace('__GUARD__',guard)
proof=subprocess.run([node,'-e',js],capture_output=True,text=True)
assert proof.returncode==0,proof.stderr
proof_data=json.loads(proof.stdout)
assert proof_data['actual_sha256']==deps[1]['sha256'] and proof_data['actual_bytes']==deps[1]['bytes']
assert sha(ROOT/deps[0]['path'])==deps[0]['sha256']
unchanged=[]
for name in ['generation_input.json','budget_proposal.json','caption_plan.json']:
    p=N/name;digest=sha(p);assert digest==oldhash[p.relative_to(ROOT).as_posix()]
    unchanged.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest})
changed=[stage,N/'generate.mjs',N/'generation_readiness.json']
receipt={'task_id':'JUN-DEP-004-SELECTED-FFMPEG-RECHECK','checked_at_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'선택된 FFmpeg SHA 가드·lock 기록과 변경 3개 파일만 재검수. 자막/정책/시안 재검수 없음.',
 'guard_lines':guard,'guard_before_credentials_and_network':True,
 'isolated_guard_proof':proof_data,'input_lock_record':'inputs.selected_ffmpeg가 실제 선택 파일의 path.resolve(ff)와 실측 SHA를 포함. 생성기 input_lock 저장 경로에 동일 inputs 전달. 실제 생성기/lock 생성은 미실행.',
 'stage_emits_same_guard':True,'node_syntax':'pass','Python_AST':'pass',
 'dependencies':deps,'unchanged_input_budget_caption':unchanged,
 'checked_file_hashes':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in changed],
 'result':'resolved_verified','authority':'승인 생성·TTS·인증 요청 없음. 네트워크 없는 새 가드 2줄만 격리 실행.'}
rp=OWN/'selected_ffmpeg_recheck_v3.json';put(rp,receipt)
rel=rp.relative_to(ROOT).as_posix()
dep=read(OWN/'issue_JUN-DEP-004.json')
dep['status']='resolved_verified'
dep['checked_revision']={p.name:sha(p) for p in changed}
dep['resolution']={'evidence':rel,'method':'실제 선택된 87638016바이트 파일의 SHA 일치 통과, 다른 바이트·파일 읽기 실패 거절을 격리 가드로 검증. 인증 단계 이전 배치와 input_lock에 실제 절대경로/SHA가 기록되는 연결 확인.',
 'actual_selected_sha256':proof_data['actual_sha256'],'selected_path':proof_data['cases'][0]['selected_ffmpeg']['path'],
 'path_policy':'다른 경로라도 동일 SHA의 동일 바이너리는 허용 가능. 실제 선택 경로를 기록하며 다른 바이너리 바이트는 거절함.',
 'generator_entrypoint_executed':False}
put(OWN/'issue_JUN-DEP-004.json',dep)
f=read(OWN/'findings.json');h=read(OWN/'handoff.json')
f['findings']=[dep if x['issue_id']=='JUN-DEP-004' else x for x in f['findings']]
f['summary']['recommended_open']=0;f['summary']['recommended_resolved_verified']=2
f['checked_at_utc']=receipt['checked_at_utc'];f['status']='completed_preproduction_QA_all_findings_closed_with_scope_limits'
f['recheck_history'].append({'revision':'selected_ffmpeg_recheck_v3','checked_at_utc':receipt['checked_at_utc'],'evidence':rel,'scope':receipt['scope'],'issue_results':{'JUN-DEP-004':'resolved_verified','JUN-CAP-003':'resolved_verified_from_v2_unchanged_caption_SHA'}})
for fresh in receipt['checked_file_hashes']:
    idx=next(i for i,x in enumerate(f['checked_file_hashes']) if x['path']==fresh['path']);f['checked_file_hashes'][idx]=fresh
f['generator_review']['dependency_recheck']=rel
f['generator_review']['current_generator_sha256']=sha(N/'generate.mjs')
put(OWN/'findings.json',f)
h['status']='completed_preproduction_QA_no_open_findings'
for p in changed:h['input_revisions'][p.name]=sha(p)
if rel not in h['outputs']:h['outputs'].append(rel)
h['open_issue_ids']=[];h['required_open_issue_ids']=[]
h['checks'].append({'check':'JUN-DEP-004 실제 선택 FFmpeg SHA 및 기록','result':'resolved_verified','evidence':rel})
h['next_actions']=['7000크레딧 상한의 현재 버전 신규 예산 승인 대기.','실제 음성 이후 정렬·발음·싱크·본편 검수 진행.']
h['summary']='사전제작 QA 종료. JUN-IN-001과 권장 JUN-CAP-003/JUN-DEP-004 모두 검증 후 닫힘. 상단 잘림 오탐 종료. 선택 FFmpeg 실제 SHA 일치 통과/다른 바이너리 거절 및 input_lock 절대경로·SHA 기록 확인. 음성 입력5290eff5…·5797문자·7000상한·현금0·자막 SHA 불변. 기존 3시안 표본 근거 유지. 청취/연속재생/전체본/TTS/인증 요청 미실행. 예산 신규 승인 대기.'
h['bounded_recheck_evidence']=rel
put(OWN/'handoff.json',h)
for p in changed:assert sha(p)==next(x['sha256'] for x in receipt['checked_file_hashes'] if x['path']==p.relative_to(ROOT).as_posix())
assert all(x['status']=='resolved_verified' for x in read(OWN/'findings.json')['findings'])
assert not read(OWN/'handoff.json')['open_issue_ids']
print(json.dumps({'result':'all_findings_closed','summary':f['summary'],'guard_tests':[{'case':x['case'],'accepted':x['accepted']} for x in proof_data['cases']],'new_hashes':receipt['checked_file_hashes'],'receipt_sha256':sha(rp)},ensure_ascii=False))
