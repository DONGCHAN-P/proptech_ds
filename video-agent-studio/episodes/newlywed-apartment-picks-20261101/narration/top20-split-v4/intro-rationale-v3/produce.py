"""승인 d884be1c4e38: 인트로 8문장만 무료 생성. 실패 후 자동 재시도 없음."""
from __future__ import annotations
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
EP = OUT.parents[2]
ROOT = EP.parents[2]
SOURCE = EP / 'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json'
AUTH = EP / 'director/top20-split-v4/part1-intro-v3/production_authorization.json'
BASELINE = EP / 'director/top20-split-v4/part1-production-v1/locked_timing.json'
HELPER = EP / 'narration/top20-split-v4/part1-v1/produce.py'
SOURCE_SHA = '0cbd68f79ca4981b13d08b68547811c19102be6594933b3d59617af51168ea5d'
DECISION = 'd884be1c4e38'
SCENE = 'P01-INTRO'
REV = 'top20-split-v4-intro-rationale-v3-free-injoon-atempo135'
spec = importlib.util.spec_from_file_location('intro_general_helpers', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
# 기존 main/prepare/generate/build/authorization은 실행하지 않고 범용 함수의 쓰기 경로만 한정한다.
h.OUT = OUT
assert h.ROOT == ROOT and h.EP == EP
assert (h.VOICE, h.RATE, h.FACTOR, h.SR) == ('ko-KR-InJoonNeural', '+0%', 1.35, 44100)
read, save, sha, rel = h.read, h.save, h.sha, h.rel


def authorize():
    assert sha(SOURCE) == SOURCE_SHA, '확정 원고 SHA 불일치'
    a, d = read(AUTH), read(SOURCE)
    s = a['scope']
    assert a['status'] == 'approved' and a['decision_id'] == DECISION
    assert s['revision'] == d['revision'] == 'intro-rationale-v3'
    assert s['part'] == 1 and s['changed_scene_ids'] == [SCENE]
    assert s['free_InJoon_intro_voice_generation'] is True and s['cash_cap_krw'] == 0
    assert all(s[k] is False for k in ['paid_generation_authorized', 'upload_authorized',
                                      'external_file_export_authorized', 'part2_production_authorized'])
    assert any(v['sha256'] == SOURCE_SHA and ROOT/v['path'] == SOURCE for v in a['artifacts'])
    assert d['scene_id'] == SCENE and len(d['sentences']) == 8
    assert [x['sentence_id'] for x in d['sentences']] == [f'P01-INTRO-V3-{i:02}' for i in range(1, 9)]
    assert all(x['text'] == x['narration_text'] for x in d['sentences'])
    return a, d


def pronounce(text):
    # 기존 helper의 '?' 손상 방지 검사는 승인된 실제 의문문에도 적용된다.
    # 마지막 문장부호만 분리해 같은 발음 함수를 호출하고 동일 문자 위치로 복원한다.
    question = text.endswith('?')
    body = text[:-1] if question else text
    reading, transforms, spans = h.pronounce(body)
    if question:
        spans.append({'source_start':len(body), 'source_end':len(text),
                      'reading_start':len(reading), 'reading_end':len(reading)+1, 'kind':'identity'})
        reading += '?'
    restored = reading
    for t in reversed(transforms):
        assert restored[t['spoken_start']:t['spoken_end']] == t['spoken_text']
        restored = restored[:t['spoken_start']] + t['source_text'] + restored[t['spoken_end']:]
    assert restored == text
    return reading, transforms, spans


def prepare():
    a, d = authorize()
    rows, display_at, reading_at = [], 0, 0
    for i, s in enumerate(d['sentences']):
        reading, transforms, spans = pronounce(s['text'])
        rows.append({'scene_id':SCENE, 'sentence_id':s['sentence_id'], 'text':s['text'],
                     'original_text':s['text'], 'display_text':s['text'], 'reading_text':reading,
                     'transformations':transforms, 'character_mapping':spans,
                     'display_roundtrip_exact':True, 'statement_type':s['statement_type'],
                     'price_role':None, 'screen_switch_id':s['sentence_id'],
                     'scene_display_char_start':display_at, 'scene_display_char_end':display_at+len(s['text']),
                     'scene_reading_char_start':reading_at, 'scene_reading_char_end':reading_at+len(reading),
                     'source_json_pointer':f'/sentences/{i}/text', 'actual_listening':False})
        display_at += len(s['text'])+1
        reading_at += len(reading)+1
    chunks = []
    for suffix, selected in [('HOOK', rows[:1]), ('REST', rows[1:])]:
        asset = f'P01-INTRO-V3-{suffix}'
        body = '\n'.join(r['reading_text'] for r in selected)
        path = OUT/'chunks'/(asset+'.txt')
        h.write_text(path, body)
        chunks.append({'scene_id':SCENE, 'asset_id':asset, 'sentence_ids':[r['sentence_id'] for r in selected],
                       'text':body, 'path':rel(path), 'sha256':sha(path), 'characters':len(body)})
    assert len(chunks) == 2 and sum(len(c['sentence_ids']) for c in chunks) == 8
    assert all(c['characters'] < 1000 for c in chunks)
    brand_info = h.inspect(h.INTRO)
    assert brand_info['frames'] == 5*h.SR
    old = next(s for s in read(BASELINE)['scenes'] if s['scene_id'] == SCENE)
    inputs = {rel(p):sha(p) for p in [SOURCE, AUTH, BASELINE, HELPER, h.INTRO, h.FFMPEG,
                                      h.DEPS/'edge_tts/communicate.py', Path(__file__)]}
    manifest = {'task_id':'intro-rationale-v3-narration', 'created_at':h.stamp(), 'decision_id':DECISION,
                'script_revision':'intro-rationale-v3', 'script_sha256':SOURCE_SHA, 'audio_revision':REV,
                'input_versions':inputs, 'voice':h.VOICE, 'rate':h.RATE, 'postprocess_atempo':h.FACTOR,
                'sample_rate':h.SR, 'sentence_count':8, 'chunk_count':2, 'chunks':chunks,
                'characters':sum(c['characters'] for c in chunks), 'brand_source':brand_info,
                'baseline_intro_duration_s':old['end_s']-old['start_s'],
                'assembly':'full_hook_pcm + unchanged_clean_brand_5s_pcm_once + full_rest_pcm',
                'target_duration_s':None, 'padding_frames':0, 'outro_insertions':0, 'old_body_audio_reused':False,
                'automatic_retry':False, 'paid_api_calls':0, 'cash_cost_krw':0, 'credentials_loaded':False}
    save(OUT/'approval_receipt.json', {'decision_id':DECISION, 'status':'approved', 'recorded_at':h.stamp(),
         'authorization_path':rel(AUTH), 'authorization_sha256':sha(AUTH), 'scope':a['scope'],
         'script_path':rel(SOURCE), 'script_sha256':SOURCE_SHA})
    save(OUT/'sentences.json', {'script_revision':'intro-rationale-v3', 'sentences':rows})
    save(OUT/'pronunciation_ledger.json', {'script_sha256':SOURCE_SHA, 'helper_sha256':sha(HELPER),
         'policy':'원문·표시문 보존, 숫자값 독립 역검사, 변환 문자 위치·반환 원문 기록. 의문문 부호 보존.',
         'sentences':rows, 'transformation_count':sum(len(r['transformations']) for r in rows),
         'numeric_value_count':sum(len(t['independent_values']) for r in rows for t in r['transformations']),
         'actual_pronunciation_listened':False})
    save(OUT/'budget_zero.json', {'decision_id':DECISION, 'currency':'KRW', 'cash_cap':0,
         'estimated_cash_cost':0, 'actual_cash_cost':0, 'provider':'microsoft_edge_consumer_tts',
         'voice':h.VOICE, 'characters':manifest['characters'], 'planned_chunks':2, 'paid_api_calls':0,
         'credentials_loaded':False, 'uploads':0, 'claude_calls':0, 'telegram_calls':0,
         'automatic_retry':False, 'permitted_external_operation':'approved_intro_text_free_synthesis_only'})
    save(OUT/'narration_manifest.json', manifest)
    h.write_text(OUT/'reading_text.txt', '\n\n'.join(c['text'] for c in chunks))
    print(json.dumps({'stage':'prepared', 'sentences':8, 'chunks':2, 'characters':manifest['characters']}, ensure_ascii=False), flush=True)


async def generate():
    authorize()
    sys.path.insert(0, str(h.DEPS))
    import edge_tts
    m = read(OUT/'narration_manifest.json')
    usage = {'provider':'microsoft_edge_consumer_tts', 'edge_tts_version':edge_tts.__version__,
             'python_version':sys.version, 'voice':h.VOICE, 'rate':h.RATE, 'atempo':h.FACTOR,
             'native_boundary':'WordBoundary', 'automatic_retry':False, 'provider_403_retry_disabled':True,
             'paid_api_calls':0, 'cash_cost_krw':0, 'credentials_loaded':False, 'chunks':[]}
    for c in m['chunks']:
        result = await h.generate_chunk(c, edge_tts)
        usage['chunks'].append(result)
        save(OUT/'generation_usage.json', usage)
        print(json.dumps({'stage':'generated', 'asset_id':c['asset_id'], 'raw_duration_s':result['duration_s'],
                          'native_words':result['boundary_count']}, ensure_ascii=False), flush=True)


def build():
    authorize()
    m = read(OUT/'narration_manifest.json')
    rows = read(OUT/'sentences.json')['sentences']
    aligned = [h.align(c, [r for r in rows if r['sentence_id'] in c['sentence_ids']]) for c in m['chunks']]
    hook, rest = aligned
    hook_pcm, rest_pcm, brand_pcm = h.pcm(Path(hook['audio_path'])), h.pcm(Path(rest['audio_path'])), h.pcm(h.INTRO)
    brand_start = len(hook_pcm)//2/h.SR
    brand_end = brand_start + len(brand_pcm)//2/h.SR
    path = OUT/'intro_with_brand.wav'
    h.write_wav(path, hook_pcm+brand_pcm+rest_pcm)
    audio_info = h.inspect(path)
    brand = {'start_s':brand_start, 'duration_s':5.0, 'end_s':brand_end, 'source_path':rel(h.INTRO),
             'source_sha256':sha(h.INTRO), 'insertions':1, 'pcm_unchanged':True}
    words, sentences, chunk_info = [], [], []
    by_id = {r['sentence_id']:r for r in rows}
    for c, a, offset in zip(m['chunks'], aligned, [0.0, brand_end]):
        row_cursors = {sid:0 for sid in c['sentence_ids']}
        native = [b for b in read(ROOT/a['provider_boundaries_path'])['boundaries'] if h.norm(b['text'])]
        assert len(native) == len(a['words'])
        for word, boundary in zip(a['words'], native):
            w = dict(word)
            r = by_id[w['sentence_id']]
            nstart = row_cursors[w['sentence_id']]
            nend = nstart+len(h.norm(w['text']))
            row_cursors[w['sentence_id']] = nend
            w.update(asset_id=c['asset_id'], audio_revision=REV,
                     chunk_normalized_char_start=w['normalized_char_start'], chunk_normalized_char_end=w['normalized_char_end'],
                     normalized_char_start=nstart, normalized_char_end=nend,
                     sentence_normalized_char_start=nstart, sentence_normalized_char_end=nend,
                     normalized_display_char_start=len(h.norm(r['display_text'][:w['display_char_start']])),
                     normalized_display_char_end=len(h.norm(r['display_text'][:w['display_char_end']])),
                     source_char_start=w['display_char_start'], source_char_end=w['display_char_end'],
                     scene_display_char_start=r['scene_display_char_start']+w['display_char_start'],
                     scene_display_char_end=r['scene_display_char_start']+w['display_char_end'],
                     scene_reading_char_start=r['scene_reading_char_start']+w['reading_char_start'],
                     scene_reading_char_end=r['scene_reading_char_start']+w['reading_char_end'],
                     native_offset_ticks=boundary['offset'], native_duration_ticks=boundary['duration'],
                     chunk_local_start_s=w['local_start_s'], chunk_local_end_s=w['local_end_s'],
                     start_s=offset+w['local_start_s'], end_s=offset+w['local_end_s'],
                     global_start_s=offset+w['local_start_s'], global_end_s=offset+w['local_end_s'],
                     local_start_s=offset+w['local_start_s'], local_end_s=offset+w['local_end_s'],
                     source_json_pointer=r['source_json_pointer'], actual_listening=False,
                     confidence='native_provider_metadata_scaled_not_listening_or_forced_alignment_verified')
            words.append(w)
        for s in a['sentence_times']:
            matched = [w for w in words if w['sentence_id'] == s['sentence_id']]
            assert row_cursors[s['sentence_id']] == len(h.norm(s['reading_text']))
            sentences.append({**s, 'scene_id':SCENE, 'asset_id':c['asset_id'], 'audio_revision':REV,
                'start_s':matched[0]['start_s'], 'end_s':matched[-1]['end_s'],
                'local_start_s':matched[0]['start_s'], 'local_end_s':matched[-1]['end_s'],
                'chunk_local_start_s':s['start_s'], 'chunk_local_end_s':s['end_s'],
                'scene_display_char_start':by_id[s['sentence_id']]['scene_display_char_start'],
                'scene_display_char_end':by_id[s['sentence_id']]['scene_display_char_end']})
        chunk_info.append({'asset_id':c['asset_id'], 'sentence_ids':c['sentence_ids'],
            'start_s':offset, 'end_s':offset+a['duration_s'], 'duration_s':a['duration_s'],
            'audio_path':rel(Path(a['audio_path'])), 'audio_sha256':a['audio_sha256'],
            'raw_mp3_path':rel(Path(a['raw_mp3_path'])), 'raw_audio_path':rel(Path(a['raw_audio_path'])),
            'native_boundaries_path':a['provider_boundaries_path'], 'metrics':a['metrics']})
    words_path = OUT/'words.json'
    save(words_path, {'audio_revision':REV, 'audio_path':rel(path), 'audio_sha256':sha(path),
         'time_origin':'intro_with_brand.wav start=0; seconds; brand gap included',
         'normalization':'Unicode isalnum; 0-based half-open Unicode codepoint offsets; normalized_char_* restart each sentence',
         'display_span_policy':'숫자 발음이 여러 토큰이면 원문 숫자 범위를 공유할 수 있음. 표시문은 원문 슬라이스를 사용.',
         'words':words, 'actual_listening':False})
    timing = {'revision':REV, 'audio_revision':REV, 'script_revision':'intro-rationale-v3',
              'script_sha256':SOURCE_SHA, 'scene_id':SCENE, 'start_s':0.0, 'end_s':audio_info['duration_s'],
              'total_s':audio_info['duration_s'], 'duration_s':audio_info['duration_s'],
              'audio_path':rel(path), 'audio_sha256':sha(path), 'brand_intro':brand,
              'sentences':sentences, 'words_file':rel(words_path), 'words_path':rel(words_path),
              'chunks':chunk_info, 'timing_basis':'actual_native_WordBoundary_ticks / 1.35 + measured_PCM_chunk_offsets',
              'duration_basis':'actual_final_PCM_frame_count / 44100', 'is_estimate':False,
              'confidence':'native_provider_metadata_not_listening_or_forced_alignment_verified',
              'actual_listening':False, 'asr_performed':False, 'changed_scene_ids':[SCENE],
              'changed_sentence_ids':[r['sentence_id'] for r in rows],
              'new_length_s':audio_info['duration_s'], 'baseline_intro_duration_s':m['baseline_intro_duration_s'],
              'timing_delta_s':audio_info['duration_s']-m['baseline_intro_duration_s'],
              'last_spoken_end_s':words[-1]['end_s'],
              'natural_tail_after_last_native_word_s':audio_info['duration_s']-words[-1]['end_s'],
              'padding_frames':0, 'outro_insertions':0, 'old_body_audio_reused':False}
    timing['scenes'] = [{'scene_id':SCENE, 'start_s':0.0, 'end_s':timing['total_s'],
                         'duration_s':timing['total_s'], 'sentences':sentences,
                         'timing_basis':timing['timing_basis'], 'audio_revision':REV}]
    save(OUT/'timing_proposals.json', timing)
    verification = verify()
    issue_id = 'INTRO-V3-LISTENING-AND-INTEGRATION'
    save(OUT/f'issue_{issue_id}.json', {'issue_id':issue_id, 'scene_id':SCENE,
         'problem':'실제 청취와 독립 음성 검수 미실시. 공통 타임록·본편 통합은 총괄 담당.',
         'evidence':[rel(OUT/'verification.json'), rel(OUT/'timing_proposals.json')],
         'proposal':'총괄이 필요 시 오프라인 전사 후 숫자·원미구·의문문·접합부·마지막 발음을 청취 검수하고 새 길이로 본문을 이동.',
         'impact':{'new_intro_length_s':timing['total_s'], 'timing_delta_s':timing['timing_delta_s'], 'brand_intro':brand},
         'next_roles':['director', 'editor', 'independent QA'], 'actual_listening':False, 'asr_performed':False})
    artifacts = ['intro_with_brand.wav', 'timing_proposals.json', 'words.json', 'sentences.json',
                 'pronunciation_ledger.json', 'narration_manifest.json', 'budget_zero.json',
                 'generation_usage.json', 'approval_receipt.json', 'verification.json', f'issue_{issue_id}.json', 'produce.py']
    save(OUT/'handoff.json', {'status':'complete_technical_narration_scope', 'decision_id':DECISION,
         'audio_revision':REV, 'audio_path':rel(path), 'audio_sha256':sha(path),
         'artifacts':[rel(OUT/n) for n in artifacts], 'input_versions':m['input_versions'],
         'new_length_s':timing['total_s'], 'total_s':timing['total_s'], 'brand_intro':brand,
         'changed_scene_ids':[SCENE], 'changed_sentence_ids':timing['changed_sentence_ids'],
         'changed_sentences':[{'sentence_id':r['sentence_id'], 'text':r['text']} for r in rows],
         'timing_delta_s':timing['timing_delta_s'], 'baseline_intro_duration_s':m['baseline_intro_duration_s'],
         'validation':verification, 'raw_and_processed_retained':True,
         'unresolved':[rel(OUT/f'issue_{issue_id}.json')], 'actual_listening':False, 'asr_performed':False,
         'paid_api_calls':0, 'cash_cost_krw':0, 'next_role':'director: common timing lock; editor: integration; independent QA: listening',
         'reproduction':'tools/python311/python.exe -B -X utf8 '+rel(OUT/'produce.py')+' all (complete receipts reused; failed provider attempt never retried)',
         'summary':'승인 인트로 8문장·2청크만 생성, hook 전체 뒤 클린 브랜드 5초 1회, rest 전체 자연 꼬리 보존. 실측 전역 시간·원문 문자 매핑 제공. 청취/ASR 미실시, 타임록·본문 이동은 총괄/편집.'})
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json', 'completion_receipt.json'])
    save(OUT/'artifact_manifest.json', {'files':[{'path':rel(p), 'sha256':sha(p), 'bytes':p.stat().st_size} for p in files]})
    save(OUT/'completion_receipt.json', {'status':'complete_technical_narration_scope', 'at':h.stamp(),
         'audio_sha256':sha(path), 'manifest_sha256':sha(OUT/'artifact_manifest.json'), 'code_sha256':sha(Path(__file__)),
         'sentence_count':8, 'chunk_count':2, 'cash_cost_krw':0, 'actual_listening':False})
    print(json.dumps({'stage':'complete', 'total_s':timing['total_s'], 'brand_interval_s':[brand_start, brand_end],
          'timing_delta_s':timing['timing_delta_s'], 'words':len(words), 'handoff':rel(OUT/'handoff.json')}, ensure_ascii=False), flush=True)


def verify():
    _, d = authorize()
    t, w = read(OUT/'timing_proposals.json'), read(OUT/'words.json')['words']
    path = ROOT/t['audio_path']
    data, brand = h.pcm(path), h.pcm(h.INTRO)
    chunks = [h.pcm(ROOT/c['audio_path']) for c in t['chunks']]
    assert data == chunks[0]+brand+chunks[1] and data.count(brand) == 1
    assert t['total_s'] == len(data)//2/h.SR and sha(path) == t['audio_sha256']
    assert [s['text'] for s in t['sentences']] == [s['text'] for s in d['sentences']]
    assert len(t['sentences']) == 8 and len(t['chunks']) == 2
    b = t['brand_intro']
    assert b['duration_s'] == 5 and b['start_s'] == len(chunks[0])//2/h.SR
    assert b['end_s'] == b['start_s']+5 and t['padding_frames'] == t['outro_insertions'] == 0
    for s in t['sentences']:
        matched = [x for x in w if x['sentence_id'] == s['sentence_id']]
        assert h.norm(''.join(x['provider_text'] for x in matched)) == h.norm(s['reading_text'])
        cursor = 0
        for x in matched:
            assert x['sentence_normalized_char_start'] == cursor
            cursor = x['sentence_normalized_char_end']
            assert s['text'][x['display_char_start']:x['display_char_end']] == x['display_text']
            assert s['reading_text'][x['reading_char_start']:x['reading_char_end']] == x['reading_text']
            assert 0 <= x['start_s'] < x['end_s'] <= t['total_s']
            assert x['end_s'] <= b['start_s'] or x['start_s'] >= b['end_s']
        assert cursor == len(h.norm(s['reading_text']))
    assert all(x['end_s'] <= y['start_s']+1e-6 for x, y in zip(w, w[1:]))
    assert t['natural_tail_after_last_native_word_s'] >= 0
    h.ff(['-i', str(path), '-f', 'null', '-'])
    result = {'checked_at':h.stamp(), 'full_decode':'passed', 'exact_pcm_concatenation':True,
              'full_hook_and_rest_samples_retained':True, 'brand_exactly_once':True,
              'native_word_coverage':1.0, 'sentence_count':8, 'chunk_count':2, 'word_count':len(w),
              'display_and_reading_offsets_exact':True, 'sentence_normalized_offsets_cumulative':True,
              'audio':h.inspect(path), 'actual_listening':False, 'asr_performed':False,
              'unverified':'실제 발음·자연스러움·음소 동기와 접합부 청취. Native 시각은 제공자 메타데이터 기반이며 강제정렬 검증 아님.'}
    save(OUT/'verification.json', result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('step', choices=['all', 'prepare', 'generate', 'build', 'verify'])
    step = p.parse_args().step
    try:
        if step in ['all', 'prepare']: prepare()
        if step in ['all', 'generate']: asyncio.run(generate())
        if step in ['all', 'build']: build()
        if step == 'verify': print(json.dumps(verify(), ensure_ascii=False))
    except Exception as e:
        issue = OUT/'issue_INTRO-V3-EXECUTION-FAILED.json'
        save(issue, {'scene_id':SCENE, 'problem':'실행 실패; 자동 재시도 없음', 'error_type':type(e).__name__,
                     'step':step, 'safe_detail':str(e)[:500] if isinstance(e, AssertionError) else '원인 상세는 raw 개별 receipt 참조',
                     'next_role':'director', 'paid_api_calls':0, 'cash_cost_krw':0})
        save(OUT/'handoff.json', {'status':'failed', 'step':step, 'issue_path':rel(issue),
             'actual_listening':False, 'automatic_retry':False, 'cash_cost_krw':0,
             'next_role':'director: 실패 근거 확인 후 허용된 대안 결정'})
        print(json.dumps({'status':'failed', 'error_type':type(e).__name__, 'issue_path':rel(issue)}, ensure_ascii=False), flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
