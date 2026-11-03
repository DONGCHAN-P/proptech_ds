"""Offline technical checks of actual generated files; does not synthesize or listen."""
import array
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('narration_runtime',HERE/'production_v1.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
OUT=HERE/'production-injoon-v2'
PREPARED=HERE/'prepare-v2-r2/prepared.json'


def check():
    plan,gate=r.check_gate(PREPARED)
    inputs=r.load(OUT/'run_inputs.json')
    assert gate==inputs['gate'] and inputs['prepared_sha256']==r.sha(PREPARED)
    assert not (OUT/'failure.json').exists()
    timing=r.load(OUT/'final_timing.json')
    assert timing['script_sha256']==r.SCRIPT_SHA and timing['voice']==r.VOICE
    assert len(timing['chapters'])==len(plan['chapters'])==10
    assert len(list((OUT/'paragraphs').glob('*/measured.json')))==45
    paragraphs=[];chapters=[];scene_times=[];cumulative=0;word_count=0;cue_count=0
    for intended,ch in zip(plan['chapters'],timing['chapters']):
        assert ch['chapter']==intended['chapter'] and ch['title']==intended['title']
        assert r.load(OUT/f'chapter_{ch["chapter"]:02}.json')==ch
        audio=r.ROOT/ch['audio_file']
        assert audio==OUT/f'chapter_{ch["chapter"]:02}.wav'
        assert r.sha(audio)==ch['audio_sha256']
        pcm,frames,signal=r.p.read_pcm(audio)
        assert frames==ch['pcm_frames'] and frames%800==0
        assert frames/r.p.RATE==ch['total_seconds']
        samples=array.array('h',pcm)
        clipped=sum(abs(value)>=32767 for value in samples)
        assert clipped==0
        assert signal==ch['last_pcm_signal_end_s']
        assert len(ch['paragraphs'])==len(intended['paragraphs'])
        leading=round(ch['leading_silence_s']*r.p.RATE)
        assert not any(pcm[:leading*2])
        offset=leading;expected_cues=[];last_native=last_pcm=None
        for index,(q,placement) in enumerate(zip(intended['paragraphs'],ch['paragraphs'])):
            folder=OUT/'paragraphs'/q['scene_id']
            request=r.load(folder/'request.json');record=r.load(folder/'measured.json')
            events=r.load(folder/'native_boundaries.json')
            assert request['script_sha256']==r.SCRIPT_SHA and request['voice']==r.VOICE
            assert request['text']==q['text'] and request['spoken_text']==q['spoken_text']
            assert request['gate']==gate and request['scene_id']==q['scene_id']
            assert r.sha(folder/'request.json')==record['request_sha256']
            assert r.sha(folder/'audio.wav')==record['audio_sha256']
            assert (folder/'audio.mp3').stat().st_size>0
            raw,pframes,psignal=r.p.read_pcm(folder/'audio.wav')
            values=array.array('h',raw)
            assert psignal is not None and not any(abs(v)>=32767 for v in values)
            assert pframes/r.p.RATE==record['measured_seconds']
            assert max(map(abs,values))==record['pcm_peak_absolute']
            assert psignal==record['pcm_signal_end_s']
            assert record['voice']==r.VOICE and record['clipped_samples']==0
            assert all(e['type']=='WordBoundary' for e in events)
            assert len(events)==record['word_count']
            native_end=max((e['offset']+e['duration'])/1e7 for e in events)
            assert native_end==record['last_word_end_s'] and native_end<=pframes/r.p.RATE+0.15
            overlap=max([max(0,(a['offset']+a['duration']-b['offset'])/1e7) for a,b in zip(events,events[1:])],default=0)
            assert overlap==record['max_native_word_overlap_s']
            actual=r.align(q,events)
            assert actual==record['cues']
            for cue in actual:
                assert len(r.compact(cue['text']))>9
                assert len(cue['display_lines']) in (1,2)
                assert max(map(len,cue['display_lines']))<=40
                assert ' '.join(' '.join(cue['display_lines']).split())==' '.join(cue['text'].split())
            for a,b in q['protected_ranges']:
                matching=[c for c in actual if c['source_start']<=a and c['source_end']>=b]
                assert len(matching)==1 and any(q['text'][a:b] in line for line in matching[0]['display_lines'])
            assert placement['paragraph']==q['paragraph']
            assert round(placement['offset_s']*r.p.RATE)==offset
            assert placement['measured_seconds']==record['measured_seconds']
            assert pcm[offset*2:(offset+pframes)*2]==raw,'Chapter PCM must preserve every original sample'
            last_native=offset/r.p.RATE+native_end;last_pcm=offset/r.p.RATE+psignal
            assert placement['last_native_word_end_s']==last_native and placement['last_pcm_signal_end_s']==last_pcm
            for cue in actual:
                c=copy.deepcopy(cue);c['id']=f'C{ch["chapter"]:02}_'+c['id']
                for key in ('start_s','end_s','native_start_s','native_end_s'):c[key]=round(c[key]+placement['offset_s'],9)
                expected_cues.append(c)
            first=actual[0]['start_s']+placement['offset_s'];last=actual[-1]['native_end_s']+placement['offset_s']
            scene_times.append({'scene_id':q['scene_id'],'paragraph':q['paragraph'],'chapter':ch['chapter'],
                'start_s':first,'end_s':last,'chapter_local':True,'body_start_s':cumulative+first,
                'body_end_s':cumulative+last,'timing_basis':'actual native WordBoundary + measured PCM placement',
                'audio_revision':OUT.name,'brand_intro_offset_applied':False})
            paragraphs.append({'scene_id':q['scene_id'],'paragraph':q['paragraph'],'directory':str(folder),
                'mp3_sha256':r.sha(folder/'audio.mp3'),'wav_sha256':record['audio_sha256'],
                'native_sha256':r.sha(folder/'native_boundaries.json'),'request_sha256':record['request_sha256'],
                'measured_seconds':record['measured_seconds'],'native_words':len(events),'meaning_cues':len(actual),
                'pcm_peak_absolute':record['pcm_peak_absolute'],'clipped_samples':0,
                'last_native_word_end_s':native_end,'last_pcm_signal_end_s':psignal,
                'max_native_word_overlap_s':overlap,'source_and_spoken_exact':True,
                'native_words_exactly_once':True,'protected_cues_and_lines_intact':True})
            word_count+=len(events);cue_count+=len(actual);offset+=pframes
            if index<len(intended['paragraphs'])-1:
                gap=round(r.CONTRACT['paragraph_gap_s']*r.p.RATE)
                assert not any(pcm[offset*2:(offset+gap)*2]);offset+=gap
        assert expected_cues==ch['cues']
        assert all(a['end_s']<=b['start_s'] for a,b in zip(ch['cues'],ch['cues'][1:]))
        assert all(0<=c['start_s']<c['end_s']<=ch['total_seconds'] for c in ch['cues'])
        assert not any(pcm[offset*2:]),'Only zero padding may follow preserved paragraph PCM'
        assert last_native==ch['last_native_word_end_s']
        assert max(last_native,last_pcm)==ch['last_speech_end_s']
        assert ch['tail_from_last_spoken_s']==ch['total_seconds']-ch['last_speech_end_s']
        target=3 if ch['chapter']==10 else 1.2
        assert ch['tail_from_last_spoken_s']>=target
        chapters.append({'chapter':ch['chapter'],'audio_file':ch['audio_file'],'sha256':ch['audio_sha256'],
            'total_seconds':ch['total_seconds'],'frames_30fps':frames//800,'native_words':sum(p['native_words'] for p in paragraphs if any(q['paragraph']==p['paragraph'] for q in intended['paragraphs'])),
            'cues':len(ch['cues']),'pcm_peak_absolute':max(map(abs,samples)),'clipped_samples':0,
            'original_paragraph_PCM_byte_identical':True,'last_native_word_end_s':last_native,
            'last_pcm_signal_end_s':last_pcm,'conservative_speech_end_s':ch['last_speech_end_s'],
            'tail_from_conservative_speech_end_s':ch['tail_from_last_spoken_s']})
        cumulative+=ch['total_seconds']
    # Re-read the gate after all offline checks to prove immutable approvals survived.
    assert r.check_gate(PREPARED)[1]==gate
    report={'status':'technical_pass_actual_generated_audio_not_listened','script_sha256':r.SCRIPT_SHA,
        'prepared_sha256':r.sha(PREPARED),'final_timing_sha256':r.sha(OUT/'final_timing.json'),
        'gate':gate,'new_paragraphs':len(paragraphs),'cross_episode_audio_reuse':0,
        'chapters':chapters,'paragraphs':paragraphs,'total_seconds':cumulative,
        'actual_native_words':word_count,'actual_meaning_cues':cue_count,
        'provisional_cues':sum(len(q['meaning_plan']) for ch in plan['chapters'] for q in ch['paragraphs']),
        'full_display_and_spoken_coverage':True,'protected_numbers_units_dates_percentpoints':True,
        'all_display_cues_nonoverlap':True,'clipped_samples':0,'30fps_all_chapter_padding':True,
        'native_overlap_metadata_preserved':True,'audio_speed_changed':False,
        'last_speech_end_basis':r.CONTRACT['last_speech_basis'],'CTA_tail_at_least_3s':True,
        'actual_listening':False,'ASR_QA_performed_here':False,'font_glyph_or_encoded_QA_performed_here':False,
        'paid_calls':0,'cash_spent_krw':0,'required_technical_errors':[],
        'pending':['Kant independent ASR/pronunciation QA','editor actual font bounds and encoded QA'],
        'coverage':'Complete source/reading/native/event/PCM checks. This is not a listening or render approval.'}
    return report,scene_times


if __name__=='__main__':
    report,times=check()
    r.save(OUT/'technical_validation.json',report)
    r.save(HERE/'timing_proposals_v2.json',{'script_sha256':r.SCRIPT_SHA,'audio_revision':OUT.name,
        'timing_basis':'measured chapter-local and cumulative body offsets; editor adds brand intro',
        'scenes':times})
    print(json.dumps({k:report[k] for k in ('status','new_paragraphs','total_seconds','actual_native_words','actual_meaning_cues','required_technical_errors')},ensure_ascii=False))
