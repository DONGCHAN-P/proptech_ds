"""Local sample-exact sentence cuts from frozen 1.35x WAVs; no TTS/network."""
import array
import audioop
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

DIR = Path(__file__).resolve().parent
OUT = DIR / 'production-v2'
EP = DIR.parents[1]
ROOT = DIR.parents[4]
DIRECTOR = EP / 'director/top20-production-v1'
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
SR = 44100


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


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


def pcm_read(p):
    with wave.open(str(p), 'rb') as w:
        assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, SR, 2)
        return w.readframes(w.getnframes())


def pcm_write(p, pcm):
    with wave.open(str(p), 'wb') as w:
        w.setparams((1, 2, SR, 0, 'NONE', 'not compressed'))
        w.writeframes(pcm)


def cut_boundary(pcm, left_sentence, right_sentence, scene_id):
    left, right = left_sentence['end_s'], right_sentence['start_s']
    assert right > left
    # Guard both native-provider boundaries. Select actual quiet PCM within the gap.
    lo = math.ceil((left + 0.04) * SR)
    hi = math.floor((right - 0.04) * SR)
    midpoint = round((left + right) / 2 * SR)
    window = round(0.020 * SR)
    half = window // 2
    if hi - lo < window:
        frame = midpoint
        search_status = 'gap_shorter_than_20ms_plus_two_40ms_guards'
    else:
        candidates = range(lo + half, hi - half + 1, max(1, round(0.002 * SR)))
        frame = min(candidates, key=lambda f: (audioop.rms(pcm[(f-half)*2:(f+half)*2], 2), abs(f-midpoint)))
        # Choose a near-zero sample inside that quiet window; no waveform stretching/fade.
        radius = round(0.003 * SR)
        samples = array.array('h', pcm[(frame-radius)*2:(frame+radius+1)*2])
        j = min(range(len(samples)), key=lambda n: (abs(samples[n]), abs(n-radius)))
        frame = frame - radius + j
        search_status = 'lowest_rms_20ms_window_then_near_zero_sample'
    sample_window = pcm[max(0, frame-half)*2:(frame+half)*2]
    rms = audioop.rms(sample_window, 2)
    peak = audioop.max(sample_window, 2)
    sample_value = array.array('h', pcm[frame*2:(frame+1)*2])[0]
    return frame, {
        'scene_id': scene_id, 'between_sentence_ids': [left_sentence['sentence_id'], right_sentence['sentence_id']],
        'provider_predicted_gap_start_s': left, 'provider_predicted_gap_end_s': right,
        'provider_predicted_gap_duration_s': right-left,
        'selected_source_frame': frame, 'selected_source_time_s': frame/SR,
        'metadata_margin_after_left_word_s': frame/SR-left,
        'metadata_margin_before_right_word_s': right-frame/SR,
        'pcm_probe_window_s': 0.020, 'pcm_rms': rms, 'pcm_peak': peak,
        'pcm_rms_dbfs': 20*math.log10(rms/32768) if rms else None,
        'pcm_sample_value_at_cut': sample_value, 'selection': search_status,
        'actual_listening_verified': False,
        'true_phonetic_boundary_error_s': None,
        'uncertainty_note': '관측한 무음/저신호 PCM과 제공자 배율 경계의 간격이다. ASR·실제 청취로 측정한 음소 오차 범위는 아니다.',
    }


