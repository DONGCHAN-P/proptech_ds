import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const dir=new URL('./',import.meta.url), episode=new URL('../../',dir);
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const save=async(p,v)=>fs.writeFile(p,JSON.stringify(v,null,2));
const SOURCE='74ed7a1af1146a7b0f93b6602869222026667dbb8de2ea0137ee81e66eb3bbba';
const MANIFEST='951efa604ddf593ff8a2e65355a25dcc3748ce48dff78930164f9052ea5bf137';
const REV='script-v2',CAP=7661;
function alignmentValid(a,text){
 assert.ok(a&&Array.isArray(a.characters),'Missing original alignment');
 assert.equal(a.characters.join(''),text,'Original alignment differs from exact input');
 const starts=a.character_start_times_seconds,ends=a.character_end_times_seconds;
 assert.equal(starts.length,a.characters.length);assert.equal(ends.length,a.characters.length);
 starts.forEach((s,i)=>{assert.ok(Number.isFinite(s)&&s>=0&&Number.isFinite(ends[i])&&ends[i]>=s);if(i)assert.ok(s>=starts[i-1]);});
 return true;
}
async function inputs(){
 const u=new URL('writer/script-v2/manifest.json',episode),bytes=await fs.readFile(u),m=await read(u);
 assert.equal(hash(bytes),MANIFEST);assert.equal(m.source_script_sha256,SOURCE);
 const chapters=[];
 for(const c of m.chapters){const text=await fs.readFile(new URL('writer/script-v2/'+c.path,episode),'utf8');assert.equal(hash(text),c.sha256);assert.equal([...text].length,c.characters);chapters.push({...c,text});}
 assert.equal(chapters.length,10);assert.equal(chapters.reduce((n,c)=>n+[...c.text].length,0),6384);
 return chapters;
}
async function approval(){
 for(const [id,gate] of [['81cdb3c2a358','script'],['fef620079862','budget']]){
 const d=await read('output/video_decisions/decisions/'+id+'.json');assert.equal(d.status,'approved');assert.equal(d.gate,gate);assert.equal(d.episode,'goyang-changneung-20261015');assert.equal(d.artifact_hashes['writer\\script-v2\\script_v2.md'],SOURCE);assert.equal(d.artifact_hashes['writer\\script-v2\\manifest.json'],MANIFEST);for(const [p,h] of Object.entries(d.artifact_hashes)){assert.equal(hash(await fs.readFile(new URL(p.replaceAll('\\','/'),episode))),h);}
 }
 const b=await read(new URL('outputs/script-review-v2/budget_proposal_v2.json',episode));assert.equal(b.source_script_sha256,SOURCE);assert.equal(b.actual_credit_hard_cap,CAP);assert.equal(b.total_submitted_character_cap,CAP);assert.equal(b.additional_cash_usd_cap,0);assert.equal(b.automatic_retry,false);assert.equal(b.overage_or_topup_authorized,false);assert.equal(b.narration_manifest_sha256,MANIFEST);assert.equal(b.input_characters,6384);
}
async function main(){
 const chapters=await inputs();assert.equal(hash(await fs.readFile(new URL('writer/script-v2/script_v2.md',episode))),SOURCE);
 if(!process.argv.includes('--execute-approved')){
  const mock={characters:[...'8만 114세대'],character_start_times_seconds:[0,1,2,3,4,5,6,7],character_end_times_seconds:[1,2,3,4,5,6,7,8]};
  alignmentValid(mock,'8만 114세대');assert.throws(()=>alignmentValid(mock,'8만114세대'));
  console.log(JSON.stringify({offline_checks:'passed',chapters:chapters.length,characters:6384,network_calls:0,paid_generation:false}));return;
 }
 const auth=await read(new URL('authorization.json',dir));assert.equal(auth.root_execution_authorized,true,'Explicit root GO required');assert.equal(auth.source_script_sha256,SOURCE);assert.equal(auth.script_decision_id,'81cdb3c2a358');assert.equal(auth.budget_decision_id,'fef620079862');assert.equal(auth.actual_credit_hard_cap,CAP);await approval();const lock=await fs.open(new URL('execution.lock',dir),'wx');await lock.writeFile(new Date().toISOString());await lock.close();
 const cfg=await read('config/tts.json');assert.equal(cfg.voice_id,'4p6UA7mnodF5q7JFFrnW');assert.equal(cfg.model,'eleven_v4');
 const env={};for(const l of(await fs.readFile('.env','utf8')).split(/\r?\n/)){const m=l.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');}
 assert.ok(env.ELEVENLABS_API_KEY,'Missing local API key');const headers={'xi-api-key':env.ELEVENLABS_API_KEY};
 const get=async p=>{const r=await fetch('https://api.elevenlabs.io'+p,{headers,signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('GET HTTP '+r.status);return r.json();};
 const ledgerUrl=new URL('generation_ledger_v2.json',dir);let ledger;
 try{ledger=await read(ledgerUrl);}catch(e){if(e.code!=='ENOENT')throw e;ledger={audio_revision:'audio-v2',script_revision:REV,source_script_sha256:SOURCE,input_manifest_sha256:MANIFEST,requests:[],actual_credit_total:0,character_total:0};}
 assert.equal(ledger.source_script_sha256,SOURCE);assert.ok(ledger.requests.every(r=>r.status==='complete'),'Prior unresolved request: no automatic retry');
 await fs.mkdir(dir,{recursive:true});
 const ffmpeg='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';
 try{
 for(const c of chapters){
  if(ledger.requests.some(r=>r.scene_id===c.scene_id&&r.status==='complete'))continue;
  assert.ok(!ledger.requests.some(r=>r.scene_id===c.scene_id),'No duplicate POST');await approval();const [sub,voice,models]=await Promise.all([get('/v1/user/subscription'),get('/v1/voices/'+cfg.voice_id),get('/v1/models')]);
  const model=models.find(m=>m.model_id===cfg.model),rate=voice.sharing?.rate,mr=model?.model_rates;
  assert.ok(sub.status==='active'&&sub.tier!=='free'&&sub.character_limit-sub.character_count>=CAP-ledger.character_total);
  assert.ok(sub.can_extend_character_limit===false&&sub.allowed_to_extend_character_limit===false&&sub.max_credit_limit_extension===0);
  assert.ok(Number.isFinite(rate)&&rate>0&&rate<=1&&mr.character_cost_multiplier>0&&mr.character_cost_multiplier<=1&&mr.cost_discount_multiplier>0&&mr.cost_discount_multiplier<=1);
  assert.ok(ledger.character_total+c.characters<=CAP&&ledger.actual_credit_total+c.characters<=CAP);
  const dest=new URL(c.scene_id+'.mp3',dir);try{await fs.access(dest);throw Error('Untracked existing audio');}catch(e){if(e.code!=='ENOENT')throw e;}
  const r={scene_id:c.scene_id,status:'request_started',characters:c.characters,text_sha256:c.sha256,started_at:new Date().toISOString(),before_character_count:sub.character_count};
  ledger.requests.push(r);ledger.status='generating';await save(ledgerUrl,ledger);
  const response=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+cfg.voice_id+'/with-timestamps?output_format=mp3_44100_128',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({text:c.text,model_id:cfg.model}),signal:AbortSignal.timeout(180000)});
  r.http_status=response.status;r.request_id=response.headers.get('request-id')??response.headers.get('x-request-id');r.response_character_cost=response.headers.get('character-cost');
  if(!response.ok){r.status='failed';await save(ledgerUrl,ledger);throw Error('TTS HTTP '+response.status+'; no automatic retry');}
  const body=await response.json();const bytes=Buffer.from(body.audio_base64??'','base64');assert.ok(bytes.length>100);
  await fs.writeFile(dest,bytes);await save(new URL(c.scene_id+'.alignment.json',dir),body.alignment);await save(new URL(c.scene_id+'.normalized_alignment.json',dir),body.normalized_alignment??null);
  r.actual_credits=Number(r.response_character_cost);assert.ok(r.response_character_cost!==null&&Number.isFinite(r.actual_credits)&&r.actual_credits>=0);
  ledger.actual_credit_total+=r.actual_credits;ledger.character_total+=c.characters;await save(ledgerUrl,ledger);
  alignmentValid(body.alignment,c.text);
  const pcm=spawnSync(ffmpeg,['-v','error','-i',fileURLToPath(dest),'-f','s16le','-ac','1','-ar','44100','pipe:1'],{maxBuffer:150*1024*1024});assert.equal(pcm.status,0,'PCM decode failed');
  r.pcm_duration_s=pcm.stdout.length/(2*44100);r.sha256=hash(bytes);r.file='narration/audio-v2/'+c.scene_id+'.mp3';r.alignment_file='narration/audio-v2/'+c.scene_id+'.alignment.json';r.script_revision=REV;
  assert.ok(Math.max(...body.alignment.character_end_times_seconds)<=r.pcm_duration_s+0.1,'Alignment exceeds decoded audio');
  const after=await get('/v1/user/subscription');r.account_observed_delta_credits=after.character_count-sub.character_count;r.after_character_count=after.character_count;r.status='complete';r.completed_at=new Date().toISOString();await save(ledgerUrl,ledger);
  assert.ok(ledger.actual_credit_total<=CAP);console.log('saved '+c.scene_id+' credits='+r.actual_credits+' pcm_s='+r.pcm_duration_s.toFixed(3));
 }
 let cursor=0;const measured=ledger.requests.map(r=>{const start=cursor;cursor+=r.pcm_duration_s;return {scene_id:r.scene_id,start_s:start,end_s:cursor,timing_basis:'decoded_PCM_duration; provider_original_character_alignment',confidence:'provider-aligned_not_listened',audio_revision:'audio-v2'};});
 await save(new URL('alignment_manifest_v2.json',dir),{audio_revision:'audio-v2',script_revision:REV,source_script_sha256:SOURCE,input_manifest_sha256:MANIFEST,actual_listening:false,chapters:ledger.requests.map(r=>({scene_id:r.scene_id,file:r.file,sha256:r.sha256,text_sha256:r.text_sha256,alignment_file:r.alignment_file,pcm_duration_s:r.pcm_duration_s,script_revision:REV}))});
 await save(new URL('timing_proposals_v2.json',dir),{audio_revision:'audio-v2',actual_listening:false,total_pcm_duration_s:cursor,scenes:measured});
 ledger.status='complete_alignment_validated_listening_unverified';await save(ledgerUrl,ledger);
 }catch(e){for(const r of ledger.requests){if(r.status==='request_started')r.status='ambiguous_stop_reconcile_required';}ledger.status='blocked_no_automatic_retry';ledger.error=e.message;await save(ledgerUrl,ledger);throw e;}
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
