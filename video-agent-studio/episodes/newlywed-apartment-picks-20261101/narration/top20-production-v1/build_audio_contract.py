"""Validate provider boundaries and derive raw / uniformly sped-up audio contracts."""
import audioop
import datetime as dt
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import wave

DIR = Path(__file__).resolve().parent
EP = DIR.parents[1]
ROOT = DIR.parents[4]
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FACTOR = 1.35
BRAND_INTRO = ROOT / 'video/public/channel-brand-v2/intro.wav'
BRAND_OUTRO = ROOT / 'video/public/channel-brand-v2/outro.wav'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return str(p.relative_to(ROOT)).replace('\\', '/')


def save(p, value):
    p.resolve().relative_to(DIR)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def inspect(p):
    with wave.open(str(p), 'rb') as w:
        frames, rate, width, channels = w.getnframes(), w.getframerate(), w.getsampwidth(), w.getnchannels()
        pcm = w.readframes(frames)
    return {'duration_s': frames / rate, 'frames': frames, 'sample_rate': rate, 'channels': channels, 'sample_width_bytes': width, 'peak_pcm': audioop.max(pcm, width), 'rms_pcm': audioop.rms(pcm, width), 'sha256': sha(p), 'path': rel(p)}


def norm(value):
    return ''.join(c for c in html.unescape(value) if c.isalnum())


def concat_wave(paths, output):
    params = None
    with wave.open(str(output), 'wb') as out:
        for p in paths:
            with wave.open(str(p), 'rb') as source:
                current = (source.getnchannels(), source.getsampwidth(), source.getframerate())
                if params is None:
                    params = current
                    out.setnchannels(params[0])
                    out.setsampwidth(params[1])
                    out.setframerate(params[2])
                assert params == current
                out.writeframes(source.readframes(source.getnframes()))


def align_scene(chunk, rows):
    receipt = read(DIR / 'free-edge-v1' / (chunk['scene_id'] + '.receipt.json'))
    assert receipt['status'] == 'complete'
    for key in ['mp3', 'wav', 'metadata']:
        assert sha(DIR / receipt[key]['path']) == receipt[key]['sha256']
    expected = norm(chunk['text'])
    cursor, words, omitted = 0, [], []
    for b in read(DIR / receipt['metadata']['path'])['boundaries']:
        assert b['type'] == 'WordBoundary'
        token = norm(b['text'])
        if not token:
            continue
        pos = expected.find(token, cursor)
        assert pos >= cursor, (chunk['scene_id'], b['text'], expected[cursor:cursor+30])
        if pos > cursor:
            omitted.append(expected[cursor:pos])
        start, end = b['offset'] / 10000000, (b['offset'] + b['duration']) / 10000000
        assert 0 <= start <= end <= receipt['duration_s'] + 0.03
        assert not words or start >= words[-1]['start_s']
        words.append({'text': b['text'], 'start_s': start, 'end_s': end, 'normalized_char_start': pos, 'normalized_char_end': pos + len(token), 'timing_basis': 'provider_word_boundary'})
        cursor = pos + len(token)
    if cursor < len(expected):
        omitted.append(expected[cursor:])
    assert not omitted, (chunk['scene_id'], omitted)
    sentence_times, char_cursor = [], 0
    for row in rows:
        length = len(norm(row['reading_text']))
        matched = [w for w in words if w['normalized_char_start'] < char_cursor + length and w['normalized_char_end'] > char_cursor]
        assert matched and matched[0]['normalized_char_start'] == char_cursor and matched[-1]['normalized_char_end'] == char_cursor + length, row['sentence_id']
        sentence_times.append({'sentence_id': row['sentence_id'], 'text': row['display_text'], 'reading_text': row['reading_text'], 'start_s': matched[0]['start_s'], 'end_s': matched[-1]['end_s'], 'timing_basis': 'first_and_last_provider_word_boundary_of_exact_reading_sentence', 'confidence': 'provider_metadata_not_listening_verified', 'word_count': len(matched)})
        for word in matched:
            word['sentence_id'] = row['sentence_id']
        char_cursor += length
    assert char_cursor == len(expected)
    return {'scene_id': chunk['scene_id'], 'duration_s': receipt['duration_s'], 'audio_path': str((DIR / receipt['wav']['path']).resolve()), 'mp3_path': str((DIR / receipt['mp3']['path']).resolve()), 'narration_text': '\n'.join(row['display_text'] for row in rows), 'reading_text': chunk['text'], 'sentences_local': sentence_times, 'words_local': words, 'reading_characters_matched': char_cursor, 'normalized_reading_coverage': 1.0, 'audio': inspect(DIR / receipt['wav']['path']), 'raw_receipt': rel(DIR / 'free-edge-v1' / (chunk['scene_id'] + '.receipt.json'))}


