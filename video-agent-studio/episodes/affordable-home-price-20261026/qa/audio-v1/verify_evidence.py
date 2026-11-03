"""Fresh evidence verification, stdlib only, read-only source/audio."""
import sys,wave,array
from pathlib import Path
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
from prepare import EP,read,sha,pin,dump
from run_asr import gate

if __name__=='__main__':
    cfg=read(QA/'config.json');gate(cfg);report=read(QA/'review.json');count=0
    def walk(o):
        global count
        if isinstance(o,dict):
            if 'path' in o and 'sha256' in o:
                p=Path(o['path'])
                assert p.is_absolute() and sha(p)==o['sha256'],o
                count+=1
            for v in o.values():walk(v)
        elif isinstance(o,list):
            for v in o:walk(v)
    walk(report)
    rows=[]
    for row in read(QA/'readiness.json')['chapters']:
        p=Path(row['audio']['path']);ch=read(Path(row['chapter_json']['path']))
        with wave.open(str(p),'rb') as w:
            frames=w.getnframes();hz=w.getframerate();a=array.array('h',w.readframes(frames))
        if sys.byteorder!='little':a.byteswap()
        peak=max(abs(min(a)),abs(max(a)));clipped=sum(abs(x)>=32767 for x in a)
        last_index=next(i for i in range(len(a)-1,-1,-1) if abs(a[i])>=33)
        pcm_end=(last_index+1)/hz;native_end=max(c['native_end_s'] for c in ch['cues'])
        tail=frames/hz-max(pcm_end,native_end)
        assert abs(pcm_end-ch['last_pcm_signal_end_s']) < 2/hz
        assert abs(native_end-ch['last_native_word_end_s']) < 2e-6
        assert clipped==0 and tail>=(3 if ch['chapter']==10 else 1.19)
        rows.append({'chapter':ch['chapter'],'audio':row['audio'],'sample_peak':peak,'clipped_samples':clipped,'last_pcm_sample_at_or_above_minus60dBFS_s':pcm_end,'max_native_word_end_s':native_end,'tail_from_max_PCM_and_native_s':tail})
    assert read(QA/'tests.json')['passed']
    d={'status':'evidence_SHA_and_actual_PCM_verified','review':pin(QA/'review.json'),'verifier':pin(QA/'verify_evidence.py'),'evidence_pin_occurrences_verified':count,'chapter_count':len(rows),'chapter_signal_checks':rows,'narrator_handoff':pin(EP/'narration/handoff.json'),'narrator_qa_packet':pin(EP/'narration/production-injoon-v2/qa_packet.json'),'narrator_technical_validation':pin(EP/'narration/production-injoon-v2/technical_validation.json'),'actual_listening':False,'continuous_playback':False,'ASR_or_audio_rerender_performed_here':False}
    dump(QA/'verification.json',d)
    hand=read(QA/'handoff.json');hand['verification']=pin(QA/'verification.json');hand['completed_small_chapters_at_handoff']=10;hand['evidence']['run_targeted_medium.py']=pin(QA/'run_targeted_medium.py');hand['evidence']['recheck_cues.py']=pin(QA/'recheck_cues.py');hand['evidence']['build_review.py']=pin(QA/'build_review.py');hand['evidence']['verify_evidence.py']=pin(QA/'verify_evidence.py')
    hand['current_required_audio_errors']='No confirmed listening errors. Required evidence follow-up:3numeric cues and2DSR cues; see review.json.'
    dump(QA/'handoff.json',hand)
    print({'verified_pins':count,'actual_chapters':len(rows),'max_sample_peak':max(r['sample_peak'] for r in rows),'clipped_samples':sum(r['clipped_samples'] for r in rows),'last_tail_s':rows[-1]['tail_from_max_PCM_and_native_s'],'required_issues':len(report['required_issues']),'approved':report['approved'],'actual_listening':False})
