// Local fixtures only. No .env copy, no account reads, no network, no synthesis.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {DIR, ROOT, EP, SCRIPT_SHA, MANIFEST_SHA, VOICE, MODEL, CAP, sha, loadInputs, saveJSON,
  costHeader, checkBudget, validateAlignment, checkAccount, checkRates} from './common.mjs';
import {validateAuthorization} from './generate.mjs';
import {captionPlan, atomsFor, timedCaptions} from './build_timing.mjs';

const inputs = await loadInputs();
const sandbox = path.join(DIR, '.offline-tests');
const base = path.join(sandbox, 'fixture');
const fixtureDir = path.join(base, path.relative(ROOT, DIR));
await fs.mkdir(fixtureDir, {recursive:true});
await fs.writeFile(path.join(sandbox,'README.txt'),'OFFLINE TEST FIXTURE ONLY. Mock decisions are not user approval. No secrets copied. Generator fetch is permanently disabled.\n');
const copy = async p => {const dest=path.join(base,path.relative(ROOT,p));await fs.mkdir(path.dirname(dest),{recursive:true});await fs.copyFile(p,dest);};
for (const p of [path.join(DIR,'manifest.json'), ...inputs.manifest.paragraphs.map(b=>path.join(DIR,b.path)),
  inputs.scriptPath, path.join(ROOT,'config/tts.json'), path.join(EP,'outputs/production-v1-budget/budget_proposal.json'),
  path.join(ROOT,'video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs'),
  path.join(DIR,'common.mjs')]) await copy(p);
const eventPath = path.join(sandbox,'network_attempts.jsonl');
await fs.writeFile(eventPath,'');
const mockPrefix = 'globalThis.fetch = async () => { await fs.appendFile('+JSON.stringify(eventPath)+', "ATTEMPT\\n"); throw Error("OFFLINE TEST: NETWORK DISABLED"); };\n';
await fs.writeFile(path.join(fixtureDir,'generate.mjs'),mockPrefix+await fs.readFile(path.join(DIR,'generate.mjs'),'utf8'));
const fixtureInputs = {...inputs, code:{'common.mjs':sha(await fs.readFile(path.join(fixtureDir,'common.mjs'))),
  'generate.mjs':sha(await fs.readFile(path.join(fixtureDir,'generate.mjs')))}};
const decisionID='000000000001', now=Date.now(), issued=new Date(now-1000).toISOString(), expires=new Date(now+3600000).toISOString();
const decision={id:decisionID,gate:'budget',episode:'regional-price-recovery-20261022',status:'approved',
  created_at:new Date(now-3600000).toISOString(),expires_at:expires,
  artifact_hashes:{'script_v3.md':SCRIPT_SHA,narration_manifest:MANIFEST_SHA},included_credit_cap:CAP,
  additional_cash_usd_cap:0,automatic_retry:false,fixture_only:true};
const dp=path.join(base,'output/video_decisions/decisions',decisionID+'.json');
await fs.mkdir(path.dirname(dp),{recursive:true});
const auth={root_execution_authorized:true,paid_api_authorized:true,external_transmission_authorized:true,
  episode_id:'regional-price-recovery-20261022',production_revision:'production-v1-jun',script_revision:'v3',
  script_sha256:SCRIPT_SHA,narration_manifest_sha256:MANIFEST_SHA,config_sha256:inputs.config_sha256,
  budget_proposal_sha256:inputs.quote_sha256,voice_id:VOICE,model:MODEL,generator_code_sha256:fixtureInputs.code,
  included_credit_cap:CAP,additional_cash_usd_cap:0,automatic_retry:false,topup_or_overage_authorized:false,
  budget_decision_id:decisionID,issued_at:issued,expires_at:expires,fixture_only:true};
