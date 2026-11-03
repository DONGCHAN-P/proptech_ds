"""네트워크/생성 없이 현재 16청크와 92문장 납품물을 검증하고 인계한다."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, subprocess, wave, math

ROOT = Path('C:/projects/realestate_reco')
OWN = Path(__file__).resolve().parent
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
def save(name, data):
    (OWN/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def ref(p): return {'path': rel(p), 'sha256': sha(p)}
now = datetime.now(timezone.utc).isoformat()
manifest = load(OWN/'narration_manifest.json')
lock = load(OWN/'input_lock.json')
ledger = load(OWN/'generation_ledger.json')
timing = load(OWN/'timing_proposals.json')
alignment = load(OWN/'native_chunk_alignment.json')
final = load(OWN/'account_final.json')
assert sha(OWN/'narration_manifest.json') == lock['manifest_sha256']
assert ledger['authorization_id'] == '9cde211f3073'
assert ledger['status'] == 'all16_generated_measured_native_alignment_not_listened'
assert len(ledger['requests']) == 16 and all(r['status']=='complete' for r in ledger['requests'])
assert sum(r['characters'] for r in ledger['requests']) == 5520
assert sum(r['actual_credits'] for r in ledger['requests']) == ledger['actual_credits'] == 2208
assert ledger['automatic_retries'] == ledger['topup_calls'] == ledger['overage_calls'] == ledger['cash_spent_krw'] == 0
assert ledger['reserved_pending_credits'] == 0
assert final['header_account_delta_matches'] and final['observed_account_delta'] == 2208
assert final['subscription']['included_remaining'] == ledger['final_included_remaining'] == 14456
assert not (OWN/'.generation.lock').exists()
executed = OWN/('executed_generator_'+lock['generator_sha256'][:12]+'.mjs')
assert sha(executed) == lock['generator_sha256']
assert len(timing['chunks']) == len(alignment['chunks']) == 16
assert len(timing['sentences']) == 92
assert len({s['sentence_id'] for s in timing['sentences']}) == 92
assert len([s for s in timing['sentences'] if s['kind']=='accepted_main']) == 90
by_id = {s['sentence_id']:s for s in manifest['sentences']}
by_chunk = {c['asset_id']:c for c in timing['chunks']}
native = {c['asset_id']:c for c in alignment['chunks']}
ff = ROOT/lock['ffmpeg_path']
assert sha(ff) == lock['ffmpeg_sha256']
checks, native_overruns = [], []
for c in manifest['chunks']:
    cid = c['asset_id']; r = next(r for r in ledger['requests'] if r['asset_id']==cid)
    assert sha(ROOT/c['path']) == c['sha256']
    text = '\n\n'.join(by_id[sid]['reading_text'] for sid in c['sentence_ids'])
    assert (ROOT/c['path']).read_text(encoding='utf-8') == text and len(text)==c['characters']
    assert r['request']['text'] == text
    assert r['request']['voice_settings'] == {'stability':.6,'similarity_boost':.95,'speed':.97}
    assert set(r['request']) == {'text','model_id','voice_settings'}
    for p,h in r['artifact_sha256'].items(): assert sha(ROOT/p)==h
    wav = ROOT/r['wav_path']
    with wave.open(str(wav),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth()) == (44100,1,2)
        count=w.getnframes(); pcm=w.readframes(count)
    assert hashlib.sha256(pcm).hexdigest() == r['pcm_sha256']
    decoded = subprocess.run([str(ff),'-v','error','-i',str(ROOT/r['raw_audio_path']),'-map','0:a:0',
        '-ac','1','-ar','44100','-f','s16le','pipe:1'], capture_output=True,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert decoded.returncode==0 and decoded.stdout==pcm, cid
    for key,filename in [('alignment','alignment.json'),('normalized_alignment','normalized_alignment.json')]:
        a=load(OWN/'raw'/cid/filename); assert native[cid][key]==a
        assert len(a['characters'])==len(a['character_start_times_seconds'])==len(a['character_end_times_seconds'])
    a=native[cid]['alignment'];assert ''.join(a['characters'])==text
    duration=count/44100
    overruns=[i for i,e in enumerate(a['character_end_times_seconds']) if e>duration+1e-9]
    assert all(not a['characters'][i].isalnum() for i in overruns)
    assert all(a['character_end_times_seconds'][i]-duration<=.081 for i in overruns)
    if overruns: native_overruns.append({'asset_id':cid,'native_overrun_s':max(a['character_end_times_seconds'])-duration,
        'characters': [a['characters'][i] for i in overruns], 'alphanumeric_overrun':False,
        'raw_alignment_modified':False,'proposal_pcm_references_clamped':True})
    assert duration == r['pcm_duration_s'] == by_chunk[cid]['duration_s']
    checks.append({'asset_id':cid,'complete_raw_decode_matches_processed_wav':True,
        'duration_s':duration,'sample_count':count,'pcm_sha256':r['pcm_sha256'],
        'native_alignment_unchanged':True,'frozen_input_sha_verified':True})
for s in timing['sentences']:
    original=by_id[s['sentence_id']]
    assert (s['display_text'],s['reading_text'])==(original['text'],original['reading_text'])
    a=native[s['asset_id']]['alignment'];cs,ce=s['chunk_char_start'],s['chunk_char_end']
    assert ''.join(a['characters'][cs:ce])==s['reading_text']
    duration=by_chunk[s['asset_id']]['duration_s']
    assert 0<=s['chunk_local_start_s']<s['chunk_local_end_s']<=duration
    offset=by_chunk[s['asset_id']]['global_start_s']
    assert math.isclose(s['global_start_s'],offset+s['chunk_local_start_s'])
    assert math.isclose(s['global_end_s'],offset+s['chunk_local_end_s'])
    assert s['reading_character_timing']['characters']==list(s['reading_text'])
    assert len(s['display_character_timing']['reading_char_spans'])==len(s['display_text'])
    for w in s['words']:
        rs,re=w['reading_char_start'],w['reading_char_end']
        assert s['reading_text'][rs:re]==w['reading_text']
        assert s['display_text'][w['display_char_start']:w['display_char_end']]==w['display_text']
        assert s['chunk_local_start_s']<=w['chunk_local_start_s']<=w['chunk_local_end_s']<=s['chunk_local_end_s']
        compact=''.join(ch for ch in w['reading_text'] if ch.isalnum())
        assert s['sentence_normalized_text'][w['sentence_normalized_char_start']:w['sentence_normalized_char_end']]==compact
    for i,ch in enumerate(s['display_text']):
        if ch.isascii() and ch.isdigit():
            assert any(p['display_char_start']<=i<p['display_char_end'] and not p['split_allowed'] for p in s['protected_numeric_spans'])
assert math.isclose(sum(c['duration_s'] for c in timing['chunks'] if c['asset_id']!='SHORTS-CTA'),656.32)
assert by_chunk['SHORTS-CTA']['duration_s']==7.68
assert len(list((OWN/'receipts').glob('*.json')))==16
assert len(list((OWN/'processed').glob('*.wav')))==16
assert len([c for c in manifest['chunks'] if c['asset_id']=='SHORTS-CTA'])==1
assert sum(len(s['words']) for s in timing['sentences'])==1317
verification={'status':'local_artifact_verification_passed','verified_at_utc':now,'network_calls':0,'new_tts_requests':0,
    'chunk_count':16,'main_sentence_count':90,'shared_cta_sentence_count':2,'word_count':1317,'native_character_count':5520,
    'main_full_pcm_duration_s':656.32,'shared_cta_duration_s':7.68,'actual_credits':2208,'included_remaining':14456,
    'checks':checks,'native_final_punctuation_overruns':native_overruns,
    'all92_original_display_and_reading_text_unchanged':True,'all_numeric_display_tokens_protected':True,
    'raw_audio_and_both_native_alignment_files_unchanged':True,'all16_full_mp3_decodes_match_untrimmed_wav_pcm':True,
    'all1317_words_have_sentence_normalized_character_ranges':True,'actual_listening':False,'continuous_playback':False,
    'independent_human_or_agent_qa':False,'scope':'로컬 입력/정렬/PCM/비용 검증; 실제 발음·자연스러움 청취 통과를 의미하지 않음'}
save('verification.json',verification)
reconciliation={'status':'reconciled','verified_at_utc':now,'authorization_id':'9cde211f3073',
    'expected_input_characters':5520,'actual_header_credit_sum':2208,'account_character_count_before':ledger['initial_character_count'],
    'account_character_count_after':final['subscription']['character_count'],'actual_account_credit_delta':2208,
    'included_remaining':14456,'authorized_cap':6500,'unused_authorized_cap':4292,'cash_spent_krw':0,
    'post_calls_total':16,'additional_post_calls_after_generation':0,'automatic_retries':0,'topup_calls':0,'overage_calls':0,
    'initial_final_account_snapshot_was_delayed':True,'account_check_count_for_delayed_reconciliation':1,
    'resolved_local_guard_issue':'예상5520과 실제 비용의 동일액을 요구한 로컬 검사 제거. 실제 헤더 합계와 지연 반영 후 계정 차분2208 일치.',
    'evidence':[ref(OWN/'generation_ledger.json'),ref(OWN/'account_preflight.json'),ref(OWN/'account_final_immediate.json'),ref(OWN/'account_final.json')],
    'generation_not_retried':True}
save('reconciliation.json',reconciliation)
# 실제 실행 당시 원본을 별도 보존했으며 정정된 생성기를 재실행하지 않는다.
ledger['reconciliation']['local_guard_fix']=reconciliation['resolved_local_guard_issue']
save('generation_ledger.json',ledger)
# ledger의 설명문 정정 후 증거 해시를 갱신한다.
reconciliation['evidence'][0]=ref(OWN/'generation_ledger.json');save('reconciliation.json',reconciliation)
output_names=['input_lock.json','generation_ledger.json','account_preflight.json','account_final.json',
    'reconciliation.json','verification.json','scene_chunk_durations.json','timing_proposals.json',
    'sentences.json','words.json','native_chunk_alignment.json','alignment_receipt.json']
handoff={'task_id':'part1-Jun-6500-generation','role':'narration','status':'generated_and_aligned_not_listened',
    'summary':'Jun 16청크/92문장 생성·새 native 정렬 완료. 실제2208/상한6500, 잔액14456, 현금0. 본편15청크656.32초+공용CTA7.68초. 추가TTS/재시도 없음. 원본 MP3·양쪽 정렬 보존, 44.1kHz mono s16 WAV 전체 길이 유지. 실제 청취 미수행.',
    'input_revisions':{'audio_revision':timing['audio_revision'],'authorization':ref(EP/'director/top20-split-v4/part1-jun-and-shorts-v1/production_authorization.json'),
        'frozen_manifest':ref(OWN/'narration_manifest.json'),'frozen_chunks':lock['chunks'],
        'reader_script':ref(ROOT/manifest['main_reader_script']),'generation_input_lock':ref(OWN/'input_lock.json'),
        'executed_generator':ref(executed),'corrected_generator_not_reexecuted':ref(OWN/'generate.mjs'),
        'text_spans_only_old_timing':ref(EP/'director/top20-split-v4/part1-map-clean-v1/locked_timing.json'),
        'timing_builder':ref(OWN/'build_timing.py'),'local_verifier':ref(OWN/'verify_and_handoff.py')},
    'outputs':[ref(OWN/name) for name in output_names],
    'chunk_assets':timing['chunks'],'affected_scene_ids':[c['scene_id'] for c in timing['chunks']],
    'changed_scene_ids':timing['changed_scene_ids'],'duration_changes':timing['changes'],
    'cost':{'actual_credit_used':2208,'actual_included_remaining':14456,'cap':6500,'unused_cap':4292,'cash_spent_krw':0,'post_calls_total':16,'automatic_retries':0,'new_generation_after_parent_finalization_request':0},
    'checks':[{'check':'16개 원본 MP3 전체 decode와 WAV PCM 해시/샘플 수 일치','result':'passed','evidence':rel(OWN/'verification.json')},
        {'check':'92문장 원문/낭독문, 1317단어 문자 범위, 71개 숫자 토큰 보호','result':'passed','evidence':rel(OWN/'alignment_receipt.json')},
        {'check':'응답별 실제 비용 합계와 최종 계정 차분','result':'passed','evidence':rel(OWN/'reconciliation.json')},
        {'check':'실제 청취·연속 재생·독립 QA','result':'not_performed','evidence':None}],
    'native_alignment_numeric_note':{'issue':'마지막 문장부호 끝이 각 PCM 끝보다80ms 늦음; 글자/숫자 발화 범위의 초과 없음',
        'raw_files_changed':False,'proposal_policy':'PCM 참조용 문자 시간만 끝 범위로 제한; 문장/단어는 첫·마지막 실제 글자 범위',
        'evidence':rel(OWN/'verification.json')},
    'assembly_contract':{'own_full_main_assembled':False,'brand_inserted':False,'outro_added_outside_frozen_script':False,
        'main_timeline':'main_concat_without_brand_or_gaps: 15청크 완전 PCM 단순 연결의 제안 원점',
        'cta_timeline':'shared_shorts_cta: 별도0초 원점, 3쇼츠에서 동일 파일 재사용',
        'reference_concat':'all16 reference_concat 시간은 자료용이며 부모의 canonical timeline이 아님',
        'chunk_local_times':'sentences/words의 chunk_local_start_s/end_s',
        'sentence_normalized_characters':'Unicode isalnum만 유지; start 포함/end 제외',
        'native_chunk_arrays':rel(OWN/'native_chunk_alignment.json'),
        'director_responsibility':'브랜드5/10초·전환·필요한 패딩을 한 번만 적용하고 공통 시간표 확정'},
    'actual_listening':False,'continuous_playback':False,'independent_qa_completed':False,
    'open_issue_ids':[],'resolved_issue_ids':['JUN_GENERATION_BLOCK'],
    'unverified_scope':['실제 숫자/고유명사 발음과 문장 경계의 청취 품질','완성본 연속 재생 및 독립 QA'],
    'next_role':'director/editor: canonical 본편 및 쇼츠 조립; qa: 실제 청취와 완성본 검수'}
save('handoff.json',handoff)
assert load(OWN/'handoff.json')['cost']['actual_credit_used']==2208
assert all(sha(ROOT/o['path'])==o['sha256'] for o in handoff['outputs'])
print(json.dumps({'status':'handoff_and_local_verification_ready','sentences':92,'words':1317,'chunks':16,
    'actual_credits':2208,'remaining':14456,'new_tts_requests':0,'input_text_issues':0,
    'punctuation_end_overrun_only_ms':80,'actual_listening':False,'handoff':rel(OWN/'handoff.json')},ensure_ascii=False))
