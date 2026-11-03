"""Measure the actual final AAC PCM and verify all34 source-voice time windows.

Zero-lag correlation checks sync/presence, never pronunciation or naturalness.
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import assemble as a
import numpy as np


def check():
    plan=a.read(a.OUT/'global_edl.json')
    movie=a.OUT/'affordable_home_price_rebuild_r2_v1.mp4'
    windows=[]
    for s in plan['scenes']:
        # The same scene-local .25..3.25s slice in the full audio and native WAV.
        start=s['start_frame']*1600+12000
        windows.append(dict(scene_id=s['scene_id'],start=start,end=start+144000,parts=[],source=s['audio_source']))
    argv=[str(a.FF),'-hide_banner','-v','error','-i',str(movie),'-map','0:a:0','-ac','1','-ar','48000','-c:a','pcm_f32le','-f','f32le','pipe:1']
    count=0;power=0.0;peak=0.0;nan=0;inf=0;rail=0
    log=a.owned(a.OUT/'audio_PCM_decode.log')
    with log.open('wb') as error:
        process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=error,cwd=a.ROOT)
        while True:
            raw=process.stdout.read(262144)
            if not raw:break
            assert len(raw)%4==0
            chunk=np.frombuffer(raw,dtype='<f4')
            nan+=int(np.isnan(chunk).sum());inf+=int(np.isinf(chunk).sum())
            valid=np.nan_to_num(chunk).astype(np.float64)
            peak=max(peak,float(np.abs(valid).max(initial=0)));power+=float(np.square(valid).sum());rail+=int((np.abs(valid)>=1).sum())
            for w in windows:
                lo=max(count,w['start']);hi=min(count+len(chunk),w['end'])
                if hi>lo:w['parts'].append(chunk[lo-count:hi-count].copy())
            count+=len(chunk)
        returncode=process.wait()
    assert returncode==0 and nan==0 and inf==0 and rail==0
    expected=plan['total_frames']*1600
    # AAC last packet can contain codec padding; MP4 stream duration remains exact.
    assert expected<=count<expected+1024
    rows=[]
    for w in windows:
        actual=np.concatenate(w['parts']).astype(np.float64)
        path=a.source(w['source']['path']);assert a.sha(path)==w['source']['sha256']
        with wave.open(str(path),'rb') as native:
            assert native.getnchannels()==1 and native.getframerate()==48000
            native.setpos(12000);reference=np.frombuffer(native.readframes(144000),dtype='<i2').astype(np.float64)/32768
        assert len(actual)==len(reference)==144000
        centered=actual-actual.mean();ref=reference-reference.mean()
        correlation=float(np.dot(centered,ref)/math.sqrt(float(np.dot(centered,centered)*np.dot(ref,ref))))
        assert correlation>.95, w['scene_id']+': final mixed AAC source voice sync mismatch'
        rows.append(dict(scene_id=w['scene_id'],global_start_sample=w['start'],local_start_sample=12000,samples=144000,zero_lag_correlation=correlation,source=w['source'],speech_present_at_expected_timing=True))
    receipt=dict(status='pass',movie=a.pin(movie),edl=a.pin(a.OUT/'global_edl.json'),sample_rate=48000,analysis_channels=1,actual_AAC_decoded_samples=count,EDL_expected_samples=expected,codec_tail_padding_samples=count-expected,peak_absolute=peak,peak_dBFS=20*math.log10(peak),RMS_dBFS=10*math.log10(power/count),NaN_samples=nan,Inf_samples=inf,rail_or_over_full_scale_samples=rail,all34_source_time_windows=rows,min_zero_lag_correlation=min(r['zero_lag_correlation'] for r in rows),decode_log=a.pin(log),command=argv,scope='actual final AAC full-stream numerical signal and native voice zero-lag windows',actual_listening=False,continuous_playback=False,pronunciation_verified=False,subjective_naturalness_reviewed=False,perceived_music_voice_balance_reviewed=False)
    a.dump(a.OUT/'encoded_audio_signal.json',receipt)
    print(json.dumps(dict(status='pass',scenes=34,samples=count,clipped_samples=rail,min_correlation=receipt['min_zero_lag_correlation']),ensure_ascii=False))


if __name__=='__main__':check()
