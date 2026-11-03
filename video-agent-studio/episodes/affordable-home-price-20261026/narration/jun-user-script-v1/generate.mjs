// This episode: 7 chapters of the user-authored 48-paragraph script; never reuses prior episode authorization.
// 명시된 승인 모드만 TTS POST 허용. 실패/불명확 receipt는 영구 중단, 자동 재시도 없음.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {sha, readJSON, saveJSON, exists, findFFmpeg, decode} from '../../../regional-price-recovery-20261022/narration/production-v1/common.mjs';
const DIR=path.dirname(fileURLToPath(import.meta.url)), EP=path.resolve(DIR,'../..'), ROOT=path.resolve(EP,'../../..');
const SCRIPT='dd419a373dd5ace01aa88381d5b59ed0199b53547b3ae84e1c9373624b82378e';
const MANIFEST='5290eff5c5724c807bc4062feab7be5889b8decea1316984e48f25b1fe32b9f5';
const VOICE='4p6UA7mnodF5q7JFFrnW', MODEL='eleven_v4', CAP=7000, RATE=44100;
const mode=process.argv[2]??'--offline';
assert.ok(['--offline','--preflight','--first','--remaining'].includes(mode));
const stamp=()=>new Date().toISOString();
const rel=p=>path.relative(ROOT,p).replaceAll('\\','/');
const bytes=p=>fs.readFile(p);
const inputPath=path.join(EP,'narration/jun-user-script-v1/generation_input.json');
const authPath=path.join(EP,'director/jun-user-script-v1/authorization.json');
const configPath=path.join(ROOT,'config/tts.json');
const [inputBytes,authBytes,cfgBytes]=await Promise.all([inputPath,authPath,configPath].map(bytes));
const input=JSON.parse(inputBytes),auth=JSON.parse(authBytes),cfg=JSON.parse(cfgBytes);
assert.equal(sha(inputBytes),MANIFEST);assert.equal(input.script_sha256,SCRIPT);
assert.equal(sha(await bytes(path.join(EP,'narration/jun-user-script-v1/narration_body.txt'))),SCRIPT);
assert.equal(auth.budget_user_reply,'7,000크레딧 상한으로 Jun 생성 승인');
assert.equal(auth.paid_voice_generation_authorized,true);assert.equal(auth.script_sha256,SCRIPT);assert.equal(auth.phonetic_input_manifest_sha256,MANIFEST);
assert.equal(auth.included_credit_cap,CAP);assert.equal(auth.additional_cash_usd_cap,0);
assert.equal(auth.topup_authorized,false);assert.equal(auth.overage_authorized,false);assert.equal(auth.automatic_retry_authorized,false);
assert.equal(auth.model,MODEL);assert.equal(auth.voice_id,VOICE);assert.equal(cfg.model,MODEL);assert.equal(cfg.voice_id,VOICE);
assert.equal(sha(cfgBytes),input.raw_manifest? (await readJSON(path.join(EP,'narration/jun-user-script-v1/generator_raw_manifest.json'))).inputs.tts_config.sha256 : 'missing');

assert.equal(auth.source_doc_sha256,input.source_doc_sha256);
assert.equal(auth.material_facts_cleared,true);
assert.equal(auth.input_characters,5797);
assert.equal(sha(await bytes(path.join(EP,'narration/jun-user-script-v1/narration_manifest.json'))),(await readJSON(path.join(EP,'narration/jun-user-script-v1/generator_raw_manifest.json'))).source_manifest_sha256);
assert.equal(input.paragraphs.length,7);assert.equal(input.paragraphs.reduce((s,p)=>s+[...p.proposed_spoken_text].length,0),5797);
if(!process.env.FFMPEG_PATH)process.env.FFMPEG_PATH=path.join(ROOT,'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe');
const ff=findFFmpeg();
const DEPENDENCIES=[{"path": "video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/common.mjs", "bytes": 10467, "sha256": "99b63053e73a9414f129e59af50d574a1b1b44cf2064608b26b5c3264d593ed1"}, {"path": "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe", "bytes": 87638016, "sha256": "2ce797a0f88d7f067180338fb227f7b1928ea727bd9a4d7a1d022f7c52af71a3"}];
for(const dependency of DEPENDENCIES)assert.equal(sha(await bytes(path.join(ROOT,dependency.path))),dependency.sha256,"Execution dependency changed");
const selectedFFmpeg={path:path.resolve(ff),sha256:sha(await bytes(ff))};
assert.equal(selectedFFmpeg.sha256,DEPENDENCIES[1].sha256,"Selected FFmpeg differs from frozen dependency");

