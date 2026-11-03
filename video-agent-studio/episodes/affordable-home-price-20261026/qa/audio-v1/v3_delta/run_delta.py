"""Four actual v3 raw paragraphs only; preserve all v2 evidence."""
import sys,re,time
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;QA=OUT.parent
sys.path.insert(0,str(QA))
sys.path.insert(0,str(OUT))
from prepare import EP,read,sha,pin,dump
from semantic_checks import compare
import run_asr as r

TARGETS=['S014','S019','S024','S030']
PROD=EP/'narration/production-injoon-v3'

def check_inputs():
    cfg=read(QA/'config.json');r.gate(cfg)
    packetp=PROD/'qa_packet.json';packet=read(packetp)
    authp=EP/'narration/main_tts_authorization_v3.json';auth=read(authp)
    preparedp=EP/'narration/prepare-v3/prepared.json';prep=read(preparedp)
    runp=PROD/'run_inputs.json';run=read(runp);g=run['gate']
    assert auth['approved'] and auth['episode_id']==EP.name
    assert auth['target_scenes']==prep['target_scenes']==TARGETS
    assert auth['script_sha256']==prep['script_sha256']==packet['script_sha256']==cfg['script_sha256']
    assert sha(preparedp)==auth['prepared_sha256']==g['v3_prepared_sha256']
    assert sha(authp)==g['v3_main_instruction_sha256']
    assert sha(EP/'narration/prepare-v3/delta_manifest.json')==auth['delta_manifest_sha256']==g['v3_delta_manifest_sha256']
    assert sha(EP/'narration/prepare-v3/spoken_diff.json')==auth['reviewed_spoken_diff_sha256']
    assert run['new_paragraphs']==4 and run['reused_paragraphs']==41
    assert not (PROD/'failure.json').exists()
    for key in ['final_timing','technical_validation','prior_qa_target_packet']:
        row=packet[key];assert sha(Path(row['path']))==row['sha256']
    timing=read(Path(packet['final_timing']['path']));original=read(EP/'narration/production-injoon-v2/final_timing.json')
    manifest=read(OUT/'v2_raw_sha_manifest.json');refs={p['scene_id']:p for c in read(QA/'expected.json')['chapters'] for p in c['paragraphs']}
    newrefs={p['scene_id']:p for c in prep['chapters'] for p in c['paragraphs']}
    reuse=[];new=[]
    for row in manifest['entries']:
        sid=row['scene_id'];assert newrefs[sid]['text']==refs[sid]['text']
        sem=compare(refs[sid]['text'],newrefs[sid]['spoken_text'])
        assert not sem['numeric_differences'] and not sem['coreterm_differences'],(sid,sem)
        hashes={}
        for key,name in [('audio','audio.wav'),('request','request.json'),('native_boundaries','native_boundaries.json')]:
            assert sha(Path(row[key]['path']))==row[key]['sha256'],('originalv2changed',sid,key)
            p=PROD/'paragraphs'/sid/name;hashes[key]=pin(p)
            if sid not in TARGETS:assert hashes[key]['sha256']==row[key]['sha256'],('reuse changed',sid,key)
        if sid in TARGETS:
            target=next(x for x in packet['targets'] if x['scene_id']==sid)
            for key in ['audio','request','native_boundaries']:assert hashes[key]==target[key]
            assert hashes['audio']['sha256']!=row['audio']['sha256']
            req=read(Path(hashes['request']['path']));assert req['spoken_text']==newrefs[sid]['spoken_text']==target['spoken_expected']
            assert req['text']==target['display_expected']==refs[sid]['text']
            assert req['voice']['rate']=='-15%' and req['voice']['name']=='ko-KR-InJoonNeural'
            new.append({'scene_id':sid,'old_audio':row['audio'],**hashes,'display_and_numeric_semantics_unchanged':True,'voice':req['voice']})
        else:reuse.append({'scene_id':sid,**hashes,'equal_original_v2':True})
    assert len(new)==4 and len(reuse)==41
    chapter_rows=[];changed_cfg={**cfg,'production_root':str(PROD)};native=[]
    for ch,old in zip(timing['chapters'],original['chapters']):
        n=ch['chapter'];p=r.resolve(ch['audio_file']);h=sha(p)
        assert h==ch['audio_sha256']
        assert [(c['id'],c['text'],c['display_lines']) for c in ch['cues']]==[(c['id'],c['text'],c['display_lines']) for c in old['cues']]
        same=h==old['audio_sha256'];assert same==(n in [1,2,3,8,9,10])
        chapter_rows.append({'chapter':n,'audio':pin(p),'previous_sha256':old['audio_sha256'],'unchanged':same,'total_seconds':ch['total_seconds']})
        if not same:
            pc=next(c for c in prep['chapters'] if c['chapter']==n)
            er={'paragraphs':[{**refs[p['scene_id']],'spoken_text':p['spoken_text']} for p in pc['paragraphs']]}
            _,_,nr=r.native_check(n,changed_cfg,er);native.append(nr)
    assert sum(len(c['cues']) for c in timing['chapters'])==150
    proof={'script_sha256':cfg['script_sha256'],'final_timing':packet['final_timing'],'qa_packet':pin(packetp),'authorization':pin(authp),'prepared':pin(preparedp),'run_inputs':pin(runp),'technical_validation':packet['technical_validation'],'approved_spoken_diff':pin(EP/'narration/prepare-v3/spoken_diff.json'),'new4':new,'reuse41':reuse,'chapters':chapter_rows,'changed_chapter_native_checks':native,'source_display_cues':150,'v2_original_preserved':True,'v2_ASR_reused_by_actual_audio_SHA':True,'total_seconds':sum(c['total_seconds'] for c in timing['chapters']),'actual_listening':False,'unchanged41_ASR_rerun':False}
    dump(OUT/'actual_v3_manifest.json',proof)
    return cfg,packet,proof,refs

