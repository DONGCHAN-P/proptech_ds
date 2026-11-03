import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const dir=new URL('./',import.meta.url),ledgerUrl=new URL('generation_ledger_v1.json',dir);
const ledger=JSON.parse(await fs.readFile(ledgerUrl,'utf8'));
const probe=path.resolve('video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe');
const ffmpeg=path.resolve('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe');
if(ledger.requests.length!==8||ledger.requests.some(r=>r.status!=='complete'))throw Error('Not all scenes generated');
let time=0;const scenes=[];
for(const r of ledger.requests){
const audio=fileURLToPath(new URL('audio-v1/'+r.scene_id+'.mp3',dir));
const p=spawnSync(probe,['-v','error','-show_entries','format=duration:stream=codec_name,sample_rate,channels','-of','json',audio],{encoding:'utf8'});if(p.status!==0)throw Error('Probe failed '+r.scene_id);
const info=JSON.parse(p.stdout),duration=Number(info.format.duration);if(!Number.isFinite(duration)||duration<=0)throw Error('Invalid duration');
const decode=spawnSync(ffmpeg,['-v','error','-i',audio,'-f','null','-'],{encoding:'utf8'});if(decode.status!==0)throw Error('Decode failed '+r.scene_id);
r.account_observed_delta_credits=r.actual_credits;const cost=Number(r.response_character_cost);if(!Number.isFinite(cost)||cost<0)throw Error('Missing response cost');r.actual_credits=cost;r.billing_basis='Provider response character-cost header; account before/after deltas can lag or include earlier request updates';r.duration_seconds=duration;r.streams=info.streams;r.decode_verified=true;
scenes.push({scene_id:r.scene_id,start_s:time,end_s:time+duration,duration_s:duration,timing_basis:'measured_ffprobe_mp3_container_duration_sequential_without_editor_gaps',confidence:'high_duration_only',audio_revision:'audio-v1',audio_path:r.audio_path,listening_verified:false});time+=duration;
await fs.writeFile(new URL('audio-v1/'+r.scene_id+'.json',dir),JSON.stringify(r,null,2));
}
ledger.actual_credit_total=ledger.requests.reduce((a,r)=>a+r.actual_credits,0);ledger.billing_basis='Sum provider character-cost response headers';ledger.total_audio_seconds=time;ledger.listening_verified=false;ledger.status='audio_generated_decode_verified_listening_pending';if(ledger.actual_credit_total>8903)throw Error('Cap exceeded');
await fs.writeFile(ledgerUrl,JSON.stringify(ledger,null,2));
await fs.writeFile(new URL('timing_proposals_v1.json',dir),JSON.stringify({revision:'timing-proposals-v1',script_revision:'script-v2',audio_revision:'audio-v1',total_duration_seconds:time,note:'Measured file lengths; no editorial gaps or trims. Director confirms common timing. No actual listening performed.',scenes},null,2));
console.log(JSON.stringify({scenes:scenes.length,total_duration_seconds:time,actual_credits:ledger.actual_credit_total,decode_all_passed:true,listening_verified:false}));
