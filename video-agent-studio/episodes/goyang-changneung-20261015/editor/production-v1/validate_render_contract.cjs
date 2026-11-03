// A fail-closed handoff check. This script never invokes paid APIs or a renderer.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const ep=path.resolve(__dirname,'../..');
function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')}
function checked(p,h){assert(p&&h,'missing path/hash');const absolute=path.resolve(ep,p);assert(fs.existsSync(absolute),`missing ${p}`);assert.equal(sha(absolute),h,`hash mismatch ${p}`);return absolute}
try{
const c=JSON.parse(fs.readFileSync(process.argv[2]||path.join(__dirname,'render_contract.template.json'),'utf8'));
assert.equal(c.status,'ready_for_local_render','Real voice, timing lock and final geographic media are required; template is not a completed video.');
assert.equal(c.timing_basis,'actual_audio_alignment');assert.equal(c.fps,30);assert.equal(c.width,1920);assert.equal(c.height,1080);
checked(c.timing_lock_path,c.timing_lock_sha256);
checked('writer/script-v2/manifest.json',c.script_manifest_sha256);
checked(c.script_review_path,c.script_review_sha256);
for(const approval of [c.script_approval,c.budget_approval]){assert(approval?.approved===true,'version-matched approvals required');checked(approval.evidence_path,approval.evidence_sha256)}
assert.equal(c.scenes.map(s=>s.scene_id).join(','),'M000,M001,M002,M003,M004,M005,M006,M007,M008,M009');
for(const s of c.scenes){
 checked(s.narration_text_path,s.narration_text_sha256);checked(s.audio_path,s.audio_sha256);
 assert(Number.isInteger(s.start_frame)&&s.end_frame>s.start_frame);assert(s.last_spoken_frame<=s.end_frame&&s.last_spoken_frame>=s.start_frame);
 checked(s.captions_path,s.captions_sha256);assert(s.shots.length>0,`${s.scene_id}: no authored shots`);
 let next=s.start_frame;
 for(const shot of s.shots){assert.equal(shot.start_frame,next,'shot gap/overlap');assert(shot.end_frame>next);next=shot.end_frame;
  checked(shot.path,shot.sha256);assert.equal(shot.status,'reviewed_for_final_video');assert(shot.rights_evidence_path&&shot.source_type);assert(!shot.path.includes('visual-review-v2'),'representative diagram is not final media');
  checked(shot.rights_evidence_path,shot.rights_evidence_sha256);
 }
 assert.equal(next,s.end_frame,'shot coverage must match measured scene');
 if(['M001','M003','M005','M007','M009'].includes(s.scene_id))assert(s.shots.some(x=>x.source_type==='verified_geographic_map'),'geographic grounding missing');
}
assert.equal(c.brand_intro.frames,150);assert.equal(c.brand_outro.frames,300);assert.equal(c.brand_outro.post_speech_hold_frames,90);
assert(c.final_media_review?.approved===true,'final media review missing');
console.log('Ready contract structural/hash checks passed. This is not audio/visual QA or approval verification.');
}catch(e){console.error(e.message);process.exitCode=1}