const inputs={script_sha256:SCRIPT,phonetic_manifest_sha256:MANIFEST,authorization_sha256:sha(authBytes),config_sha256:sha(cfgBytes),generator_sha256:sha(await bytes(fileURLToPath(import.meta.url))),
  dependencies:DEPENDENCIES,selected_ffmpeg:selectedFFmpeg,authorization_id:auth.authorization_id,authorization_quote:auth.budget_user_reply,model:MODEL,voice_id:VOICE,speed:.97,output_format:'mp3_44100_128',chapter_count:7,input_characters:5797,
  cap:CAP,additional_cash_usd:0,automatic_retry:false,ffmpeg_path:ff};
if(!await exists(path.join(DIR,'input_lock.json')))await saveJSON(path.join(DIR,'input_lock.json'),inputs);
await saveJSON(path.join(DIR,'input_lock.'+mode.slice(2)+'.'+inputs.generator_sha256.slice(0,12)+'.json'),inputs);
if(mode==='--offline'){console.log(JSON.stringify({status:'offline_guards_passed',chapters:7,characters:5797,cap:CAP,post_calls:0}));process.exit(0);}
let key=process.env.ELEVENLABS_API_KEY;
if(!key){const env=await fs.readFile(path.join(ROOT,'.env'),'utf8');key=env.match(/^\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*?)\s*$/m)?.[1].replace(/^(['"])(.*)\1$/,'$2');}
assert.ok(key,'API key missing');
const headers={'xi-api-key':key};
const safeFailure=e=>({kind:e instanceof assert.AssertionError?'guard_failure':e.name,code:e.cause?.code??e.code??null,
  reason:e instanceof assert.AssertionError ? e.message.slice(0,500):e.safeReason??'네트워크/응답 처리 오류; 재시도 금지'});
async function get(endpoint){
  let waited=0;
  for(let attempt=0;attempt<3;attempt++){
    const r=await fetch('https://api.elevenlabs.io'+endpoint,{method:'GET',headers,redirect:'error',signal:AbortSignal.timeout(30000)});
    await fs.appendFile(path.join(DIR,'readonly_queries.jsonl'),JSON.stringify({at_utc:stamp(),method:'GET',endpoint,http_status:r.status,attempt:attempt+1})+'\n');
    if(r.status===429&&attempt<2){
      const hint=Number(r.headers.get('retry-after'));
      const delay=Math.min(60000-waited,Math.max(attempt===0?20000:40000,Number.isFinite(hint)?hint*1000:0));
      if(delay<=0)break;waited+=delay;
      console.log(JSON.stringify({status:'read_only_429_bounded_backoff',endpoint,wait_ms:delay,total_wait_ms:waited,tts_retry:false}));
      await new Promise(resolve=>setTimeout(resolve,delay));continue;
    }
    if(!r.ok){const e=new Error();e.safeReason='GET '+endpoint+' HTTP '+r.status;throw e;}return r.json();
  }
  const e=new Error();e.safeReason='GET '+endpoint+' HTTP 429 after maximum60s read-only backoff';throw e;
}
const safeSub=s=>({tier:s.tier,status:s.status,character_count:s.character_count,character_limit:s.character_limit,included_remaining:s.character_limit-s.character_count,
  max_credit_limit_extension:s.max_credit_limit_extension,can_extend_character_limit:s.can_extend_character_limit,allowed_to_extend_character_limit:s.allowed_to_extend_character_limit});
function checkSub(s,need){assert.equal(s.status,'active');assert.notEqual(s.tier,'free');assert.equal(s.max_credit_limit_extension,0);assert.equal(s.can_extend_character_limit,false);assert.equal(s.allowed_to_extend_character_limit,false);assert.ok(s.character_limit-s.character_count>=need,'Insufficient live included balance');}
async function account(){
  const [s,models,v]=await Promise.all([get('/v1/user/subscription'),get('/v1/models'),get('/v1/voices/'+VOICE)]);
  const m=models.find(x=>x.model_id===MODEL);assert.ok(m);assert.equal(m.can_do_text_to_speech,true);assert.equal(m.model_rates.character_cost_multiplier,1);assert.equal(m.model_rates.cost_discount_multiplier,1);
  assert.equal(v.voice_id,VOICE);assert.equal(v.sharing?.rate,1);assert.equal(v.settings?.speed,.97);assert.equal(v.fine_tuning?.state?.[MODEL],'fine_tuned');
  const stored={stability:v.settings.stability,similarity_boost:v.settings.similarity_boost,speed:v.settings.speed};
  const safe={checked_at_utc:stamp(),subscription:safeSub(s),model:{model_id:m.model_id,model_rates:m.model_rates,can_use_style:m.can_use_style,can_use_speaker_boost:m.can_use_speaker_boost,serves_pro_voices:m.serves_pro_voices,maximum_text_length_per_request:m.maximum_text_length_per_request},
    voice:{voice_id:v.voice_id,rate:v.sharing.rate,category:v.category,fine_tuning_state:v.fine_tuning.state[MODEL],supported_request_settings:stored},http_statuses:[200,200,200]};
  return {s,m,v,stored,safe};
}
let live;
try{live=await account();checkSub(live.s,CAP);await saveJSON(path.join(DIR,'account_preflight.'+mode.slice(2)+'.json'),live.safe);}
catch(e){await saveJSON(path.join(DIR,'preflight_block.'+mode.slice(2)+'.json'),{at_utc:stamp(),status:'preflight_failed_before_post',error:safeFailure(e),post_calls:0});console.error(JSON.stringify({status:'preflight_failed_before_post',error:safeFailure(e),post_calls:0}));process.exit(1);}
if(mode==='--preflight'){console.log(JSON.stringify({status:'live_preflight_passed',included_remaining:live.safe.subscription.included_remaining,model:live.safe.model,settings:live.stored,post_calls:0}));process.exit(0);}
await fs.mkdir(path.join(DIR,'receipts'),{recursive:true});await fs.mkdir(path.join(DIR,'paragraphs'),{recursive:true});
const ledgerPath=path.join(DIR,'generation_ledger.json');
const ledger=await exists(ledgerPath)?await readJSON(ledgerPath):{...inputs,status:'ready',created_at_utc:stamp(),actual_credits:0,submitted_characters:0,reserved_pending_credits:0,requests:[],actual_listening:false,topup_calls:0,overage_calls:0,automatic_retries:0};
assert.equal(ledger.authorization_sha256,inputs.authorization_sha256);assert.equal(ledger.phonetic_manifest_sha256,MANIFEST);
assert.ok(!ledger.requests.some(r=>r.status!=='complete'),'Pending/failed/ambiguous request: stop, no automatic retry');
assert.equal(ledger.actual_credits,ledger.requests.reduce((s,r)=>s+r.actual_credits,0));
assert.ok(ledger.actual_credits<=CAP);
ledger.execution_epochs??=[];
ledger.execution_epochs.push({at_utc:stamp(),generator_sha256:inputs.generator_sha256,mode,completed_before:ledger.requests.length,
  reason:'사용자 지시: GET429만 최대60초 대기; 장별 조회로 줄이고 완료/제출된 POST는 재전송하지 않음'});
let snapshotCreditBase=ledger.actual_credits;
const lockPath=path.join(DIR,'.generation.lock');await saveJSON(lockPath,{pid:process.pid,started_at_utc:stamp(),mode},true);
const choose=mode==='--first'?input.paragraphs.slice(0,1):input.paragraphs;
try{
 for(const p of choose){
  const id=p.paragraph_id, text=p.proposed_spoken_text, n=[...text].length;
  assert.equal(n,p.characters);assert.equal(sha(text),p.proposed_spoken_text_sha256);
  const old=ledger.requests.find(r=>r.paragraph_id===id);
  if(old){assert.equal(old.status,'complete');for(const [file,hash]of Object.entries(old.artifact_sha256))assert.equal(sha(await bytes(path.join(DIR,file))),hash);continue;}
  if(mode==='--remaining')assert.ok(ledger.requests.some(r=>r.paragraph_id==='C01P01'&&r.status==='complete'),'Inspect first paragraph before remaining batch');
  assert.equal(sha(await bytes(authPath)),inputs.authorization_sha256);assert.equal(sha(await bytes(inputPath)),MANIFEST);assert.equal(sha(await bytes(configPath)),inputs.config_sha256);
  if(id.endsWith('P01')){live=await account();snapshotCreditBase=ledger.actual_credits;assert.deepEqual(live.stored,{stability:.6,similarity_boost:.95,speed:.97});await saveJSON(path.join(DIR,'account_checkpoint.'+p.scene_id+'.json'),live.safe);}
  assert.ok(n<=live.m.maximum_text_length_per_request);
  const remaining=input.paragraphs.filter(x=>!ledger.requests.some(r=>r.paragraph_id===x.paragraph_id)).reduce((s,x)=>s+x.characters,0);
  assert.ok(ledger.actual_credits+remaining<=CAP);assert.ok(ledger.submitted_characters+n<=CAP);
  const before=live.s;
  const shadowRemaining=before.character_limit-before.character_count-(ledger.actual_credits-snapshotCreditBase);
  checkSub(before,0);assert.ok(shadowRemaining>=CAP-ledger.actual_credits,'Per-chapter included balance minus known request costs is insufficient');
  const base=path.join(DIR,'paragraphs',id);await fs.mkdir(base,{recursive:true});
  assert.equal(await exists(path.join(DIR,'receipts',id+'.json')),false,'Untracked receipt blocks new charge');
  for(const f of ['audio.mp3','audio.wav','alignment.json','normalized_alignment.json'])assert.equal(await exists(path.join(base,f)),false,'Untracked audio blocks new charge');
  const request={text,model_id:MODEL,voice_settings:live.stored};
  const receipt={paragraph_id:id,scene_id:p.scene_id,status:'pending_no_automatic_retry',started_at_utc:stamp(),authorization_sha256:inputs.authorization_sha256,
    text_sha256:p.proposed_spoken_text_sha256,phonetic_manifest_sha256:MANIFEST,request,reserved_credits:n,characters:n,actual_credits:null,charge_known:false,
    account_before:safeSub(before),account_before_scope:'실행 재개/장 시작 GET 스냅샷. 즉시 요청 전 실시간 계정값으로 해석하지 않음.',
    account_snapshot_at_utc:live.safe.checked_at_utc,local_shadow_remaining_before:shadowRemaining,actual_listening:false};
  const rp=path.join(DIR,'receipts',id+'.json');await saveJSON(rp,receipt,true);
  ledger.requests.push(receipt);ledger.submitted_characters+=n;ledger.reserved_pending_credits=n;ledger.status='generating';await saveJSON(ledgerPath,ledger);
  try{
   const response=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+VOICE+'/with-timestamps?output_format=mp3_44100_128',{
     method:'POST',headers:{...headers,'Content-Type':'application/json'},redirect:'error',body:JSON.stringify(request),signal:AbortSignal.timeout(180000)});
   receipt.http_status=response.status;receipt.response_headers=Object.fromEntries(['request-id','x-request-id','character-cost','content-type','date'].map(k=>[k,response.headers.get(k)]));await saveJSON(rp,receipt);
   if(!response.ok){const body=await response.json().catch(()=>null);receipt.api_error={code:body?.detail?.status??null,message:String(body?.detail?.message??'').split(key).join('[REDACTED]').replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,'[EMAIL]').slice(0,1800)};await saveJSON(rp,receipt);const e=new Error();e.safeReason='TTS HTTP '+response.status+' '+(receipt.api_error.code??'');throw e;}
   const body=await response.json();const audio=Buffer.from(body.audio_base64??'','base64');assert.ok(audio.length>100,'Missing audio');
   await fs.writeFile(path.join(base,'audio.mp3'),audio,{flag:'wx'});await saveJSON(path.join(base,'alignment.json'),body.alignment??null,true);await saveJSON(path.join(base,'normalized_alignment.json'),body.normalized_alignment??null,true);
   const raw=receipt.response_headers['character-cost'];assert.ok(typeof raw==='string'&&/^\d+(?:\.\d+)?$/.test(raw),'Unknown charge: stop');
   receipt.actual_credits=Number(raw);receipt.charge_known=true;assert.ok(receipt.actual_credits>=0&&receipt.actual_credits<=n,'Actual charge exceeds reserved credits');
   ledger.actual_credits+=receipt.actual_credits;ledger.reserved_pending_credits=0;assert.ok(ledger.actual_credits<=CAP);await saveJSON(ledgerPath,ledger);
   const pcm=decode(ff,path.join(base,'audio.mp3'));receipt.pcm_samples=pcm.length/2;receipt.pcm_duration_s=receipt.pcm_samples/RATE;
   const a=body.alignment;assert.equal(a?.characters?.join(''),text,'Provider character alignment differs from approved input');
   assert.equal(a.characters.length,a.character_start_times_seconds.length);assert.equal(a.characters.length,a.character_end_times_seconds.length);
   for(let i=0;i<a.characters.length;i++){const s=a.character_start_times_seconds[i],e=a.character_end_times_seconds[i];assert.ok(Number.isFinite(s)&&Number.isFinite(e)&&s>=0&&e>=s&&e<=receipt.pcm_duration_s+.1);if(i)assert.ok(s>=a.character_start_times_seconds[i-1]&&e>=a.character_end_times_seconds[i-1]);}
   receipt.provider_last_spoken_end_s=Math.max(...a.character_end_times_seconds);
   const wav=spawnSync(ff,['-v','error','-n','-i',path.join(base,'audio.mp3'),'-ac','1','-ar',String(RATE),'-c:a','pcm_s16le',path.join(base,'audio.wav')],{windowsHide:true});assert.equal(wav.status,0,'Local PCM conversion failed');
   receipt.artifact_sha256={};for(const f of ['audio.mp3','audio.wav','alignment.json','normalized_alignment.json'])receipt.artifact_sha256[rel(path.join(base,f)).slice(rel(DIR).length+1)]=sha(await bytes(path.join(base,f)));
   receipt.account_after={status:'no_per_paragraph_get_rate_limit_policy',local_shadow_remaining_after:shadowRemaining-receipt.actual_credits,observed_remaining:null};
   receipt.account_observed_delta=null;
   receipt.status='complete';receipt.completed_at_utc=stamp();await saveJSON(rp,receipt);await saveJSON(ledgerPath,ledger);
   console.log(JSON.stringify({paragraph:id,status:'complete',credits:receipt.actual_credits,total_credits:ledger.actual_credits,duration_s:receipt.pcm_duration_s}));
  }catch(e){receipt.status='failed_or_ambiguous_no_automatic_retry';receipt.failure=safeFailure(e);receipt.failed_at_utc=stamp();ledger.status='blocked_no_automatic_retry';await saveJSON(rp,receipt);await saveJSON(ledgerPath,ledger);throw e;}
 }
 ledger.status=ledger.requests.length===7?'all7_chapters_generated_measured_alignment_validated_not_listened':'first_paragraph_ready_for_inspection';ledger.updated_at_utc=stamp();await saveJSON(ledgerPath,ledger);
 if(ledger.requests.length===7){const final=await get('/v1/user/subscription');checkSub(final,0);await saveJSON(path.join(DIR,'account_final.json'),{checked_at_utc:stamp(),subscription:safeSub(final),header_actual_credits:ledger.actual_credits,account_delta_is_not_request_attribution:true});}
 console.log(JSON.stringify({status:ledger.status,paragraphs:ledger.requests.length,actual_credits:ledger.actual_credits,reserve_remaining:CAP-ledger.actual_credits,post_calls:ledger.requests.length}));
}catch(e){ledger.status='blocked_no_automatic_retry';ledger.failure=safeFailure(e);await saveJSON(ledgerPath,ledger);console.error(JSON.stringify({status:ledger.status,failure:ledger.failure,completed:ledger.requests.filter(r=>r.status==='complete').length,actual_credits:ledger.actual_credits,pending_reserved:ledger.reserved_pending_credits}));process.exitCode=1;}
finally{await fs.unlink(lockPath);}