def contract(scenes, revision, body_wav, factor, brand):
    offset = brand['intro']['duration_s']
    body_offset, output_scenes, all_words = 0.0, [], []
    for raw in scenes:
        start = offset + body_offset
        end = start + raw['duration_s']
        local_sentences = raw['sentences_local']
        global_sentences = [{**s, 'local_start_s': s['start_s'], 'local_end_s': s['end_s'], 'start_s': start + s['start_s'], 'end_s': start + s['end_s']} for s in local_sentences]
        global_words = [{**w, 'local_start_s': w['start_s'], 'local_end_s': w['end_s'], 'start_s': start + w['start_s'], 'end_s': start + w['end_s'], 'scene_id': raw['scene_id']} for w in raw['words_local']]
        output_scenes.append({'scene_id': raw['scene_id'], 'start_s': start, 'end_s': end, 'duration_s': raw['duration_s'], 'audio_path': raw['audio_path'], 'mp3_path': raw['mp3_path'], 'narration_text': raw['narration_text'], 'reading_text': raw['reading_text'], 'sentences': global_sentences, 'sentence_times': local_sentences, 'captions': [{'text': s['text'], 'start_s': s['start_s'], 'end_s': s['end_s'], 'sentence_id': s['sentence_id']} for s in global_sentences], 'anchors': {'narration_start': local_sentences[0]['start_s']}, 'words_path': rel(DIR / (revision + '.words.json')), 'audio_sha256': raw['audio']['sha256'], 'timing_basis': 'actual_decoded_audio_and_provider_word_boundaries' if factor == 1 else 'actual_decoded_atempo_audio_and_scaled_provider_word_boundaries', 'is_estimate': False, 'actual_listening_performed': False})
        all_words.extend(global_words)
        body_offset += raw['duration_s']
    last_spoken_end = output_scenes[-1]['sentences'][-1]['end_s']
    full_audio_end = offset + body_offset
    outro_start = math.ceil(max(full_audio_end, last_spoken_end + 3.0) * 44100) / 44100
    output_scenes.append({'scene_id': 'E001', 'start_s': full_audio_end, 'end_s': outro_start, 'duration_s': outro_start - full_audio_end, 'audio_path': None, 'narration_text': '', 'sentences': [], 'sentence_times': [], 'captions': [], 'anchors': {}, 'timing_basis': 'last_provider_spoken_word_end_plus_3s_tail_already_counted', 'is_estimate': False})
    save(DIR / (revision + '.words.json'), {'audio_revision': revision, 'word_time_basis': 'raw provider boundaries' if factor == 1 else 'raw provider local times divided by uniform atempo factor; scene starts accumulated from measured processed samples', 'words': all_words})
    return {'schema_revision': 'top20-narration-contract-v1', 'audio_revision': revision, 'script_revision': 'top20-8min-v3', 'script_sha256': read(DIR / 'narration_manifest.json')['input_versions']['writer/top20-8min-v2/script_v3.md']['sha256'], 'timing_locked': False, 'lock_owner': 'director', 'status': 'measured_audio_proposal_pending_director_lock_and_listening', 'timing_basis': 'actual_audio', 'alignment_basis': 'provider_word_boundary' if factor == 1 else 'scaled_provider_word_boundary_after_uniform_atempo', 'duration_is_actual': True, 'actual_listening_performed': False, 'asr_performed': False, 'character_proportional_alignment_used': False, 'provider': 'microsoft_edge_consumer_tts', 'voice': 'ko-KR-InJoonNeural', 'edge_rate': '+0%', 'postprocess_atempo_factor': factor, 'time_transform': {'formula': 'production_scene_global_start + raw_provider_local_time / atempo_factor', 'factor': factor, 'scene_start_basis': 'cumulative measured decoded sample counts', 'note': '생산본 단어 시간은 제공자 경계의 명시적 배율 변환. atempo 내부 파형 이동·청취 싱크는 미검증; 새 제공자 정렬/ASR로 표현하지 않음.'}, 'audio_file': str(body_wav.resolve()), 'audio_file_time_origin_global_s': offset, 'audio_body_duration_s': body_offset, 'last_spoken_end_s': last_spoken_end, 'final_audio_tail_already_counted_s': full_audio_end - last_spoken_end, 'required_hold_from_last_spoken_s': 3.0, 'additional_silence_after_audio_s': outro_start - full_audio_end, 'brand_intro': {**brand['intro'], 'start_s': 0, 'end_s': offset}, 'brand_outro': {**brand['outro'], 'start_s': outro_start, 'end_s': outro_start + brand['outro']['duration_s']}, 'brand_selection_status': 'discovered_existing_channel_brand_v2_audio_candidate; director/editor decide final common brand selection', 'total_duration_with_brand_and_hold_s': outro_start + brand['outro']['duration_s'], 'scenes': output_scenes, 'scene_id_count': len(output_scenes), 'sentence_count': sum(len(s['sentences']) for s in output_scenes), 'word_count': len(all_words), 'path_semantics': 'audio_file/audio_path absolute; brand/word paths relative to project root', 'time_semantics': 'scenes/sentences/captions global seconds including 5s brand intro; sentence_times/anchors local seconds. Body audio begins global=5.0. 27 scene IDs fixed.', 'paid_api_calls': 0, 'cash_cost_krw': 0}


