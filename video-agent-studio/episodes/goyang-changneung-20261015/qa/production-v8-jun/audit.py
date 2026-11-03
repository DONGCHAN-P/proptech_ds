import json,hashlib,subprocess,wave,re
from pathlib import Path
import numpy as np
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v8-jun'); ep=q.parents[1];o=ep/'outputs/production-v8-jun';rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda s:re.sub(r'\s+','',s)
p=rd(o/'project_v8_jun.json');h=rd(ep/'editor/production-v8-jun/handoff.json');errors=[]
for x in h['artifacts']+h['input_versions']:
 if sha(Path(x['path']))!=x['sha256']:errors.append(['hash',x['path']])
packet=rd(ep/'writer/revision-v8/narration_packet.json');segs=rd(ep/'narration/jun-v8-final/segments.json'); align={s['scene_id']:rd(ep/f"narration/jun-v8-final/{s['scene_id']}.alignment.json") for s in packet['scenes']}
for scene in packet['scenes']:
 a=align[scene['scene_id']]
 if norm(''.join(a['characters']))!=norm(scene['text']):errors.append(['provider_source',scene['scene_id']])
 ss=[s for s in segs if s['scene_id']==scene['scene_id']]
 if norm(''.join(s['text'] for s in ss))!=norm(scene['text']):errors.append(['semantic_source',scene['scene_id']])
 for s in ss:
  if ''.join(a['characters'][s['source_character_start']:s['source_character_end_exclusive']])!=s['text']:errors.append(['unit_character_slice',s['unit_id']])
units={u['unit_id']:u for u in p['audio_units']};checks=[];display=[]
for s in segs:
 u=units[s['unit_id']];cs=[c for c in p['captions'] if c['unit_id']==s['unit_id']]
 if norm(''.join(c['text'] for c in cs))!=norm(s['text']):display.append(s['unit_id'])
 if not cs or cs[0]['start_frame']!=u['start_frame'] or cs[-1]['end_frame']>u['end_frame']:errors.append(['cue_bounds',s['unit_id']])
 with wave.open(u['audio_path']) as w:duration=w.getnframes()/w.getframerate()
 if u['original_start_s']<0 or u['original_end_s']>duration+0.00001:errors.append(['pcm_bounds',s['unit_id']])
 delta=(u['end_frame']-u['start_frame'])/30-(u['original_end_s']-u['original_start_s']);checks.append(delta)
 if abs(delta)>1/30+.0001:errors.append(['unit_rounding',s['unit_id'],delta])
for a,b in zip(p['visual_intervals'],p['visual_intervals'][1:]):
 if a['end_frame']!=b['start_frame']:errors.append(['visual_gap',a['unit_id']])
cs=p['captions'];sus=[]
for a,b in zip(cs,cs[1:]):
 if a['end_frame']>b['start_frame']:errors.append(['cue_overlap',a['unit_id']])
 if re.search(r'\d$',a['text']) and re.match(r'(년|월|일|억|만|원|분|세대|층|㎡|제곱)',b['text']):sus.append([a,b])
intervals=p['visual_intervals'];cards=[x for x in intervals if x['kind']=='chapter'];brands=[x for x in intervals if x['kind']in ['intro','outro']]
ff=Path('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe');mp=o/'changneung_full_v8_jun.mp4'
r=subprocess.run([str(ff),'-v','error','-i',str(mp),'-map','0:v:0','-map','0:a:0','-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'],capture_output=True)
(q/'decode_stderr.txt').write_bytes(r.stderr)
# Decode final AAC to PCM independently for signal and clipping measurement.
r2=subprocess.run([str(ff),'-v','error','-y','-i',str(mp),'-vn','-ac','1','-ar','22050','-c:a','pcm_s16le','-f','wav',str(q/'final_audio.wav')],capture_output=True);w=wave.open(str(q/'final_audio.wav'));a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');active=np.flatnonzero(np.abs(a.astype(np.int32))>33)
# Entire MP4 includes brand music, so final nonzero measures mix, not last narration.
res=dict(final_sha256=sha(mp),bytes=mp.stat().st_size,errors=errors,semantic_units=len(units),provider_source_scenes=len(align),display_only_differences=display,caption_count=len(cs),minimum_caption_s=min((c['end_frame']-c['start_frame'])/30 for c in cs),subsecond_cues=sum(c['end_frame']-c['start_frame']<30 for c in cs),numeric_split_suspects=sus,max_unit_rounding_s=max(map(abs,checks)),chapters=[{'unit_id':x['unit_id'],'frames':x['duration_frames']} for x in cards],brands=[{'kind':x['kind'],'frames':x['duration_frames']} for x in brands],replacement_ids=sorted(set(x['props']['replacementId'] for x in intervals if x['props'].get('replacementId'))),note_intervals=sum(x['props'].get('mode')=='note' for x in intervals),independent_full_av_decode={'exit_code':r.returncode,'stderr':r.stderr.decode()},final_aac_pcm={'decode_exit_code':r2.returncode,'samples':len(a),'peak':int(np.abs(a.astype(np.int32)).max())/32768,'clipped_samples':int((np.abs(a.astype(np.int32))>=32767).sum()),'nonzero_signal':bool(len(active))},coverage={'cuts':len(rd(o/'evidence_manifest.json')['cuts']),'motions':len(rd(o/'evidence_manifest.json')['motions']),'boundaries':len(rd(o/'evidence_manifest.json')['boundaries'])})
(q/'independent_audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res,ensure_ascii=False))

