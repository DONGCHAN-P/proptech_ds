"""지도 기준 두 문장만 무료 생성. 기존 범용 함수 재사용; 자동 재시도 없음."""
from __future__ import annotations
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
EP = OUT.parents[2]
ROOT = EP.parents[2]
SOURCE = EP / 'writer/top20-split-v4/map-clean-v1/criteria_script.json'
AUTH = EP / 'director/top20-split-v4/part1-map-clean-v1/production_authorization.json'
DECISION_FILE = AUTH.with_name('script_decision.json')
HELPER = EP / 'narration/top20-split-v4/part1-v1/produce.py'
STRATEGY = EP / 'narration/top20-split-v4/intro-rationale-v3/produce.py'
SOURCE_SHA = '6fe716bc6454a6c1e564f713b10b7fd2e8022af653c44ba4d4c74a660018c7d4'
DECISION = '291dc0fbeafc'
SCENE = 'P01-CRITERIA'
ASSET = 'P01-CRITERIA'
REV = 'top20-split-v4-map-clean-v1-free-injoon-atempo135'
spec = importlib.util.spec_from_file_location('criteria_general_helpers', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
# 원본 담당 폴더에는 쓰지 않는다. 기존 승인/준비/전체 생성/브랜드/조립 함수는 호출하지 않는다.
h.OUT = OUT
assert h.ROOT == ROOT and h.EP == EP
assert (h.VOICE, h.RATE, h.FACTOR, h.SR) == ('ko-KR-InJoonNeural', '+0%', 1.35, 44100)
read, save, sha, rel = h.read, h.save, h.sha, h.rel


def authorize():
    assert sha(SOURCE) == SOURCE_SHA, '입력 원고 SHA 불일치'
    a, d, decision = read(AUTH), read(SOURCE), read(DECISION_FILE)
    scope = a['scope']
    assert a['status'] == decision['status'] == 'approved'
    assert a['decision_id'] == decision['id'] == DECISION
    assert scope['revision'] == d['revision'] == 'map-clean-v1'
    assert scope['part'] == d['part'] == 1
    assert scope['free_InJoon_criteria_voice_generation'] is True
    assert scope['cash_cap_krw'] == d['cash_cap_krw'] == decision['cash_cap_krw'] == 0
    assert all(scope[k] is False for k in ['paid_generation_authorized', 'upload_authorized',
        'external_file_export_authorized', 'part2_production_authorized'])
    assert a['approval_basis'] == decision['approval_basis'] == 'direct_user_scoped_revision_instruction'
    assert a['exact_generated_wording_user_approval'] is decision['exact_generated_wording_user_approval'] is False
    assert a['script_sha256'] == SOURCE_SHA and ROOT/a['script'] == SOURCE
    assert any(x['sha256'] == SOURCE_SHA and ROOT/x['path'] == SOURCE for x in decision['artifacts'])
    assert d['scene_id'] == SCENE and len(d['sentences']) == 2
    assert [s['sentence_id'] for s in d['sentences']] == [f'{SCENE}-{i:02}' for i in (1, 2)]
    return a, d


def number_checks(rows):
    expected = [['2026', '5', '10', '83', '85'], ['11', '3']]
    checks = []
    for row, values in zip(rows, expected):
        assert re.findall(r'\d+', row['text']) == values
        numeric = [v for t in row['transformations'] for v in t['independent_values']]
        assert [v['source_value'] for v in numeric] == values
        assert [v['decoded_value'] for v in numeric] == values
        for t in row['transformations']:
            if t['independent_values']:
                checks.append({'sentence_id':row['sentence_id'], 'source_text':t['source_text'],
                    'reading_text':t['spoken_text'], 'values':t['independent_values'], 'passed':True})
    assert '이천이십육 년' in rows[0]['reading_text']
    assert '오 월부터 시월까지' in rows[0]['reading_text']
    assert '팔십삼에서 팔십오 제곱미터' in rows[0]['reading_text']
    assert '십일 월 삼 일' in rows[1]['reading_text']
    return checks


def prepare():
    a, d = authorize()
    rows, display_at, reading_at = [], 0, 0
    for i, s in enumerate(d['sentences']):
        reading, transformations, spans = h.pronounce(s['text'])
        row = {'id':s['sentence_id'], 'sentence_id':s['sentence_id'], 'scene_id':SCENE,
            'text':s['text'], 'display_text':s['text'], 'original_text':s['text'], 'reading_text':reading,
            'transformations':transformations, 'character_mapping':spans, 'display_roundtrip_exact':True,
            'statement_type':'existing_displayed_transaction_criteria', 'price_role':None,
            'screen_switch_id':s['sentence_id'], 'source_json_pointer':f'/sentences/{i}/text',
            'scene_display_char_start':display_at, 'scene_display_char_end':display_at+len(s['text']),
            'scene_reading_char_start':reading_at, 'scene_reading_char_end':reading_at+len(reading),
            'actual_listening':False}
        rows.append(row)
        display_at += len(s['text'])+1
        reading_at += len(reading)+1
    checks = number_checks(rows)
    body = '\n'.join(r['reading_text'] for r in rows)
    chunk_path = OUT/'chunks'/(ASSET+'.txt')
    h.write_text(chunk_path, body)
    chunk = {'scene_id':SCENE, 'asset_id':ASSET, 'sentence_ids':[r['sentence_id'] for r in rows],
        'text':body, 'path':rel(chunk_path), 'sha256':sha(chunk_path), 'characters':len(body)}
    assert len(body.encode('utf-8')) < 1000
    inputs = {rel(p):sha(p) for p in [SOURCE, AUTH, DECISION_FILE, HELPER, STRATEGY, Path(__file__),
        h.FFMPEG, h.DEPS/'edge_tts/communicate.py']}
    manifest = {'task_id':'map-clean-v1-criteria-voice-only', 'created_at':h.stamp(),
        'decision_id':DECISION, 'script_revision':'map-clean-v1', 'script_sha256':SOURCE_SHA,
        'audio_revision':REV, 'input_versions':inputs, 'voice':h.VOICE, 'rate':h.RATE,
        'postprocess_atempo':h.FACTOR, 'sample_rate':h.SR, 'sentence_count':2, 'chunk_count':1,
        'chunks':[chunk], 'characters':len(body), 'target_duration_s':None,
        'assembly':'single_full_chunk_all_processed_PCM_samples_retained',
        'padding_frames':0, 'cropped_frames':0, 'brand_insertions':0, 'outro_insertions':0,
        'existing_approved_audio_generated':False, 'automatic_retry':False, 'cash_cost_krw':0,
        'paid_api_calls':0, 'credentials_loaded':False, 'claude_calls':0}
    save(OUT/'sentences.json', {'script_revision':'map-clean-v1', 'sentences':rows})
    save(OUT/'pronunciation_ledger.json', {'script_sha256':SOURCE_SHA, 'helper_sha256':sha(HELPER),
        'policy':'표시문 원문 보존. 발음 변환별 문자 위치·역변환 및 숫자값 독립 역검사.',
        'sentences':rows, 'numeric_checks':checks, 'numeric_value_count':7,
        'all_display_reading_roundtrips_exact':True, 'actual_pronunciation_listened':False})
    save(OUT/'approval_receipt.json', {'decision_id':DECISION, 'status':'scoped_edit_authorized',
        'recorded_at':h.stamp(), 'authorization_path':rel(AUTH), 'authorization_sha256':sha(AUTH),
        'script_decision_path':rel(DECISION_FILE), 'scope':a['scope'],
        'approval_basis':a['approval_basis'], 'exact_generated_wording_user_approval':False,
        'latest_task_authorizes_two_sentence_free_generation':True, 'script_path':rel(SOURCE),
        'script_sha256':SOURCE_SHA})
    save(OUT/'budget_zero.json', {'decision_id':DECISION, 'currency':'KRW', 'cash_cap':0,
        'estimated_cash_cost':0, 'actual_cash_cost':0, 'provider':'microsoft_edge_consumer_tts',
        'voice':h.VOICE, 'rate':h.RATE, 'atempo':h.FACTOR, 'characters':len(body), 'planned_chunks':1,
        'paid_api_calls':0, 'credentials_loaded':False, 'uploads':0, 'claude_calls':0,
        'automatic_retry':False, 'permitted_external_operation':'two_criteria_sentences_free_synthesis_only'})
    save(OUT/'narration_manifest.json', manifest)
    h.write_text(OUT/'reading_text.txt', body)
    print(json.dumps({'stage':'prepared', 'sentences':2, 'chunks':1,
        'characters':len(body), 'numeric_values_checked':7}, ensure_ascii=False), flush=True)


async def generate():
    authorize()
    sys.path.insert(0, str(h.DEPS))
    import edge_tts
    m = read(OUT/'narration_manifest.json')
    assert len(m['chunks']) == 1
    result = await h.generate_chunk(m['chunks'][0], edge_tts)
    save(OUT/'generation_usage.json', {'provider':'microsoft_edge_consumer_tts',
        'edge_tts_version':edge_tts.__version__, 'python_version':sys.version, 'voice':h.VOICE,
        'rate':h.RATE, 'atempo':h.FACTOR, 'native_boundary':'WordBoundary',
        'automatic_retry':False, 'provider_403_retry_disabled':True, 'paid_api_calls':0,
        'cash_cost_krw':0, 'credentials_loaded':False, 'claude_calls':0, 'chunks':[result]})
    print(json.dumps({'stage':'generated', 'raw_duration_s':result['duration_s'],
        'native_words':result['boundary_count']}, ensure_ascii=False), flush=True)


def build():
    authorize()
    m = read(OUT/'narration_manifest.json')
    rows = read(OUT/'sentences.json')['sentences']
    chunk = m['chunks'][0]
    aligned = h.align(chunk, rows)
    path = OUT/'criteria.wav'
    h.write_wav(path, h.pcm(Path(aligned['audio_path'])))
    info = h.inspect(path)
    native_path = ROOT/aligned['provider_boundaries_path']
    native = [b for b in read(native_path)['boundaries'] if h.norm(b['text'])]
    assert len(native) == len(aligned['words'])
    words, sentences, cursors = [], [], {r['sentence_id']:0 for r in rows}
    by_id = {r['sentence_id']:r for r in rows}
    for word, boundary in zip(aligned['words'], native):
        w = dict(word)
        row = by_id[w['sentence_id']]
        start = cursors[w['sentence_id']]
        end = start+len(h.norm(w['provider_text']))
        cursors[w['sentence_id']] = end
        w.update(asset_id=ASSET, audio_revision=REV, word_index=len(words),
            chunk_normalized_char_start=w['normalized_char_start'],
            chunk_normalized_char_end=w['normalized_char_end'],
            normalized_char_start=start, normalized_char_end=end,
            sentence_normalized_char_start=start, sentence_normalized_char_end=end,
            normalized_display_char_start=len(h.norm(row['text'][:w['display_char_start']])),
            normalized_display_char_end=len(h.norm(row['text'][:w['display_char_end']])),
            source_char_start=w['display_char_start'], source_char_end=w['display_char_end'],
            scene_display_char_start=row['scene_display_char_start']+w['display_char_start'],
            scene_display_char_end=row['scene_display_char_start']+w['display_char_end'],
            scene_reading_char_start=row['scene_reading_char_start']+w['reading_char_start'],
            scene_reading_char_end=row['scene_reading_char_start']+w['reading_char_end'],
            native_offset_ticks=boundary['offset'], native_duration_ticks=boundary['duration'],
            start_s=w['local_start_s'], end_s=w['local_end_s'],
            global_start_s=w['local_start_s'], global_end_s=w['local_end_s'],
            source_json_pointer=row['source_json_pointer'], actual_listening=False,
            confidence='native_provider_metadata_scaled_not_listening_or_forced_alignment_verified')
        words.append(w)
    for sentence in aligned['sentence_times']:
        sid = sentence['sentence_id']
        matched = [w for w in words if w['sentence_id'] == sid]
        assert cursors[sid] == len(h.norm(sentence['reading_text']))
        sentences.append({**sentence, 'id':sid, 'scene_id':SCENE, 'audio_revision':REV,
            'words':matched, 'actual_listening':False})
    words_path = OUT/'words.json'
    save(words_path, {'audio_revision':REV, 'audio_path':rel(path), 'audio_sha256':sha(path),
        'time_origin':'criteria.wav start=0; seconds; no inserted gap',
        'normalization':'Unicode isalnum; 0-based half-open Unicode codepoint offsets; sentence offsets restart',
        'native_boundaries_file':rel(native_path), 'words':words, 'actual_listening':False})
    timing = {'revision':REV, 'audio_revision':REV, 'script_revision':'map-clean-v1',
        'script_sha256':SOURCE_SHA, 'scene_id':SCENE, 'audio_path':rel(path), 'audio_sha256':sha(path),
        'start_s':0.0, 'end_s':info['duration_s'], 'total_s':info['duration_s'],
        'duration_s':info['duration_s'], 'sentences':sentences, 'words_file':rel(words_path),
        'native_boundaries_file':rel(native_path), 'chunk_count':1,
        'chunks':[{'asset_id':ASSET, 'start_s':0.0, 'end_s':info['duration_s'],
            'duration_s':info['duration_s'], 'audio_path':rel(Path(aligned['audio_path'])),
            'audio_sha256':aligned['audio_sha256'], 'raw_mp3_path':rel(Path(aligned['raw_mp3_path'])),
            'raw_audio_path':rel(Path(aligned['raw_audio_path'])), 'native_boundaries_path':rel(native_path)}],
        'timing_basis':'actual_native_WordBoundary_ticks / 1.35; criteria.wav local origin=0',
        'duration_basis':'actual_final_PCM_frame_count / 44100', 'is_estimate':False,
        'confidence':'native_provider_metadata_not_listening_or_forced_alignment_verified',
        'actual_listening':False, 'asr_performed':False, 'changed_scene_ids':[SCENE],
        'changed_sentence_ids':[r['sentence_id'] for r in rows],
        'new_length_s':info['duration_s'], 'previous_criteria_audio_length_s':0.0,
        'timing_delta_s':info['duration_s'], 'delta_basis':'new_insert_only; final_placement_owned_by_director',
        'last_spoken_end_s':words[-1]['end_s'],
        'natural_tail_after_last_native_word_s':info['duration_s']-words[-1]['end_s'],
        'target_duration_s':None, 'padding_frames':0, 'cropped_frames':0,
        'brand_insertions':0, 'outro_insertions':0, 'existing_approved_audio_generated':False}
    timing['scenes'] = [{'scene_id':SCENE, 'start_s':0.0, 'end_s':info['duration_s'],
        'duration_s':info['duration_s'], 'timing_basis':timing['timing_basis'],
        'confidence':timing['confidence'], 'audio_revision':REV, 'sentences':sentences}]
    save(OUT/'timing_proposals.json', timing)
    verification = verify()
    issue_id = 'MAP-CLEAN-V1-LISTENING-AND-INTEGRATION'
    issue_path = OUT/f'issue_{issue_id}.json'
    save(issue_path, {'issue_id':issue_id, 'scene_id':SCENE,
        'problem':'실제 청취·독립 음성 검수 및 공통 시간표 반영은 미실시.',
        'evidence':[rel(OUT/'verification.json'), rel(OUT/'timing_proposals.json')],
        'proposal':'두 문장 전체와 자연 꼬리를 삽입. 숫자 2026·5·10·83~85·11월3일 및 마지막 구했습니다 발음을 청취 검수.',
        'impact':{'changed_scene_ids':[SCENE], 'new_length_s':timing['total_s'],
            'timing_delta_s':timing['timing_delta_s'], 'delta_basis':timing['delta_basis']},
        'next_roles':['director', 'editor', 'independent QA'], 'actual_listening':False})
    artifacts = ['criteria.wav', 'timing_proposals.json', 'words.json', 'sentences.json',
        'pronunciation_ledger.json', 'narration_manifest.json', 'approval_receipt.json',
        'budget_zero.json', 'generation_usage.json', 'verification.json', issue_path.name, 'produce.py']
    save(OUT/'handoff.json', {'task_id':m['task_id'], 'role':'narration',
        'status':'complete_technical_narration_scope', 'decision_id':DECISION,
        'input_revisions':m['input_versions'], 'outputs':[rel(OUT/n) for n in artifacts],
        'audio_revision':REV, 'audio_path':rel(path), 'audio_sha256':sha(path),
        'total_s':timing['total_s'], 'new_length_s':timing['total_s'],
        'timing_delta_s':timing['timing_delta_s'], 'delta_basis':timing['delta_basis'],
        'affected_scene_ids':[SCENE], 'changed_scene_ids':[SCENE],
        'changed_sentences':[{'sentence_id':r['sentence_id'], 'text':r['text']} for r in rows],
        'checks':[{'check':'full_decode_PCM_tail_numeric_roundtrip_native_boundaries',
            'result':'passed', 'evidence':rel(OUT/'verification.json')}],
        'open_issue_ids':[issue_id], 'unresolved':[rel(issue_path)],
        'actual_listening':False, 'asr_performed':False, 'cash_cost_krw':0, 'paid_api_calls':0,
        'next_role':'director: common timing lock; editor: full natural-tail integration; independent QA: listening',
        'summary':'지도 기준 2문장·1청크 생성. InJoon +0% / atempo1.35. 전체 PCM과 자연 꼬리 보존. 숫자 7개·원문 역변환·단어 경계·전체 디코드 통과. 청취·공통 타임록 미실시.'})
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json', 'completion_receipt.json'])
    save(OUT/'artifact_manifest.json', {'files':[{'path':rel(p), 'sha256':sha(p),
        'bytes':p.stat().st_size} for p in files]})
    save(OUT/'completion_receipt.json', {'status':'complete_technical_narration_scope',
        'at':h.stamp(), 'audio_sha256':sha(path), 'manifest_sha256':sha(OUT/'artifact_manifest.json'),
        'sentence_count':2, 'chunk_count':1, 'cash_cost_krw':0, 'paid_api_calls':0,
        'credentials_loaded':False, 'claude_calls':0, 'actual_listening':False,
        'total_s':timing['total_s'], 'full_natural_tail_preserved':True})
    print(json.dumps({'stage':'complete', 'total_s':timing['total_s'],
        'sentence_times':[{'id':s['id'], 'start_s':s['start_s'], 'end_s':s['end_s']} for s in sentences],
        'natural_tail_s':timing['natural_tail_after_last_native_word_s'], 'words':len(words),
        'handoff':rel(OUT/'handoff.json'), 'cash_cost_krw':0}, ensure_ascii=False), flush=True)


def verify():
    _, d = authorize()
    t = read(OUT/'timing_proposals.json')
    words = read(OUT/'words.json')['words']
    rows = read(OUT/'sentences.json')['sentences']
    path = ROOT/t['audio_path']
    processed = ROOT/t['chunks'][0]['audio_path']
    data = h.pcm(path)
    assert data == h.pcm(processed), '전체 처리 PCM 샘플 보존 실패'
    assert t['total_s'] == len(data)//2/h.SR and sha(path) == t['audio_sha256']
    assert [s['text'] for s in t['sentences']] == [s['text'] for s in d['sentences']]
    assert len(t['sentences']) == 2 and len(t['chunks']) == 1
    assert t['padding_frames'] == t['cropped_frames'] == t['brand_insertions'] == t['outro_insertions'] == 0
    numeric = number_checks(rows)
    for row, s in zip(rows, t['sentences']):
        restored = row['reading_text']
        for change in reversed(row['transformations']):
            assert restored[change['spoken_start']:change['spoken_end']] == change['spoken_text']
            restored = restored[:change['spoken_start']]+change['source_text']+restored[change['spoken_end']:]
        assert restored == row['text'] == s['text']
        matched = [w for w in words if w['sentence_id'] == s['sentence_id']]
        assert matched == s['words']
        assert h.norm(''.join(w['provider_text'] for w in matched)) == h.norm(s['reading_text'])
        cursor = 0
        for w in matched:
            assert w['sentence_normalized_char_start'] == cursor
            cursor = w['sentence_normalized_char_end']
            assert s['text'][w['display_char_start']:w['display_char_end']] == w['display_text']
            assert s['reading_text'][w['reading_char_start']:w['reading_char_end']] == w['reading_text']
            assert w['start_s'] == w['native_offset_ticks']/1e7/h.FACTOR
            assert w['end_s'] == (w['native_offset_ticks']+w['native_duration_ticks'])/1e7/h.FACTOR
            assert 0 <= w['start_s'] < w['end_s'] <= t['total_s']
        assert cursor == len(h.norm(s['reading_text']))
    assert h.norm(words[-1]['reading_text']) == '구했습니다'
    assert all(x['end_s'] <= y['start_s']+1e-6 for x, y in zip(words, words[1:]))
    assert t['natural_tail_after_last_native_word_s'] >= 0
    # 독립적인 전체 필터 재실행은 로컬 기술 검증이며 외부 합성을 추가 호출하지 않는다.
    raw = ROOT/t['chunks'][0]['raw_audio_path']
    probe = h.subprocess.run([str(h.FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', str(raw),
        '-af', 'atempo=1.35', '-ac', '1', '-ar', str(h.SR), '-c:a', 'pcm_s16le', '-f', 's16le', '-'],
        capture_output=True, creationflags=getattr(h.subprocess, 'CREATE_NO_WINDOW', 0))
    assert probe.returncode == 0 and probe.stdout == data, '전체 atempo 출력과 최종 PCM 불일치'
    h.ff(['-i', str(path), '-f', 'null', '-'])
    info = h.inspect(path)
    assert info['rms_pcm'] > 0 and not info['clip_peak_reached']
    result = {'checked_at':h.stamp(), 'full_decode':'passed',
        'exact_full_processed_PCM_samples_retained':True, 'independent_full_atempo_PCM_match':True,
        'natural_tail_preserved':True, 'native_word_coverage':1.0, 'sentence_count':2,
        'chunk_count':1, 'word_count':len(words), 'numeric_value_count':7,
        'numeric_checks':numeric, 'display_reading_roundtrip_exact':True,
        'display_and_reading_offsets_exact':True, 'sentence_normalized_offsets_cumulative':True,
        'final_native_word':words[-1]['provider_text'], 'last_native_word_end_s':words[-1]['end_s'],
        'natural_tail_after_last_native_word_s':t['natural_tail_after_last_native_word_s'],
        'target_duration_s':None, 'cropped_frames':0, 'padding_frames':0, 'audio':info,
        'actual_listening':False, 'asr_performed':False,
        'unverified':'실제 숫자 발음·문장 경계·자연스러움·끝 음절 청취. 제공자 메타데이터 시각은 강제정렬 검증 아님.'}
    save(OUT/'verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['all', 'prepare', 'generate', 'build', 'verify'])
    step = parser.parse_args().step
    try:
        if step in ['all', 'prepare']: prepare()
        if step in ['all', 'generate']: asyncio.run(generate())
        if step in ['all', 'build']: build()
        if step == 'verify': print(json.dumps(verify(), ensure_ascii=False))
    except Exception as e:
        issue = OUT/'issue_MAP-CLEAN-V1-EXECUTION-FAILED.json'
        save(issue, {'issue_id':'MAP-CLEAN-V1-EXECUTION-FAILED', 'scene_id':SCENE,
            'problem':'실행 실패; 자동 재시도 및 유료 대체 없음', 'error_type':type(e).__name__,
            'step':step, 'safe_detail':str(e)[:700] if isinstance(e, AssertionError) else
                '무료 합성 raw receipt의 error_type/http_status/os_error 또는 로컬 검증 단계 확인',
            'receipt_path':rel(OUT/'raw'/(ASSET+'.receipt.json')), 'next_role':'director',
            'cash_cost_krw':0, 'paid_api_calls':0, 'actual_listening':False})
        save(OUT/'handoff.json', {'task_id':'map-clean-v1-criteria-voice-only', 'role':'narration',
            'status':'failed', 'step':step, 'issue_path':rel(issue), 'affected_scene_ids':[SCENE],
            'actual_listening':False, 'automatic_retry':False, 'cash_cost_krw':0,
            'next_role':'director: 실패 근거 확인 후 허용된 대안 결정'})
        print(json.dumps({'status':'failed', 'error_type':type(e).__name__,
            'issue_path':rel(issue)}, ensure_ascii=False), flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