def main():
    cfg,packet,proof,refs=check_inputs()
    model,fw,np,versions=r.runtime(cfg,'small');rows=[]
    for target in packet['targets']:
        sid=target['scene_id'];dest=OUT/'runs'/sid;dest.mkdir(parents=True,exist_ok=True)
        wp=Path(target['audio']['path']);raw,frames=r.pcm(wp)
        events=[w for w in read(Path(target['native_boundaries']['path'])) if w['type']=='WordBoundary']
        compact=lambda s:re.sub(r'[^0-9A-Za-z가-힣]','',s)
        assert compact(''.join(w['text'] for w in events))==compact(target['spoken_expected'])
        assert (events[-1]['offset']+events[-1]['duration'])/1e7<=frames/24000
        audio=fw.audio.decode_audio(str(wp),sampling_rate=16000);started=time.monotonic()
        segments,info=r.transcribe(model,audio);text=''.join(s['text'] for s in segments).strip()
        comp=compare(target['spoken_expected'],text)
        d={'scene_id':sid,'audio':target['audio'],'script_sha256':cfg['script_sha256'],'expected_display':target['display_expected'],'expected_spoken':target['spoken_expected'],'transcript':text,'comparison':comp,'segments':segments,'info':info,'ASR_input_seconds':len(audio)/16000,'actual_PCM_seconds':frames/24000,'model':cfg['models']['small'],'versions':versions,'inference':cfg['inference'],'elapsed_s':time.monotonic()-started,'DSP':r.dsp(wp,np),'native_word_count':len(events),'native_spoken_coverage':True,'prompt':None,'hotwords':None,'actual_listening':False}
        dump(dest/'small.json',d);assert sha(wp)==target['audio']['sha256']
        critical=bool(comp['numeric_differences'] or comp['coreterm_differences'])
        rows.append({'scene_id':sid,'small':pin(dest/'small.json'),'needs_targeted_medium':critical})
        print({'completed_small':sid,'transcript':text,'numeric_differences':comp['numeric_differences'],'coreterm_differences':comp['coreterm_differences']},flush=True)
    del model
    pending=[x for x in rows if x['needs_targeted_medium']]
    if pending:
        model,fw,np,versions=r.runtime(cfg,'medium')
        for row in pending:
            sid=row['scene_id'];target=next(t for t in packet['targets'] if t['scene_id']==sid);wp=Path(target['audio']['path'])
            audio=fw.audio.decode_audio(str(wp),sampling_rate=16000);segments,info=r.transcribe(model,audio)
            text=''.join(s['text'] for s in segments).strip();comp=compare(target['spoken_expected'],text)
            dest=OUT/'runs'/sid
            dump(dest/'medium.json',{'scene_id':sid,'audio':target['audio'],'script_sha256':cfg['script_sha256'],'expected_display':target['display_expected'],'expected_spoken':target['spoken_expected'],'transcript':text,'comparison':comp,'segments':segments,'info':info,'ASR_input_seconds':len(audio)/16000,'model':cfg['models']['medium'],'versions':versions,'inference':cfg['inference'],'prompt':None,'hotwords':None,'scope':'Only this discrepant new raw paragraph, preserving its complete native context and silence; not a full chapter pass','actual_listening':False})
            row['medium']=pin(dest/'medium.json');assert sha(wp)==target['audio']['sha256']
            print({'completed_medium':sid,'transcript':text,'numeric_differences':comp['numeric_differences'],'coreterm_differences':comp['coreterm_differences']},flush=True)
    dump(OUT/'ASR_index.json',{'script_sha256':cfg['script_sha256'],'final_timing':packet['final_timing'],'manifest':pin(OUT/'actual_v3_manifest.json'),'small_paragraphs':4,'targeted_medium_paragraphs':len(pending),'rows':rows,'actual_listening':False,'continuous_playback':False})
    check_inputs()
if __name__=='__main__':main()
