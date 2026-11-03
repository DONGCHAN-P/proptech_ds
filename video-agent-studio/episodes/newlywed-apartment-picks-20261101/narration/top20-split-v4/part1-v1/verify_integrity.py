"""Independent local structural/PCM audit; never synthesizes or performs ASR."""
import hashlib
import html
import json
from pathlib import Path
import subprocess
import wave

OUT=Path(__file__).resolve().parent
EP=OUT.parents[2]
ROOT=EP.parents[2]


def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t): return ''.join(c for c in html.unescape(t) if c.isalnum())
def pcm(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,44100)
        return w.readframes(w.getnframes())
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    timing=read(OUT/'timing_proposals.json')
    words=read(OUT/'words.json')['words']
    ledger=read(OUT/'pronunciation_ledger.json')
    approval=read(OUT/'approval_receipt.json')
    manifest=read(OUT/'narration_manifest.json')
    canonical=read(ROOT/approval['scene_json_path'])
    md=(ROOT/approval['script_md_path']).read_text(encoding='utf-8-sig')
    assert sha(ROOT/approval['scene_json_path'])==approval['scene_json_sha256']
    assert sha(ROOT/approval['script_md_path'])==approval['script_md_sha256']
    # Source selection is strictly the approved PART1 canonical scene list.
    expected=[(s['scene_id'],r['sentence_id'],r['text']) for s in canonical['scenes'] for r in s['sentences']]
    actual=[(s['scene_id'],r['sentence_id'],r['text']) for s in timing['scenes'] for r in s['sentences']]
    assert actual==expected and len(actual)==85 and len(timing['scenes'])==12
    assert all(x[0].startswith('P01-') for x in actual)
    assert [s['scene_id'] for s in timing['scenes']]==[s['scene_id'] for s in canonical['scenes']]
    rows={r['sentence_id']:r for r in ledger['sentences']}
    for r in rows.values():
        restored=r['reading_text']
        for t in reversed(r['transformations']):
            assert restored[t['spoken_start']:t['spoken_end']]==t['spoken_text']
            restored=restored[:t['spoken_start']]+t['source_text']+restored[t['spoken_end']:]
            assert all(float(v['source_value'])==float(v['decoded_value']) for v in t['independent_values'])
        assert restored==r['display_text']
    all_pcm=pcm(Path(timing['audio_file']))
    segments={seg['asset_id']:seg for s in timing['scenes'] for seg in s['segments']}
    assert len(segments)==13
    for c in manifest['chunks']:
        seg=segments[c['asset_id']]
        assert sha(Path(seg['audio_path']))==seg['audio_sha256']
        assert all_pcm[seg['start_frame']*2:seg['end_frame']*2]==pcm(Path(seg['audio_path']))
        receipt=read(OUT/'raw'/(c['asset_id']+'.receipt.json'))
        assert receipt['status']=='complete' and receipt['automatic_retry'] is False
        assert all(sha(ROOT/v['path'])==v['sha256'] for v in receipt['outputs'].values())
        boundaries=read(ROOT/receipt['outputs']['metadata']['path'])['boundaries']
        ww=[w for w in words if w['asset_id']==c['asset_id']]
        assert norm(''.join(b['text'] for b in boundaries))==norm(c['text'])
        assert len(ww)==len([b for b in boundaries if norm(b['text'])])
        raw_end=max((b['offset']+b['duration'])/1e7 for b in boundaries)
        assert raw_end<=receipt['duration_s']+.03
    for s in timing['scenes']:
        assert all_pcm[round(s['start_s']*44100)*2:round(s['end_s']*44100)*2]==pcm(Path(s['audio_path']))
        for r in s['sentences']:
            ww=[w for w in words if w['sentence_id']==r['sentence_id']]
            assert norm(''.join(w['provider_text'] for w in ww))==norm(r['reading_text'])
            assert r['text']==rows[r['sentence_id']]['display_text']
            assert abs(r['start_s']-ww[0]['start_s'])<1e-8 and abs(r['end_s']-ww[-1]['end_s'])<1e-8
            assert s['start_s']<=r['start_s']<r['end_s']<=s['end_s']+.04
        for w in [x for x in words if x['scene_id']==s['scene_id']]:
            seg=segments[w['asset_id']];r=rows[w['sentence_id']]
            assert abs(w['start_s']-(seg['start_s']+w['raw_start_s']/1.35))<1e-8
            assert abs(w['end_s']-(seg['start_s']+w['raw_end_s']/1.35))<1e-8
            assert abs(w['local_start_s']-(w['start_s']-s['start_s']))<1e-8
            assert r['display_text'][w['source_char_start']:w['source_char_end']]==w['display_text']
            assert md[w['reader_md_char_start']:w['reader_md_char_end']]==w['display_text']
    for a,b in zip(words,words[1:]): assert a['end_s']<=b['start_s']+.000001
    for b in [timing['brand_intro'],timing['brand_outro']]:
        assert all_pcm[round(b['start_s']*44100)*2:round(b['end_s']*44100)*2]==pcm(Path(b['audio_path']))
        assert all(w['end_s']<=b['start_s'] or w['start_s']>=b['end_s'] for w in words)
    intro=timing['brand_intro'];outro=timing['brand_outro']
    assert words[0]['sentence_id']=='P01-INTRO-V2-01'
    assert timing['scenes'][0]['sentences'][0]['end_s']<=intro['start_s']
    assert timing['scenes'][0]['sentences'][1]['start_s']>=intro['end_s']
    last=words[-1]['end_s']
    assert abs(last-timing['last_spoken_end_s'])<1e-8
    assert 3<=outro['start_s']-last<=3+1/44100
    assert abs((timing['final_audio_tail_already_counted_s']+timing['additional_silence_after_audio_s'])-(outro['start_s']-last))<1e-8
    assert len(all_pcm)//2==round(timing['total_duration_with_brand_and_hold_s']*44100)
    assert timing['actual_listening'] is False and timing['asr_performed'] is False
    # Validate every frozen input/output hash, then strictly decode the delivered WAV.
    for path,value in manifest['input_versions'].items(): assert sha(ROOT/path)==value,path
    artifact=read(OUT/'artifact_manifest.json')
    for f in artifact['files']: assert sha(ROOT/f['path'])==f['sha256'],f['path']
    ffmpeg=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
    result=subprocess.run([str(ffmpeg),'-v','error','-xerror','-i',timing['audio_file'],'-f','null','-'],capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0,result.stderr.decode('utf-8',errors='replace')
    report={'status':'passed_structural_PCM_and_full_decode_audit','sentence_count':85,'scene_count':12,
            'chunk_count':13,'word_count':len(words),'duration_s':len(all_pcm)/2/44100,
            'brand_intervals_s':{'intro':[intro['start_s'],intro['end_s']],'outro':[outro['start_s'],outro['end_s']]},
            'last_speech_end_s':last,'native_word_coverage_exact':True,'source_offsets_exact':True,
            'all_processed_PCM_samples_preserved':True,'all_input_and_artifact_hashes_verified':True,
            'strict_full_decode_exit_code':result.returncode,'strict_decode_stderr':result.stderr.decode('utf-8',errors='replace'),
            'actual_listening':False,'asr_performed':False,'independent_role_QA_performed':False,
            'scope':'별도 로컬 감사 코드의 구조·PCM 검사. 독립 담당 검수나 실제 청취는 미수행.'}
    save(OUT/'integrity_audit.json',report)
    artifact['files']=[f for f in artifact['files'] if not f['path'].endswith('/integrity_audit.json')]
    p=OUT/'integrity_audit.json'
    artifact['files'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
    save(OUT/'artifact_manifest.json',artifact)
    receipt=read(OUT/'completion_receipt.json');receipt['artifact_manifest_sha256']=sha(OUT/'artifact_manifest.json')
    receipt['integrity_audit_sha256']=sha(p);save(OUT/'completion_receipt.json',receipt)
    print(json.dumps({k:report[k] for k in ['status','sentence_count','word_count','duration_s']},ensure_ascii=False))


if __name__=='__main__': main()
