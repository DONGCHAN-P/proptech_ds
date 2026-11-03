"""Episode-local, offline ASR evidence. Does not synthesize, listen or approve media."""
import argparse, json, os, re, socket, sys, time, wave
from pathlib import Path
sys.dont_write_bytecode = True
QA = Path(__file__).resolve().parent
sys.path.insert(0, str(QA))
from prepare import EP, ROOT, read, sha, pin, dump
from checks import compare

def resolve(p):
    p = Path(p)
    if p.is_absolute(): return p.resolve()
    return ((ROOT if p.parts[0] == 'video-agent-studio' else EP) / p).resolve()

def within(p, root):
    assert p.resolve().is_relative_to(root.resolve()), ('outside authorized scope', str(p))
    return p

def gate(cfg):
    for v in cfg['inputs'].values(): assert sha(Path(v['path'])) == v['sha256'], v
    assert sha(QA/'expected.json') == cfg['expected_sha256']
    authp, lockp = Path(cfg['main_authorization']), Path(cfg['locked_script'])
    auth, lock = read(authp), read(lockp)
    prod = within(Path(cfg['production_root']), EP/'narration/production-injoon-v2')
    runp = prod/'run_inputs.json'; run = read(runp); g = run['gate']
    assert auth['approved'] and lock['approved']
    assert auth['episode_id'] == cfg['episode_id']
    assert auth['script_sha256'] == lock['script_sha256'] == g['script_sha256'] == cfg['script_sha256']
    assert sha(resolve(lock['script_path'])) == cfg['script_sha256']
    assert auth['prepared_sha256'] == run['prepared_sha256'] == cfg['inputs']['narration/prepare-v2-r2/prepared.json']['sha256']
    assert sha(authp) == g['main_instruction_sha256'] and sha(lockp) == g['lock_sha256']
    assert run['cross_episode_audio_reuse'] == 0 and run['new_paragraphs'] == 45
    receipts = []
    for who in ['codex','claude']:
        row = g['receipts'][who]; p = within(resolve(row['path']), EP)
        assert sha(p) == row['sha256']
        d = read(p); assert d.get('approved') is True and not d.get('required_issues',[]) and not d.get('critical_issues',[])
        assert d.get('script_sha256',d.get('checked_sha256')) == cfg['script_sha256']
        receipts.append(pin(p))
    assert receipts[0]['path'] != receipts[1]['path']
    assert not (prod/'failure.json').exists(), 'narrator failure requires main review'
    return {'authorization':pin(authp),'locked_script':pin(lockp),'run_inputs':pin(runp),'content_receipts':receipts}

def pcm(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate()) == (1,2,24000)
        count = w.getnframes(); data = w.readframes(count)
    assert len(data) == count*2
    return data, count

