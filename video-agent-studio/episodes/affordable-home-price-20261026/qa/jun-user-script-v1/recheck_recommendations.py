"""JUN-CAP-003 / JUN-DEP-004 한정 재검수. 원자료·시안 재검수 없음."""
from pathlib import Path
import ast, hashlib, json, re, subprocess
from datetime import datetime, timezone

OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+','',s)
prior=read(OWN/'findings.json')
prior_hash={x['path']:x['sha256'] for x in prior['checked_file_hashes']}
checks=[]
def check(name,ok,evidence):
    checks.append({'check':name,'result':'pass' if ok else 'fail','evidence':evidence})
paths=[N/'generation_input.json',N/'budget_proposal.json',N/'narration_manifest.json']
for p in paths:check(p.name+'_unchanged',sha(p)==prior_hash[p.relative_to(ROOT).as_posix()],sha(p))
g=read(paths[0]);b=read(paths[1]);m=read(paths[2]);c=read(N/'caption_plan.json')
check('voice_text_and_budget_unchanged',sum(len(p['proposed_spoken_text']) for p in g['paragraphs'])==5797 and b['included_credit_cap_proposed']==7000 and b['additional_cash_cap_krw']==0,{'generation_input_sha256':sha(paths[0]),'budget_sha256':sha(paths[1]),'billed_characters':5797,'cap':7000,'cash_krw':0})
proposal=read(OWN/'issue_JUN-CAP-003.json')['수정안']['exact_proposals']
qs={x['cue_id']:x for x in c['cues']}
match=[{'cue_id':p['cue_id'],'matches':all(qs[p['cue_id']][k]==v for k,v in p.items()),'source_start':qs[p['cue_id']]['source_start'],'source_end':qs[p['cue_id']]['source_end'],'display_lines':qs[p['cue_id']]['display_lines']} for p in proposal]
check('five_exact_caption_changes',all(x['matches'] for x in match) and len(match)==5,match)
by_id={p['paragraph_id']:p['text'] for p in m['paragraphs']}
errors=[];protected=0;boundaries=0
amount=re.compile(r'\d[\d,]*(?:\.\d+)?(?:[억천백십만](?:\d[\d,]*(?:\.\d+)?)?)*(?:원|퍼센트|제곱미터|개월|년|주택)?')
for pid,text in by_id.items():
    selected=[q for q in c['cues'] if q['paragraph_id']==pid]
    if norm(''.join(q['text'] for q in selected))!=norm(text):errors.append([pid,'coverage'])
    spans=[(x.start(),x.end(),x.group()) for x in amount.finditer(norm(text))];protected+=len(spans)
    offset=0;last=0
    for q in selected:
        a,z=q['source_start'],q['source_end']
        if a<last or text[last:a].strip() or text[a:z]!=q['text']:errors.append([q['cue_id'],'source_range'])
        if norm(''.join(q['display_lines']))!=norm(q['text']) or not 1<=len(q['display_lines'])<=2:errors.append([q['cue_id'],'display'])
        for line in q['display_lines']:
            offset+=len(norm(line));boundaries+=1
            for x,y,token in spans:
                if x<offset<y:errors.append([q['cue_id'],'amount_unit_split',token])
        if q['start_s'] is not None or q['end_s'] is not None:errors.append([q['cue_id'],'invented_timing'])
        last=z
    if text[last:].strip():errors.append([pid,'tail'])
check('caption_156_48_paragraphs_ranges_and_numeric_boundaries',len(c['cues'])==len(qs)==156 and len(by_id)==48 and not errors,{'errors':errors,'protected_spans':protected,'line_or_cue_boundaries':boundaries,'cue_count':len(qs),'paragraphs':len(by_id),'max_line_characters':max(len(s) for q in c['cues'] for s in q['display_lines'])})
ast.parse((N/'prepare_captions.py').read_text('utf-8-sig'))
ast.parse((EP/'director/jun-user-script-v1/stage_generator.py').read_text('utf-8-sig'))
code=(N/'generate.mjs').read_text('utf-8-sig');ready=read(N/'generation_readiness.json')
dep_json=re.search(r'^const DEPENDENCIES=(\[.*\]);$',code,re.M)
assert dep_json,'Missing generated DEPENDENCIES'
deps=json.loads(dep_json[1]);actual=[]
for dep in deps:
    p=ROOT/dep['path'];actual.append({**dep,'measured_bytes':p.stat().st_size,'measured_sha256':sha(p)})