def main():
    OUT.mkdir(exist_ok=True)
    plan_path = DIRECTOR / 'editorial_cut_plan.json'
    scene_path = DIRECTOR / 'scene_proposals_v4.json'
    script_path = DIRECTOR / 'script_v4.md'
    plan, v4, source = read(plan_path), read(scene_path), read(DIR / 'proposed_timing.json')
    assert source['postprocess_atempo_factor'] == 1.35
    assert source['audio_revision'] == plan['source_audio_revision']
    assert sha(script_path) == plan['script_v4_sha256']
    assert sha(EP / 'writer/top20-8min-v2/scene_proposals_v3.json') == plan['source_sha256']
    drop, keep = set(plan['drop_sentence_ids']), set(plan['keep_sentence_ids'])
    assert len(drop) == 13 and len(keep) == 103 and not drop & keep
    expected = [(t['sentence_id'], s['scene_id'], t['text']) for s in v4['scenes'] for t in s.get('sentences', [])]
    assert [i for i, _, _ in expected] == plan['keep_sentence_ids']
    source_sentence_rows = read(DIR / 'sentences.json')['sentences']
    retained_text = [r for r in source_sentence_rows if r['sentence_id'] in keep]
    assert [(r['sentence_id'], r['scene_id'], r['display_text']) for r in retained_text] == expected
    # Freeze ALL current v1 audio/timing inputs; this script never writes to these paths.
    frozen_paths = [p for directory in ['free-edge-v1', 'free-edge-atempo135-v1'] for p in (DIR / directory).glob('*') if p.is_file()]
    frozen_paths += [DIR/n for n in ['proposed_timing.json', 'proposed_timing_raw.json', 'timing_proposals.json', 'free-edge-injoon-raw-v1.words.json', 'free-edge-injoon-atempo135-v1.words.json', 'audio_raw_manifest.json', 'audio_production_manifest.json']]
    frozen = {rel(p): sha(p) for p in frozen_paths}
    save(OUT / 'v1_frozen_inputs.json', {'at_utc': stamp(), 'files': frozen})
    source_words = read(DIR / 'free-edge-injoon-atempo135-v1.words.json')['words']
    offset_frames = round(source['brand_intro']['duration_s'] * SR)
    body_frames = 0
    scenes, words_all, cuts_all, groups_all, wavs = [], [], [], [], []
    for original_scene in source['scenes']:
        scene_id = original_scene['scene_id']
        if not original_scene['sentence_times']:
            assert scene_id == 'E001'
            continue
        source_audio = Path(original_scene['audio_path'])
        assert sha(source_audio) == original_scene['audio_sha256']
        pcm = pcm_read(source_audio)
        source_frames = len(pcm)//2
        source_sentences = original_scene['sentence_times']
        selected_indices = [i for i,s in enumerate(source_sentences) if s['sentence_id'] in keep]
        assert selected_indices
        runs = []
        for index in selected_indices:
            if not runs or index != runs[-1][-1]+1:
                runs.append([index])
            else:
                runs[-1].append(index)
        groups, new_pcm = [], b''
        cuts = []
        for run in runs:
            first, last = run[0], run[-1]
            if first == 0:
                begin_frame = 0
            else:
                begin_frame, evidence = cut_boundary(pcm, source_sentences[first-1], source_sentences[first], scene_id)
                evidence['edge'] = 'retained_group_start'
                cuts.append(evidence)
            if last == len(source_sentences)-1:
                end_frame = source_frames
            else:
                end_frame, evidence = cut_boundary(pcm, source_sentences[last], source_sentences[last+1], scene_id)
                evidence['edge'] = 'retained_group_end'
                cuts.append(evidence)
            assert begin_frame < end_frame
            assert begin_frame/SR <= source_sentences[first]['start_s']
            assert end_frame/SR >= source_sentences[last]['end_s']
            output_begin_frame = len(new_pcm)//2
            new_pcm += pcm[begin_frame*2:end_frame*2]
            groups.append({'scene_id': scene_id, 'source_start_frame': begin_frame, 'source_end_frame': end_frame, 'source_start_s': begin_frame/SR, 'source_end_s': end_frame/SR, 'output_start_frame': output_begin_frame, 'output_start_s': output_begin_frame/SR, 'kept_sentence_ids': [source_sentences[i]['sentence_id'] for i in run], 'pcm_bytes_preserved_exactly': True})
        wav = OUT / (scene_id + '.wav')
        if len(selected_indices) == len(source_sentences):
            shutil.copyfile(source_audio, wav)
            assert sha(wav) == sha(source_audio)
        else:
            pcm_write(wav, new_pcm)
        assert pcm_read(wav) == new_pcm
        mp3 = OUT / (scene_id + '.mp3')
        p = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', str(wav), '-c:a', 'libmp3lame', '-b:a', '128k', '-y', str(mp3)], capture_output=True)
        assert p.returncode == 0
        duration_s = len(new_pcm)//2/SR
        local_sentences, scene_words = [], []
        new_normalized_char_cursor = 0
        for sentence in source_sentences:
            if sentence['sentence_id'] not in keep:
                continue
            group = next(g for g in groups if sentence['sentence_id'] in g['kept_sentence_ids'])
            shift = group['output_start_s'] - group['source_start_s']
            revised = {**sentence, 'start_s': sentence['start_s']+shift, 'end_s': sentence['end_s']+shift, 'source_v1_local_start_s': sentence['start_s'], 'source_v1_local_end_s': sentence['end_s'], 'timing_basis': 'provider_word_boundary_divided_by_1.35_then_exact_sample_cut_translation'}
            assert 0 <= revised['start_s'] < revised['end_s'] <= duration_s+0.04
            local_sentences.append(revised)
            sentence_source_words = [word for word in source_words if word['sentence_id'] == sentence['sentence_id']]
            source_sentence_char_start = sentence_source_words[0]['normalized_char_start']
            source_sentence_char_end = sentence_source_words[-1]['normalized_char_end']
            for word in sentence_source_words:
                if word['sentence_id'] != sentence['sentence_id']:
                    continue
                # v1 word local values are already uniformly scaled by 1.35.
                local_start, local_end = word['local_start_s']+shift, word['local_end_s']+shift
                scene_words.append({**word, 'local_start_s': local_start, 'local_end_s': local_end, 'source_v1_local_start_s': word['local_start_s'], 'source_v1_local_end_s': word['local_end_s'], 'source_v1_normalized_char_start': word['normalized_char_start'], 'source_v1_normalized_char_end': word['normalized_char_end'], 'normalized_char_start': new_normalized_char_cursor+word['normalized_char_start']-source_sentence_char_start, 'normalized_char_end': new_normalized_char_cursor+word['normalized_char_end']-source_sentence_char_start, 'sentence_normalized_char_start': word['normalized_char_start']-source_sentence_char_start, 'sentence_normalized_char_end': word['normalized_char_end']-source_sentence_char_start, 'timing_basis': revised['timing_basis']})
            new_normalized_char_cursor += source_sentence_char_end-source_sentence_char_start
        start_s = (offset_frames+body_frames)/SR
        end_s = start_s+duration_s
        global_sentences = [{**s, 'local_start_s': s['start_s'], 'local_end_s': s['end_s'], 'start_s': start_s+s['start_s'], 'end_s': start_s+s['end_s']} for s in local_sentences]
        for w in scene_words:
            w['start_s'] = start_s+w['local_start_s']
            w['end_s'] = start_s+w['local_end_s']
        words_all.extend(scene_words)
        scene_rows = [r for r in retained_text if r['scene_id'] == scene_id]
        scenes.append({'scene_id': scene_id, 'start_s': start_s, 'end_s': end_s, 'duration_s': duration_s, 'audio_path': str(wav.resolve()), 'mp3_path': str(mp3.resolve()), 'audio_sha256': sha(wav), 'source_v1_audio_sha256': original_scene['audio_sha256'], 'narration_text': '\n'.join(r['display_text'] for r in scene_rows), 'reading_text': '\n'.join(r['reading_text'] for r in scene_rows), 'sentences': global_sentences, 'sentence_times': local_sentences, 'captions': [{'sentence_id': s['sentence_id'], 'text': s['text'], 'start_s': s['start_s'], 'end_s': s['end_s']} for s in global_sentences], 'anchors': {'narration_start': local_sentences[0]['start_s']}, 'words_path': rel(OUT / 'words_v2.json'), 'timing_basis': 'actual_sample_cut_audio_with_translated_scaled_provider_boundaries', 'is_estimate': False, 'audio_revision': 'free-edge-injoon-atempo135-sentencecut-v2', 'actual_listening_performed': False})
        cuts_all.extend(cuts)
        groups_all.extend(groups)
        wavs.append(wav)
        body_frames += len(new_pcm)//2
    assert [s['sentence_id'] for scene in scenes for s in scene['sentences']] == plan['keep_sentence_ids']
    body_pcm = b''.join(pcm_read(wav) for wav in wavs)
    body_wav = OUT / 'narration_body.wav'
    pcm_write(body_wav, body_pcm)
    assert len(body_pcm)//2 == body_frames
    last_speech = scenes[-1]['sentences'][-1]['end_s']
    body_end = (offset_frames+body_frames)/SR
    outro_frame = max(offset_frames+body_frames, math.ceil((last_speech+3)*SR))
    hold_frames = outro_frame-offset_frames-body_frames
    scenes.append({'scene_id': 'E001', 'start_s': body_end, 'end_s': outro_frame/SR, 'duration_s': hold_frames/SR, 'audio_path': None, 'narration_text': '', 'sentences': [], 'sentence_times': [], 'captions': [], 'anchors': {}, 'timing_basis': 'last_scaled_provider_word_end_plus_3s_sample_quantized; existing_tail_counted_once', 'is_estimate': False})
    intro_path = ROOT/source['brand_intro']['path']
    outro_path = ROOT/source['brand_outro']['path']
    assert sha(intro_path) == source['brand_intro']['sha256'] and sha(outro_path) == source['brand_outro']['sha256']
    full_pcm = pcm_read(intro_path)+body_pcm+b'\0\0'*hold_frames+pcm_read(outro_path)
    full_wav = OUT/'narration_full_brand.wav'
    pcm_write(full_wav, full_pcm)
    total_duration = len(full_pcm)//2/SR
    low, high = plan['acceptable_natural_duration_range_seconds']
    assert low <= total_duration <= high, ('Duration outside approved target window', total_duration)
    total_scene_time = sum(s['duration_s'] for s in scenes)
    contract = {**{k:v for k,v in source.items() if k not in ['scenes', 'audio_file', 'audio_file_time_origin_global_s', 'audio_revision', 'word_count', 'script_revision', 'script_sha256', 'time_transform']}, 'audio_revision': 'free-edge-injoon-atempo135-sentencecut-v2', 'script_revision': v4['revision'], 'script_sha256': sha(script_path), 'cut_plan_sha256': sha(plan_path), 'source_scene_proposals_v4_sha256': sha(scene_path), 'timing_locked': False, 'timing_basis': 'actual_audio', 'alignment_basis': 'raw_provider_words_scaled_by_1.35_then_sample_cut_translation', 'audio_file': str(body_wav.resolve()), 'audio_file_time_origin_global_s': 5.0, 'full_brand_audio_file': str(full_wav.resolve()), 'full_brand_audio_file_time_origin_global_s': 0.0, 'audio_body_duration_s': body_frames/SR, 'last_spoken_end_s': last_speech, 'final_audio_tail_already_counted_s': body_end-last_speech, 'required_hold_from_last_spoken_s': 3.0, 'additional_silence_after_audio_s': hold_frames/SR, 'brand_intro': {**source['brand_intro'], 'start_s': 0, 'end_s': 5.0}, 'brand_outro': {**source['brand_outro'], 'start_s': outro_frame/SR, 'end_s': total_duration}, 'total_duration_with_brand_and_hold_s': total_duration, 'scenes': scenes, 'sentence_count': 103, 'word_count': len(words_all), 'scene_id_count': 27, 'removed_sentence_ids': plan['drop_sentence_ids'], 'changed_scene_ids': [s['scene_id'] for s in source['scenes'] if any(t['sentence_id'] in drop for t in s.get('sentence_times', []))], 'timing_delta_s': total_duration-source['total_duration_with_brand_and_hold_s'], 'time_transform': {'formula': 'new_scene_global_start + (raw_provider_local_time/1.35 - kept_group_source_start_frame/44100 + kept_group_output_start_frame/44100)', 'source_audio_regenerated': False, 'atempo_factor_unchanged': 1.35, 'edit_mode': 'PCM slices in word-gap quiet windows; no further compression, silence padding, or resynthesis', 'caution': '原 제공자 경계 배율에 대한 cut 이동. 실제 음소 정렬·청취 검증 아님.'}, 'boundary_qa': rel(OUT/'cut_boundary_qa.json'), 'path_semantics': 'audio_file/audio_path absolute; metadata paths project root relative', 'time_semantics': 'scene/sentences/captions global seconds including intro5; sentence_times/anchors local seconds; body audio origin global5; full_brand_audio origin0', 'status': 'v2_complete_measured_proposal_pending_director_lock_and_listening', 'actual_listening_performed': False, 'asr_performed': False, 'tts_calls_this_edit': 0, 'cash_cost_krw': 0, 'paid_api_calls': 0}
    save(OUT/'words_v2.json', {'audio_revision': contract['audio_revision'], 'sentence_count': 103, 'word_count': len(words_all), 'words': words_all})
    actual_sentence_rows = []
    for scene in scenes:
        for sentence in scene['sentences']:
            original_row = next(r for r in retained_text if r['sentence_id'] == sentence['sentence_id'])
            actual_sentence_rows.append({key:original_row[key] for key in ['sentence_id','scene_id','original_text','display_text','reading_text','claim_ids','numerical_transformations']})
            actual_sentence_rows[-1].update(start_s=sentence['start_s'], end_s=sentence['end_s'], local_start_s=sentence['local_start_s'], local_end_s=sentence['local_end_s'], audio_revision=contract['audio_revision'], timing_basis=sentence['timing_basis'], actual_listening_performed=False)
    save(OUT/'sentences_v4.json', {'script_revision': v4['revision'], 'original_sentence_ids_retained': True, 'time_origin': 'global seconds including intro5; local times relative to each scene', 'sentences': actual_sentence_rows})
    save(OUT/'cut_groups.json', {'sample_rate': SR, 'sample_width_bytes': 2, 'groups': groups_all})
    save(OUT/'cut_boundary_qa.json', {'checked_at_utc': stamp(), 'cut_count': len(cuts_all), 'method': '20ms PCM RMS search in provided sentence gap, keeping40ms guards when available; nearest-zero sample', 'cut_boundaries': cuts_all, 'max_rms_pcm_at_cuts': max(c['pcm_rms'] for c in cuts_all), 'max_peak_pcm_at_cuts': max(c['pcm_peak'] for c in cuts_all), 'minimum_metadata_guard_s': min(min(c['metadata_margin_after_left_word_s'],c['metadata_margin_before_right_word_s']) for c in cuts_all), 'sample_quantization_s': 1/SR, 'true_phonetic_alignment_error_s': None, 'actual_listening_performed': False, 'asr_performed': False, 'required_qa': '모든 문장 삭제 접합부를 실제 청취해 받침/첫 음절/호흡/클릭/숫자 발음을 점검. metadata 간격·낮은 RMS를 청취 통과로 표현하지 않음.'})
    save(DIR/'timing_proposals_v2.json', contract)
    save(OUT/'proposed_timing_v2.json', contract)
    # One full PCM decode validates the combined track; individual WAV slices are byte-checked above.
    result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', str(full_wav), '-f', 'null', '-'], capture_output=True)
    assert result.returncode == 0
    assert all(sha(ROOT/path) == digest for path,digest in frozen.items()), 'V1 changed'
    assert sum(len(s['sentences']) for s in scenes) == 103
    assert set(w['sentence_id'] for w in words_all) == keep
    assert not drop & set(w['sentence_id'] for w in words_all)
    assert abs(total_scene_time + 15-total_duration) < 1/SR
    for scene in scenes:
        for sentence in scene['sentences']:
            assert scene['start_s'] <= sentence['start_s'] < sentence['end_s'] <= scene['end_s']+0.04
    files = [p for p in OUT.glob('*') if p.is_file() and p.name not in ['artifact_manifest.json', 'handoff.json']]
    save(OUT/'artifact_manifest.json', {'files': [{'path': rel(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files]})
    save(OUT/'verification.json', {'status': 'passed_pcm_cut_and_contract_checks_listening_unverified', 'checked_at_utc': stamp(), 'v1_files_hash_checked_unchanged': len(frozen), 'full_track_decode_passed': True, 'pcm_cuts_byte_preserving': True, 'script_v4_exact_sentence_and_order_match': True, 'kept_sentences': 103, 'removed_sentences': 13, 'scene_count_including_E001': 27, 'word_count': len(words_all), 'duration_with_brand_and_hold_s': total_duration, 'body_duration_s': body_frames/SR, 'last_spoken_hold_s': outro_frame/SR-last_speech, 'target_window_s': [low,high], 'within_target_window': True, 'all_20_rank_scene_ids_preserved': all(f'S{i:03}' in [s['scene_id'] for s in scenes] for i in range(3,23)), 'silence_padding_to_hit_duration_used': False, 'atempo_factor': 1.35, 'new_tts_calls': 0, 'paid_api_calls': 0, 'actual_listening_performed': False, 'asr_performed': False, 'independent_qa_performed': False})
    summary = {'task_id': 'top20-narration-sentencecut-v2', 'role': 'narration', 'status': contract['status'], 'input_revisions': {'script_v4.md': sha(script_path), 'scene_proposals_v4.json': sha(scene_path), 'editorial_cut_plan.json': sha(plan_path), 'source_proposed_timing_v1.json': sha(DIR/'proposed_timing.json')}, 'outputs': [rel(DIR/'timing_proposals_v2.json'), rel(body_wav), rel(full_wav), rel(OUT/'words_v2.json'), rel(OUT/'cut_boundary_qa.json'), rel(OUT/'verification.json'), rel(OUT/'artifact_manifest.json')], 'audio_revision': contract['audio_revision'], 'body_duration_s': body_frames/SR, 'total_duration_s': total_duration, 'timing_delta_from_v1_s': contract['timing_delta_s'], 'affected_scene_ids': contract['changed_scene_ids'], 'checks': [{'check': '샘플 편집/103문장/제공자 경계 이동/27장면/v1 보존', 'result': 'passed', 'evidence': 'verification.json'}, {'check': '절단부 실제 청취/ASR/독립QA', 'result': 'not_performed', 'evidence': 'cut_boundary_qa.json'}], 'open_issue_ids': ['CUT_BOUNDARY_LISTENING_UNVERIFIED'], 'next_role': 'director→editor→qa', 'generation_cost_krw': 0, 'new_tts_calls': 0, 'unresolved': '내부 무음 선택값은 측정했으나 음소 경계 오차 미측정. 실제 청취 QA 필요.'}
    save(OUT/'handoff.json', summary)
    print(json.dumps({'status':'v2_complete_no_tts', 'sentences':103, 'words':len(words_all), 'body_duration_s': body_frames/SR, 'full_duration_s':total_duration, 'removed_timeline_s':-contract['timing_delta_s'], 'cut_boundaries':len(cuts_all), 'max_cut_rms_pcm':max(c['pcm_rms']for c in cuts_all), 'min_metadata_guard_s':min(min(c['metadata_margin_after_left_word_s'],c['metadata_margin_before_right_word_s'])for c in cuts_all), 'frozen_v1_files_unchanged':len(frozen), 'timing':rel(DIR/'timing_proposals_v2.json'), 'full_brand_audio':rel(full_wav), 'paid_api_calls':0},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