def native_check(n, cfg, expected):
    prod = Path(cfg['production_root']); jp = prod/f'chapter_{n:02}.json'; jsha = sha(jp); ch = read(jp)
    wp = within(resolve(ch['audio_file']), prod); wsha = sha(wp)
    assert ch['chapter'] == n and ch['audio_sha256'] == wsha
    data,count = pcm(wp)
    assert count == ch['pcm_frames'] and count % 800 == 0
    assert abs(count/24000-ch['total_seconds']) < 1e-7
    assert len(ch['paragraphs']) == len(expected['paragraphs'])
    rows=[]; words_total=0; previous_end=0
    compact=lambda s: re.sub(r'[^0-9A-Za-z가-힣]','',s)
    for actual, ref in zip(ch['paragraphs'],expected['paragraphs']):
        assert actual['paragraph'] == ref['paragraph']
        rawp = within(resolve(actual['wave_file']),prod/'paragraphs'/ref['scene_id'])
        raw, frames = pcm(rawp); start=round(actual['offset_s']*24000)
        assert data[start*2:(start+frames)*2] == raw, ref['scene_id']
        assert abs(frames/24000-actual['measured_seconds']) < 1e-7
        nbp=rawp.parent/'native_boundaries.json'; events=read(nbp)
        words=[v for v in events if v['type']=='WordBoundary']
        assert compact(''.join(w['text'] for w in words)) == compact(ref['spoken_text']), ref['scene_id']
        cues=[c for c in ch['cues'] if c['scene_id']==ref['scene_id']]
        assert compact(''.join(c['text'] for c in cues)) == compact(ref['text'])
        assert compact(''.join(c['spoken_text'] for c in cues)) == compact(ref['spoken_text'])
        indexes=[]
        for c in cues:
            assert c['text'] == ref['text'][c['source_start']:c['source_end']]
            assert c['spoken_text'] == ref['spoken_text'][c['spoken_start']:c['spoken_end']]
            assert previous_end <= c['start_s'] < c['end_s'] <= ch['total_seconds']; previous_end=c['end_s']
            first,last=c['first_word_index'],c['last_word_index']; indexes.extend(range(first,last+1))
            assert abs(c['native_start_s']-(actual['offset_s']+words[first]['offset']/1e7)) < 2e-6
            assert abs(c['native_end_s']-(actual['offset_s']+(words[last]['offset']+words[last]['duration'])/1e7)) < 2e-6
        assert indexes == list(range(len(words)))
        words_total += len(words)
        rows.append({**ref,'start_s':actual['offset_s'],'end_s':actual['offset_s']+frames/24000,'raw_audio':pin(rawp),'native_events':pin(nbp),'word_count':len(words),'cue_count':len(cues),'PCM_byte_identical_in_chapter':True})
    assert ch['tail_from_last_spoken_s'] >= (3 if n==10 else 1.19)
    assert sha(jp)==jsha and sha(wp)==wsha, 'file changed during inspection'
    return ch,wp,{'chapter_json':pin(jp),'audio':pin(wp),'total_seconds':count/24000,'paragraphs':rows,'native_word_count':words_total,'cue_count':len(ch['cues']),'PCM_frames':count,'native_boundary_and_source_checks_passed':True,'tail_from_last_spoken_s':ch['tail_from_last_spoken_s']}