const writeAuth = async (d=decision, a={}) => {
  await saveJSON(dp,d); const hash=sha(await fs.readFile(dp));
  await saveJSON(path.join(fixtureDir,'authorization.json'),{...auth,budget_decision_sha256:hash,...a});
  return {...auth,budget_decision_sha256:hash,...a};
};
const results=[];
function unit(name, fn) {fn();results.push({check:name,result:'passed'});}
async function rejected(name, expected) {
  const r=spawnSync(process.execPath,[path.join(fixtureDir,'generate.mjs'),'--execute-approved'],
    {cwd:base,encoding:'utf8',windowsHide:true,maxBuffer:1024*1024});
  assert.equal(r.error,undefined, name+': process launch'); assert.notEqual(r.status,0,name+': must reject');
  const output=r.stderr+r.stdout; assert.match(output,expected,name+': rejection reason');
  assert.equal(await fs.readFile(eventPath,'utf8'),'','Any network attempt is a test failure');
  results.push({check:name,result:'passed',exit_code:r.status,network_calls:0});
}
// Ensure the mocked fetch is live: a positive control writes an event and rejects without external I/O.
const mockProbe=spawnSync(process.execPath,['--input-type=module','-e',
  'import fs from "node:fs/promises";'+mockPrefix+'try {await fetch("https://invalid.local");}catch {}'],{encoding:'utf8',windowsHide:true});
