"""v6 delta verification, preserving v5 evidence; no listening or ASR claim."""
import array
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import wave

SIDE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SIDE))
import repair_v6 as r
import production_narration as p
import production_generate as g


def main():
    plan,gate=g.gate_for_plan(r.PREP)
    manifest=p.load(r.PREP.with_name('repair_manifest.json'))
    final=p.load(r.OUT/'final_timing.json');old=p.load(r.BASE/'final_timing.json')
    summary=p.load(r.OUT/'repair_summary.json');old_tech=p.load(r.BASE/'technical_validation.json')
    assert final['script_sha256']==r.NEW_SHA
    assert p.digest(SIDE/'final_timing.json')==p.digest(SIDE/'final_timing.v6.json')==p.digest(r.OUT/'final_timing.json')
    assert p.digest(SIDE/'final_timing.v5.json')==manifest['root_v5_sha256']==p.digest(r.BASE/'final_timing.json')
    assert len(final['chapters'])==10 and not (r.OUT/'failure.json').exists()
    for name,sha in manifest['v5_file_sha256'].items():assert p.digest(r.BASE/name)==sha
    assert summary['new_tts_calls']==2 and summary['reused_paragraphs']==52
    compact=lambda text:re.sub(r'\s+','',text)
    reused=set(manifest['comparison']['reused_ids']);changed=set(manifest['comparison']['changed_ids'])
    old_rows={row['paragraph_id']:row for row in old_tech['source_audio']}
    old_chapter={row['chapter']:row for row in old_tech['chapters']}
    source=Path(gate['script_path']).read_text(encoding='utf-8-sig')
    events_total=0;reused_verified=0;new_verified=0;cue_ids=set();chapters=[];source_records=[]
    ffmpeg=g.ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
    for chapter,previous,prepared in zip(final['chapters'],old['chapters'],plan['chapters']):
        number=chapter['chapter'];audio=g.ROOT/chapter['audio_file']
        assert number==previous['chapter']==prepared['chapter']
        assert p.digest(audio)==chapter['audio_sha256']
        with wave.open(str(audio),'rb') as wav:
            params=wav.getparams()
            assert (params.nchannels,params.sampwidth,params.framerate)==(1,2,24000)
            assert params.nframes==chapter['pcm_frames'] and params.nframes%800==0
            assert params.nframes/24000==chapter['total_seconds']
            if number in (5,6):samples=array.array('h',wav.readframes(params.nframes))
        assert chapter['total_seconds']-chapter['last_speech_end_s']>=(3 if number==10 else 1.2)-1e-8
        if number in (5,6):
            decode=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(audio),'-f','null','-'],capture_output=True)
            assert decode.returncode==0
            clipped=sum(abs(x)>=32767 for x in samples);assert clipped==0
            leading=0.6 if number==1 else 3.5
            assert all(x==0 for x in samples[:round(leading*24000)])
            decode_basis='new v6 chapter full decode and PCM clipping scan'
        else:
            assert chapter['audio_sha256']==previous['audio_sha256']==old_chapter[number]['audio_sha256']
            assert chapter['cues']==previous['cues'] and chapter['total_seconds']==previous['total_seconds']
            clipped=old_chapter[number]['clipped_samples'];assert clipped==0
            decode_basis='exact SHA reuse of v5 full-decode and clipping-pass receipt'
        last=0
        for cue in chapter['cues']:
            assert cue['id'] not in cue_ids;cue_ids.add(cue['id'])
            assert 0<=cue['start_s']<cue['end_s']<=chapter['total_seconds']
            assert cue['start_s']>=last-1e-8;last=cue['end_s']
        assert compact(''.join(x['text'] for x in chapter['cues']))==compact(''.join(x['text'] for x in prepared['paragraphs']))
        assert compact(''.join(x['spoken_text'] for x in chapter['cues']))==compact(''.join(x['spoken_text'] for x in prepared['paragraphs']))
        for index,(paragraph,position) in enumerate(zip(prepared['paragraphs'],chapter['paragraphs'])):
            identifier=paragraph['paragraph_id'];folder=r.OUT/'paragraphs'/identifier
            request=p.load(folder/'request.json');measured=p.load(folder/'measured.json');events=p.load(folder/'native_boundaries.json')
            assert source[paragraph['source_start']:paragraph['source_end']]==paragraph['text']
            assert request['text']==paragraph['text'] and request['spoken_text']==paragraph['spoken_text'] and request['voice']==g.VOICE
            assert p.digest(folder/'request.json')==measured['request_sha256']
            assert p.digest(folder/'audio.wav')==measured['audio_sha256']
            assert all(e['type']=='WordBoundary' for e in events)
            assert p.norm(''.join(e['text'] for e in events))==p.norm(paragraph['spoken_text'])
            if identifier in reused:
                assert request['script_sha256']==r.OLD_SHA and measured['applicable_script_sha256']==r.NEW_SHA
                baseline=old_rows[identifier]
                for name,key in [('audio.mp3','mp3_sha256'),('audio.wav','wav_sha256'),('native_boundaries.json','native_boundaries_sha256')]:
                    assert p.digest(folder/name)==baseline[key]
                reused_verified+=1
            else:
                assert identifier in changed and request['script_sha256']==measured['script_sha256']==r.NEW_SHA
                assert p.digest(folder/'audio.wav')!=old_rows[identifier]['wav_sha256']
                decoded=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(folder/'audio.wav'),'-f','null','-'],capture_output=True)
                assert decoded.returncode==0
                _,frames,signal=p.read_pcm(folder/'audio.wav');assert frames/24000==measured['measured_seconds'] and signal is not None
                new_verified+=1
            if index+1<len(chapter['paragraphs']):
                following=chapter['paragraphs'][index+1]
                assert abs(following['offset_s']-position['offset_s']-position['measured_seconds']-0.35)<1e-8
            events_total+=len(events)
            source_records.append({'paragraph_id':identifier,'reused':identifier in reused,
                'wav_sha256':p.digest(folder/'audio.wav'),'mp3_sha256':p.digest(folder/'audio.mp3'),
                'native_sha256':p.digest(folder/'native_boundaries.json')})
        chapters.append({'chapter':number,'seconds':chapter['total_seconds'],
            'delta_seconds':round(chapter['total_seconds']-previous['total_seconds'],9),
            'audio_sha256':chapter['audio_sha256'],'same_v5_audio_sha256':chapter['audio_sha256']==previous['audio_sha256'],
            'cue_count':len(chapter['cues']),'clipped_samples':clipped,'decode_basis':decode_basis,
            'last_native_word_end_s':chapter['last_native_word_end_s'],
            'last_pcm_signal_end_s':chapter['last_pcm_signal_end_s'],
            'tail_seconds':chapter['total_seconds']-chapter['last_speech_end_s']})
    assert (reused_verified,new_verified)==(52,2)
    assert len(list((r.OUT/'paragraphs').glob('*/reuse_evidence.json')))==52
    assert len(list((r.OUT/'paragraphs').glob('*/request.json')))==54
    result={'task_id':'narration-v6-two-paragraph-repair','checked_at':datetime.now(timezone.utc).isoformat(),
        'status':'technical_pass_pending_two_paragraph_ASR_QA','script_sha256':r.NEW_SHA,'gate':gate,
        'reused_paragraphs':52,'newly_synthesized_paragraphs':2,'application_new_tts_calls':2,
        'body_paragraphs':54,'chapters':chapters,'total_seconds':sum(x['seconds'] for x in chapters),
        'delta_seconds':round(sum(x['seconds'] for x in chapters)-summary['previous_total_seconds'],9),
        'previous_cues':341,'display_cues':len(cue_ids),'cue_delta':len(cue_ids)-341,
        'native_word_events':events_total,'strict_original_and_spoken_punctuation_coverage':'passed',
        'all_v5_original_files_preserved':len(manifest['v5_file_sha256']),
        'unchanged_chapter_sha_verified':[1,2,3,4,7,8,9,10],'rebuilt_chapters':[5,6],
        'newly_decoded_files':4,'reused_decode_receipts':8,'clipped_samples':0,
        'final_timing_sha256':p.digest(SIDE/'final_timing.json'),'v5_root_archive_sha256':p.digest(SIDE/'final_timing.v5.json'),
        'source_audio':source_records,'paid_api_calls':0,'cash_budget_krw':0,
        'actual_listening':False,'ASR_QA_performed_by_narration':False,'final_media_approved':False,
        'next_owner':'QA Kant / video_director / editor Carson'}
    g.save(r.OUT/'technical_validation.json',result)
    print(json.dumps({key:result[key] for key in ('status','reused_paragraphs','newly_synthesized_paragraphs','total_seconds','delta_seconds','display_cues','cue_delta','native_word_events')},ensure_ascii=False))


if __name__=='__main__':main()
