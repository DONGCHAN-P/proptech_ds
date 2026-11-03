"""권장 2건 재검수 결과만 기존 QA 패킷에 추가한다."""
from pathlib import Path
import json, hashlib
OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text('utf-8-sig'))
put=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
receipt=read(OWN/'recommendation_recheck_v2.json')
receipt_path=(OWN/'recommendation_recheck_v2.json').relative_to(ROOT).as_posix()
newhash={Path(x['path']).name:x['sha256'] for x in receipt['checked_file_hashes']}
f=read(OWN/'findings.json');h=read(OWN/'handoff.json')
before={'checked_at_utc':f['checked_at_utc'],'summary':f['summary'].copy(),'input_revisions':h['input_revisions'].copy()}
cap=read(OWN/'issue_JUN-CAP-003.json')
cap['status']='resolved_verified'
cap['checked_revision']={'caption_plan_sha256':newhash['caption_plan.json'],'prepare_captions_sha256':newhash['prepare_captions.py']}
cap['resolution']={'evidence':receipt_path,'result':'5개 제안 정확히 적용. P039Q01/02의 source_start/end가 이동한 실제 원문 범위와 일치. 156큐/48문단 커버리지 및 숫자·단위 경계 유지. 음성 싱크 미확인.','prior_preview_pixel_evidence_reused_without_reinspection':True}
put(OWN/'issue_JUN-CAP-003.json',cap)
dep=read(OWN/'issue_JUN-DEP-004.json')
dep['status']='open_optional'
dep['checked_revision']={'generate_mjs_sha256':newhash['generate.mjs'],'stage_generator_sha256':newhash['stage_generator.py'],'generation_readiness_sha256':newhash['generation_readiness.json']}
dep['followup_recheck']={'evidence':receipt_path,'verified':'common.mjs와 87638016바이트 FFmpeg의 실제 SHA가 readiness 및 생성기 DEPENDENCIES와 일치. 입력 lock에 dependencies 필드가 연결되며 고정 파일 SHA 검사가 인증·GET/POST보다 앞섬.',
 'remaining':'generate.mjs는 const ff=findFFmpeg()로 실행 파일을 선택한 뒤 고정된 dependency.path 두 개만 검사한다. FFMPEG_PATH 또는 findFFmpeg의 fallback으로 다른 ff가 선택되어도 선택 파일 경로/SHA는 검사하지 않는다.',
 'proof':'새 DEPENDENCIES 선언과 검사문만 네트워크 없는 격리 실행. 가상의 미고정 ff 값에서도 고정 파일 SHA 가드는 통과함. 가상의 파일은 읽거나 실행하지 않음.'}
dep['수정안']={'exact_change':'stage_generator.py에서 FFmpeg dependency의 path를 expectedFFmpeg로 생성하고 process.env.FFMPEG_PATH=expectedFFmpeg로 고정한 뒤 findFFmpeg()를 호출한다. 반환 ff의 realpath를 expectedFFmpeg의 realpath와 비교하고, sha(await bytes(ff))를 해당 dependency.sha256와 비교한 뒤 인증·API 단계로 진행한다. common.mjs/readiness/inputs.dependencies 기록은 현재 구현을 유지한다.',
 'required_asserts':['assert.equal(await fs.realpath(ff), await fs.realpath(expectedFFmpeg), "Selected FFmpeg differs from frozen dependency");','assert.equal(sha(await bytes(ff)), frozenFFmpeg.sha256, "Selected FFmpeg changed");'],
 'verification':'외부 요청 없이 선택 파일 불일치가 거절되는지 확인하고 새 generator/readiness SHA만 갱신한다. 음성 입력·5797문자·7000상한 변경 불필요.'}
put(OWN/'issue_JUN-DEP-004.json',dep)
f['findings']=[cap if x['issue_id']=='JUN-CAP-003' else dep if x['issue_id']=='JUN-DEP-004' else x for x in f['findings']]
f['recheck_history']=f.get('recheck_history',[])+[{'revision':'recommendation_recheck_v2','checked_at_utc':receipt['checked_at_utc'],'evidence':receipt_path,'prior_packet':before,'scope':receipt['scope'],'issue_results':receipt['issue_results']}]
f['summary']['recommended_open']=1
f['summary']['recommended_resolved_verified']=1
f['checked_at_utc']=receipt['checked_at_utc']
f['status']='input_QA_valid_bounded_recheck_one_optional_dependency_item_open'
for fresh in receipt['checked_file_hashes']:
    idx=next((i for i,x in enumerate(f['checked_file_hashes']) if x['path']==fresh['path']),None)
    if idx is None:f['checked_file_hashes'].append(fresh)
    else:f['checked_file_hashes'][idx]=fresh
f['input_validation']['latest_caption_plan_sha256']=newhash['caption_plan.json']
f['input_validation']['meaning_boundary_recheck']=receipt_path
f['generator_review']['dependency_recheck']=receipt_path
f['generator_review']['current_generator_sha256']=newhash['generate.mjs']
put(OWN/'findings.json',f)
h['status']='completed_bounded_recheck_one_optional_open'
for name in ['caption_plan.json','generate.mjs','stage_generator.py']:
    h['input_revisions'][name]=newhash[name]
h['input_revisions']['generation_readiness.json']=newhash['generation_readiness.json']
h['input_revisions']['prepare_captions.py']=newhash['prepare_captions.py']
if receipt_path not in h['outputs']:h['outputs'].append(receipt_path)
h['checks'] += [{'check':'JUN-CAP-003 5개 경계·P039 범위·156큐 유지','result':'resolved_verified','evidence':receipt_path},{'check':'JUN-DEP-004 SHA 고정/실행 선택 결합','result':'partially_verified_optional_open','evidence':receipt_path}]
h['open_issue_ids']=['JUN-DEP-004']
h['required_open_issue_ids']=[]
h['next_actions']=['권장 JUN-DEP-004의 실제 선택 ff 경로·SHA 결합 여부 판단. 정확한 수정안은 해당 이슈 파일 참조.','기존 신규 예산 승인 게이트 유지. 음성 입력 SHA 5290eff5…·5797문자·7000상한·추가현금0 유지.']
h['summary']='권장2건 한정 재검수. 자막5개 제안·P039 source-range 이동·156큐/48문단·숫자단위 보호 확인 후 JUN-CAP-003 종료. common/87MB FFmpeg SHA와 readiness/input_lock 연결은 확인했으나 실제 선택된 ff가 고정 경로/SHA에 결합되지 않아 JUN-DEP-004 권장1건 열림. 필수미해결0. 음성 입력·예산 불변. 시안/정책 재검수·TTS·인증요청·청취·전체본 실행 없음.'
h['checked_file_hashes']['count']=len(f['checked_file_hashes'])
h['bounded_recheck_evidence']=receipt_path
put(OWN/'handoff.json',h)
print(json.dumps({'findings':f['summary'],'open_issues':h['open_issue_ids'],'receipt_sha256':hashlib.sha256((OWN/'recommendation_recheck_v2.json').read_bytes()).hexdigest()},ensure_ascii=False))
