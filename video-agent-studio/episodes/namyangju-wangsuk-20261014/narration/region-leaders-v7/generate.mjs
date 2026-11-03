import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {account} from '../series-hook-v6/preflight.mjs';
const dir=new URL('./',import.meta.url),ep=new URL('../../',dir);
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const save=async(p,v)=>fs.writeFile(p,JSON.stringify(v,null,2));
const CAP=1850,SHA='6ce6fefb6cbd439b7073091a0107ec65261ba8638aeeb0f339369c0e68640737';
async function authorize(){
 const a=await read(new URL('authorization.json',dir));assert.equal(a.root_execution_authorized,true);assert.equal(a.source_script_sha256,SHA);assert.equal(a.submitted_character_hard_cap,CAP);assert.equal(a.actual_credit_hard_cap,CAP);assert.equal(a.additional_cash_usd_cap,0);assert.equal(a.automatic_retry,false);
 assert.equal(hash(await fs.readFile(new URL(a.source_script_path,ep))),SHA);
 for(const [id,gate] of [[a.script_decision_id,'script'],[a.budget_decision_id,'budget']]){const d=await read('output/video_decisions/decisions/'+id+'.json');assert.equal(d.status,'approved');assert.equal(d.gate,gate);assert.equal(d.episode,'namyangju-wangsuk-20261014');assert.ok(d.summary.includes(SHA));}
}
async function main(){
 const m=await read(new URL('outputs/story-review-v7/manifest.json',ep));assert.equal(m.source_script_sha256,SHA);assert.equal(m.new_input_characters,1541);assert.equal(m.chapters.length,2);
 const input=[];for(const c of m.chapters){const raw=await fs.readFile(new URL(c.path,ep),'utf8');assert.equal(hash(raw),c.sha256);const text=raw.replaceAll('\r\n','\n');assert.equal([...text].length,c.characters);const cues=await read(new URL('outputs/story-review-v7/'+c.scene_id+'_semantic_captions.json',ep));for(const q of cues.cues)assert.equal([...text].slice(q.char_start,q.char_end).join(''),q.text);input.push({...c,text,cues,submitted_text_sha256:hash(text),crlf_normalized:raw!==text});}
 assert.equal(input.reduce((s,c)=>s+c.cues.cues.length,0),72);
 if(!process.argv.includes('--execute-approved')){console.log(JSON.stringify({offline_checks:'passed',characters:1541,cues:72,network_calls:0}));return;}
 await authorize();const lu=new URL('ledger.json',dir);let l;try{l=await read(lu);}catch(e){if(e.code!=='ENOENT')throw e;l={script_revision:'script-v7-region-leaders',source_script_sha256:SHA,requests:[],submitted_characters:0,actual_credits:0};}
 assert.equal(l.source_script_sha256,SHA);assert.ok(l.requests.every(r=>r.status==='complete'),'Unresolved request; no automatic retry');
 try{
 for(const c of input){
 if(l.requests.some(r=>r.scene_id===c.scene_id&&r.status==='complete'))continue;
 await authorize();const {safe,headers,cfg,get}=await account();assert.ok(safe.included_remaining>=CAP-l.submitted_characters);assert.ok(l.submitted_characters+c.characters<=CAP&&l.actual_credits+c.characters<=CAP);
 const file=new URL(c.scene_id+'.mp3',dir);try{await fs.access(file);throw Error('Existing untracked audio');}catch(e){if(e.code!=='ENOENT')throw e;}
 const r={scene_id:c.scene_id,status:'request_started',text_sha256:c.sha256,submitted_text_sha256:c.submitted_text_sha256,crlf_normalized:c.crlf_normalized,characters:c.characters,before:safe,started_at:new Date().toISOString()};l.requests.push(r);l.status='generating';await save(lu,l);
 const res=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+cfg.voice_id+'/with-timestamps?output_format=mp3_44100_128',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({text:c.text,model_id:cfg.model}),signal:AbortSignal.timeout(180000)});
 r.http_status=res.status;r.request_id=res.headers.get('request-id')??res.headers.get('x-request-id');r.character_cost=res.headers.get('character-cost');await save(lu,l);assert.ok(res.ok,'TTS HTTP '+res.status);
 const b=await res.json(),bytes=Buffer.from(b.audio_base64??'','base64');assert.ok(bytes.length>100);await fs.writeFile(file,bytes);await save(new URL(c.scene_id+'.alignment.json',dir),b.alignment);await save(new URL(c.scene_id+'.normalized_alignment.json',dir),b.normalized_alignment??null);
 r.actual_credits=Number(r.character_cost);assert.ok(r.character_cost!==null&&Number.isFinite(r.actual_credits)&&r.actual_credits>=0);l.actual_credits+=r.actual_credits;l.submitted_characters+=c.characters;await save(lu,l);assert.ok(l.actual_credits<=CAP);
 const a=b.alignment;assert.equal(a.characters.join(''),c.text);const starts=a.character_start_times_seconds,ends=a.character_end_times_seconds;assert.equal(starts.length,a.characters.length);assert.equal(ends.length,a.characters.length);starts.forEach((s,i)=>{assert.ok(Number.isFinite(s)&&Number.isFinite(ends[i])&&s>=0&&ends[i]>=s);if(i)assert.ok(s>=starts[i-1]);});
 const ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';const pcm=spawnSync(ff,['-v','error','-i',fileURLToPath(file),'-f','s16le','-ac','1','-ar','44100','pipe:1'],{maxBuffer:150*1024*1024});assert.equal(pcm.status,0);r.pcm_duration_s=pcm.stdout.length/(2*44100);r.frames_30fps=Math.ceil(r.pcm_duration_s*30);r.frame_padded_duration_s=r.frames_30fps/30;
 const over=a.characters.map((ch,i)=>({character:ch,index:i,start_s:starts[i],end_s:ends[i]})).filter(x=>x.end_s>r.pcm_duration_s);assert.ok(over.every(x=>/^[\s.,!?。！？]$/.test(x.character)&&x.end_s-r.pcm_duration_s<=0.1),'Spoken alignment exceeds PCM; stop');
 r.alignment_end_overrun_characters=over;r.clamp_policy='Only nonspoken terminal punctuation end clipped to PCM in derived captions; original alignment preserved; no global shift';
 for(const q of c.cues.cues){q.start_s=starts[q.char_start];q.provider_end_s=ends[q.char_end-1];q.end_s=Math.min(q.provider_end_s,r.pcm_duration_s);q.end_clamped_to_pcm=q.end_s!==q.provider_end_s;q.timing_basis='provider_original_exact_character_alignment';assert.ok(q.end_s>=q.start_s);}
 c.cues.pcm_duration_s=r.pcm_duration_s;c.cues.actual_listening=false;await save(new URL(c.scene_id+'.captions_timed.json',dir),c.cues);
 r.sha256=hash(bytes);r.file='narration/region-leaders-v7/'+c.scene_id+'.mp3';r.alignment_file='narration/region-leaders-v7/'+c.scene_id+'.alignment.json';r.captions_file='narration/region-leaders-v7/'+c.scene_id+'.captions_timed.json';r.script_revision='script-v7-region-leaders';const after=await get('/v1/user/subscription');r.account_after_count=after.character_count;r.account_observed_delta=after.character_count-safe.character_count;r.status='complete';r.completed_at=new Date().toISOString();await save(lu,l);console.log(JSON.stringify({scene_id:r.scene_id,credits:r.actual_credits,pcm_s:r.pcm_duration_s,frames:r.frames_30fps}));
 }
 let cursor=0;const scenes=l.requests.map(r=>{const start=cursor;cursor+=r.pcm_duration_s;return {scene_id:r.scene_id,start_s:start,end_s:cursor,audio_revision:'region-leaders-v7',timing_basis:'actual_decoded_PCM',confidence:'measured_not_listened'};});
 await save(new URL('alignment_manifest.json',dir),{script_revision:'script-v7-region-leaders',source_script_sha256:SHA,actual_listening:false,chapters:l.requests});await save(new URL('timing_proposals.json',dir),{relative_to:'M008_start; director sets global times',total_pcm_duration_s:cursor,scenes});l.status='complete_alignment_validated_listening_unverified';await save(lu,l);
 }catch(e){l.status='blocked_no_automatic_retry';l.error=e.message;await save(lu,l);throw e;}
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
