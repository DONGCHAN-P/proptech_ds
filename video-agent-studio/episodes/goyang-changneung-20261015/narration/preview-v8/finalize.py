import pathlib,json,wave,hashlib,array,math
root=pathlib.Path(__file__).resolve().parents[2]; out=root/'narration/preview-v8'; audio=root/'outputs/production-v8-preview/audio'
units=json.loads((out/'units.json').read_text(encoding='utf-8')); timeline=[]; scene_times=[]; cursor=0; all_pcm=[]; params=None
for u in units:
    p=audio/u['file']
    with wave.open(str(p),'rb') as w:
        params=w.getparams(); pcm=w.readframes(w.getnframes()); duration=w.getnframes()/w.getframerate()
    u.update(start_s=round(cursor,6),end_s=round(cursor+duration,6),duration_s=round(duration,6),audio_path=str(p),timing_basis='measured PCM frame count of individually synthesized semantic unit',confidence='high for file boundaries; internal word boundaries unmeasured',audio_revision='audio-v8-preview-heami-rate0')
    u['unit_id']=p.stem
    timeline.append(u);all_pcm.append(pcm);cursor+=duration
    if not scene_times or scene_times[-1]['scene_id']!=u['scene_id']:scene_times.append(dict(scene_id=u['scene_id'],start_s=u['start_s'],end_s=u['end_s'],timing_basis=u['timing_basis'],confidence='high',audio_revision=u['audio_revision']))
    else:scene_times[-1]['end_s']=u['end_s']
combined=audio/'narration_v8_preview.wav'
with wave.open(str(combined),'wb') as w:w.setparams(params);w.writeframes(b''.join(all_pcm))
for s in scene_times:
    selected=[u for u in timeline if u['scene_id']==s['scene_id']]
    p=audio/(s['scene_id']+'.wav')
    with wave.open(str(p),'wb') as w:
        w.setparams(params)
        for u in selected:
            with wave.open(u['audio_path'],'rb') as src:w.writeframes(src.readframes(src.getnframes()))
    s['audio_path']=str(p);s['duration_s']=round(s['end_s']-s['start_s'],6)
(out/'segments.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'timing_proposals.json').write_text(json.dumps(scene_times,ensure_ascii=False,indent=2),encoding='utf-8')
def stamp(t):
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
(out/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(u["start_s"])} --> {stamp(u["end_s"])}\n{u["text"]}' for i,u in enumerate(timeline))+'\n',encoding='utf-8')
pcm=b''.join(all_pcm); samples=array.array('h',pcm); peak=max(abs(x) for x in samples);rms=math.sqrt(sum(x*x for x in samples)/len(samples))
handoff=dict(status='generated_measured_not_listened',script_revision='script-v8',audio_revision='audio-v8-preview-heami-rate0',voice='Microsoft Heami Desktop - Korean',engine='Windows SAPI COM',rate=0,cost=0,network_used=False,duration_s=cursor,ten_minute_requirement_met=cursor>=600,scene_count=len(scene_times),semantic_unit_count=len(units),audio_path=str(combined),captions=str(out/'captions.srt'),segments=str(out/'segments.json'),timing_proposals=str(out/'timing_proposals.json'),input_hashes=json.loads((out/'input_hashes.json').read_text()),audio_sha256=hashlib.sha256(combined.read_bytes()).hexdigest(),technical_validation=dict(sample_rate=params.framerate,channels=params.nchannels,sample_width=params.sampwidth,peak=peak,rms=rms),verification=['117 WAV units parsed and PCM frame durations measured','Combined WAV and 10 chapter WAVs created','No inserted silence; each unit uses native TTS sentence ending'],unverified=['Actual listening and pronunciation QA not performed','Subtitle internal word boundaries not measured; each caption exactly matches synthesized semantic file','Voice is free review placeholder; final Jun replacement requires new measured timing'],changed_scene_ids=[s['scene_id'] for s in scene_times],next_owner='video_editor',notes=['Restricted process SAPI failed 0x80045040; same generation succeeded under approved local execution escalation','Timeline starts at 0; editor adds intro/outro offsets','No source Jun audio reused'])
handoff['verification']=[f'{len(units)} WAV units parsed and PCM frame durations measured',f'Combined WAV and {len(scene_times)} chapter WAVs created','No inserted silence; each unit uses native TTS sentence ending','Every subtitle scene matches writer narration packet after whitespace normalization','Approved script SHA256 verified before generation','Rate0 first-unit sample PCM validation passed before full generation']
last_nonzero=next((i for i in range(len(samples)-1,-1,-1) if samples[i]!=0),-1)
last_above_minus60db=next((i for i in range(len(samples)-1,-1,-1) if abs(samples[i])>=33),-1)
handoff['pcm_tail_measurement']={'last_nonzero_end_s':(last_nonzero+1)/params.framerate,'last_above_minus60db_end_s':(last_above_minus60db+1)/params.framerate,'trailing_exact_zero_s':(len(samples)-last_nonzero-1)/params.framerate,'method':'Scan decoded signed16 PCM samples; amplitude >=33 approximates -60dBFS; this is signal evidence, not human-listened speech boundary','editor_outro_instruction':'Add at least 3 seconds after measured audio end; chapter and brand inserts belong to editor'}
handoff['authorization']={'script_decision_id':'7d9fc3575dff','mode':'user-approved free review TTS full video','paid_api_used':False}
handoff['unverified'].append('Forced alignment not performed')
(out/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'duration_s':cursor,'ten_minutes':cursor>=600,'scenes':scene_times,'peak':peak,'rms':rms},ensure_ascii=False,indent=2))