assert.equal(mockProbe.status,0);assert.equal(await fs.readFile(eventPath,'utf8'),'ATTEMPT\n');await fs.writeFile(eventPath,'');
results.push({check:'network_mock_positive_control',result:'passed',external_requests:0});
// The fixture directory is reused; remove only the specifically named fixture authorization, if present.
try {await fs.unlink(path.join(fixtureDir,'authorization.json'));} catch(e) {if(e.code!=='ENOENT')throw e;}
await rejected('missing_authorization_rejected_before_network',/authorization missing/);
await writeAuth({...decision,status:'pending'});
await rejected('pending_budget_rejected_before_network',/Budget decision is not approved/);
await writeAuth(decision,{script_sha256:'0'.repeat(64)});
await rejected('authorization_script_sha_mismatch_before_network',/99b40e8730/);
await writeAuth(decision,{narration_manifest_sha256:'0'.repeat(64)});
await rejected('authorization_manifest_sha_mismatch_before_network',/92ee18d147/);
await writeAuth({...decision,artifact_hashes:{...decision.artifact_hashes,narration_manifest:'0'.repeat(64)}});
await rejected('decision_manifest_sha_mismatch_before_network',/92ee18d147/);
await writeAuth();
const fixtureScript=path.join(base,path.relative(ROOT,inputs.scriptPath));
await fs.appendFile(fixtureScript,'\nOFFLINE MUTATION');
await rejected('changed_script_bytes_before_network',/Approved script changed/);await copy(inputs.scriptPath);
await fs.appendFile(path.join(fixtureDir,'manifest.json'),' ');
await rejected('changed_manifest_bytes_before_network',/Frozen manifest changed/);await copy(path.join(DIR,'manifest.json'));
const rd=path.join(fixtureDir,'receipts');await fs.mkdir(rd,{recursive:true});
for (const status of ['request_started','pending_no_automatic_retry','failed','failed_no_automatic_retry']) {
  await saveJSON(path.join(rd,'S001-P1.json'),{status,fixture_only:true});
  await rejected(status+'_receipt_before_network',/pending\/failed, no retry or duplicate/);
}
await fs.unlink(path.join(rd,'S001-P1.json'));
const validAuth=await writeAuth();
unit('valid_matching_authorization_positive_control',()=>validateAuthorization(validAuth,decision,fixtureInputs,validAuth.budget_decision_sha256,now));
unit('expired_authorization_rejected',()=>assert.throws(()=>validateAuthorization({...validAuth,expires_at:issued},decision,fixtureInputs,validAuth.budget_decision_sha256,now)));
unit('missing_unknown_or_excess_charge_rejected',()=>{for(const raw of [null,'','unknown','NaN','1e3','-1','101'])assert.throws(()=>costHeader(raw,100));assert.equal(costHeader('100',100),100);});
unit('cumulative_reserved_cost_cap_enforced',()=>{checkBudget(4839,968,0);assert.throws(()=>checkBudget(4839,969,0));});
unit('live_included_only_and_rates_guard',()=>{
  const s={status:'active',tier:'starter',character_limit:40000,character_count:17442,can_extend_character_limit:false,allowed_to_extend_character_limit:false,max_credit_limit_extension:0};
  checkAccount(s,4839);assert.throws(()=>checkAccount({...s,can_extend_character_limit:true},1));assert.throws(()=>checkAccount(s,30000));
  const rates={passed:true,overage_enabled:false,allowed_to_extend:false,max_extension:0,voice_rate:1,model_rates:{character_cost_multiplier:1,cost_discount_multiplier:1}};
  checkRates(rates);assert.throws(()=>checkRates({...rates,voice_rate:1.1}));
});
unit('alignment_exact_text_monotonic_duration_guards',()=>{
  const a={characters:['가','나'],character_start_times_seconds:[0,0.5],character_end_times_seconds:[0.5,1]};
  validateAlignment(a,'가나',1);assert.throws(()=>validateAlignment(a,'가다',1));
  assert.throws(()=>validateAlignment({...a,character_start_times_seconds:[0.5,0]},'가나',1));assert.throws(()=>validateAlignment(a,'가나',0.9));
});
unit('protected_number_unit_atoms',()=>{
  for(const s of ['칠 년 구 개월이 걸렸습니다.','삼 점 사 퍼센트 하락입니다.','8만 114세대가 입주합니다.','2029년 3월에 입주합니다.','약 삼 점 사 퍼센트 하락입니다.']) {
    const a=atomsFor(s);assert.ok(a[0].text.includes(s.split(' ').slice(0,-1).join(' ')),s);
  }
});
const plans=inputs.manifest.paragraphs.map(b=>({beat_id:b.beat_id,scene_id:b.scene_id,timing_basis:'untimed_offline_candidate',captions:captionPlan(b.text)}));
unit('all_39_original_caption_plans_lossless_55chars_2lines',()=>{
  for(const [i,b]of inputs.manifest.paragraphs.entries()) {
    const plan=plans[i].captions;assert.equal(plan.map(c=>c.spoken_text).join(''),b.text);
    for(const c of plan){assert.ok([...c.text].length<=55);assert.ok(c.lines.length<=2);assert.ok(c.lines.every(l=>[...l].length<=28));}
  }
});
unit('caption_times_are_global_body_with_local_mapping',()=>{
  const text='서울은 삼 년 뒤입니다.',chars=[...text];const a={characters:chars,character_start_times_seconds:chars.map((_,i)=>i/10),character_end_times_seconds:chars.map((_,i)=>(i+1)/10)};
  const cues=timedCaptions(text,a,10);assert.equal(cues[0].start,10);assert.equal(cues[0].start,cues[0].local_start+10);assert.equal(cues.at(-1).end,cues.at(-1).local_end+10);
});
const builder=spawnSync(process.execPath,[path.join(DIR,'build_timing.mjs')],{encoding:'utf8',windowsHide:true});
assert.notEqual(builder.status,0);assert.match(builder.stderr,/No actual timing lock/);
assert.equal(await fs.readFile(eventPath,'utf8'),'');
results.push({check:'timing_builder_refuses_missing_actual_audio',result:'passed',network_calls:0});
await saveJSON(path.join(DIR,'offline_caption_plan.json'),{script_sha256:SCRIPT_SHA,manifest_sha256:MANIFEST_SHA,timing_locked:false,actual_listening:false,plans});
const report={task_id:'RPR-PROD1-JUN-PREP',status:'passed',at:new Date().toISOString(),checks:results,
  source_sha256:Object.fromEntries(await Promise.all(['common.mjs','generate.mjs','build_timing.mjs','offline_checks.mjs'].map(async f=>[f,sha(await fs.readFile(path.join(DIR,f)))]))),
  external_requests:0,paid_calls:0,credentials_read:false,actual_audio_generated:false,actual_listening:false,
  remaining_validation:'Live account, synthesis, ffmpeg decode/concat and actual listening require director execution after budget approval.'};
await saveJSON(path.join(DIR,'offline_verification.json'),report);
await fs.unlink(path.join(fixtureDir,'authorization.json')); // Leave no executable authorization in fixtures.
console.log(JSON.stringify({status:'passed',checks:results.length,caption_chunks:plans.reduce((n,p)=>n+p.captions.length,0),external_requests:0,paid_calls:0}));
