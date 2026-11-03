import fs from 'node:fs/promises';
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
export async function account(){
 const cfg=await read('config/tts.json');if(cfg.voice_id!=='4p6UA7mnodF5q7JFFrnW'||cfg.model!=='eleven_v4')throw Error('Voice configuration mismatch');
 const env={};for(const l of(await fs.readFile('.env','utf8')).split(/\r?\n/)){const m=l.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');}
 const headers={'xi-api-key':env.ELEVENLABS_API_KEY};
 const get=async p=>{const r=await fetch('https://api.elevenlabs.io'+p,{headers,signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('GET HTTP '+r.status);return r.json();};
 const [s,v,models]=await Promise.all([get('/v1/user/subscription'),get('/v1/voices/'+cfg.voice_id),get('/v1/models')]);const m=models.find(m=>m.model_id===cfg.model),rate=v.sharing?.rate;
 const passed=s.status==='active'&&s.tier!=='free'&&s.character_limit-s.character_count>=284&&s.can_extend_character_limit===false&&s.allowed_to_extend_character_limit===false&&s.max_credit_limit_extension===0&&rate>0&&rate<=1&&m?.model_rates?.character_cost_multiplier>0&&m.model_rates.character_cost_multiplier<=1&&m.model_rates.cost_discount_multiplier>0&&m.model_rates.cost_discount_multiplier<=1;
 const safe={checked_at:new Date().toISOString(),passed,tier:s.tier,status:s.status,included_remaining:s.character_limit-s.character_count,character_count:s.character_count,character_limit:s.character_limit,voice_rate:rate,model_rates:m?.model_rates,overage_enabled:s.can_extend_character_limit,allowed_to_extend:s.allowed_to_extend_character_limit,max_extension:s.max_credit_limit_extension,paid_api_called:false};
 if(!passed)throw Error('Account/credit/rate preflight failed');return {safe,headers,cfg,get};
}
if(process.argv.includes('--get-only')){try{const {safe}=await account();await fs.writeFile(new URL('preflight.json',import.meta.url),JSON.stringify(safe,null,2));console.log(JSON.stringify(safe));}catch(e){console.error(e.message);process.exitCode=1;}}
