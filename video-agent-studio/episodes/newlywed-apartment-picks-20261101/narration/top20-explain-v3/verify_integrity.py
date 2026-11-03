"""Read back artifacts and sample placement. Same-agent technical audit, not QA/listening."""
from pathlib import Path
import datetime as dt
import hashlib
import html
import json
import re
import wave

O=Path(__file__).resolve().parent
E=O.parents[1]
R=O.parents[4]
SR=44100

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t): return ''.join(c for c in html.unescape(t) if c.isalnum())
def save(p,d):
    p.resolve().relative_to(O)
    p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def pcm(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(SR,1,2)
        return w.readframes(w.getnframes())

def main():
    t=read(O/'timing_proposals.json'); wdoc=read(O/'words.json'); words=wdoc['words']
    manifest=read(O/'narration_manifest.json'); rows=read(O/'sentences.json')['sentences']
    doc=read(E/'writer/top20-explain-v3/scene_proposals_v6.json')
    assert sha(E/'writer/top20-explain-v3/script_v6.md')==t['script_sha256']==manifest['approval']['script_md_sha256']
    assert sha(E/'writer/top20-explain-v3/scene_proposals_v6.json')==t['scene_json_sha256']==manifest['approval']['scene_json_sha256']
    approved=[(s['scene_id'],q['sentence_id'],q['text']) for s in doc['scenes'] for q in s['sentences']]
    assert [(r['scene_id'],r['sentence_id'],r['display_text']) for r in rows]==approved
    assert [(s['scene_id'],q['sentence_id'],q['display_text']) for s in t['scenes'] for q in s['sentence_times']]==approved
    assert len(approved)==133 and len(words)==1496
    assert not t['timing_locked'] and t['lock_owner']=='director' and t['timing_basis']=='actual_audio'
    assert sha(R/t['words_file'])==t['words_file_sha256']
    assert sha(Path(t['audio_file']))==t['audio_sha256']
    full=pcm(Path(t['audio_file']))
    spoken=[s for s in t['scenes'] if s['sentence_times']]
    placements=[]
    for scene in spoken:
        segment=pcm(Path(scene['audio_path']))
        start=round(scene['start_s']*SR)
        assert full[start*2:start*2+len(segment)]==segment
        assert abs(scene['end_s']*SR-(start+len(segment)//2))<.00001
        sw=[w for w in words if w['scene_id']==scene['scene_id']]
        provider=read(R/scene['provider_boundaries_path'])['boundaries']
        provider=[b for b in provider if norm(b['text'])]
        assert len(provider)==len(sw)
        for b,w in zip(provider,sw):
            assert norm(b['text'])==norm(w['text'])
            assert abs(w['local_start_s']-b['offset']/1e7/1.35)<1e-10
            assert abs(w['local_end_s']-(b['offset']+b['duration'])/1e7/1.35)<1e-10
            assert abs(w['start_s']-scene['start_s']-w['local_start_s'])<1e-10
            assert abs(w['end_s']-scene['start_s']-w['local_end_s'])<1e-10
        for q in scene['sentence_times']:
            row=next(r for r in rows if r['sentence_id']==q['sentence_id'])
            qw=[w for w in sw if w['sentence_id']==q['sentence_id']]
            assert norm(''.join(w['text'] for w in qw))==norm(row['reading_text'])
            assert q['start_s']==qw[0]['local_start_s'] and q['end_s']==qw[-1]['local_end_s']
            covered=set()
            for w in qw:
                assert row['display_text'][w['display_char_start']:w['display_char_end']]==w['display_text']
                assert row['reading_text'][w['reading_char_start']:w['reading_char_end']]==w['reading_text']
                covered.update(range(w['display_char_start'],w['display_char_end']))
            assert all(i in covered for i,c in enumerate(row['display_text']) if c.isalnum())
        placements.append({'scene_id':scene['scene_id'],'exact_full_audio_pcm_segment':True,'sample_count':len(segment)//2,'scene_audio_sha256':sha(Path(scene['audio_path']))})
    for name in ['brand_intro','brand_outro']:
        b=t[name];data=pcm(Path(b['audio_path']));start=round(b['start_s']*SR)
        assert full[start*2:start*2+len(data)]==data
        assert len(data)//2==round(b['duration_s']*SR)
    assert abs(t['brand_intro']['start_s']-spoken[0]['end_s'])<1e-10
    last=words[-1]['end_s'];outro=t['brand_outro']['start_s']
    assert 0<=outro-last-3<=1/SR
    assert abs(len(full)/2/SR-(outro+10))<1e-10
    e001=t['scenes'][-1]
    assert e001['scene_id']=='E001'
    gap=full[round(e001['start_s']*SR)*2:round(e001['end_s']*SR)*2]
    assert not any(gap)
    values=0
    for row in rows:
        original=row['reading_text']
        for tr in reversed(row['transformations']):
            assert original[tr['spoken_start']:tr['spoken_end']]==tr['spoken_text']
            original=original[:tr['spoken_start']]+tr['source_text']+original[tr['spoken_end']:]
            for value in tr['independent_values']:
                assert float(value['source_value'])==float(value['decoded_value'])
                values+=1
        assert original==row['display_text']
    lookup={r['sentence_id']:r for r in rows}
    assert lookup['O002-07A']['reading_text'].count('시월')==1
    assert lookup['O002-07D']['reading_text'].startswith('시월')
    assert '십 월' not in ''.join(lookup[k]['reading_text'] for k in ['O002-07A','O002-07D'])
    assert lookup['S010-21']['reading_text'].count('와이시티')==1
    assert '잠실 이 단지와 삼 단지' in lookup['S021-02']['reading_text']
    assert '지티엑스 에이' in lookup['S005-03']['reading_text']
    assert '지밸리' in lookup['S008-04']['reading_text']
    assert '이편한' in lookup['S006-21']['reading_text']
    receipts=[read(p) for p in (O/'raw').glob('*.receipt.json')]
    assert len(receipts)==26 and all(r['status']=='complete' for r in receipts)
    assert all(r['paid_api_calls']==0 and r['cash_cost_krw']==0 and not r['automatic_retry'] for r in receipts)
    old=read(O/'superseded/initial-reading-v1/partial_timing_proposals.json')
    old_o=next(s for s in old['scenes'] if s['scene_id']=='O002')
    new_o=next(s for s in spoken if s['scene_id']=='O002')
    change={'changed_scene_ids':['O002'],'changed_sentence_ids':['O002-07A','O002-07D'],'change':'10월 standard pronunciation 시월; display and source bytes unchanged','previous_scene_duration_s':old_o['duration_s'],'new_scene_duration_s':new_o['duration_s'],'timing_delta_s':new_o['duration_s']-old_o['duration_s'],'replacement_raw_audio':new_o['raw_audio_path'],'replacement_processed_audio':new_o['audio_path'],'global_later_scene_timing_shift_s':new_o['duration_s']-old_o['duration_s'],'old_partial_evidence':'superseded/initial-reading-v1/partial_handoff.json','current_partial_handoff':'partial_handoff.json','source_originals_preserved':True}
    save(O/'pronunciation_change_receipt.json',change)
    save(O/'generation_usage.json',{'completed_free_TTS_requests':26,'current_spoken_scenes':25,'superseded_successful_requests':1,'revision_reason':'user correction 10월→시월 for O002 only','failed_requests':0,'automatic_retries':0,'paid_api_calls':0,'cash_cost_krw':0,'credentials_loaded':False,'total_sent_characters_including_superseded':sum(r['characters'] for r in receipts),'current_text_characters':manifest['characters']})
    audit={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'passed_same_agent_artifact_audit_not_independent_QA','script_and_scene_bytes_unchanged':True,'approved_sentences_exact_order':133,'numeric_values_roundtripped':values,'word_count':len(words),'all_provider_ticks_rechecked':True,'display_alphanumeric_coverage':1.0,'scene_audio_exact_full_PCM_placements':placements,'brand_PCM_source_exact':True,'silent_hold_PCM_zero':True,'last_word_to_outro_s':outro-last,'all_audio_duration_s':len(full)/2/SR,'first3_handoff_updated':True,'important_pronunciation_lexical_checks_passed':True,'actual_listening':False,'asr_performed':False,'independent_QA_performed':False,'new_paid_api_calls':0,'cash_cost_krw':0}
    save(O/'integrity_audit.json',audit)
    h=read(O/'handoff.json')
    h['reading_revision_changes']=[change]
    h['generation_usage_path']=(O/'generation_usage.json').relative_to(R).as_posix()
    h['outputs'] += [(O/n).relative_to(R).as_posix() for n in ['pronunciation_change_receipt.json','generation_usage.json','integrity_audit.json'] if (O/n).relative_to(R).as_posix() not in h['outputs']]
    h['checks'].append({'check':'sample-exact placement, all native provider ticks and display character coverage readback','result':'passed_same_agent_not_independent_QA','evidence':(O/'integrity_audit.json').relative_to(R).as_posix()})
    save(O/'handoff.json',h)
    files=[p for p in O.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','completion_receipt.json'] and p.suffix!='.tmp']
    save(O/'artifact_manifest.json',{'created_at':audit['at'],'files':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]})
    completion=read(O/'completion_receipt.json');completion.update(artifact_manifest_sha256=sha(O/'artifact_manifest.json'),integrity_audit_sha256=sha(O/'integrity_audit.json'),verification_code_sha256=sha(Path(__file__)),free_requests_completed=26,latest_pronunciation_revision='O002-month-v2')
    save(O/'completion_receipt.json',completion)
    print(json.dumps({k:audit[k] for k in ['status','approved_sentences_exact_order','numeric_values_roundtripped','word_count','last_word_to_outro_s','all_audio_duration_s','actual_listening']},ensure_ascii=False))

if __name__=='__main__': main()
