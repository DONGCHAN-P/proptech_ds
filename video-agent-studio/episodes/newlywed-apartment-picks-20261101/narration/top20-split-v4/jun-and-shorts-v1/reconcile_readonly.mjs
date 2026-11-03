// 생성 후 계정의 지연 반영을 한 번만 GET으로 대조. 이 파일에는 POST 기능이 없다.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const ROOT='C:/projects/realestate_reco',DIR=path.dirname(fileURLToPath(import.meta.url));
const sha=x=>createHash('sha256').update(x).digest('hex');
const json=async p=>JSON.parse(await fs.readFile(p,'utf8'));
async function save(p,x){const tmp=p+'.tmp';await fs.writeFile(tmp,JSON.stringify(x,null,2)+'\n');await fs.rename(tmp,p);}
const ledger=await json(path.join(DIR,'generation_ledger.json'));
assert.equal(ledger.requests.length,16);assert.ok(ledger.requests.every(r=>r.status==='complete'));
assert.equal(ledger.actual_credits,ledger.requests.reduce((s,r)=>s+Number(r.response_headers['character-cost']),0));
assert.ok(0<=ledger.actual_credits&&ledger.actual_credits<=ledger.submitted_characters&&ledger.submitted_characters<=6500);
for(const r of ledger.requests){
  assert.equal(r.actual_credits,Number(r.response_headers['character-cost']));
  for(const [p,h]of Object.entries(r.artifact_sha256))assert.equal(sha(await fs.readFile(path.join(ROOT,p))),h);
}
const before=await json(path.join(DIR,'account_final.json'));
if(!await fs.access(path.join(DIR,'account_final_immediate.json')).then(()=>true,()=>false))await save(path.join(DIR,'account_final_immediate.json'),before);
const env=await fs.readFile(path.join(ROOT,'.env'),'utf8');
const key=env.match(/^\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*?)\s*$/m)?.[1].replace(/^(['"])(.*)\1$/,'$2');
assert.ok(key,'Credential missing');
const response=await fetch('https://api.elevenlabs.io/v1/user/subscription',{method:'GET',headers:{'xi-api-key':key},redirect:'error',signal:AbortSignal.timeout(30000)});
assert.equal(response.status,200,'Reconciliation GET failed; no automatic retry');
const s=await response.json();assert.equal(s.max_credit_limit_extension,0);assert.equal(s.can_extend_character_limit,false);assert.equal(s.allowed_to_extend_character_limit,false);
const at=new Date().toISOString(),delta=s.character_count-ledger.initial_character_count;
const safe={checked_at_utc:at,subscription:{tier:s.tier,status:s.status,character_count:s.character_count,character_limit:s.character_limit,
  included_remaining:s.character_limit-s.character_count,max_credit_limit_extension:s.max_credit_limit_extension,can_extend_character_limit:s.can_extend_character_limit,allowed_to_extend_character_limit:s.allowed_to_extend_character_limit},
  header_actual_credits:ledger.actual_credits,observed_account_delta:delta,header_account_delta_matches:delta===ledger.actual_credits,
  get_calls_this_reconciliation:1,tts_post_calls_this_reconciliation:0,immediate_snapshot_preserved:'account_final_immediate.json'};
await save(path.join(DIR,'account_final.json'),safe);
assert.equal(safe.header_account_delta_matches,true,'Account delta not yet reconciled; do not regenerate or retry POST');
ledger.resolved_local_validation_failure=ledger.failure;
delete ledger.failure;
ledger.status='all16_generated_measured_native_alignment_not_listened';ledger.updated_at_utc=at;
ledger.final_included_remaining=safe.subscription.included_remaining;ledger.observed_account_delta=delta;ledger.header_account_delta_matches=true;
ledger.reconciliation={at_utc:at,source:'per_request_character_cost_headers_and_final_account_GET',
  initial_final_snapshot_delay_observed:true,post_retries:0,additional_paid_calls:0,
  local_guard_fix:'예산은 실비 상한이며 예상5520과의 동일액은 조건이 아님; 실제2208을 헤더 합계와 계정 차분으로 대조'};
await save(path.join(DIR,'generation_ledger.json'),ledger);
const ip=path.join(DIR,'issue_JUN_GENERATION_BLOCK.json');
const issue=await json(ip);issue.status='resolved_without_new_generation';issue.resolution={at_utc:at,actual_credits:ledger.actual_credits,included_remaining:ledger.final_included_remaining,header_account_delta_matches:true,additional_paid_calls:0};await save(ip,issue);
console.log(JSON.stringify({status:ledger.status,actual_credits:ledger.actual_credits,account_delta:delta,included_remaining:ledger.final_included_remaining,unused_cap:6500-ledger.actual_credits,post_calls:0}));
