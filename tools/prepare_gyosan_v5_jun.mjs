import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {account} from '../video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs';
const ep='video-agent-studio/episodes/hanam-gyosan-20261019',out=ep+'/outputs/jun-v5-budget',plan=ep+'/narration/jun-v5-plan';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
await fs.mkdir(out,{recursive:true});await fs.mkdir(plan,{recursive:true});
const scenes=await read(ep+'/writer/scenes_v5.json'),script=await fs.readFile(ep+'/outputs/script-review-v5/script_v5.md'),cfg=await read('config/tts.json');
const chapters=[];
for(const s of scenes){const text=s.units.map(u=>u.text).join('\n');await fs.writeFile(plan+'/'+s.scene_id+'.txt',text);chapters.push({scene_id:s.scene_id,path:s.scene_id+'.txt',sha256:hash(text),characters:[...text].length});}
const characters=chapters.reduce((x,c)=>x+c.characters,0),cap=characters+Math.ceil(characters*.2);
const manifest={script_revision:'v5',source_script:'outputs/script-review-v5/script_v5.md',source_script_sha256:hash(script),scenes_sha256:hash(await fs.readFile(ep+'/writer/scenes_v5.json')),config_sha256:hash(await fs.readFile('config/tts.json')),characters,chapters,text_policy:'Exact approved narration; per-scene newline separators; no added tags or word substitutions.'};
await fs.writeFile(plan+'/manifest.json',JSON.stringify(manifest,null,2));
let snapshot;
try{const a=await account();snapshot=a.safe;}catch(e){snapshot={status:'read_failed',failure:'Read-only network/account preflight failed; no synthesis attempted',paid_api_called:false};}
await fs.writeFile(out+'/account_readonly.json',JSON.stringify(snapshot,null,2));
const budget={status:'proposed_requires_scoped_budget_approval',script_revision:'v5',source_script_sha256:manifest.source_script_sha256,narration_manifest_sha256:hash(await fs.readFile(plan+'/manifest.json')),voice:cfg.voice_name,model:cfg.model,input_characters:characters,correction_allowance:cap-characters,included_credit_cap:cap,additional_cash_usd_cap:0,automatic_retry:false,topup_or_overage_authorized:false,included_remaining:snapshot.included_remaining??null,generation_started:false,upload_visibility:'private; final artifact-specific completed/pre_upload gates still required'};
await fs.writeFile(out+'/budget_proposal.json',JSON.stringify(budget,null,2));
console.log(JSON.stringify({budget,account:snapshot}));
