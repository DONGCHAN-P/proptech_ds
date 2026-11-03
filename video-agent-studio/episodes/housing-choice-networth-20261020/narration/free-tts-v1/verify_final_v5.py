"""Offline technical/source checks only; never claims listening or ASR QA."""
import array
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import wave

SIDE=Path(__file__).resolve().parent
sys.path.insert(0,str(SIDE))
import production_narration as p
import production_generate as g


def main():
    plan,gate=g.gate_for_plan(SIDE/'prepare-v5/prepared.json')
    final=p.load(SIDE/'final_timing.json')
    out=SIDE/final['audio_revision']
    assert final['script_sha256']==plan['script_sha256']=='babeb15213477f3f6dcb8e8ab958e1a4ccc691c53c1fca6ca9ceae99cc5f269b'
    contract=p.load(g.CONTRACT)
    assert all(key in final for key in contract['narration_required_keys'])
    assert len(final['chapters'])==10 and p.digest(out/'final_timing.json')==p.digest(SIDE/'final_timing.json')
    assert len(list((out/'paragraphs').glob('*/measured.json')))==54
    failure_history=list(out.glob('failure_*.json'))
    if failure_history:
        resolution=p.load(out/'local_finalization_receipt.json')
        assert resolution['status']=='resolved_local_manifest_only' and resolution['new_tts_calls']==0
        before=p.load(out/'before_local_finalization.json')
        assert all(p.digest(out/path)==sha for path,sha in before['audio_hashes'].items())
    reports=[];cue_ids=set();paragraph_count=0;event_count=0;source_files=[]
    for chapter,source in zip(final['chapters'],plan['chapters']):
        assert chapter['chapter']==source['chapter']
        audio=g.ROOT/chapter['audio_file']
        assert audio.is_relative_to(SIDE) and p.digest(audio)==chapter['audio_sha256']
        with wave.open(str(audio),'rb') as stream:
            params=stream.getparams();samples=array.array('h',stream.readframes(stream.getnframes()))
        assert (params.nchannels,params.sampwidth,params.framerate)==(1,2,24000)
        assert params.nframes%800==0 and params.nframes/params.framerate==chapter['total_seconds']
        assert chapter['total_seconds']>=chapter['last_speech_end_s']+(3 if chapter['chapter']==10 else 1.2)-1e-8
        leading=0.6 if chapter['chapter']==1 else 3.5
        assert all(value==0 for value in samples[:round(leading*24000)])
        decode=subprocess.run([str(g.ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'),
            '-nostdin','-v','error','-i',str(audio),'-f','null','-'],capture_output=True)
        assert decode.returncode==0
        previous_end=0
        for cue in chapter['cues']:
            assert all(key in cue for key in ('id','paragraph','text','spoken_text','start_s','end_s','timing_basis'))
            assert cue['id'] not in cue_ids;cue_ids.add(cue['id'])
            assert leading<=cue['start_s']<cue['end_s']<=chapter['total_seconds']
            assert cue['start_s']>=previous_end-1e-8
            previous_end=cue['end_s']
        assert p.norm(''.join(c['text'] for c in chapter['cues']))==p.norm(''.join(x['text'] for x in source['paragraphs']))
        assert p.norm(''.join(c['spoken_text'] for c in chapter['cues']))==p.norm(''.join(x['spoken_text'] for x in source['paragraphs']))
        for i,(paragraph,position) in enumerate(zip(source['paragraphs'],chapter['paragraphs'])):
            folder=out/'paragraphs'/paragraph['paragraph_id']
            request=p.load(folder/'request.json');measured=p.load(folder/'measured.json');events=p.load(folder/'native_boundaries.json')
            assert request['text']==paragraph['text'] and request['spoken_text']==paragraph['spoken_text']
            assert request['script_sha256']==plan['script_sha256'] and request['voice']==g.VOICE
            assert p.digest(folder/'audio.wav')==measured['audio_sha256']
            assert p.digest(folder/'request.json')==measured['request_sha256']
            assert all(e['type']=='WordBoundary' for e in events)
            assert p.norm(''.join(e['text'] for e in events))==p.norm(paragraph['spoken_text'])
            assert position['paragraph']==paragraph['paragraph']
            if i+1<len(chapter['paragraphs']):
                gap=chapter['paragraphs'][i+1]['offset_s']-position['offset_s']-position['measured_seconds']
                assert abs(gap-0.35)<1e-8
            event_count+=len(events);paragraph_count+=1
            source_files.append({'paragraph_id':paragraph['paragraph_id'],
                'mp3_sha256':p.digest(folder/'audio.mp3'),'wav_sha256':measured['audio_sha256'],
                'native_boundaries_sha256':p.digest(folder/'native_boundaries.json')})
        clipped=sum(abs(value)>=32767 for value in samples)
        assert clipped==0, '클리핑 발견: 실제 검수 필요'
        reports.append({'chapter':chapter['chapter'],'audio_file':chapter['audio_file'],
            'seconds':chapter['total_seconds'],'frames':params.nframes,'cue_count':len(chapter['cues']),
            'peak':max(abs(value) for value in samples),'clipped_samples':clipped,'full_decode':'passed',
            'last_native_word_end_s':chapter['last_native_word_end_s'],
            'last_pcm_signal_end_s':chapter['last_pcm_signal_end_s'],
            'last_speech_end_s':chapter['last_speech_end_s'],
            'tail_seconds':chapter['total_seconds']-chapter['last_speech_end_s'],
            'audio_sha256':chapter['audio_sha256']})
    assert paragraph_count==54
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'status':'source_audio_timing_technical_checks_passed_not_listened',
        'script_sha256':plan['script_sha256'],'gate':gate,'chapters':reports,'paragraphs':paragraph_count,
        'native_word_events':event_count,'display_cues':len(cue_ids),'total_seconds':sum(c['seconds'] for c in reports),
        'final_timing_sha256':p.digest(SIDE/'final_timing.json'),
        'checks':['current gate and receipt hashes','all 54 original/readings exact','native word coverage',
                  'nonoverlapping display cues','10 WAV full decode','PCM 24k mono16 / 30fps frame ceiling',
                  'leading and 0.35s paragraph gap','last-spoken based tails','clipping zero'],
        'actual_listening':False,'continuous_playback':False,'ASR_QA_performed':False,
        'final_media_approved':False,'paid_api_calls':0,'source_audio':source_files,
        'resolved_local_failure_history':[f.name for f in failure_history]}
    g.save(out/'technical_validation.json',result)
    print(json.dumps({key:result[key] for key in ('status','paragraphs','native_word_events','display_cues','total_seconds')},ensure_ascii=False))


if __name__=='__main__':
    main()
