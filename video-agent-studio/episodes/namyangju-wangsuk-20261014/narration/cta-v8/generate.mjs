import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {account} from '../series-hook-v6/preflight.mjs';
const dir=new URL('./',import.meta.url),episode=new URL('../../',dir);
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const save=async(p,v)=>fs.writeFile(p,JSON.stringify(v,null,2));
async function main(){
 const text=await fs.readFile(new URL('outputs/story-review-v8/M010_cta.txt',episode),'utf8');
 assert.equal(hash(text),'d67f35c05d75736239d631a8afab1c9f6d84a1523ed0b03f5dc653651ba18d11');assert.equal([...text].length,59);
 if(!process.argv.includes('--execute-approved')){console.log(JSON.stringify({offline_input_check:'passed',characters:59,network_calls:0}));return;}
 const auth=await read(new URL('authorization.json',dir));assert.equal(auth.root_execution_authorized,true);assert.equal(auth.actual_credit_hard_cap,71);assert.equal(auth.submitted_character_hard_cap,71);assert.equal(auth.additional_cash_usd_cap,0);assert.equal(auth.text_sha256,hash(text));assert.ok(/^[a-f0-9]{64}$/.test(auth.source_script_sha256));
 for(const [id,gate] of [[auth.script_decision_id,'script'],[auth.budget_decision_id,'budget']]){assert.ok(/^[a-f0-9]{12}$/.test(id));const d=await read('output/video_decisions/decisions/'+id+'.json');assert.equal(d.status,'approved');assert.equal(d.gate,gate);assert.equal(d.episode,'namyangju-wangsuk-20261014');assert.ok(d.summary.includes(auth.source_script_sha256));}
 const script=await fs.readFile(new URL(auth.source_script_path,episode));assert.equal(hash(script),auth.source_script_sha256);
 const receipt=new URL('generation_receipt.json',dir);try{await fs.access(receipt);throw Error('Existing request receipt; no automatic retry or duplicate');}catch(e){if(e.code!=='ENOENT')throw e;}
 const {safe,headers,cfg,get}=await account();const r={status:'request_started',scene_id:'M010',characters:59,text_sha256:hash(text),source_script_sha256:auth.source_script_sha256,before:safe,started_at:new Date().toISOString()};await save(receipt,r);
 try{
 const res=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+cfg.voice_id+'/with-timestamps?output_format=mp3_44100_128',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({text,model_id:cfg.model}),signal:AbortSignal.timeout(180000)});
 r.http_status=res.status;r.request_id=res.headers.get('request-id')??res.headers.get('x-request-id');r.character_cost=res.headers.get('character-cost');await save(receipt,r);assert.ok(res.ok,'TTS HTTP '+res.status);
 const body=await res.json(),bytes=Buffer.from(body.audio_base64??'','base64');assert.ok(bytes.length>100);const file=new URL('M010.mp3',dir);await fs.writeFile(file,bytes);await save(new URL('M010.alignment.json',dir),body.alignment);await save(new URL('M010.normalized_alignment.json',dir),body.normalized_alignment??null);
 r.actual_credits=Number(r.character_cost);assert.ok(r.character_cost!==null&&Number.isFinite(r.actual_credits)&&r.actual_credits>=0&&r.actual_credits<=71);await save(receipt,r);
 const a=body.alignment;assert.equal(a.characters.join(''),text);assert.equal(a.characters.length,a.character_start_times_seconds.length);assert.equal(a.characters.length,a.character_end_times_seconds.length);a.characters.forEach((_,i)=>{const s=a.character_start_times_seconds[i],e=a.character_end_times_seconds[i];assert.ok(Number.isFinite(s)&&Number.isFinite(e)&&s>=0&&e>=s);if(i)assert.ok(s>=a.character_start_times_seconds[i-1]);});
 const ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';const pcm=spawnSync(ff,['-v','error','-i',fileURLToPath(file),'-f','s16le','-ac','1','-ar','44100','pipe:1'],{maxBuffer:30*1024*1024});assert.equal(pcm.status,0);r.pcm_duration_s=pcm.stdout.length/(2*44100);assert.ok(Math.max(...a.character_end_times_seconds)<=r.pcm_duration_s+0.1);
 r.sha256=hash(bytes);r.account_after=(await get('/v1/user/subscription')).character_count;r.actual_listening=false;r.status='complete_alignment_validated_listening_unverified';await save(receipt,r);
 console.log(JSON.stringify({status:r.status,credits:r.actual_credits,pcm_duration_s:r.pcm_duration_s}));
 }catch(e){r.status='blocked_no_automatic_retry';r.error=e.message;await save(receipt,r);throw e;}
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