def runtime(cfg,name):
    os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',HF_HOME=str(QA/'cache/hf'),XDG_CACHE_HOME=str(QA/'cache'),TOKENIZERS_PARALLELISM='false')
    def denied(*a,**k): raise RuntimeError('Network forbidden in local ASR QA')
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,cfg['shared_deps_readonly'])
    import faster_whisper, ctranslate2, numpy, av, onnxruntime
    onnxruntime.disable_telemetry_events()
    assert faster_whisper.__version__=='1.2.1'
    m=cfg['models'][name]
    for p in m['files']+[m['license_file']]: assert sha(Path(p['path']))==p['sha256']
    model=faster_whisper.WhisperModel(m['path'],device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
    assert model.model.compute_type in ['int8','int8_float32']
    versions={'faster-whisper':faster_whisper.__version__,'ctranslate2':ctranslate2.__version__,'numpy':numpy.__version__,'av':av.__version__,'onnxruntime':onnxruntime.__version__,'actual_compute_type':model.model.compute_type}
    return model,faster_whisper,numpy,versions

def transcribe(model, audio):
    segments,info=model.transcribe(audio,language='ko',task='transcribe',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
    rows=[]
    for s in segments:
        rows.append({'id':s.id,'start_s':s.start,'end_s':s.end,'text':s.text,'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob,'words':[{'start_s':w.start,'end_s':w.end,'word':w.word,'probability':w.probability} for w in (s.words or [])]})
    return rows,{'language':info.language,'duration':info.duration,'duration_after_vad':info.duration_after_vad}

def dsp(wp,np):
    raw,count=pcm(wp); a=np.frombuffer(raw,dtype='<i2').astype(np.int32); peak=int(np.max(np.abs(a)))
    rms=max(float(np.sqrt(np.mean(a.astype(float)**2))),1e-10)
    return {'pcm_frames':count,'sample_peak':peak,'clipped_samples':int(np.count_nonzero(np.abs(a)>=32767)),'rms_dbfs':float(20*np.log10(rms/32768)),'digital_silence_samples':int(np.count_nonzero(a==0)),'scope':'PCM technical measurement; no listening, no final music mix approval'}

def save_summary():
    reports=[]
    for p in sorted((QA/'runs').glob('ch*-small-*/report.json')):
        d=read(p); reports.append({'chapter':d['chapter'],'report':pin(p),'audio':d['audio'],'duration_s':d['duration_s'],'target_count':len(d['medium_candidates'])})
    dump(QA/'progress.json',{'status':'small_reports_completed','chapters_completed':len(reports),'duration_s':sum(r['duration_s'] for r in reports),'reports':reports,'actual_listening':False,'continuous_playback':False,'audio_approval':False})

def run_chapters(args,cfg):
    evidence=gate(cfg); expected=read(QA/'expected.json'); model=fw=np=versions=None
    for n in args.chapters:
        ref=next(c for c in expected['chapters'] if c['chapter']==n)
        ch,wp,native=native_check(n,cfg,ref)
        dest=QA/'runs'/f'ch{n:02}-small-{native["audio"]["sha256"][:12]}'
        if (dest/'report.json').exists():
            assert read(dest/'report.json')['audio']==native['audio']; print(f'REUSE own actual chapter {n:02} small report',flush=True);continue
        dest.mkdir(parents=True,exist_ok=True)
        dump(dest/'native_checks.json',native)
        if model is None:model,fw,np,versions=runtime(cfg,'small')
        audio=fw.audio.decode_audio(str(wp),sampling_rate=16000)
        assert abs(len(audio)/16000-ch['total_seconds'])<1/16000
        started=time.monotonic(); rows,info=transcribe(model,audio)
        dump(dest/'transcript.json',{'segments':rows,'info':info,'sample_rate':16000,'decoded_samples':len(audio),'whole_chapter_decoded_without_VAD':True})
        words=[w for s in rows for w in s['words']]; comparisons=[]; candidates=[]
        for p in native['paragraphs']:
            selected=[w for w in words if p['start_s'] <= (w['start_s']+w['end_s'])/2 < p['end_s']]
            text=''.join(w['word'] for w in selected).strip(); comp=compare(p['spoken_text'],text)
            row={'scene_id':p['scene_id'],'paragraph':p['paragraph'],'start_s':p['start_s'],'end_s':p['end_s'],'expected_display':p['text'],'expected_spoken':p['spoken_text'],'transcript':text,**comp}
            row['target_medium']=bool(comp['numeric_differences'] or comp['coreterm_differences'] or (comp['text_similarity']<0.78 and (comp['reference_numbers'] or p['protected_occurrences'])))
            row['classification']='unconfirmed_ASR_discrepancy' if row['target_medium'] else 'no_automatic_numeric_coreterm_discrepancy'
            comparisons.append(row)
            if row['target_medium']:candidates.append(p['scene_id'])
        assert sha(wp)==native['audio']['sha256'] and sha(Path(native['chapter_json']['path']))==native['chapter_json']['sha256']
        gate(cfg)
        report={'chapter':n,'script_sha256':cfg['script_sha256'],'audio':native['audio'],'chapter_json':native['chapter_json'],'duration_s':ch['total_seconds'],'ASR_input_seconds':len(audio)/16000,'model':cfg['models']['small'],'versions':versions,'inference':cfg['inference'],'elapsed_s':time.monotonic()-started,'gate':evidence,'native_checks':pin(dest/'native_checks.json'),'transcript':pin(dest/'transcript.json'),'DSP':dsp(wp,np),'comparisons':comparisons,'medium_candidates':candidates,'actual_listening':False,'continuous_playback':False,'quality_naturalness_approved':False,'numeric_errors_confirmed_by_listening':0,'reference_used_as_prompt_or_hotwords':False,'notes':['ASR spelling, numeral normalization and word timestamp assignment may create false discrepancies.','Full chapter ASR, per-paragraph reference comparison. Silent tails are not speech coverage.']}
        dump(dest/'report.json',report);save_summary()
        print(json.dumps({'completed_chapter':n,'duration_s':ch['total_seconds'],'medium_candidates':candidates,'report':str(dest/'report.json')},ensure_ascii=False),flush=True)

def run_medium(args,cfg):
    gate(cfg); source=within(Path(args.small_report).resolve(),QA/'runs'); sr=read(source)
    assert sr['script_sha256']==cfg['script_sha256']; wp=Path(sr['audio']['path']); assert sha(wp)==sr['audio']['sha256']
    targets=args.scenes or sr['medium_candidates']; assert targets and set(targets)<=set(sr['medium_candidates'])
    model,fw,np,versions=runtime(cfg,'medium'); audio=fw.audio.decode_audio(str(wp),sampling_rate=16000)
    for sid in targets:
        p=next(p for p in sr['comparisons'] if p['scene_id']==sid)
        dest=QA/'runs'/f'ch{sr["chapter"]:02}-medium-{sr["audio"]["sha256"][:12]}'/sid
        if (dest/'comparison.json').exists():print(f'REUSE own actual medium {sid}',flush=True);continue
        lo=max(0,p['start_s']-.4); hi=min(len(audio)/16000,p['end_s']+.4); clip=audio[round(lo*16000):round(hi*16000)]
        assert len(clip)>1600 and np.max(np.abs(clip))>.01, 'near-silent clip; refuse decoder hallucination risk'
        rows,info=transcribe(model,clip)
        text=''.join(w['word'] for s in rows for w in s['words'] if p['start_s'] <= lo+(w['start_s']+w['end_s'])/2 < p['end_s']).strip()
        comp=compare(p['expected_spoken'],text); dest.mkdir(parents=True,exist_ok=True)
        dump(dest/'transcript.json',{'segments':rows,'info':info,'clip_start_s':lo,'clip_end_s':hi,'context_s':.4,'source_audio':sr['audio'],'reference_as_prompt':False,'hotwords':None})
        unresolved=bool(comp['numeric_differences'] or comp['coreterm_differences'] or comp['text_similarity']<.78)
        dump(dest/'comparison.json',{'scene_id':sid,'chapter':sr['chapter'],'script_sha256':cfg['script_sha256'],'audio':sr['audio'],'small_report':pin(source),'small_transcript':p['transcript'],'medium_transcript':text,'expected_display':p['expected_display'],'expected_spoken':p['expected_spoken'],'small_comparison':{k:p[k] for k in ['reference_numbers','recognized_numbers','numeric_differences','coreterm_differences','text_similarity']},'medium_comparison':comp,'model':cfg['models']['medium'],'versions':versions,'transcript':pin(dest/'transcript.json'),'unresolved_requires_manual_evidence_review':unresolved,'classification':'unresolved_ASR_evidence_not_confirmed_listening_error' if unresolved else 'medium_agrees_with_reference_small_discrepancy_not_confirmed','actual_listening':False,'continuous_playback':False,'audio_naturalness_approved':False})
        assert sha(wp)==sr['audio']['sha256']; print(json.dumps({'medium_completed':sid,'unresolved':unresolved,'report':str(dest/'comparison.json')},ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('small');p.add_argument('--chapters',type=int,nargs='+',required=True)
    p=sub.add_parser('medium');p.add_argument('--small-report',required=True);p.add_argument('--scenes',nargs='*')
    p=sub.add_parser('check-ready');p.add_argument('--chapters',type=int,nargs='+',required=True)
    args=ap.parse_args();cfg=read(QA/'config.json');gate(cfg)
    if args.command=='small':run_chapters(args,cfg)
    elif args.command=='medium':run_medium(args,cfg)
    else:
        e=read(QA/'expected.json');rows=[]
        for n in args.chapters:
            _,_,r=native_check(n,cfg,next(c for c in e['chapters'] if c['chapter']==n));rows.append(r)
        dump(QA/'readiness.json',{'script_sha256':cfg['script_sha256'],'chapters':rows,'actual_listening':False,'ASR_executed_here':False})
        print(json.dumps({'ready_chapters':len(rows),'native_words':sum(r['native_word_count'] for r in rows),'cues':sum(r['cue_count'] for r in rows),'seconds':sum(r['total_seconds'] for r in rows)},ensure_ascii=False))
if __name__=='__main__':main()
