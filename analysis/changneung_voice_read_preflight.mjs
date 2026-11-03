import fs from 'node:fs/promises';
const env={};
for(const line of(await fs.readFile('.env','utf8')).split(/\r?\n/)){
  const m=line.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);
  if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');
}
if(!env.ELEVENLABS_API_KEY)throw Error('Missing configured key');
async function get(path){const r=await fetch('https://api.elevenlabs.io'+path,{headers:{'xi-api-key':env.ELEVENLABS_API_KEY},signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('Read HTTP '+r.status);return r.json();}
const [s,v,models]=await Promise.all([get('/v1/user/subscription'),get('/v1/voices/4p6UA7mnodF5q7JFFrnW'),get('/v1/models')]);
const model=models.find(x=>x.model_id==='eleven_v4');
const out={checked_at:new Date().toISOString(),requests:'GET only',generation_started:false,
subscription:{tier:s.tier,used:s.character_count??s.credit_count,limit:s.character_limit??s.credit_limit,overage_allowed:s.allowed_to_extend_character_limit??s.allowed_to_extend_credit_limit},
voice:{id:v.voice_id,name:v.name,credit_multiplier:v.credit_multiplier??v.sharing?.credit_multiplier??null,sharing_rate:v.sharing?.rate??null},
model:model?{id:model.model_id,token_cost_factor:model.token_cost_factor,model_rates:model.model_rates??null}:null};
out.subscription.remaining=out.subscription.limit-out.subscription.used;
await fs.mkdir('video-agent-studio/episodes/goyang-changneung-20261015/narration',{recursive:true});
await fs.writeFile('video-agent-studio/episodes/goyang-changneung-20261015/narration/read_preflight_v2.json',JSON.stringify(out,null,2));
console.log(JSON.stringify(out));
