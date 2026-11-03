import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
const ep=path.resolve('video-agent-studio/episodes/goyang-changneung-20261015');
const read=p=>JSON.parse(fs.readFileSync(path.join(ep,p),'utf8').replace(/^\uFEFF/,''));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ep,p))).digest('hex');
const lock=read('editor/production-v3/timing_lock_v3.json'),manifest=read('writer/script-v3/manifest.json'),am=read('narration/audio-v3/alignment_manifest_v3.json');
const out={revision:'production-v3-input-audit-v1',checked_at:new Date().toISOString(),inputs:{timing_lock_sha256:hash('editor/production-v3/timing_lock_v3.json'),writer_manifest_sha256:hash('writer/script-v3/manifest.json'),alignment_manifest_sha256:hash('narration/audio-v3/alignment_manifest_v3.json')},checks:[],chapters:[],proposal_semantic_candidates:[],actual_listening:false,continuous_playback:false};
const check=(name,pass,detail)=>out.checks.push({name,pass,detail});
check('writer_manifest_identity',out.inputs.writer_manifest_sha256===am.input_manifest_sha256,am.input_manifest_sha256);
check('script_source_consistency',lock.source_script_sha256===am.source_script_sha256&&manifest.source_script_sha256===am.source_script_sha256,am.source_script_sha256);
const original=read('writer/script-v3/scene_proposals.json').scenes;
const ffmpeg=path.resolve('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe');
for(const c of am.chapters){
 const s=manifest.chapters.find(s=>s.scene_id===c.scene_id),text=fs.readFileSync(path.join(ep,'writer/script-v3',s.path),'utf8'),a=read(c.alignment_file),proposal=read(`narration/audio-v3/${c.scene_id}.caption_cues_proposal.json`),chars=[...text];
 const decoded=spawnSync(ffmpeg,['-v','error','-i',path.join(ep,c.file),'-c:a','pcm_s16le','-f','wav','-ac','1','-ar','44100','pipe:1'],{maxBuffer:50*1024*1024});
 let pcmSamples=null;
 const wav=decoded.stdout;
 if(decoded.status===0&&wav?.toString('ascii',0,4)==='RIFF'){for(let i=12;i+8<=wav.length;){const name=wav.toString('ascii',i,i+4),size=wav.readUInt32LE(i+4);if(name==='data'){pcmSamples=Math.min(size,wav.length-i-8)/2;break;}i+=8+size+(size%2);}}
 const detail={scene_id:c.scene_id,audio_sha256:hash(c.file),audio_hash_matches:hash(c.file)===c.sha256,text_hash_matches:hash('writer/script-v3/'+s.path)===c.text_sha256&&c.text_sha256===s.sha256,characters:chars.length,alignment_characters_exact:a.characters.join('')===text,scene_text_exact:original.find(x=>x.scene_id===c.scene_id).narration_text===text,pcm_samples:pcmSamples,pcm_samples_match:decoded.status===0&&pcmSamples===c.pcm_samples_mono_44100,provider_minus_pcm_s:c.provider_last_spoken_end_s-pcmSamples/44100,proposal_source_spans_exact:proposal.cues.every(q=>chars.slice(q.source_start_character,q.source_end_character_exclusive).join('')===q.text),proposal_join_exact:proposal.cues.map(q=>q.text).join('')===text,proposal_timing_monotonic:proposal.cues.every((q,i)=>q.start_s<=q.end_s&&(!i||q.start_s>=proposal.cues[i-1].end_s-0.00001)),alignment_lengths_equal:a.characters.length===a.character_start_times_seconds.length&&a.characters.length===a.character_end_times_seconds.length};
 out.chapters.push(detail);
 for(let i=0;i<proposal.cues.length;i++){const q=proposal.cues[i],t=q.text.trim();if(t.length<9||/\d\s*$/.test(t)||/^[,·.%억만원㎡]/.test(t))out.proposal_semantic_candidates.push({scene_id:c.scene_id,cue_id:q.cue_id,text:t,start_s:q.start_s,end_s:q.end_s,previous:proposal.cues[i-1]?.text,next:proposal.cues[i+1]?.text});}
}
check('all_input_identity_and_pcm',out.chapters.every(x=>x.audio_hash_matches&&x.text_hash_matches&&x.alignment_characters_exact&&x.scene_text_exact&&x.pcm_samples_match&&x.proposal_source_spans_exact&&x.proposal_join_exact&&x.proposal_timing_monotonic&&x.alignment_lengths_equal),'10 source MP3 decoded to PCM and compared to declared sample counts; no listening');
check('timeline_contiguous',lock.segments.every((s,i)=>s.end_frame===s.start_frame+s.duration_frames&&(!i||s.start_frame===lock.segments[i-1].end_frame))&&lock.segments.at(-1).end_frame===lock.duration_frames,lock.duration_frames);
check('intro_outro_lengths',lock.segments.find(s=>s.kind==='brand_intro').duration_frames===150&&lock.segments.find(s=>s.kind==='brand_outro').duration_frames===300,'30fps 5s/10s');
check('last_provider_gap_90_frames',lock.outro_start_frame-lock.last_provider_spoken_frame===90,{outro:lock.outro_start_frame,spoken:lock.last_provider_spoken_frame});
check('lock_audio_hashes',lock.segments.filter(s=>s.kind==='narration').every(s=>hash(s.audio_file)===s.audio_sha256),'source hashes, not final render audio identity');
const m0=lock.segments.filter(s=>s.scene_id==='M000'&&s.kind==='narration');
check('M000_source_contiguous',m0[0].audio_start_s===0&&m0[0].audio_end_s===m0[1].audio_start_s&&m0[1].audio_end_s===am.chapters[0].pcm_duration_s,m0);
fs.writeFileSync(path.join(ep,'qa/production-v3/input_audit.json'),JSON.stringify(out,null,2));
console.log(JSON.stringify({checks:out.checks,chapters:out.chapters.length,semantic_candidates:out.proposal_semantic_candidates},null,2));