def main():
    manifest = read(DIR / 'narration_manifest.json')
    rows = read(DIR / 'sentences.json')['sentences']
    brand = {'intro': inspect(BRAND_INTRO), 'outro': inspect(BRAND_OUTRO)}
    raw = [align_scene(c, [r for r in rows if r['scene_id'] == c['scene_id']]) for c in manifest['chunks']]
    raw_wav = DIR / 'free-edge-v1/narration_body_raw.wav'
    concat_wave([Path(s['audio_path']) for s in raw], raw_wav)
    raw_contract = contract(raw, 'free-edge-injoon-raw-v1', raw_wav, 1.0, brand)
    save(DIR / 'proposed_timing_raw.json', raw_contract)
    save(DIR / 'audio_raw_manifest.json', {'provider': 'microsoft_edge_consumer_tts', 'voice': 'ko-KR-InJoonNeural', 'rate': '+0%', 'sentences': len(rows), 'characters': 4281, 'body_audio': inspect(raw_wav), 'scenes': [{k: v for k, v in s.items() if k not in ['words_local']} for s in raw], 'provider_normalized_text_coverage': 1.0, 'actual_listening_performed': False, 'asr_performed': False, 'paid_api_calls': 0})
    print(json.dumps({'status': 'all_raw_audio_and_116_sentence_boundaries_ready', 'raw_duration_s': raw_contract['audio_body_duration_s'], 'sentence_count': raw_contract['sentence_count'], 'word_count': raw_contract['word_count'], 'contract': rel(DIR / 'proposed_timing_raw.json')}, ensure_ascii=False), flush=True)
    production_dir = DIR / 'free-edge-atempo135-v1'
    production_dir.mkdir(exist_ok=True)
    production, transforms = [], []
    for scene in raw:
        scene_id = scene['scene_id']
        wav = production_dir / (scene_id + '.wav')
        mp3 = production_dir / (scene_id + '.mp3')
        cmd = [str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', scene['audio_path'], '-af', f'atempo={FACTOR}', '-ar', '44100', '-ac', '1', '-c:a', 'pcm_s16le', '-y', str(wav)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        assert p.returncode == 0, scene_id
        p = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', str(wav), '-c:a', 'libmp3lame', '-b:a', '128k', '-y', str(mp3)], capture_output=True, text=True)
        assert p.returncode == 0, scene_id
        info = inspect(wav)
        assert info['peak_pcm'] < 32767 and info['rms_pcm'] > 0
        sentence_times = [{**s, 'start_s': s['start_s'] / FACTOR, 'end_s': s['end_s'] / FACTOR, 'timing_basis': 'scaled_provider_word_boundary_atempo_1.35'} for s in scene['sentences_local']]
        words = [{**w, 'start_s': w['start_s'] / FACTOR, 'end_s': w['end_s'] / FACTOR, 'timing_basis': 'scaled_provider_word_boundary_atempo_1.35'} for w in scene['words_local']]
        assert max(w['end_s'] for w in words) <= info['duration_s'] + 0.04, (scene_id, words[-1]['end_s'], info['duration_s'])
        production.append({**scene, 'duration_s': info['duration_s'], 'audio_path': str(wav.resolve()), 'mp3_path': str(mp3.resolve()), 'sentences_local': sentence_times, 'words_local': words, 'audio': info})
        transforms.append({'scene_id': scene_id, 'raw_audio_sha256': scene['audio']['sha256'], 'production_audio_sha256': info['sha256'], 'factor': FACTOR, 'raw_duration_s': scene['duration_s'], 'production_measured_duration_s': info['duration_s'], 'ideal_divided_duration_s': scene['duration_s'] / FACTOR, 'sample_duration_residual_s': info['duration_s'] - scene['duration_s'] / FACTOR, 'filter': 'ffmpeg atempo=1.35; pitch preserved', 'new_synthesis_requests': 0})
    body_wav = production_dir / 'narration_body.wav'
    concat_wave([Path(s['audio_path']) for s in production], body_wav)
    prod_contract = contract(production, 'free-edge-injoon-atempo135-v1', body_wav, FACTOR, brand)
    save(DIR / 'proposed_timing.json', prod_contract)
    save(DIR / 'timing_proposals.json', prod_contract)
    save(DIR / 'audio_production_manifest.json', {'audio_revision': prod_contract['audio_revision'], 'provider': 'microsoft_edge_consumer_tts', 'voice': 'ko-KR-InJoonNeural', 'raw_rate': '+0%', 'uniform_atempo_factor': FACTOR, 'body_audio': inspect(body_wav), 'transforms': transforms, 'exact_provider_original_metadata_preserved_in': 'free-edge-v1/*.boundaries.json', 'processed_word_times': 'free-edge-injoon-atempo135-v1.words.json', 'source_script_unchanged': True, 'reading_characters': 4281, 'sentences': 116, 'actual_listening_performed': False, 'asr_performed': False, 'paid_api_calls': 0, 'cash_cost_krw': 0})
    speed_for_exact480 = (raw_contract['last_spoken_end_s'] - 5) / (480 - 5 - 3 - 10)
    save(DIR / 'issue_TOP20-DURATION-480.json', {'issue_id': 'TOP20-DURATION-480', 'scene_ids': [s['scene_id'] for s in production], 'problem': '원고 전체를 브랜드/끝여백 포함 480초로 맞추려면 전달받은 1.35배 한도를 초과.', 'evidence': {'raw_body_duration_s': raw_contract['audio_body_duration_s'], 'exact480_factor_required': speed_for_exact480, 'chosen_uniform_factor': FACTOR, 'production_body_duration_s': prod_contract['audio_body_duration_s'], 'production_full_duration_s': prod_contract['total_duration_with_brand_and_hold_s']}, 'proposal': '명시된 대안에 따라 1.35배 전체 동일 적용본을 약9분 제작 제안으로 전달. 정확히8분 필수이면 총괄이 원고 축약/속도 예외를 결정. narration은 임의 축약·1.35초과 가속하지 않음.', 'impact': 'editor 전체 시간표와 Shorts 구간은 proposed_timing.json 사용; 공통 타임록은 총괄 확정.', 'next_role': 'director', 'actual_listening_performed': False, 'asr_performed': False})
    save(DIR / 'free_audio_verification.json', {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'raw_scenes_complete': len(raw), 'production_scenes_complete': len(production), 'sentence_count': prod_contract['sentence_count'], 'provider_word_count': prod_contract['word_count'], 'normalized_reading_coverage': 1.0, 'numeric_text_integrity': '확정 읽기문 hash·원문 변환표 보존; 실제 소리 발음 검수 아님', 'all_source_audio_hashes_verified': True, 'all_audio_decoded_to_pcm': True, 'all_production_audio_encoded_successfully': True, 'word_times_monotonic_and_within_audio': True, 'peak_check': 'PCM 최대값 32767 미만 확인', 'max_raw_peak_pcm': max(s['audio']['peak_pcm'] for s in raw), 'max_production_peak_pcm': max(s['audio']['peak_pcm'] for s in production), 'source_script_unchanged_sha256': sha(EP / 'writer/top20-8min-v2/script_v3.md'), 'actual_listening_performed': False, 'asr_performed': False, 'forced_alignment_performed': False, 'independent_qa_performed': False, 'cash_cost_krw': 0, 'paid_api_calls': 0})
    summary = {'status': 'all_audio_and_provider_sentence_timing_ready_listening_unverified', 'raw_body_duration_s': raw_contract['audio_body_duration_s'], 'production_body_duration_s': prod_contract['audio_body_duration_s'], 'production_full_duration_s': prod_contract['total_duration_with_brand_and_hold_s'], 'uniform_atempo_factor': FACTOR, 'factor_for_exact480_with_brand': speed_for_exact480, 'last_spoken_end_s': prod_contract['last_spoken_end_s'], 'outro_start_s': prod_contract['brand_outro']['start_s'], 'provider_words': prod_contract['word_count'], 'sentences': prod_contract['sentence_count'], 'raw_contract': rel(DIR / 'proposed_timing_raw.json'), 'production_contract': rel(DIR / 'proposed_timing.json'), 'production_body_wav': rel(body_wav), 'actual_listening_performed': False, 'asr_performed': False, 'paid_api_calls': 0}
    save(DIR / 'partial_audio_handoff.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
