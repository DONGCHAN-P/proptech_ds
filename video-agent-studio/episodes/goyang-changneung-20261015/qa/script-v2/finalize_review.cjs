const fs=require('fs'),crypto=require('crypto'),path=require('path');
const q=__dirname,p=path.resolve(q,'../..');
const get=f=>JSON.parse(fs.readFileSync(path.join(q,f),'utf8').replace(/^\uFEFF/,''));
const put=(f,v)=>fs.writeFileSync(path.join(q,f),JSON.stringify(v,null,2)+'\n');
const h=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(p,f))).digest('hex');
const checks=get('independent_checks.json');
if(checks.chapters.some(x=>!x.hash_match||!x.text_match||!x.count_match)||checks.inputs.some(x=>!x.match)||!checks.joined_match||!checks.script_hash_match||!checks.source_xlsx_hash_match||checks.commute_calculation.some(x=>!x.all_arithmetic_match))throw Error('Independent check failed');
const evidence={
 'QA-V2-001':'M006 낭독의 제한기간 내 소유권 이전등기 완료 예외 및 거주의무 별도 문장을 직접 재확인. 보존 공고 TXT와 일치.',
 'QA-V2-002':'M002 홍대·김포 시간 낭독 제거, 원흥 출발 목적지역 시간 우선으로 변경됨.',
 'QA-V2-003':'M002 원흥→경복궁24/종로3가28/교대49분. 코레일 공개표 2022.08.01 시행·평일07~09시 조건, 접근·대기·회사이동 제외 명시. 새 조사13claims 및 추가보고서·계산JSON을 읽고 18편씩 차감 산술과 원본파일해시 확인. 실측 및 최신 변경공지 전수검증으로 승격하지 않음.',
 'QA-V2-004':'M003 LX 방문안내 사례 한정, 상세번호 화면 이동, 노선안내상 7728 표현, 새 단지 정류장·입주시 실제운행 재확인 문장 직접 확인.'
};
let findings=get('findings.json');findings.revision='qa-script-v2-corrected';for(const x of findings.findings){x.initial_checked_revision=x.checked_revision;x.checked_revision='script-v2-corrected '+checks.script_hash;x.status='closed_verified';x.recheck_evidence=evidence[x.issue_id];}put('findings.json',findings);
let r=get('final_review.json');r.revision='qa-script-v2-corrected';r.status='passed_script_scope';r.checked_script_sha256=checks.script_hash;r.checked_joined_sha256=checks.joined_sha256;r.chapter_character_sum=checks.individual_character_sum;r.joined_character_count=checks.individual_character_sum+18;r.open_required=[];r.open_critical=[];r.rechecked_scenes=['M002','M003','M004','M006'];r.connection_scenes=['M001','M005','M007'];r.coverage.research_checked+='; corrected commute-v3 facts 13claims, addendum_ilsan.md, ilsan_calculation.json';r.coverage.commute_calculation='4 destinations ×18 samples arithmetic verified; preserved XLSX file hash matched. XLSX cells not independently parsed by QA; researcher extraction inherited.';r.limitations.push('상암·여의도·마곡 전체시간은 미확보로 임의 수치를 추가하지 않음. 목적지역까지 철도 구간의 대표 시간은 도심·교대 사례에 한정.');r.confirmed.push('수정4건 직접 재검수로 closed_verified. M004 반복 경고 축소 후 현재비교·미래값 구분 유지.');put('final_review.json',r);
let hand=get('handoff.json');hand.revision=r.revision;hand.status='passed_script_scope';hand.input_script_sha256=checks.script_hash;hand.input_joined_sha256=checks.joined_sha256;hand.input_versions=['script-v2-corrected 6384 characters','commute-v3 with ilsan addendum and 13claims','price-stage-v3','production-v2','prices-v2'];hand.unresolved=[];hand.closed_issues=Object.keys(evidence);hand.next_owner='director: revised script/budget user decision gate';hand.peer_contact='초기 required 문제를 writer 및 총괄에 직접 전달. 작가 수정 후 실제 텍스트·근거·해시를 재검수하여 닫음.';hand.validation.push('원흥 목적지역 18편 산술 및 XLSX 파일해시 확인; 원XML 셀 재파싱 아님');hand.outputs_sha256={};for(const f of hand.outputs){hand.outputs_sha256[f]=h(f);}put('handoff.json',hand);
console.log(JSON.stringify({status:r.status,script_sha256:checks.script_hash,characters:r.chapter_character_sum,open_required:0,outputs:hand.outputs_sha256}));
