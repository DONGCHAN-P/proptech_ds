import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {account} from '../video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs';
const ep='video-agent-studio/episodes/regional-price-recovery-20261022';
const out=ep+'/outputs/production-v1-budget',plan=ep+'/narration/production-v1';
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.mkdir(out,{recursive:true});await fs.mkdir(plan,{recursive:true});
const input=ep+'/outputs/script-review-v3/scenes_v3.json',scenes=await read(input),cfg=await read('config/tts.json');
const paragraphs=[];
for(const scene of scenes.scenes)for(const beat of scene.beats){
 const text=beat.narration_text;const file=beat.beat_id+'.txt';
 await fs.writeFile(plan+'/'+file,text,'utf8');
 paragraphs.push({beat_id:beat.beat_id,scene_id:scene.scene_id,path:file,text,characters:[...text].length,sha256:sha(text)});
}
const characters=paragraphs.reduce((s,p)=>s+p.characters,0),cap=characters+Math.ceil(characters*.2);
const manifest={script_revision:'v3',script_sha256:sha(await fs.readFile(ep+'/outputs/script-review-v3/script_v3.md')),scenes_sha256:sha(await fs.readFile(input)),config_sha256:sha(await fs.readFile('config/tts.json')),voice_id:cfg.voice_id,model:cfg.model,characters,paragraphs,text_policy:'Exact approved v3 narration, no substitutions or added tags; separate paragraph requests for precise data emphasis.'};
await fs.writeFile(plan+'/manifest.json',JSON.stringify(manifest,null,2)+'\n');
let snapshot={status:'not_queried',paid_api_called:false};
if(process.argv.includes('--account')){
 try{snapshot=(await account()).safe;}catch(e){snapshot={status:'read_failed',failure:e.message,paid_api_called:false};}
}
await fs.writeFile(out+'/account_readonly.json',JSON.stringify(snapshot,null,2)+'\n');
const budget={status:'proposed_requires_scoped_budget_approval',at_utc:new Date().toISOString(),script_revision:'v3',script_sha256:manifest.script_sha256,narration_manifest_sha256:sha(await fs.readFile(plan+'/manifest.json')),voice:cfg.voice_name,model:cfg.model,input_characters:characters,paragraph_requests:paragraphs.length,correction_allowance:cap-characters,included_credit_cap:cap,additional_cash_usd_cap:0,automatic_retry:false,topup_or_overage_authorized:false,included_remaining:snapshot.included_remaining??null,account_checks_passed:snapshot.passed??false,cap_fits_included:snapshot.included_remaining>=cap,cloud_render_paid:false,new_paid_images_or_music:false,generation_started:false};
await fs.writeFile(out+'/budget_proposal.json',JSON.stringify(budget,null,2)+'\n');
console.log(JSON.stringify({budget,account:snapshot}));
