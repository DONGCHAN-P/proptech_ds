import fs from 'node:fs/promises';
const env={};
for(const line of(await fs.readFile('.env','utf8')).split(/\r?\n/)){
 const m=line.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);
 if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');
}
if(!env.ELEVENLABS_API_KEY)throw Error('Missing configured ElevenLabs key');
async function read(path){const r=await fetch('https://api.elevenlabs.io'+path,{headers:{'xi-api-key':env.ELEVENLABS_API_KEY},signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('Read check HTTP '+r.status);return r.json();}
const results=await Promise.allSettled([read('/v1/user/subscription'),read('/v1/voices/4p6UA7mnodF5q7JFFrnW'),read('/v1/models')]);
const out={checked_at:new Date().toISOString(),generation_started:false,requests:'GET only',errors:results.filter(x=>x.status==='rejected').map(x=>x.reason.message)};
if(results[0].status==='fulfilled'){const s=results[0].value;out.subscription={tier:s.tier,status:s.status,used:s.character_count??s.credit_count,limit:s.character_limit??s.credit_limit,overage_allowed:s.allowed_to_extend_character_limit??s.allowed_to_extend_credit_limit,max_extension:s.max_character_limit_extension??s.max_credit_limit_extension};out.subscription.remaining=out.subscription.limit-out.subscription.used;}
if(results[1].status==='fulfilled'){const v=results[1].value;out.voice={voice_id:v.voice_id,name:v.name,credit_multiplier:v.credit_multiplier??v.sharing?.credit_multiplier??null};}
if(results[2].status==='fulfilled'){const m=results[2].value.find(x=>x.model_id==='eleven_v4');out.model=m?{model_id:m.model_id,token_cost_factor:m.token_cost_factor,requires_alpha_access:m.requires_alpha_access}:null;}
out.status=out.errors.length?'blocked':'read_checks_complete';
await fs.writeFile(new URL('preflight_v2.json',import.meta.url),JSON.stringify(out,null,2));
console.log(JSON.stringify(out));
