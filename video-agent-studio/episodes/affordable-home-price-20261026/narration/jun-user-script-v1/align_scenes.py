"""Map actual provider characters to original paragraphs, cues and literal beats.

No proportional time estimates. Raw provider timestamps are preserved separately;
only decoder boundary differences <=100ms may be clipped to the measured PCM.
"""
from pathlib import Path
import json, hashlib, re, wave, math

OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def ref(p):return {'path':rel(p),'sha256':sha(p)}
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def pcm_duration(p):
    with wave.open(str(p),'rb') as f:
        assert f.getframerate()==44100 and f.getnchannels()==1 and f.getsampwidth()==2
        return f.getnframes()/f.getframerate()

manifest=load(OWN/'narration_manifest.json')
caps=load(OWN/'caption_plan.json')
plan=load(EP/'director/user-recording-v1/scene_plan.json')
ledger=load(OWN/'generation_ledger.json')
assert len(ledger['requests'])==7 and all(r['status']=='complete' for r in ledger['requests'])
assert ledger['actual_credits']<=7000 and ledger['automatic_retries']==0
assert len(manifest['paragraphs'])==48 and len(caps['cues'])==156 and len(plan['scenes'])==31
by_id={p['paragraph_id']:p for p in manifest['paragraphs']}
units=[]; scenes=[];clamps=[];native_checks=[]
for ch in manifest['chapters']:
    cid=ch['chapter_id']; base=OWN/'paragraphs'/(cid+'P01')
    receipt=next(r for r in ledger['requests'] if r['paragraph_id']==cid+'P01')
    for file,digest in receipt['artifact_sha256'].items():assert sha(OWN/file)==digest
    a=load(base/'alignment.json'); wav=base/'audio.wav'; duration=pcm_duration(wav)
    text=''.join(a['characters'])
    assert text==ch['text']
    starts=a['character_start_times_seconds'];ends=a['character_end_times_seconds']
    assert len(starts)==len(ends)==len(text)
    assert all(math.isfinite(s) and math.isfinite(e) and 0<=s<=e<=duration+.101 for s,e in zip(starts,ends))
    clamped=sum(e>duration or s>duration for s,e in zip(starts,ends))
    if clamped:clamps.append({'chapter':cid,'count':clamped,'max_overrun_s':max(ends)-duration,'basis':'Provider vs decoded PCM end; raw timestamps unchanged.'})
    starts=[min(s,duration) for s in starts];ends=[min(e,duration) for e in ends]
    units.append({'audio_unit_id':cid,**ref(wav),'duration_s':duration,'provider_alignment':ref(base/'alignment.json'),'last_spoken_end_s':max(ends[i] for i,c in enumerate(text) if c.isalnum())})
    offsets={};cursor=0
    for pid in ch['paragraph_ids']:
        p=by_id[pid];assert text[cursor:cursor+len(p['spoken_text'])]==p['spoken_text']
        offsets[pid]=cursor;cursor+=len(p['spoken_text'])+2
    assert cursor-2==len(text)
    chapter_scenes=[s for s in plan['scenes'] if s['chapter']==ch['chapter']]
    boundaries=[0.0]
    for s in chapter_scenes[1:]:
        pid=s['paragraph_ids'][0];offset=offsets[pid]
        first=next(i for i,c in enumerate(by_id[pid]['spoken_text']) if not c.isspace())
        boundaries.append(starts[offset+first])
    boundaries.append(duration)
    for idx,s in enumerate(chapter_scenes):
        scene_start,scene_end=boundaries[idx:idx+2]
        assert 0<=scene_start<scene_end<=duration
        scene_d=scene_end-scene_start
        local=lambda v:max(0.0,min(v-scene_start,scene_d))
        maps={};characters=[];original='';orig_to_spoken_start=[];orig_to_spoken_end=[]
        for j,pid in enumerate(s['paragraph_ids']):
            p=by_id[pid];offset=offsets[pid];ss=[];ee=[];o=0;sp=0
            for part in p['display_mapping']:
                original_part,spoken_part=part['original'],part['spoken']
                assert p['text'][o:o+len(original_part)]==original_part
                assert p['spoken_text'][sp:sp+len(spoken_part)]==spoken_part
                for k in range(len(original_part)):
                    ss.append(offset+sp+k if part['kind']=='literal' else offset+sp)
                    ee.append(offset+sp+k if part['kind']=='literal' else offset+sp+len(spoken_part)-1)
                o+=len(original_part);sp+=len(spoken_part)
            assert o==len(p['text']) and sp==len(p['spoken_text'])
            maps[pid]=(ss,ee)
            if j:
                original+='\n\n';orig_to_spoken_start.extend([ss[0]]*2);orig_to_spoken_end.extend([ss[0]]*2)
            original+=p['text'];orig_to_spoken_start.extend(ss);orig_to_spoken_end.extend(ee)
            n=len(p['spoken_text'])
            characters.append({'paragraph_id':pid,'spoken_sha256':p['spoken_sha256'],'start_s':[local(t) for t in starts[offset:offset+n]],'end_s':[local(t) for t in ends[offset:offset+n]]})
        compact_positions=[i for i,c in enumerate(original) if not c.isspace()]
        compact=''.join(original[i] for i in compact_positions)
        beats=[];search_from=0
        for bi,b in enumerate(s['beats']):
            anchor=b['anchor'];target=re.sub(r'\s+','',anchor)
            found=compact.find(target,search_from)
            assert found>=0,(s['scene_id'],anchor,'Anchor order/match needs explicit review')
            left=compact_positions[found];right=compact_positions[found+len(target)-1]
            ai=orig_to_spoken_start[left];zi=orig_to_spoken_end[right]
            beats.append({'beat_id':s['scene_id']+f'.b{bi+1:02}','anchor_original':anchor,'start_s':local(starts[ai]),'end_s':local(ends[zi]),'provider_char_start':ai,'provider_char_end':zi+1,'timing_basis':'provider_character_alignment_verified'})
            search_from=found
        captions=[]
        for c in caps['cues']:
            if c['scene_id']!=s['scene_id']:continue
            ss,ee=maps[c['paragraph_id']];ai=ss[c['source_start']];zi=ee[c['source_end']-1]
            st,en=local(starts[ai]),local(ends[zi])
            assert st<en,(c['cue_id'],st,en)
            captions.append({'cue_id':c['cue_id'],'text':c['text'],'display_lines':c['display_lines'],'start_s':st,'end_s':en,'paragraph_id':c['paragraph_id'],'timing_basis':'provider_character_alignment_verified'})
        scenes.append({'scene_id':s['scene_id'],'chapter':s['chapter'],'paragraph_ids':s['paragraph_ids'],'audio_unit_id':cid,'audio_start_s':scene_start,'audio_end_s':scene_end,'duration_s':scene_d,'last_spoken_end_s':max(local(ends[orig_to_spoken_end[i]]) for i,c in enumerate(original) if c.isalnum()),'characters':characters,'beats':beats,'captions':captions})
    native_checks.append({'chapter':cid,'characters':len(text),'duration_s':duration,'audio_sha256':sha(wav),'alignment_sha256':sha(base/'alignment.json')})
