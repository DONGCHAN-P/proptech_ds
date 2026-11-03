"""Four bounded no-ASCII-digit ASR runs on unchanged v3 S019/S024 WAV.

The generic token ban is derived solely from each tokenizer vocabulary.
No expected numeral, source text, prompt, hotword or allowed-word list is fed
to the decoder. Constrained decoding is diagnostic, not actual listening.
"""
import sys,re,json,hashlib,time,shutil,inspect
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;DELTA=OUT.parent;QA=DELTA.parent
sys.path.insert(0,str(QA));sys.path.insert(0,str(DELTA))
from prepare import EP,read,sha,pin,dump
import run_asr as r
from semantic_checks import compare

TARGETS=('S019','S024')

def list_sha(ids):
    return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode('utf-8')).hexdigest()

def snapshot():
    folder=OUT/'standard_snapshot';folder.mkdir(parents=True,exist_ok=True);rows=[]
    files=[DELTA/n for n in ['review.json','handoff.json','verification.json','ASR_index.json','actual_v3_manifest.json','remaining_target_packet.json']]
    for sid in TARGETS:
        files.extend(DELTA/'runs'/sid/n for n in ['small.json','medium.json'])
    for p in files:
        dest=folder/p.relative_to(DELTA);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert sha(dest)==sha(p),'snapshot already exists with different evidence'
        else:shutil.copyfile(p,dest)
        assert sha(dest)==sha(p);rows.append({'original':pin(p),'snapshot':pin(dest)})
    dump(folder/'manifest.json',{'scope':'Exact original standard v3 evidence captured before phonetic decoder runs','entries':rows,'actual_listening':False})
    return pin(folder/'manifest.json')

def ban_all_ascii_digit_tokens(model):
    # Model tokenizer only: source/expected text cannot influence the ban.
    tokenizer=model.hf_tokenizer;rows=[]
    for i in range(tokenizer.get_vocab_size(with_added_tokens=True)):
        decoded=tokenizer.decode([i],skip_special_tokens=False)
        if re.search(r'[0-9]',decoded):
            rows.append({'id':i,'decoded':decoded,'vocabulary_token':tokenizer.id_to_token(i)})
    ids=[x['id'] for x in rows]
    assert ids and len(ids)==len(set(ids))
    from faster_whisper.tokenizer import Tokenizer
    from faster_whisper.transcribe import get_suppressed_tokens
    tok=Tokenizer(tokenizer,True,task='transcribe',language='ko')
    requested=[-1]+ids
    effective=list(get_suppressed_tokens(tok,requested.copy()))
    assert set(ids)<=set(effective)
    # Timestamp special token spellings contain digits, too. They are banned
    # by the same rule; no-timestamps mode avoids requiring their generation.
    timestamps=[x['id'] for x in rows if x['id']>=tok.timestamp_begin]
    assert all(not re.search(r'[0-9]',tokenizer.decode([i],skip_special_tokens=False)) or i in ids for i in range(tokenizer.get_vocab_size(with_added_tokens=True)))
    return {'rule':'Suppress every token whose individually decoded string (skip_special_tokens=False) contains any ASCII0-9; uniform tokenizer-only rule, no expected values','vocabulary_size':tokenizer.get_vocab_size(with_added_tokens=True),'digit_token_count':len(ids),'digit_token_ids':ids,'digit_token_ids_canonical_json_sha256':list_sha(ids),'digit_token_rows':rows,'timestamp_tokens_in_digit_ban':len(timestamps),'requested_suppress_tokens':requested,'requested_list_sha256':list_sha(requested),'effective_suppress_tokens':effective,'effective_list_sha256':list_sha(effective),'retain_default_non_speech_suppression':True,'special_suppression_method':'[-1]+digit_token_ids passed to API; get_suppressed_tokens adds default non-speech and required task specials','without_timestamps':True,'word_timestamps':False}

