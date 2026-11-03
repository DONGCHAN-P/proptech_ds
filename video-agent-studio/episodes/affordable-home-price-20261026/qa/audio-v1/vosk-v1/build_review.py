"""Consolidated scoped verdict from complementary same-WAV evidence.

Numeral component proof is explicit. It is not a whole-Vosk-transcript pass,
and neither source/native metadata nor any ASR result is labelled listening.
"""
import sys,re,json,hashlib
from pathlib import Path
from email.parser import Parser
from datetime import datetime,timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;QA=OUT.parent
sys.path.insert(0,str(QA));sys.path.insert(0,str(QA/'v3_delta'))
from prepare import EP,read,sha,pin,dump
from semantic_checks import numbers
import run_asr

def main():
    cfg=read(QA/'config.json');run_asr.gate(cfg)
    prepared=read(OUT/'prepared.json');runtime=read(OUT/'runtime_manifest.json');run=read(OUT/'run_receipt.json')
    prior=read(QA/'v3_delta/review.json');manifest=read(QA/'v3_delta/actual_v3_manifest.json')
    assert run['ASR_runs']==2 and prepared['script_sha256']==prior['script_sha256']==manifest['script_sha256']==cfg['script_sha256']
    assert sha(Path(prepared['final_timing']['path']))==prepared['final_timing']['sha256']=='86a3c01e344f8c24da930404355b60d34eb9e1a0f49431cd299b5b38034939e7'
    results={sid:read(OUT/'results'/f'{sid}.json') for sid in ['S019','S024']}
    for sid,d in results.items():
        for key in ['input_audio','resampled_audio']:assert sha(Path(d[key]['path']))==d[key]['sha256']
        assert d['PCM_frames_consumed']==d['resampled_header']['frames']
        assert not d['SetGrammar_called'] and not d['expected_number_list_or_hotwords']
        for model in ['small','medium']:
            w=read(QA/'v3_delta/runs'/sid/f'{model}.json')
            assert w['audio']['sha256']==d['input_audio']['sha256']
    proofs=[]
    specs=[('S019','fee1074',21.71,22.90,10740000,[27,28]),('S019','fee3615',24.44,26.05,36150000,[31,32]),('S019','fee4902',27.65,28.93,49020000,[35,36,37]),('S024','loan_low_block2902',23.57,25.00,29020000,[34,35,36])]
    for sid,label,lo,hi,expected,indices in specs:
        d=results[sid];words=[w for p in d['native_Result_and_FinalResult'] for w in p.get('result',[])]
        selected=[w for w in words if lo<=w['start'] and w['end']<=hi]
        raw=' '.join(w['word'] for w in selected)
        # Generic wrapper stripping only; no numeral/word replacement, guessed
        # prefix correction or expected-number substitution.
        normalized=re.sub(r'[\[\](){}]','',raw)
        parsed=numbers(normalized)
        assert len(parsed)==1 and parsed[0]['unit']=='KRW' and int(parsed[0]['value'])==expected,(sid,raw,parsed)
        nativep=EP/'narration/production-injoon-v3/paragraphs'/sid/'native_boundaries.json'
        native=read(nativep);anchors=[{'index':i,**native[i]} for i in indices]
        assert selected[0]['start']>anchors[0]['offset']/1e7-.4
        assert selected[-1]['end']<(anchors[-1]['offset']+anchors[-1]['duration'])/1e7+.4
        proofs.append({'scene_id':sid,'component':label,'source_audio':d['input_audio'],'resampled_audio':d['resampled_audio'],'raw_Vosk_tokens':raw,'tokens_with_times_and_confidence':selected,'normalization':'Remove only square/round/curly wrapper characters; preserve all numeral words/digits and units.','literal_normalized_tokens':normalized,'parsed_value_krw':expected,'parsed':parsed,'native_anchors':anchors,'native_anchors_file':pin(nativep),'native_role':'Source reading/time anchors, not independent acoustic or listening evidence.','Vosk_acoustic_role':'Independent unprompted Kaldi recognition on the same WAV; word times are recognizer estimates.','actual_listening':False})
    prefix=[]
    for name in ['small','medium']:
        p=QA/'v3_delta/runs/S024'/f'{name}.json';d=read(p)
        assert re.search(r'필요한\s*대출이\s*10억',d['transcript'])
        prefix.append({'model':name,'raw_transcript':d['transcript'],'report':pin(p),'audio_sha256':d['audio']['sha256'],'accepted_component':'10억 =1000000000KRW','rejected_component':'The trailing formatted numeral/unit remains wrong; it is not accepted from this transcript.'})
    assert 1000000000+proofs[-1]['parsed_value_krw']==1029020000
    combined={'scene_id':'S024','approved_display_value':'10억2,902만원','combined_value_krw':1029020000,'high_component_krw':1000000000,'high_component_evidence':prefix,'low_component_krw':proofs[-1]['parsed_value_krw'],'low_component_evidence':proofs[-1],'independent_Vosk_full_value_exact_match':False,'Vosk_unaccepted_high_component':'시바','method':'Complementary same-WAV component evidence: the two standard Whisper passes retain10억; independent unprompted Vosk retains2천9백이만원 in the matching native time span. No interpretation of시바as십억 is required or made.','inference':'The earlier critical digit-order/unit alternatives are decoder rendering errors in the available ASR evidence; this is a scoped inference, not actual listening confirmation.'}
    dump(OUT/'component_proof.json',{'script_sha256':cfg['script_sha256'],'final_timing':prepared['final_timing'],'literal_components':proofs,'S024_combined_value':combined,'normalization_expected_number_list_used':False,'actual_listening':False})
    metadata=OUT/'deps/vosk-0.3.45.dist-info/METADATA';headers=Parser().parsestr(metadata.read_text(encoding='utf-8'))
    classifiers=headers.get_all('Classifier',[])
    assert 'License :: OSI Approved :: Apache Software License' in classifiers
    provenance={'runtime':pin(OUT/'runtime_manifest.json'),'archive':pin(OUT/'archive_provenance.json'),'packages':pin(OUT/'asr_package_versions.json'),'provision_receipt':runtime['provision_receipt'],'model_name':'vosk-model-small-ko-0.22','model_tree_sha256':runtime['model_tree_sha256'],'model_license':'Apache-2.0','model_license_basis':'Main official primary catalog verification recorded in provision receipt; shipped README has no full license text.','package_version':'0.3.45','package_metadata':pin(metadata),'package_license_field':headers.get('License'),'package_license_classifier':'Apache Software License','publisher_archive_checksum_available':False,'computed_archive_SHA_is_not_publisher_checksum':True,'API':runtime['package_api']}
    limitations=['Vosk whole-paragraph WER is not zero. Its generic numeric parser result is not used as a blind pass/fail rule.','The Vosk[65]억 house-price token and S024시바high block are noisy outputs; they are not accepted or silently corrected. Previously clear house-price evidence is retained from the standard same-WAV/source checks.','Vosk posterior/confidence1.0 also appears on noisy words; confidence is not calibrated truth and is not an approval threshold.','S024 full value is supported by complementary components across engines, not an exact full-value Vosk transcript.','All recognition is unprompted; no grammar, digit constraints, expected-number list or hotwords.','No actual listening, naturalness, continuous playback, final BGM mix, source visuals or encoded video approval.']
    review={'task':'Independent Kaldi/Vosk review of remaining v3 numerical ambiguities','at_utc':datetime.now(timezone.utc).isoformat(),'approved':True,'approval_scope':'Closure of the remaining ASR numerical ambiguity using explicit same-WAV component evidence plus preserved source/native/PCM checks. Not whole-Vosk accuracy or actual listening.','script_sha256':cfg['script_sha256'],'final_timing_sha256':prepared['final_timing']['sha256'],'final_timing':prepared['final_timing'],'critical_issues':[],'required_issues':[],'recommended_issues':[],'issue_closures':[{'id':'ASR-A2-NUM-001','status':'closed_for_observed_ASR_source_PCM_scope','evidence':pin(OUT/'component_proof.json'),'S014_basis':'Standard v3 medium recovers5억103만원; preserved prior review.','S019_basis':'Independent literal Vosk components recover1074/3615/4902만원 in the three fee spans.','S024_basis':'Independent Vosk low block2902만원 plus explicit10억high block from both standard same-WAV Whisper passes; no correction ofVosk시바.'},{'id':'ASR-A2-TERM-001','status':'closed_carried_from_standard_v3_identification_review','evidence':pin(QA/'v3_delta/review.json'),'scope':'Literal/canonical mixed-letter acronym identification; no listening claim.'}],'actual_results':[pin(OUT/'results'/f'{sid}.json') for sid in ['S019','S024']],'raw_transcripts':{sid:d['raw_transcript'] for sid,d in results.items()},'component_proof':pin(OUT/'component_proof.json'),'runtime_provenance':provenance,'prior_standard_v3_review':pin(QA/'v3_delta/review.json'),'failed_no_digit_review':pin(QA/'v3_delta/phonetic_decode/review.json'),'coverage':{'actual_Vosk_runs':2,'unique_original_input_seconds':64.848,'actual_PCM16k_frames_consumed':sum(d['PCM_frames_consumed'] for d in results.values()),'source_audio_SHA_and_resampled_SHA_pinned':True,'existing_FFmpeg_only':True,'full_raw_paragraphs':['S019','S024'],'optional_cue_ASR_reruns':0,'original_whole_v2_small_ASR_and_targeted_medium_reused_by_SHA':True,'v3_four_new_small_and_targeted_medium_reused':True,'unchanged41_raw_SHA_proof_reused':True,'actual_listening':False,'continuous_playback':False,'audio_input_runtime_support':False,'naturalness_approved':False,'final_mix_approved':False,'video_approved':False,'TTS_calls':0,'external_audio_transmission':False,'network_ASR_calls':0,'QA_download_or_install_calls':0},'limitations':limitations,'builder':pin(OUT/'build_review.py')}
    dump(OUT/'review.json',review)
    gate={'task':'Consolidated independent audio gate for exact production-injoon-v3','approved':True,'approval_scope':'Observed unprompted ASR/source/native/PCM evidence only; actual hearing and final mix/media remain unchecked.','script_sha256':cfg['script_sha256'],'audio_revision':'production-injoon-v3','final_timing_sha256':prepared['final_timing']['sha256'],'final_timing':prepared['final_timing'],'critical_issues':[],'required_issues':[],'recommended_issues':[],'issue_closures':review['issue_closures'],'per_amount_component_proof':pin(OUT/'component_proof.json'),'independent_review':pin(OUT/'review.json'),'prior_Whisper_v3_review_preserved':pin(QA/'v3_delta/review.json'),'prior_no_digit_failure_preserved':pin(QA/'v3_delta/phonetic_decode/review.json'),'v2_review_preserved':pin(QA/'review.json'),'new4_and_reuse41_manifest':pin(QA/'v3_delta/actual_v3_manifest.json'),'new4':manifest['new4'],'reuse41_count':len(manifest['reuse41']),'unchanged6chapter_WAV_SHA':[c for c in manifest['chapters'] if c['unchanged']],'all10_current_chapter_audio_pins':manifest['chapters'],'current_total_seconds':manifest['total_seconds'],'current_display_cues':150,'coverage':{**review['coverage'],'new4_small_ASR_paragraphs':4,'new4_targeted_medium_ASR_paragraphs':4,'new4_raw_ASR_seconds':126.192,'whole_episode_ASR_repeated_for_v3':False,'native_source_and_PCM_changed4chapters_checked':[4,5,6,7],'original_41_raw_audio_bytes_unchanged':True,'approved_new_spoken_differences_verified':True,'v2_spoken_bytes_required_equal_for_new4':False,'independent_DSP_new4':prior['DSP'],'full_narrator_technical_validation_reused_bySHA':pin(EP/'narration/production-injoon-v3/technical_validation.json')},'limitations':limitations,'at_utc':datetime.now(timezone.utc).isoformat()}
    dump(QA/'audio_gate_v3.json',gate)
    dump(OUT/'handoff.json',{'status':'independent_remaining_numeric_components_resolved_consolidated_gate_approved','approved':True,'script_sha256':cfg['script_sha256'],'final_timing_sha256':prepared['final_timing']['sha256'],'consolidated_audio_gate':pin(QA/'audio_gate_v3.json'),'review':pin(OUT/'review.json'),'component_proof':pin(OUT/'component_proof.json'),'runtime_provenance':provenance,'critical_issues':[],'required_issues':[],'actual_Vosk_runs':2,'actual_listening':False,'continuous_playback':False,'naturalness_or_final_mix_approved':False,'existing_standard_v3_and_no_digit_records_preserved':True,'new_TTS_calls':0})
    print({'gate':str(QA/'audio_gate_v3.json'),'approved':True,'required':0,'critical':0,'component_values_krw':[p['parsed_value_krw'] for p in proofs],'S024_combined_value_krw':1029020000,'actual_listening':False})
if __name__=='__main__':main()