assert [s['scene_id'] for s in scenes]==[s['scene_id'] for s in plan['scenes']]
assert sum(len(s['paragraph_ids']) for s in scenes)==48
assert sum(len(s['captions']) for s in scenes)==156
assert sum(len(s['beats']) for s in scenes)==sum(len(s['beats']) for s in plan['scenes'])
result={'schema_version':'jun-scene-alignment-v1','timing_locked':True,'timing_basis':'provider_character_alignment_verified','source_doc_sha256':manifest['source_doc_sha256'],'manifest':ref(OWN/'narration_manifest.json'),'caption_plan':ref(OWN/'caption_plan.json'),'scene_plan':ref(EP/'director/user-recording-v1/scene_plan.json'),'voice':{'name':'Jun','revision':'jun-user-script-v1','speed':.97},'audio_units':units,'scenes':scenes,'actual_listening':False,'native_checks':native_checks,'decoder_boundary_clamps':clamps,'total_audio_duration_s':sum(u['duration_s'] for u in units),'actual_credits':ledger['actual_credits']}
save(OWN/'scene_alignment.json',result)
save(OWN/'alignment_receipt.json',{'status':'actual_character_alignment_mapped','scene_count':31,'paragraph_count':48,'caption_count':156,'beat_count':sum(len(s['beats']) for s in scenes),'total_audio_duration_s':result['total_audio_duration_s'],'actual_credits':ledger['actual_credits'],'source_doc_sha256':manifest['source_doc_sha256'],'alignment_sha256':sha(OWN/'scene_alignment.json'),'decoder_boundary_clamps':clamps,'actual_listening':False})
print(json.dumps({'status':'actual_character_alignment_mapped','seconds':result['total_audio_duration_s'],'scenes':31,'cues':156,'beats':sum(len(s['beats']) for s in scenes),'credits':ledger['actual_credits']},ensure_ascii=False))
