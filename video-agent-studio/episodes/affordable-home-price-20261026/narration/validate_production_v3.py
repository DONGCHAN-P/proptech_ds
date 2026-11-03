"""Offline actual v3 delta validation. Does not synthesize, transcribe or listen."""
import array
import copy
import importlib.util
from pathlib import Path
import json
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('delta_runtime',HERE/'repair_v3.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.r


def check():
    plan,gate=m.gate();out=m.OUT
    assert r.load(out/'run_inputs.json')['gate']==gate
    assert not (out/'failure.json').exists()
    timing=r.load(out/'final_timing.json');baseline=r.load(m.BASE/'final_timing.json')
    assert timing['gate_evidence']==gate and timing['script_sha256']==r.SCRIPT_SHA
    assert timing['voice']==r.VOICE and timing['paragraph_voice_overrides']=={s:m.VOICE for s in m.TARGETS}
    assert len(timing['chapters'])==10 and len(list((out/'paragraphs').glob('*/assembly_record.json')))==45
    paragraphs=[];chapters=[];scenes=[];body=0;native_total=0;cue_total=0
    for qchapter,ch,old in zip(plan['chapters'],timing['chapters'],baseline['chapters']):
        assert r.load(out/f'chapter_{ch["chapter"]:02}.json')==ch
        wave=out/f'chapter_{ch["chapter"]:02}.wav'
        assert r.ROOT/ch['audio_file']==wave and r.sha(wave)==ch['audio_sha256']
        pcm,frames,signal=r.p.read_pcm(wave);samples=array.array('h',pcm)
        assert frames==ch['pcm_frames'] and frames%800==0 and frames/r.p.RATE==ch['total_seconds']
        assert not any(abs(v)>=32767 for v in samples) and signal==ch['last_pcm_signal_end_s']
        offset=round(ch['leading_silence_s']*r.p.RATE)
        assert not any(pcm[:offset*2]);expected=[];last_native=last_signal=None
        assert len(qchapter['paragraphs'])==len(ch['paragraphs'])
        for index,(q,placement) in enumerate(zip(qchapter['paragraphs'],ch['paragraphs'])):
            scene=q['scene_id'];folder=out/'paragraphs'/scene;changed=scene in m.TARGETS
            pin=next(x for x in plan['paragraph_pins'] if x['scene_id']==scene)
            request=r.load(folder/'request.json');record=r.load(folder/'assembly_record.json')
            events=r.load(folder/'native_boundaries.json')
            if not changed:
                for name,digest in pin['files'].items():assert r.sha(folder/name)==digest
                original=r.load(folder/'measured.json');original['wave_file']=str(folder/'audio.wav')
                assert record==original
            else:
                assert record==r.load(folder/'measured.json') and request['gate']==gate
            voice=m.VOICE if changed else r.VOICE
            assert request['voice']==record['voice']==voice
            assert request['script_sha256']==r.SCRIPT_SHA
            assert request['text']==q['text'] and request['spoken_text']==q['spoken_text']
            assert r.sha(folder/'request.json')==record['request_sha256']
            assert r.sha(folder/'audio.wav')==record['audio_sha256'] and (folder/'audio.mp3').stat().st_size>0
            raw,pframes,psignal=r.p.read_pcm(folder/'audio.wav');values=array.array('h',raw)
            assert psignal is not None and not any(abs(v)>=32767 for v in values)
            assert pframes/r.p.RATE==record['measured_seconds'] and psignal==record['pcm_signal_end_s']
            assert max(map(abs,values))==record['pcm_peak_absolute'] and record['clipped_samples']==0
            aligned=m.fixed_align(q,events)
            fields=('id','text','spoken_text','display_lines','source_start','source_end','spoken_start','spoken_end',
                'start_s','end_s','native_start_s','native_end_s','first_word_index','last_word_index','paragraph','scene_id')
            assert [{k:c[k] for k in fields} for c in aligned]==[{k:c[k] for k in fields} for c in record['cues']]
            for a,b in q['protected_ranges']:
                matches=[c for c in aligned if c['source_start']<=a and c['source_end']>=b]
                assert len(matches)==1 and any(q['text'][a:b] in line for line in matches[0]['display_lines'])
            for c in aligned:
                assert len(r.compact(c['text']))>9 and len(c['display_lines']) in (1,2)
                assert max(map(len,c['display_lines']))<=40
                assert ' '.join(' '.join(c['display_lines']).split())==' '.join(c['text'].split())
            native=max((e['offset']+e['duration'])/1e7 for e in events)
            assert native==record['last_word_end_s'] and native<=pframes/r.p.RATE+0.15
            overlap=max([max(0,(a['offset']+a['duration']-b['offset'])/1e7) for a,b in zip(events,events[1:])],default=0)
            assert overlap==record['max_native_word_overlap_s'] and len(events)==record['word_count']
            assert placement['paragraph']==q['paragraph'] and round(placement['offset_s']*r.p.RATE)==offset
            assert placement['wave_file']==str(folder/'audio.wav') and placement['measured_seconds']==record['measured_seconds']
            assert pcm[offset*2:(offset+pframes)*2]==raw
            last_native=placement['offset_s']+native;last_signal=placement['offset_s']+psignal
            assert placement['last_native_word_end_s']==last_native and placement['last_pcm_signal_end_s']==last_signal
            for cue in record['cues']:
                c=copy.deepcopy(cue);c['id']=f'C{ch["chapter"]:02}_'+c['id']
                for key in ('start_s','end_s','native_start_s','native_end_s'):c[key]=round(c[key]+placement['offset_s'],9)
                expected.append(c)
            scenes.append({'scene_id':scene,'chapter':ch['chapter'],'paragraph':q['paragraph'],
                'start_s':placement['offset_s']+aligned[0]['start_s'],
                'end_s':placement['offset_s']+aligned[-1]['native_end_s'],
                'body_start_s':body+placement['offset_s']+aligned[0]['start_s'],
                'body_end_s':body+placement['offset_s']+aligned[-1]['native_end_s'],
                'brand_offset_applied':False,'timing_basis':'actual native WordBoundary + measured PCM placement'})
            paragraphs.append({'scene_id':scene,'chapter':ch['chapter'],'newly_synthesized':changed,'voice':voice,
                'wave_file':str(folder/'audio.wav'),'wav_sha256':r.sha(folder/'audio.wav'),
                'mp3_sha256':r.sha(folder/'audio.mp3'),'native_sha256':r.sha(folder/'native_boundaries.json'),
                'request_sha256':r.sha(folder/'request.json'),'measured_seconds':pframes/r.p.RATE,
                'previous_seconds':r.load(m.BASE/'paragraphs'/scene/'measured.json')['measured_seconds'],
                'native_words':len(events),'meaning_cues':len(aligned),'max_native_overlap_s':overlap,
                'last_native_word_end_s':native,'last_pcm_signal_end_s':psignal,
                'clipped_samples':0,'source_spoken_and_protected_expressions':True,
                'unchanged5_raw_files_SHA':not changed})
            native_total+=len(events);cue_total+=len(aligned);offset+=pframes
            if index<len(qchapter['paragraphs'])-1:
                gap=round(r.CONTRACT['paragraph_gap_s']*r.p.RATE)
                assert not any(pcm[offset*2:(offset+gap)*2]);offset+=gap
        assert expected==ch['cues']
        assert all(0<=c['start_s']<c['end_s']<=ch['total_seconds'] for c in expected)
        assert all(a['end_s']<=b['start_s'] for a,b in zip(expected,expected[1:]))
        assert not any(pcm[offset*2:])
        assert ch['last_speech_end_s']==max(last_native,last_signal)
        assert ch['last_pcm_signal_end_s']==signal and ch['last_native_word_end_s']==last_native
        assert ch['tail_from_last_spoken_s']==ch['total_seconds']-ch['last_speech_end_s']
        assert ch['tail_from_last_spoken_s']>=(3 if ch['chapter']==10 else 1.2)
        unchanged=ch['chapter'] not in (4,5,6,7)
        if unchanged:assert ch['audio_sha256']==old['audio_sha256'] and ch['total_seconds']==old['total_seconds']
        else:assert ch['audio_sha256']!=old['audio_sha256']
        display_fields=('id','scene_id','paragraph','text','source_start','source_end','display_lines')
        assert [{k:c[k] for k in display_fields} for c in ch['cues']]==[{k:c[k] for k in display_fields} for c in old['cues']]
        chapters.append({'chapter':ch['chapter'],'audio_file':ch['audio_file'],'sha256':ch['audio_sha256'],
            'previous_sha256':old['audio_sha256'],'unchanged_audio':unchanged,'total_seconds':ch['total_seconds'],
            'previous_seconds':old['total_seconds'],'delta_seconds':ch['total_seconds']-old['total_seconds'],
            'frames_30fps':frames//800,'clipped_samples':0,'cues':len(expected),
            'tail_from_conservative_speech_end_s':ch['tail_from_last_spoken_s']})
        body+=ch['total_seconds']
    assert cue_total==150 and len(paragraphs)==45 and sum(x['newly_synthesized'] for x in paragraphs)==4
    assert sum(x['unchanged_audio'] for x in chapters)==6
    m.verify_pins(plan);assert m.gate()[1]==gate
    assert r.sha(HERE/'final_timing.json')==plan['base_final_timing_sha256'],'Preserve root v2 timing pending adoption'
    report={'status':'v3_delta_actual_technical_pass_pending_independent_ASR','script_sha256':r.SCRIPT_SHA,
        'prepared_sha256':r.sha(m.PREPARED),'generator_sha256':r.sha(m.HERE/'repair_v3.py'),'gate':gate,
        'new_paragraphs':4,'reused_paragraphs_verified':41,'unchanged_audio_chapters_verified':6,
        'paragraphs':paragraphs,'chapters':chapters,'actual_meaning_cues':cue_total,'actual_native_words':native_total,
        'total_seconds':body,'previous_seconds':sum(c['total_seconds'] for c in baseline['chapters']),
        'delta_seconds':body-sum(c['total_seconds'] for c in baseline['chapters']),
        'all150_display_ID_source_ranges_and_lines_unchanged':True,'full45_spoken_native_coverage':True,
        'original_paragraph_PCM_byte_identical_in_chapters':True,'all45_clipped_samples':0,
        'all10_30fps_padding':True,'CTA_from_max_native_PCM_end_at_least_3s':True,
        'raw_native_overlaps_preserved_display_nonoverlap':True,'root_and_versioned_v2_preserved':True,
        'final_timing_sha256':r.sha(out/'final_timing.json'),'required_technical_errors':[],
        'actual_listening':False,'naturalness_verified':False,'ASR_QA_performed_here':False,
        'paid_calls':0,'cash_spent_krw':0,'automatic_retry':False,'next_role':'Kant only4 changed paragraph ASR; main adopts after approval'}
    return report,scenes


if __name__=='__main__':
    report,scenes=check();r.save(m.OUT/'technical_validation.json',report)
    r.save(HERE/'timing_proposals_v3.json',{'script_sha256':r.SCRIPT_SHA,'audio_revision':m.OUT.name,
        'timing_basis':'chapter-local and cumulative body offsets; editor applies brand anchors','scenes':scenes})
    print(json.dumps({k:report[k] for k in ('status','new_paragraphs','reused_paragraphs_verified','total_seconds','delta_seconds','actual_native_words','actual_meaning_cues','required_technical_errors')},ensure_ascii=False))
