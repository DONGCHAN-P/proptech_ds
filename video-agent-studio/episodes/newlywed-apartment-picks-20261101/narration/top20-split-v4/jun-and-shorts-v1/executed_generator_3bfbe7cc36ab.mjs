// Jun 승인 9cde211f3073 전용. POST 1회/청크, 실패 재시도 및 제공자 대체 금지.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

const ROOT='C:/projects/realestate_reco';
const DIR=path.dirname(fileURLToPath(import.meta.url));
const EP=path.join(ROOT,'video-agent-studio/episodes/newlywed-apartment-picks-20261101');
assert.equal(DIR.replaceAll('\\','/'),path.join(EP,'narration/top20-split-v4/jun-and-shorts-v1').replaceAll('\\','/'));
const AUTH=path.join(EP,'director/top20-split-v4/part1-jun-and-shorts-v1/production_authorization.json');
const MAN=path.join(DIR,'narration_manifest.json');
const HASH='f4bd6d8bfefb3fff65ded62ea8ec013658df5ad1e19cfc1cff836dcc37b7ebe1';
const VOICE='4p6UA7mnodF5q7JFFrnW', MODEL='eleven_v4', CAP=6500, RATE=44100;
const SETTINGS={stability:.6,similarity_boost:.95,speed:.97};
const FF=path.join(ROOT,'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe');
const mode=process.argv[2];assert.ok(['--offline','--generate'].includes(mode));
const sha=x=>createHash('sha256').update(x).digest('hex');
const rel=p=>path.relative(ROOT,p).replaceAll('\\','/');
const stamp=()=>new Date().toISOString();
const read=p=>fs.readFile(p);
const json=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const exists=async p=>fs.access(p).then(()=>true,()=>false);
async function save(p,x,exclusive=false){
  if(exclusive)return fs.writeFile(p,JSON.stringify(x,null,2)+'\n',{flag:'wx'});
  const tmp=p+'.tmp';await fs.writeFile(tmp,JSON.stringify(x,null,2)+'\n');await fs.rename(tmp,p);
}
const [mb,ab,cb,ffb]=await Promise.all([read(MAN),read(AUTH),read(path.join(ROOT,'config/tts.json')),read(FF)]);
assert.equal(sha(mb),HASH);const manifest=JSON.parse(mb),auth=JSON.parse(ab),cfg=JSON.parse(cb);
assert.equal(auth.status,'approved');assert.equal(auth.decision_id,'9cde211f3073');
assert.equal(auth.generation_authorized,true);assert.equal(auth.manifest_sha256,HASH);
assert.equal(auth.included_credit_cap,CAP);assert.equal(auth.additional_cash_cap_krw,0);
assert.equal(auth.top_up_authorized,false);assert.equal(auth.automatic_retry,false);
assert.equal(auth.model,MODEL);assert.equal(auth.voice_id,VOICE);
assert.equal(cfg.model,MODEL);assert.equal(cfg.voice_id,VOICE);
assert.equal(manifest.sentences.length,92);assert.equal(manifest.chunks.length,16);
assert.equal(manifest.input_characters_to_send,5520);
assert.equal(manifest.sentences.filter(s=>s.kind==='accepted_main').length,90);
const byId=new Map(manifest.sentences.map(s=>[s.sentence_id,s]));
const chunks=[];
for(const c of manifest.chunks){
  const p=path.resolve(ROOT,c.path);assert.ok(p.startsWith(DIR+path.sep));
  const raw=await read(p);assert.equal(sha(raw),c.sha256,'Frozen input file SHA mismatch');
  // 元ファイルのCRLFは保持。manifestの5520文字と一致するLFのみを送信する。
  const text=raw.toString('utf8').replaceAll('\r\n','\n');
  assert.equal(text,c.sentence_ids.map(id=>byId.get(id).reading_text).join('\n\n'));
  assert.equal([...text].length,c.characters);chunks.push({...c,text,request_text_sha256:sha(text)});
}
assert.equal(chunks.reduce((n,c)=>n+c.characters,0),5520);
assert.equal(new Set(chunks.flatMap(c=>c.sentence_ids)).size,92);
assert.equal(sha(await read(path.join(ROOT,manifest.main_reader_script))),manifest.main_reader_script_sha256);
const inputs={revision:manifest.revision,authorization_id:auth.decision_id,authorization_sha256:sha(ab),manifest_sha256:HASH,
  reader_script_sha256:manifest.main_reader_script_sha256,config_sha256:sha(cb),generator_sha256:sha(await read(fileURLToPath(import.meta.url))),
  ffmpeg_path:rel(FF),ffmpeg_sha256:sha(ffb),model:MODEL,voice_id:VOICE,voice_settings:SETTINGS,output_format:'mp3_44100_128',
  input_characters:5520,chunk_count:16,sentence_count:92,included_credit_cap:CAP,cash_cap_krw:0,automatic_retry:false,
  newline_policy:'불변 파일의 바이트/SHA 보존; CRLF→LF만 전송 시 정규화하여 manifest 5520문자와 일치',
  chunks:chunks.map(({text,...c})=>c),actual_listening:false};