check('two_dependency_files_SHA_and_readiness_match',len(deps)==2 and deps==ready['dependencies'] and all(x['bytes']==x['measured_bytes'] and x['sha256']==x['measured_sha256'] for x in actual),actual)
check('readiness_generator_hash_and_input_lock_dependency_field',ready['generator_sha256']==sha(N/'generate.mjs') and ready['generation_input_sha256']==sha(N/'generation_input.json') and 'dependencies:DEPENDENCIES,authorization_id:auth.authorization_id' in code,{'generator_sha256':sha(N/'generate.mjs'),'input_lock':'生成기 inputs.dependencies 필드 정적 확인; 실제 lock 파일 미생성'})
guard_line=next(line for line in code.splitlines() if line.startswith('for(const dependency of DEPENDENCIES)'))
check('fixed_dependency_checks_before_credentials_and_network',code.index(guard_line)<code.index('let key=')<code.index('await fetch('),guard_line)
node=Path('C:/Program Files/nodejs/node.exe')
syntax=subprocess.run([str(node),'--check',str(N/'generate.mjs')],capture_output=True,text=True)
check('node_syntax_and_Python_AST',syntax.returncode==0,{'node_exit':syntax.returncode,'stderr':syntax.stderr,'Python_AST':'pass'})
# 원본 생성기 실행 없이 새 의존성 가드 2줄만 격리해 실제 선택 파일 결합 여부를 확인.
# 가상의 ff 경로는 읽거나 실행하지 않는다. 읽기는 고정된 두 로컬 파일뿐이다.
js="""const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=p=>fs.readFile(p);
const ROOT=__ROOT__;
const ff='C:/QA-NOT-EXECUTED/unfrozen-ffmpeg.exe';
(async()=>{__DECL__
__GUARD__
console.log(JSON.stringify({fixed_dependencies_pass:true,selected_ffmpeg:ff,selected_ffmpeg_is_declared:DEPENDENCIES.some(d=>path.resolve(ROOT,d.path)===path.resolve(ff)),external_file_read_or_execution:false,authenticated_requests:0}));})().catch(e=>{console.error(e.message);process.exitCode=1});
""".replace('__ROOT__',json.dumps(str(ROOT))).replace('__DECL__',dep_json[0]).replace('__GUARD__',guard_line)
proof=subprocess.run([str(node),'-e',js],capture_output=True,text=True)
assert proof.returncode==0,proof.stderr
proof_data=json.loads(proof.stdout)
check('selected_ffmpeg_is_bound_by_new_guard',proof_data['selected_ffmpeg_is_declared'],{'isolated_guard_test':proof_data,'finding':'FFMPEG_PATH를 따르는 findFFmpeg()의 반환 ff가 고정 FFmpeg 경로/해시와 결합되지 않음. 고정 파일 두 개만 무결해도 새 가드는 통과함.','scope':'새 의존성 가드 2줄만 격리 실행. 전체 생성기·외부 바이너리·네트워크 실행 없음.'})
checked_paths=[N/'prepare_captions.py',N/'caption_plan.json',EP/'director/jun-user-script-v1/stage_generator.py',N/'generate.mjs',N/'generation_readiness.json']+paths+[ROOT/d['path'] for d in deps]
report={'task_id':'JUN-USER-SCRIPT-V1-RECOMMENDATION-RECHECK','checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'JUN-CAP-003 및 JUN-DEP-004 변경분만. 기존 시안 픽셀·원자료·정책 재검수 없음.','checks':checks,'checked_file_hashes':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in checked_paths],'issue_results':{'JUN-CAP-003':'resolved_verified','JUN-DEP-004':'open_optional_selected_ffmpeg_not_bound'},'no_generator_entrypoint_or_authenticated_execution':True}
report['checks'][next(i for i,x in enumerate(checks) if x['check']=='readiness_generator_hash_and_input_lock_dependency_field')]['evidence']['input_lock']='생성기 inputs.dependencies 필드 정적 확인; 실제 lock 파일 미생성'
(OWN/'recommendation_recheck_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed_checks':[x['check'] for x in checks if x['result']=='fail'],'issues':report['issue_results']},ensure_ascii=False))