def main():
    cfg=read(QA/'config.json');r.gate(cfg)
    snap=snapshot();packet=read(EP/'narration/production-injoon-v3/qa_packet.json')
    targets=[next(t for t in packet['targets'] if t['scene_id']==sid) for sid in TARGETS]
    for t in targets:assert sha(Path(t['audio']['path']))==t['audio']['sha256']
    results=[]
    for name in ['small','medium']:
        model,fw,np,versions=r.runtime(cfg,name)
        signature=inspect.signature(model.transcribe);assert 'suppress_tokens' in signature.parameters
        constraint=ban_all_ascii_digit_tokens(model)
        modeldir=OUT/name;modeldir.mkdir(parents=True,exist_ok=True)
        dump(modeldir/'token_constraint.json',constraint)
        import faster_whisper.transcribe as api
        api_file=Path(inspect.getsourcefile(type(model)))
        for t in targets:
            wp=Path(t['audio']['path']);before=sha(wp);assert before==t['audio']['sha256']
            audio=fw.audio.decode_audio(str(wp),sampling_rate=16000)
            assert len(audio)>1600 and np.max(np.abs(audio))>.01
            started=time.monotonic()
            segments,info=model.transcribe(audio,language='ko',task='transcribe',beam_size=5,temperature=0,word_timestamps=False,without_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,prefix=None,hotwords=None,suppress_tokens=constraint['requested_suppress_tokens'].copy())
            rows=[]
            for s in segments:
                rows.append({'id':s.id,'start_s':s.start,'end_s':s.end,'text':s.text,'tokens':s.tokens,'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob})
            text=''.join(s['text'] for s in rows).strip()
            assert not re.search(r'[0-9]',text),('ASCII digit escaped constraint',text)
            actual=list(info.transcription_options.suppress_tokens)
            assert actual==constraint['effective_suppress_tokens']
            assert sha(wp)==before
            comparison=compare(t['spoken_expected'],text) # Expected read only after decoder output.
            dest=modeldir/f'{t["scene_id"]}.json'
            result={'mode':'generic_no_ASCII_digit_tokens_diagnostic','scene_id':t['scene_id'],'model_name':name,'at_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':cfg['script_sha256'],'audio':t['audio'],'unchanged_audio_SHA_before_after':before,'ASR_input_seconds':len(audio)/16000,'same_full_raw_paragraph_no_cutting':True,'raw_Korean_transcript':text,'segments':rows,'reported_segment_times_are_not_native_alignment':True,'comparison_after_decoding_only':comparison,'model':cfg['models'][name],'versions':versions,'API_source':pin(api_file),'API_signature':str(signature),'token_constraint':pin(modeldir/'token_constraint.json'),'effective_suppress_tokens_sha256':list_sha(actual),'inference':{'device':'cpu','requested_compute_type':'int8','actual_compute_type':model.model.compute_type,'language':'ko','beam_size':5,'temperature':0,'without_timestamps':True,'word_timestamps':False,'condition_on_previous_text':False,'vad_filter':False,'initial_prompt':None,'prefix':None,'hotwords':None,'suppress_blank':True},'elapsed_seconds':time.monotonic()-started,'actual_listening':False,'continuous_playback':False,'constraint_forces_expected_numerals':False,'interpretation':'This bans Arabic-digit formatting and timestamp tokens; it does not guarantee literal phonemes or correct Korean numerals. Compare actual raw output and retain standard unconstrained evidence.'}
            dump(dest,result);results.append(pin(dest))
            print(json.dumps({'model':name,'scene':t['scene_id'],'token_count':constraint['digit_token_count'],'digit_token_ids_sha256':constraint['digit_token_ids_canonical_json_sha256'],'transcript':text,'numeric_differences':comparison['numeric_differences'],'report':str(dest)},ensure_ascii=False),flush=True)
        del model
    for row in read(OUT/'standard_snapshot/manifest.json')['entries']:
        assert sha(Path(row['original']['path']))==row['original']['sha256']
    dump(OUT/'run_receipt.json',{'status':'four_actual_constrained_ASR_runs_complete','script_sha256':cfg['script_sha256'],'same_two_raw_audio':[{k:t[k] for k in ['scene_id','audio']} for t in targets],'original_standard_review_snapshot':snap,'results':results,'runner':pin(OUT/'run_phonetic.py'),'actual_runs':4,'models':['small','medium'],'network_calls':0,'paid_calls':0,'TTS_calls':0,'audio_or_standard_QA_modified':False,'actual_listening':False,'continuous_playback':False,'automatic_issue_closure':False})
if __name__=='__main__':main()
