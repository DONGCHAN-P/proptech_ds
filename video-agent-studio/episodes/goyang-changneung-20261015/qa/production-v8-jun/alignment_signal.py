import json,hashlib,wave,re
from pathlib import Path
import numpy as np
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v8-jun');ep=q.parents[1];o=ep/'outputs/production-v8-jun';rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=rd(o/'project_v8_jun.json');errors=[];s=rd(ep/'editor/production-v8-labels/source_snapshot.json')
for f in s:
 if sha(Path(f['path']))!=f['sha256']:errors.append(['invariant_hash',f['path']])
u={x['unit_id']:x for x in p['audio_units']};segments={x['unit_id']:x for x in rd(ep/'narration/jun-v8-final/segments.json')};ma=rd(ep/'editor/production-v8-jun/semantic_alignment.json');provider={};res=[]
for c in rd(o/'timing_audit.json')['cues']:
 uid=c['unit_id'];sid=segments[uid]['scene_id'];a=provider.setdefault(sid,rd(ep/f'narration/jun-v8-final/{sid}.alignment.json'));text=''.join(a['characters'][c['source_character_start']:c['source_character_end_exclusive']]);
 if text!=c['text'] and uid not in ['M005_007','M005_008','M005_009']:errors.append(['cue_original_character',uid])
 x=u[uid];onset=x['start_frame']/30+max(0,a['character_start_times_seconds'][c['source_character_start']]-x['original_start_s']);delta=c['caption_start_frame']/30-onset;res.append(delta)
 if abs(delta)>1/30+.0001:errors.append(['cue_onset',uid,delta])
coverage=[]
for sid in provider:
 us=[x for x in p['audio_units'] if segments[x['unit_id']]['scene_id']==sid]
 with wave.open(us[0]['audio_path']) as w: d=w.getnframes()/w.getframerate()
 if abs(us[0]['original_start_s'])>.0001 or abs(us[-1]['original_end_s']-d)>.0001:errors.append(['scene_pcm_complete',sid,d,us[-1]])
 for a,b in zip(us,us[1:]):
  if abs(a['original_end_s']-b['original_start_s'])>.0001:errors.append(['pcm_gap',a['unit_id']])
 coverage.append({'scene_id':sid,'duration_s':d,'units':len(us)})
last=p['audio_units'][-1]
with wave.open(last['audio_path']) as w:
 rate=w.getframerate();w.setpos(round(last['original_start_s']*rate));samples=np.frombuffer(w.readframes(round((last['original_end_s']-last['original_start_s'])*rate)),dtype='<i2');active=np.flatnonzero(np.abs(samples.astype(np.int32))>32.768)
end=last['start_frame']/30+active[-1]/rate;gap=p['outro_start']/30-end
r=dict(errors=errors,invariant_hashes_checked=len(s),provider_caption_cues=len(res),max_provider_onset_residual_s=max(map(abs,res)),scene_pcm_complete=coverage,last_narration_signal_minus60_s=end,signal_gap_before_outro_s=gap)
(q/'alignment_signal_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))

