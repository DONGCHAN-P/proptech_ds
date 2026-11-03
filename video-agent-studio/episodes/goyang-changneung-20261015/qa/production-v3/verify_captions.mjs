import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const ep=path.resolve('video-agent-studio/episodes/goyang-changneung-20261015');
const json=p=>JSON.parse(fs.readFileSync(path.join(ep,p),'utf8').replace(/^\uFEFF/,''));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ep,p))).digest('hex');
const p=json('outputs/production-v3/project_v3.json'),lock=json('editor/production-v3/timing_lock_v3.json'),scenes=json('writer/script-v3/scene_proposals.json').scenes;
const n=s=>s.replace(/\s/g,'');
const report={revision:'production-v3-semantic-audit-v1',checked_at:new Date().toISOString(),project_sha256:hash('outputs/production-v3/project_v3.json'),srt_sha256:hash('outputs/production-v3/changneung_full_v3.srt'),checks:[],scene_checks:[],candidates:[],actual_frame_review:false,actual_listening:false};
const add=(name,pass,detail)=>report.checks.push({name,pass,detail});
for(const s of scenes){const cues=p.captions.filter(c=>c.scene_id===s.scene_id),chars=[...s.narration_text];report.scene_checks.push({scene_id:s.scene_id,exact_normalized_join:n(cues.map(c=>c.text).join(''))===n(s.narration_text),source_spans:cues.every(c=>chars.slice(c.source_start_character,c.source_end_character_exclusive).join('')===c.raw_text),raw_equals_display:cues.every(c=>n(c.raw_text)===n(c.text)),ordered_spans:cues.every((c,i)=>!i||c.source_start_character>=cues[i-1].source_end_character_exclusive)});}
add('exact_original_and_spans',report.scene_checks.every(c=>c.exact_normalized_join&&c.source_spans&&c.raw_equals_display&&c.ordered_spans),'all 10 chapters');
add('timing_lock_identity',p.timing_lock_sha256===hash('editor/production-v3/timing_lock_v3.json'),p.timing_lock_sha256);
add('cue_time_bounds',p.captions.every((c,i)=>c.start_frame>=0&&c.end_frame>c.start_frame&&c.end_frame<=lock.duration_frames&&(!i||c.start_frame>=p.captions[i-1].end_frame)),{count:p.captions.length,first:p.captions[0].start_frame,last:p.captions.at(-1).end_frame});
const hidden=lock.segments.filter(s=>s.captions_visible===false);
add('no_captions_in_brand_hold',p.captions.every(c=>hidden.every(s=>c.end_frame<=s.start_frame||c.start_frame>=s.end_frame)),hidden.map(s=>({kind:s.kind,start:s.start_frame,end:s.end_frame})));
add('visual_intervals_contiguous',p.visual_intervals.every((v,i)=>v.duration_frames===v.end_frame-v.start_frame&&(!i||v.start_frame===p.visual_intervals[i-1].end_frame))&&p.visual_intervals[0].start_frame===0&&p.visual_intervals.at(-1).end_frame===lock.duration_frames,p.visual_intervals.length);
add('persistent_body_box',p.visual_intervals.filter(v=>v.kind==='frame'&&!hidden.some(s=>v.start_frame>=s.start_frame&&v.end_frame<=s.end_frame)).every(v=>v.hideCaption===false),'source JSON only, final encoded result pending');
add('max_two_lines',p.captions.every(c=>c.text.split('\n').length<=2),Math.max(...p.captions.map(c=>c.text.split('\n').length)));
const srt=fs.readFileSync(path.join(ep,'outputs/production-v3/changneung_full_v3.srt'),'utf8').replace(/^\uFEFF/,'').replace(/\r/g,'').trim().split(/\n\n+/).map(x=>{const l=x.split('\n');return {id:Number(l[0]),time:l[1],text:l.slice(2).join('\n')}});
const ms=t=>{const m=t.match(/(\d+):(\d+):(\d+),(\d+)/);return (+m[1]*3600+ +m[2]*60+ +m[3])*1000+ +m[4]};
add('srt_json_text_and_time',srt.length===p.captions.length&&srt.every((s,i)=>{const c=p.captions[i],t=s.time.split(' --> ');return s.id===i+1&&s.text===c.text&&Math.abs(ms(t[0])-c.startMs)<=0.51&&Math.abs(ms(t[1])-c.endMs)<=0.51}),srt.length);
for(let i=0;i<p.captions.length;i++){const c=p.captions[i],next=p.captions[i+1];if(c.text.trim().length<12||/지티엑스\s*\n\s*에이/.test(c.text)||(/년\s*$/.test(c.text)&&next&&/^[가-힣\d]+월/.test(next.text)))report.candidates.push({cue_id:c.cue_id,text:c.text,next:next?.text,start_frame:c.start_frame,end_frame:c.end_frame});}
fs.writeFileSync(path.join(ep,'qa/production-v3/semantic_audit.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
