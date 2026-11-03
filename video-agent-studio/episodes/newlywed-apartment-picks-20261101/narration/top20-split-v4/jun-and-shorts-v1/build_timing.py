"""확정 원문/낭독문을 새 Jun native character alignment에 연결한다.

기존 무료 음성의 시간은 복사하지 않는다. SHA가 기록된 기존 자료에서는
원문↔낭독문 문자 범위와 변경 전 길이만 재사용한다. 본편/브랜드 조립은 하지 않는다.
"""
from pathlib import Path
import json, hashlib, re, wave, difflib, math

ROOT = Path('C:/projects/realestate_reco')
OWN = Path(__file__).resolve().parent
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
OLD_PATH = EP / 'director/top20-split-v4/part1-map-clean-v1/locked_timing.json'
AUDIO_REVISION = 'top20-split-v4-jun-and-shorts-v1-native097'
MANIFEST_SHA = 'f4bd6d8bfefb3fff65ded62ea8ec013658df5ad1e19cfc1cff836dcc37b7ebe1'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
def save(name, data):
    (OWN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def ref(p):
    return {'path': rel(p), 'sha256': sha(p)}

assert sha(OWN / 'narration_manifest.json') == MANIFEST_SHA
manifest = load(OWN / 'narration_manifest.json')
ledger = load(OWN / 'generation_ledger.json')
assert len(ledger['requests']) == 16 and all(r['status'] == 'complete' for r in ledger['requests'])
assert ledger['actual_credits'] <= 6500 and ledger['automatic_retries'] == 0
assert ledger['header_account_delta_matches'] is True
by_id = {s['sentence_id']: s for s in manifest['sentences']}
receipts = {r['asset_id']: r for r in ledger['requests']}
old = load(OLD_PATH)
old_sentences = old['criteria_sentences'] + [s for sc in old['body_scenes'] for s in sc['sentences']]
old_by_id = {s['sentence_id']: s for s in old_sentences}

def display_map(sentence):
    """반개구간 display→reading 매핑. 비문자 그대로의 숫자 표현은 통째 보호한다."""
    d, t = sentence['text'], sentence['reading_text']
    spans = [None] * len(d)
    for tag, ds, de, rs, re_ in difflib.SequenceMatcher(None, d, t, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(de - ds): spans[ds + k] = [rs + k, rs + k + 1]
        elif tag in ('replace', 'delete'):
            left, right = (rs, re_) if rs < re_ else (max(0, rs - 1), min(len(t), rs + 1))
            for k in range(ds, de): spans[k] = [left, right]
    assert all(x and 0 <= x[0] < x[1] <= len(t) for x in spans)
    prior = old_by_id.get(sentence['sentence_id'])
    mapping_basis = 'literal_or_context_anchored_display_reading_map'
    if prior:
        assert prior.get('display_text', prior['text']) == d and prior['reading_text'] == t
        known = [[] for _ in d]
        for word in prior['words']:
            ds, de = word['display_char_start'], word['display_char_end']
            rs, re_ = word['reading_char_start'], word['reading_char_end']
            assert d[ds:de] == word['display_text'] and t[rs:re_] == word['reading_text']
            for k in range(ds, de):
                # 같은 길이의 문자 그대로인 단어만 글자별 연결한다.
                known[k].append([rs + k - ds, rs + k - ds + 1] if d[ds:de] == t[rs:re_] else [rs, re_])
        for i, options in enumerate(known):
            if options: spans[i] = [min(x[0] for x in options), max(x[1] for x in options)]
        mapping_basis = 'verified_existing_text_spans_only_plus_literal_punctuation_no_old_times'
    protected = []
    for token in re.finditer(r'\S+', d):
        if not re.search(r'[0-9]', token.group()): continue
        ds, de = token.span()
        # 숫자의 내부 쉼표/범위/단위/조사는 유지하고 문장 끝 부호만 제외한다.
        while ds < de and d[ds] in '([{': ds += 1
        while de > ds and d[de-1] in '.,?!;:)]}': de -= 1
        rs, re_ = min(x[0] for x in spans[ds:de]), max(x[1] for x in spans[ds:de])
        for k in range(ds, de): spans[k] = [rs, re_]
        protected.append({'display_text': d[ds:de], 'display_char_start': ds, 'display_char_end': de,
                          'reading_text': t[rs:re_], 'reading_char_start': rs, 'reading_char_end': re_,
                          'split_allowed': False})
    return spans, protected, mapping_basis

sentences, words, chunks, char_chunks, changes, clamps = [], [], [], [], [], []
main_cursor = 0.0
reference_cursor = 0.0
for chunk in manifest['chunks']:
    cid = chunk['asset_id']; receipt = receipts[cid]
    for p, h in receipt['artifact_sha256'].items(): assert sha(ROOT / p) == h
    wav = ROOT / receipt['wav_path']
    with wave.open(str(wav), 'rb') as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (44100, 1, 2)
        sample_count = w.getnframes(); duration = sample_count / 44100
        assert hashlib.sha256(w.readframes(sample_count)).hexdigest() == receipt['pcm_sha256']
    assert duration == receipt['pcm_duration_s']
    alignment_path = OWN / 'raw' / cid / 'alignment.json'
    normalized_path = OWN / 'raw' / cid / 'normalized_alignment.json'
    a, na = load(alignment_path), load(normalized_path)
    text = '\n\n'.join(by_id[sid]['reading_text'] for sid in chunk['sentence_ids'])
    assert ''.join(a['characters']) == text
    assert (ROOT / chunk['path']).read_text(encoding='utf-8') == text
    raw_starts, raw_ends = a['character_start_times_seconds'], a['character_end_times_seconds']
    assert len(text) == len(raw_starts) == len(raw_ends)
    assert all(math.isfinite(s) and math.isfinite(e) and 0 <= s <= e <= duration + .101 for s,e in zip(raw_starts,raw_ends))
    assert all(x <= y for x,y in zip(raw_starts,raw_starts[1:]))
    assert all(x <= y for x,y in zip(raw_ends,raw_ends[1:]))
    for label, arr in [('alignment', a), ('normalized_alignment', na)]:
        assert isinstance(arr, dict), (cid, label)
        assert len(arr['characters']) == len(arr['character_start_times_seconds']) == len(arr['character_end_times_seconds'])
    if max(raw_ends) > duration:
        clamps.append({'asset_id': cid, 'overrun_s': max(raw_ends)-duration,
                       'policy': 'raw 그대로 보존; PCM 참조 시간만 최대 100ms 이내 decoder 끝으로 제한'})
    starts, ends = [min(t, duration) for t in raw_starts], [min(t, duration) for t in raw_ends]
    is_main = cid != 'SHORTS-CTA'
    timeline_id = 'main_concat_without_brand_or_gaps' if is_main else 'shared_shorts_cta'
    offset = main_cursor if is_main else 0.0
    chunk_record = {'asset_id': cid, 'scene_id': cid, 'audio_revision': AUDIO_REVISION, 'timeline_id': timeline_id,
                    'wav_path': rel(wav), 'wav_sha256': sha(wav), 'pcm_sha256': receipt['pcm_sha256'],
                    'raw_audio': ref(ROOT / receipt['raw_audio_path']), 'alignment': ref(alignment_path),
                    'normalized_alignment': ref(normalized_path), 'sample_rate_hz': 44100, 'channels': 1,
                    'sample_count': sample_count, 'duration_s': duration, 'chunk_duration_s': duration,
                    'start_s': offset, 'end_s': offset + duration, 'global_start_s': offset,
                    'global_end_s': offset + duration, 'reference_concat_start_s': reference_cursor,
                    'reference_concat_end_s': reference_cursor + duration, 'sentence_ids': chunk['sentence_ids'],
                    'provider_speed': .97, 'tempo_factor': 1, 'trimmed': False, 'tail_preserved': True,
                    'timing_basis': 'measured_complete_pcm_samples_native_provider_character_alignment',
                    'confidence': 'provider_metadata_and_pcm_verified_not_listening_verified', 'actual_listening': False,
                    'reuse_policy': '동일 파일을 3쇼츠에서 재사용; 추가 CTA 생성 없음' if not is_main else '본편/쇼츠 공용'}
    char_chunks.append({'asset_id': cid, 'audio_revision': AUDIO_REVISION, 'timeline_id': timeline_id,
                        'global_offset_s': offset, 'wav_path': rel(wav), 'duration_s': duration,
                        'alignment': a, 'normalized_alignment': na,
                        'timing_basis': 'unaltered_native_provider_character_arrays_chunk_local_seconds'})
    cursor = 0
    for sid in chunk['sentence_ids']:
        original = by_id[sid]; d, t = original['text'], original['reading_text']; n = len(t)
        assert text[cursor:cursor+n] == t
        significant = [i for i,c in enumerate(t) if c.isalnum()]
        first, last = significant[0], significant[-1]
        local_start, local_end = starts[cursor+first], ends[cursor+last]
        assert 0 <= local_start < local_end <= duration
        mapping, protected, mapping_basis = display_map(original)
        norm = [0]
        for c in t: norm.append(norm[-1] + int(c.isalnum()))
        dnorm = [0]
        for c in d: dnorm.append(dnorm[-1] + int(c.isalnum()))
        sentence = {**original, 'scene_id': cid, 'asset_id': cid, 'chunk_id': cid, 'audio_revision': AUDIO_REVISION,
                    'timeline_id': timeline_id, 'wav_path': rel(wav), 'chunk_duration_s': duration,
                    'chunk_char_start': cursor, 'chunk_char_end': cursor+n,
                    'chunk_local_start_s': local_start, 'chunk_local_end_s': local_end,
                    'local_start_s': local_start, 'local_end_s': local_end,
                    'start_s': offset+local_start, 'end_s': offset+local_end,
                    'global_start_s': offset+local_start, 'global_end_s': offset+local_end,
                    'reference_concat_start_s': reference_cursor+local_start,
                    'reference_concat_end_s': reference_cursor+local_end,
                    'duration_s': local_end-local_start, 'display_text': d,
                    'sentence_normalized_text': ''.join(c for c in t if c.isalnum()),
                    'display_mapping_basis': mapping_basis, 'protected_numeric_spans': protected,
                    'timing_basis': 'new_Jun_native_character_alignment_first_last_alphanumeric_no_tempo_scaling',
                    'confidence': 'provider_metadata_and_pcm_verified_not_listening_verified', 'actual_listening': False}
        sentence_words = []
        for token in re.finditer(r'\S+', t):
            rs, re_ = token.span()
            while rs < re_ and not t[rs].isalnum(): rs += 1
            while re_ > rs and not t[re_-1].isalnum(): re_ -= 1
            if rs == re_: continue
            matched = [i for i,(a_,b_) in enumerate(mapping) if a_ < re_ and b_ > rs and not d[i].isspace()]
            assert matched, (sid, t[rs:re_])
            ds, de = min(matched), max(matched)+1
            st, en = starts[cursor+rs], ends[cursor+re_-1]
            word = {'sentence_id': sid, 'scene_id': cid, 'asset_id': cid, 'chunk_id': cid,
                    'word_index': len(sentence_words), 'text': t[rs:re_], 'reading_text': t[rs:re_],
                    'display_text': d[ds:de], 'reading_char_start': rs, 'reading_char_end': re_,
                    'display_char_start': ds, 'display_char_end': de,
                    'sentence_normalized_char_start': norm[rs], 'sentence_normalized_char_end': norm[re_],
                    'display_normalized_char_start': dnorm[ds], 'display_normalized_char_end': dnorm[de],
                    'chunk_char_start': cursor+rs, 'chunk_char_end': cursor+re_,
                    'chunk_local_start_s': st, 'chunk_local_end_s': en,
                    'local_start_s': st, 'local_end_s': en, 'start_s': offset+st, 'end_s': offset+en,
                    'global_start_s': offset+st, 'global_end_s': offset+en, 'timeline_id': timeline_id,
                    'audio_revision': AUDIO_REVISION,
                    'timing_basis': 'new_native_provider_character_span_no_old_time_reuse', 'actual_listening': False}
            assert sentence['chunk_local_start_s'] <= st <= en <= sentence['chunk_local_end_s']
            assert ''.join(c for c in t[rs:re_] if c.isalnum()) == sentence['sentence_normalized_text'][norm[rs]:norm[re_]]
            sentence_words.append(word); words.append(word)
        sentence['words'] = sentence_words
        sentence['reading_character_timing'] = {'characters': list(t),
             'chunk_local_start_times_seconds': starts[cursor:cursor+n], 'chunk_local_end_times_seconds': ends[cursor:cursor+n],
             'native_chunk_char_start': cursor}
        sentence['display_character_timing'] = {
            'characters': list(d), 'reading_char_spans': mapping,
            'chunk_local_start_times_seconds': [starts[cursor+r[0]] for r in mapping],
            'chunk_local_end_times_seconds': [ends[cursor+r[1]-1] for r in mapping],
            'nonliteral_number_policy': '숫자·단위 토큰 전체를 대응 낭독 범위로 묶음; 임의 비례 보간 없음'}
        for p in protected:
            p['chunk_local_start_s'] = starts[cursor+p['reading_char_start']]
            p['chunk_local_end_s'] = ends[cursor+p['reading_char_end']-1]
        sentences.append(sentence); cursor += n+2
    assert cursor-2 == len(text)
    chunks.append(chunk_record)
    if is_main: main_cursor += duration
    reference_cursor += duration

assert len(sentences) == 92 and len({s['sentence_id'] for s in sentences}) == 92
assert sum(len(x['alignment']['characters']) for x in char_chunks) == 5520
assert len([s for s in sentences if s['kind'] == 'accepted_main']) == 90
old_durations = {s['scene_id']: s['duration_s'] for s in old['body_scenes']}
for c in chunks:
    previous = old_durations.get(c['asset_id'])
    changes.append({'scene_id': c['scene_id'], 'changed_sentence_ids': c['sentence_ids'],
        'text_changed': False, 'voice_changed': True, 'new_duration_s': c['duration_s'],
        'previous_duration_s': previous, 'timing_delta_s': c['duration_s']-previous if previous is not None else None,
        'previous_duration_basis': '기존 body scene 구간; 전환 포함 여부가 달라 음성 길이와 직접 동일시하지 않음' if previous else '동일 청크 경계의 이전 값 없음',
        'new_audio_path': c['wav_path']})
metadata = {'audio_revision': AUDIO_REVISION, 'manifest': ref(OWN/'narration_manifest.json'),
    'source_text_mapping_only': ref(OLD_PATH), 'actual_listening': False, 'continuous_playback': False,
    'timeline_policy': 'main_concat_without_brand_or_gaps는 15청크의 완전 PCM 단순 연결 기준. SHORTS-CTA는 별도 0초 원점. reference_concat은 16청크 자료용 연결 기준이며 편집 확정 시간 아님.',
    'global_times_provisional_assembly_offsets': True, 'timing_locked_by_director': False,
    'normalized_character_policy': 'Unicode isalnum만 유지; 공백·문장부호 제외; 모든 범위는 start 포함/end 제외',
    'native_arrays_preserved': True, 'tempo_factor': 1, 'provider_speed': .97, 'trimmed': False,
    'main_full_chunk_duration_s': main_cursor, 'shared_cta_duration_s': chunks[-1]['duration_s'],
    'all16_full_chunk_duration_s': reference_cursor, 'sentence_count': 92, 'word_count': len(words),
    'character_count': 5520, 'decoder_boundary_clamps': clamps,
    'display_mapping_reused_sentence_count': sum(s['sentence_id'] in old_by_id for s in sentences),
    'protected_numeric_span_count': sum(len(s['protected_numeric_spans']) for s in sentences)}
save('sentences.json', {'metadata': metadata, 'sentences': sentences})
save('words.json', {'metadata': metadata, 'words': words})
save('native_chunk_alignment.json', {'metadata': metadata, 'chunks': char_chunks})
save('scene_chunk_durations.json', {'metadata': metadata, 'chunks': chunks})
save('timing_proposals.json', {**metadata, 'status': 'measured_native_alignment_proposals_not_director_locked',
    'chunks': chunks, 'sentences': sentences, 'changed_scene_ids': [c['scene_id'] for c in chunks], 'changes': changes})
save('alignment_receipt.json', {'status': 'all92_mapped_to_new_native_char_alignment', 'metadata': metadata,
    'outputs': [ref(OWN/name) for name in ['sentences.json','words.json','native_chunk_alignment.json','scene_chunk_durations.json','timing_proposals.json']],
    'all16_pcm_sha_verified': True, 'all92_display_reading_preserved': True,
    'all_ascii_numeric_tokens_protected': True, 'old_times_copied_to_new_alignment': False,
    'actual_credits': ledger['actual_credits'], 'actual_listening': False, 'continuous_playback': False})
print(json.dumps({'status': 'all92_mapped', 'sentences': len(sentences), 'words': len(words),
    'main_duration_s': main_cursor, 'cta_duration_s': chunks[-1]['duration_s'],
    'protected_numeric_spans': metadata['protected_numeric_span_count'], 'actual_listening': False}, ensure_ascii=False))
