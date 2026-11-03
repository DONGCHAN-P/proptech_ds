import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const dir=new URL('./',import.meta.url),episode=new URL('../',dir);
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const scenes=(await read(new URL('writer/scene_proposals_v2.json',episode))).scenes;
const cfg=await read('config/tts.json'),budget=await read(new URL('budget_v1.json',episode));
const env={};for(const l of(await fs.readFile('.env','utf8')).split(/\r?\n/)){const m=l.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');}
const headers={'xi-api-key':env.ELEVENLABS_API_KEY};
async function get(path){const r=await fetch('https://api.elevenlabs.io'+path,{headers,signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('GET '+path+' HTTP '+r.status);return r.json();}
const ledgerUrl=new URL('generation_ledger_v1.json',dir);
let ledger;try{ledger=await read(ledgerUrl);}catch{ledger={audio_revision:'audio-v1',script_revision:'script-v2',budget_revision:'budget-v1',approval_decision:'e2e510eebb19',started_at:null,status:'preflight',requests:[],actual_credit_total:0,character_total:0};}
const save=()=>fs.writeFile(ledgerUrl,JSON.stringify(ledger,null,2));
if(ledger.requests.some(r=>r.status!=='complete'))throw Error('Unresolved prior request: no automatic retry');
if(cfg.model!=='eleven_v4'||cfg.voice_id!=='4p6UA7mnodF5q7JFFrnW'||budget.effective_credit_hard_cap!==8903)throw Error('Approval scope mismatch');
if(scenes.reduce((a,s)=>a+s.narration_text.length,0)!==7419)throw Error('Approved input count changed');
const [sub,voice,models]=await Promise.all([get('/v1/user/subscription'),get('/v1/voices/'+cfg.voice_id),get('/v1/models')]);
const model=models.find(m=>m.model_id===cfg.model);
if(sub.status!=='active'||sub.tier==='free'||sub.character_limit-sub.character_count<8903||sub.can_extend_character_limit!==false||sub.allowed_to_extend_character_limit!==false||sub.max_credit_limit_extension!==0||voice.sharing?.rate!==1||model?.model_rates?.character_cost_multiplier!==1||model.model_rates.cost_discount_multiplier!==1)throw Error('Preflight budget/account condition mismatch');
ledger.preflight={checked_at:new Date().toISOString(),tier:sub.tier,status:sub.status,count:sub.character_count,limit:sub.character_limit,remaining:sub.character_limit-sub.character_count,voice_multiplier:1,model_multiplier:1,commercial_terms_source:'https://elevenlabs.io/docs/overview/administration/billing',additional_cash_usd:0,settings_policy:'Same as approved benchmark: only text and model_id; saved voice defaults retained, no new style settings.'};
await fs.mkdir(new URL('audio-v1/',dir),{recursive:true});
try{
for(const scene of scenes){
if(ledger.requests.some(r=>r.scene_id===scene.scene_id&&r.status==='complete'))continue;
const dest=new URL('audio-v1/'+scene.scene_id+'.mp3',dir);try{await fs.access(dest);throw Error('Untracked existing audio');}catch(e){if(e.code!=='ENOENT')throw e;}
const before=await get('/v1/user/subscription'),chars=scene.narration_text.length;
if(before.character_limit-before.character_count<chars||ledger.actual_credit_total+chars>8903||ledger.character_total+chars>8903)throw Error('Budget stop');
const receipt={scene_id:scene.scene_id,characters:chars,text_sha256:crypto.createHash('sha256').update(scene.narration_text).digest('hex'),status:'request_started',started_at:new Date().toISOString(),before_character_count:before.character_count};
ledger.started_at??=receipt.started_at;ledger.status='generating';ledger.requests.push(receipt);await save();console.log('generation_request_started '+scene.scene_id);
const res=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+cfg.voice_id+'?output_format=mp3_44100_128',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({text:scene.narration_text,model_id:cfg.model}),signal:AbortSignal.timeout(180000)});
receipt.request_id=res.headers.get('request-id')??res.headers.get('x-request-id');receipt.response_character_cost=res.headers.get('character-cost');receipt.http_status=res.status;
if(!res.ok){const j=await res.json().catch(()=>({}));receipt.status='failed';receipt.error_status=j.detail?.status??'rejected';await save();throw Error('TTS HTTP '+res.status+' '+receipt.error_status);}
const bytes=Buffer.from(await res.arrayBuffer());if(bytes.length<100)throw Error('Empty audio');await fs.writeFile(dest,bytes);
const after=await get('/v1/user/subscription');receipt.after_character_count=after.character_count;receipt.account_observed_delta_credits=after.character_count-before.character_count;receipt.actual_credits=Number(receipt.response_character_cost);receipt.billing_basis='Provider character-cost response header; account deltas can lag';
if(!Number.isFinite(receipt.actual_credits)||receipt.actual_credits<0)throw Error('Invalid billing delta');
receipt.bytes=bytes.length;receipt.sha256=crypto.createHash('sha256').update(bytes).digest('hex');receipt.completed_at=new Date().toISOString();receipt.status='complete';receipt.audio_path='narration/audio-v1/'+scene.scene_id+'.mp3';
ledger.actual_credit_total+=receipt.actual_credits;ledger.character_total+=chars;await fs.writeFile(new URL('audio-v1/'+scene.scene_id+'.json',dir),JSON.stringify(receipt,null,2));await save();
if(ledger.actual_credit_total>8903)throw Error('Actual billing cap exceeded: stop');console.log('saved '+scene.scene_id+' actual_credits='+receipt.actual_credits+' bytes='+bytes.length);
}
ledger.status='generated_pending_duration_and_listening';ledger.completed_at=new Date().toISOString();await save();console.log(JSON.stringify({status:ledger.status,scenes:ledger.requests.length,actual_credit_total:ledger.actual_credit_total}));
}catch(e){ledger.status='blocked';ledger.error=e.message;await save();console.log(JSON.stringify({status:'blocked',error:e.message,actual_credit_total:ledger.actual_credit_total}));process.exitCode=1;}