await save(path.join(DIR,'input_lock.json'),inputs);
if(mode==='--offline'){console.log(JSON.stringify({status:'offline_guards_passed',characters:5520,chunks:16,post_calls:0}));process.exit(0);}
// 환경 변수나 명령줄로 키를 전달하지 않고 지정 .env 내부에서만 읽는다.
const env=await fs.readFile(path.join(ROOT,'.env'),'utf8');
const key=env.match(/^\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*?)\s*$/m)?.[1].replace(/^(['"])(.*)\1$/,'$2');
assert.ok(key,'Credential missing in .env');
const headers={'xi-api-key':key};
const safeError=e=>({type:e.name,network_code:e.cause?.code??e.code??null,
  reason:e instanceof assert.AssertionError?e.message.slice(0,400):e.safeReason??'네트워크 또는 응답 처리 오류; POST 재시도 금지'});
async function get(endpoint){
  const r=await fetch('https://api.elevenlabs.io'+endpoint,{method:'GET',headers,redirect:'error',signal:AbortSignal.timeout(30000)});
  await fs.appendFile(path.join(DIR,'readonly_queries.jsonl'),JSON.stringify({at_utc:stamp(),method:'GET',endpoint,http_status:r.status})+'\n');
  if(!r.ok){const e=new Error();e.safeReason='GET '+endpoint+' HTTP '+r.status;throw e;}
  return r.json();
}
const safeSub=s=>({tier:s.tier,status:s.status,character_count:s.character_count,character_limit:s.character_limit,
  included_remaining:s.character_limit-s.character_count,max_credit_limit_extension:s.max_credit_limit_extension,
  max_character_limit_extension:s.max_character_limit_extension,can_extend_character_limit:s.can_extend_character_limit,allowed_to_extend_character_limit:s.allowed_to_extend_character_limit});
function checkSub(s,need){assert.equal(s.status,'active');assert.equal(s.max_credit_limit_extension,0);assert.equal(s.can_extend_character_limit,false);assert.equal(s.allowed_to_extend_character_limit,false);assert.ok(s.character_limit-s.character_count>=need,'Included balance insufficient');}
const lp=path.join(DIR,'generation_ledger.json'),lock=path.join(DIR,'.generation.lock');
const ledger=await exists(lp)?await json(lp):{authorization_id:auth.decision_id,authorization_sha256:inputs.authorization_sha256,manifest_sha256:HASH,
  status:'ready',actual_credits:0,submitted_characters:0,reserved_pending_credits:0,requests:[],created_at_utc:stamp(),automatic_retries:0,topup_calls:0,overage_calls:0,cash_spent_krw:0,actual_listening:false};
assert.equal(ledger.authorization_sha256,inputs.authorization_sha256);assert.equal(ledger.manifest_sha256,HASH);
assert.ok(ledger.requests.every(r=>r.status==='complete'),'Failed/pending/ambiguous POST blocks new generation');
assert.equal(ledger.actual_credits,ledger.requests.reduce((n,r)=>n+r.actual_credits,0));
await save(lock,{pid:process.pid,started_at_utc:stamp(),generator_sha256:inputs.generator_sha256},true);
await fs.mkdir(path.join(DIR,'receipts'),{recursive:true});await fs.mkdir(path.join(DIR,'raw'),{recursive:true});await fs.mkdir(path.join(DIR,'processed'),{recursive:true});
let live,baseCredits;
try{
  const [s,models,v]=await Promise.all([get('/v1/user/subscription'),get('/v1/models'),get('/v1/voices/'+VOICE)]);
  const m=models.find(x=>x.model_id===MODEL);assert.ok(m);assert.equal(m.can_do_text_to_speech,true);
  assert.equal(m.model_rates.character_cost_multiplier,1);assert.equal(m.model_rates.cost_discount_multiplier,1);
  assert.equal(m.can_use_style,false);assert.equal(m.can_use_speaker_boost,false);
  assert.equal(v.voice_id,VOICE);assert.equal(v.sharing.rate,1);assert.equal(v.fine_tuning.state[MODEL],'fine_tuned');
  assert.deepEqual({stability:v.settings.stability,similarity_boost:v.settings.similarity_boost,speed:v.settings.speed},SETTINGS);
  checkSub(s,CAP-ledger.actual_credits);baseCredits=ledger.actual_credits;
  live={checked_at_utc:stamp(),subscription:safeSub(s),model:{model_id:m.model_id,maximum_text_length_per_request:m.maximum_text_length_per_request,model_rates:m.model_rates,can_use_style:m.can_use_style,can_use_speaker_boost:m.can_use_speaker_boost},voice:{voice_id:VOICE,rate:v.sharing.rate,settings:SETTINGS}};
  await save(path.join(DIR,'account_preflight.json'),live);
  ledger.initial_included_remaining??=live.subscription.included_remaining;ledger.initial_character_count??=s.character_count;
  await save(lp,ledger);
  for(const c of chunks){
    const old=ledger.requests.find(r=>r.asset_id===c.asset_id);
    if(old){assert.equal(old.request_text_sha256,c.request_text_sha256);for(const [p,h]of Object.entries(old.artifact_sha256))assert.equal(sha(await read(path.join(ROOT,p))),h);continue;}
    assert.equal(sha(await read(MAN)),HASH);assert.equal(sha(await read(AUTH)),inputs.authorization_sha256);
    assert.equal(sha(await read(path.join(ROOT,c.path))),c.sha256);
    const remaining=chunks.filter(x=>!ledger.requests.some(r=>r.asset_id===x.asset_id)).reduce((n,x)=>n+x.characters,0);
    assert.ok(ledger.actual_credits+remaining<=CAP);assert.ok(ledger.submitted_characters+c.characters<=CAP);
    const shadow=live.subscription.included_remaining-(ledger.actual_credits-baseCredits);
    assert.ok(shadow>=CAP-ledger.actual_credits);assert.ok(c.characters<=live.model.maximum_text_length_per_request);
    const rawDir=path.join(DIR,'raw',c.asset_id);assert.equal(await exists(rawDir),false,'Untracked raw asset blocks duplicate POST');
    const rp=path.join(DIR,'receipts',c.asset_id+'.json');assert.equal(await exists(rp),false,'Existing receipt blocks duplicate POST');
    await fs.mkdir(rawDir);
    const request={text:c.text,model_id:MODEL,voice_settings:SETTINGS};
    const receipt={asset_id:c.asset_id,sentence_ids:c.sentence_ids,status:'pending_no_automatic_retry',started_at_utc:stamp(),authorization_id:auth.decision_id,
      authorization_sha256:inputs.authorization_sha256,manifest_sha256:HASH,input_file_sha256:c.sha256,request_text_sha256:c.request_text_sha256,
      characters:c.characters,reserved_credits:c.characters,actual_credits:null,charge_known:false,request,
      endpoint:'/v1/text-to-speech/'+VOICE+'/with-timestamps?output_format=mp3_44100_128',local_shadow_remaining_before:shadow,actual_listening:false};
    await save(rp,receipt,true);ledger.requests.push(receipt);ledger.submitted_characters+=c.characters;
    ledger.reserved_pending_credits=c.characters;ledger.status='generating';await save(lp,ledger);
    try{
      const response=await fetch('https://api.elevenlabs.io'+receipt.endpoint,{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(request),redirect:'error',signal:AbortSignal.timeout(180000)});
      receipt.http_status=response.status;receipt.response_headers=Object.fromEntries(['request-id','x-request-id','character-cost','content-type','date'].map(k=>[k,response.headers.get(k)]));
      await save(rp,receipt);
      if(!response.ok){const body=await response.json().catch(()=>null);const code=body?.detail?.status;receipt.api_error_code=typeof code==='string'&&/^[a-zA-Z0-9_.-]{1,80}$/.test(code)?code:null;const e=new Error();e.safeReason='TTS HTTP '+response.status+' '+(receipt.api_error_code??'');throw e;}
      const body=await response.json();const audio=Buffer.from(body.audio_base64??'','base64');assert.ok(audio.length>100,'Missing audio');
      await fs.writeFile(path.join(rawDir,'audio.mp3'),audio,{flag:'wx'});
      await save(path.join(rawDir,'alignment.json'),body.alignment??null,true);
      await save(path.join(rawDir,'normalized_alignment.json'),body.normalized_alignment??null,true);
      const charge=receipt.response_headers['character-cost'];assert.ok(typeof charge==='string'&&/^\d+(?:\.\d+)?$/.test(charge),'Missing exact character-cost; stop');
      receipt.actual_credits=Number(charge);receipt.charge_known=true;ledger.actual_credits+=receipt.actual_credits;ledger.reserved_pending_credits=0;
      await save(rp,receipt);await save(lp,ledger);
      assert.ok(receipt.actual_credits>=0&&receipt.actual_credits<=c.characters,'Charge exceeds reserved credits');assert.ok(ledger.actual_credits<=CAP);
      const wav=path.join(DIR,'processed',c.asset_id+'.wav');
      const conv=spawnSync(FF,['-v','error','-n','-i',path.join(rawDir,'audio.mp3'),'-map','0:a:0','-ac','1','-ar',String(RATE),'-c:a','pcm_s16le',wav],{windowsHide:true,encoding:'utf8'});
      assert.equal(conv.status,0,'Local lossless decode failed');
      const decoded=spawnSync(FF,['-v','error','-i',wav,'-f','s16le','-ac','1','-ar',String(RATE),'pipe:1'],{windowsHide:true,maxBuffer:128*1024*1024});
      assert.equal(decoded.status,0,'PCM decode failed');assert.ok(decoded.stdout.length>0&&decoded.stdout.length%2===0);
      receipt.pcm_samples=decoded.stdout.length/2;receipt.pcm_duration_s=receipt.pcm_samples/RATE;
      const a=body.alignment;assert.equal(a?.characters?.join(''),c.text,'Native alignment text differs from sent frozen reading');
      assert.equal(a.characters.length,a.character_start_times_seconds.length);assert.equal(a.characters.length,a.character_end_times_seconds.length);
      for(let i=0;i<a.characters.length;i++){const t=a.character_start_times_seconds[i],e=a.character_end_times_seconds[i];assert.ok(Number.isFinite(t)&&Number.isFinite(e)&&t>=0&&e>=t&&e<=receipt.pcm_duration_s+.1);if(i){assert.ok(t>=a.character_start_times_seconds[i-1]);assert.ok(e>=a.character_end_times_seconds[i-1]);}}
      receipt.provider_last_alignment_end_s=Math.max(...a.character_end_times_seconds);receipt.complete_tail_after_alignment_s=receipt.pcm_duration_s-receipt.provider_last_alignment_end_s;
      receipt.wav_path=rel(wav);receipt.raw_audio_path=rel(path.join(rawDir,'audio.mp3'));receipt.alignment_path=rel(path.join(rawDir,'alignment.json'));
      receipt.pcm_sha256=sha(decoded.stdout);receipt.artifact_sha256={};
      for(const p of [path.join(rawDir,'audio.mp3'),path.join(rawDir,'alignment.json'),path.join(rawDir,'normalized_alignment.json'),wav])receipt.artifact_sha256[rel(p)]=sha(await read(p));
      receipt.processing={sample_rate_hz:RATE,channels:1,codec:'pcm_s16le',tempo_factor:1,trimmed:false,tail_preserved:true,provider_speed:.97};
      receipt.local_shadow_remaining_after=shadow-receipt.actual_credits;receipt.status='complete';receipt.completed_at_utc=stamp();await save(rp,receipt);await save(lp,ledger);
      console.log(JSON.stringify({asset_id:c.asset_id,status:'complete',actual_credits:receipt.actual_credits,total_credits:ledger.actual_credits,duration_s:receipt.pcm_duration_s}));
    }catch(e){receipt.status='failed_or_ambiguous_no_automatic_retry';receipt.failure=safeError(e);receipt.failed_at_utc=stamp();ledger.status='blocked_no_automatic_retry';await save(rp,receipt);await save(lp,ledger);throw e;}
  }
  const final=await get('/v1/user/subscription');checkSub(final,0);
  ledger.final_included_remaining=final.character_limit-final.character_count;
  ledger.observed_account_delta=final.character_count-ledger.initial_character_count;
  ledger.header_account_delta_matches=ledger.observed_account_delta===ledger.actual_credits;
  await save(path.join(DIR,'account_final.json'),{checked_at_utc:stamp(),subscription:safeSub(final),header_actual_credits:ledger.actual_credits,observed_account_delta:ledger.observed_account_delta,header_account_delta_matches:ledger.header_account_delta_matches});
  assert.equal(ledger.requests.length,16);assert.equal(ledger.submitted_characters,5520);assert.equal(ledger.actual_credits,5520);
  assert.equal(ledger.header_account_delta_matches,true,'Account delta differs; do not attribute unrelated usage');
  ledger.status='all16_generated_measured_native_alignment_not_listened';ledger.updated_at_utc=stamp();await save(lp,ledger);
  console.log(JSON.stringify({status:ledger.status,actual_credits:ledger.actual_credits,included_remaining:ledger.final_included_remaining,unused_cap:CAP-ledger.actual_credits}));
}catch(e){ledger.status='blocked_no_automatic_retry';ledger.failure=safeError(e);ledger.updated_at_utc=stamp();await save(lp,ledger);await save(path.join(DIR,'issue_JUN_GENERATION_BLOCK.json'),{issue_id:'JUN_GENERATION_BLOCK',scene_ids:ledger.requests.filter(r=>r.status!=='complete').flatMap(r=>r.sentence_ids),problem:ledger.failure,evidence:rel(lp),proposal:'실패 POST 재전송 금지. 보존된 자산과 사용량을 총괄이 확인한 뒤 필요한 별도 결정을 진행',impact:'남은 Jun 생성/새 타이밍 납품 보류',actual_credits:ledger.actual_credits,pending_reserved:ledger.reserved_pending_credits});console.error(JSON.stringify({status:ledger.status,failure:ledger.failure,completed:ledger.requests.filter(r=>r.status==='complete').length,actual_credits:ledger.actual_credits,pending_reserved:ledger.reserved_pending_credits}));process.exitCode=1;}
finally{await fs.unlink(lock);}
