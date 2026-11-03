"""Local narration preparation only. No network, synthesis, shared-state writes."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal, ROUND_CEILING
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

OUT = Path(__file__).resolve().parent
EP = OUT.parents[1]
ROOT = OUT.parents[4]
SCRIPT = EP / 'writer/top20-8min-v2/script_v3.md'
SCENES = EP / 'writer/top20-8min-v2/scene_proposals_v3.json'
EXPECTED_SCRIPT_SHA = '4cc70ef2ae3cabda13b560104dd96ef0df0fe1f815a5f1372ac680e729d3be17'
STAMP = dt.datetime.now(dt.timezone.utc).isoformat()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def text(p, value):
    p.resolve().relative_to(OUT)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(value.encode('utf-8'))


def save(p, value):
    text(p, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


DIGITS = '영일이삼사오육칠팔구'


def sino(n):
    if not n:
        return '영'
    result = ''
    if n >= 10000:
        high, n = divmod(n, 10000)
        result = sino(high) + '만'
        if n:
            result += ' '
    for place, unit in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        digit, n = divmod(n, place)
        if digit:
            result += ('' if digit == 1 and place > 1 else DIGITS[digit]) + unit
    return result


def parse_sino(value):
    """Independent Korean-number parser for value-preservation checks."""
    value = value.replace(' ', '')
    number, subtotal, total = 0, 0, 0
    for c in value:
        if c in DIGITS:
            number = DIGITS.index(c)
        elif c in '십백천':
            subtotal += (number or 1) * {'십': 10, '백': 100, '천': 1000}[c]
            number = 0
        elif c == '만':
            total += (subtotal + number or 1) * 10000
            subtotal, number = 0, 0
        else:
            raise ValueError(c)
    return total + subtotal + number


NUMBER = re.compile(r'TOP20|\d[\d,]*(?:\.\d+)?(?:만(?:[ \t]*\d[\d,]*)?|천)?(?:퍼센트|년|월|일|위|쌍|개)?')
DATE = '2024년 11월 1일'
DATE_READING = '이천이십사 년 십일 월 일 일'


def convert_number(surface):
    if surface == 'TOP20':
        return '스무 곳', '20', '개 지역', 'native_twenty_title', '20'
    unit_match = re.search(r'(퍼센트|년|월|일|위|쌍|개)$', surface)
    unit = unit_match[0] if unit_match else ''
    body = surface[:-len(unit)] if unit else surface
    body = body.replace(',', '').strip()
    if '만' in body:
        high, rest = body.split('만')
        number = int(high) * 10000 + int(rest.strip() or '0')
    elif body.endswith('천'):
        number = int(body[:-1]) * 1000
    else:
        number = Decimal(body)
    canonical = str(number)
    if surface == '53개':
        return '쉰세 개', canonical, unit, 'native_counter', '53'
    if '.' in body:
        integer, decimals = body.split('.')
        spoken_number = sino(int(integer)) + ' 점 ' + ' '.join(DIGITS[int(c)] for c in decimals)
        parsed = str(Decimal(parse_sino(spoken_number.split(' 점 ')[0])) + Decimal('0.' + ''.join(str(DIGITS.index(c)) for c in spoken_number.split(' 점 ')[1].replace(' ', ''))))
        # Preserve lexical precision separately, e.g. 7.0 remains 칠 점 영.
        reason = 'decimal_digits_and_precision_preserved'
    else:
        spoken_number = sino(int(number))
        parsed = str(parse_sino(spoken_number))
        reason = 'sino_number_and_unit'
    reading = spoken_number + (' ' + unit if unit else '')
    return reading, canonical, unit, reason, parsed


def pronounce(original):
    matches = []
    date_spans = [(m.start(), m.end()) for m in re.finditer(re.escape(DATE), original)]
    for start, end in date_spans:
        matches.append((start, end, DATE_READING, '2024-11-01', 'date', 'writer_pronunciation_dictionary', '2024-11-01'))
    for m in NUMBER.finditer(original):
        if any(a <= m.start() < b for a, b in date_spans):
            continue
        replacement, canonical, unit, reason, parsed = convert_number(m[0])
        matches.append((m.start(), m.end(), replacement, canonical, unit, reason, parsed))
    matches.sort()
    parts, transforms, cursor, spoken_offset = [], [], 0, 0
    for start, end, replacement, canonical, unit, reason, parsed in matches:
        untouched = original[cursor:start]
        parts.append(untouched)
        spoken_offset += len(untouched)
        if unit != 'date':
            assert Decimal(canonical) == Decimal(parsed), (original, canonical, parsed)
        else:
            year, month, day = re.fullmatch(r'(.+) 년 (.+) 월 (.+) 일', replacement).groups()
            assert [parse_sino(t) for t in (year, month, day)] == [2024, 11, 1]
        transforms.append({
            'source_start': start, 'source_end': end, 'source_text': original[start:end],
            'spoken_start': spoken_offset, 'spoken_end': spoken_offset + len(replacement),
            'spoken_text': replacement, 'exact_value': canonical, 'unit': unit,
            'reason': reason, 'independently_decoded_value': parsed,
            'value_preserved': True,
        })
        parts.append(replacement)
        spoken_offset += len(replacement)
        cursor = end
    parts.append(original[cursor:])
    reading = ''.join(parts)
    assert not re.search(r'[0-9]', reading), reading
    # Restore all original spans and prove no non-numeric text was changed.
    restored = reading
    for tr in reversed(transforms):
        assert restored[tr['spoken_start']:tr['spoken_end']] == tr['spoken_text']
        restored = restored[:tr['spoken_start']] + tr['source_text'] + restored[tr['spoken_end']:]
    assert restored == original
    return reading, transforms


def main():
    assert sha(SCRIPT) == EXPECTED_SCRIPT_SHA, '승인 원고 SHA 불일치'
    scene_doc = read(SCENES)
    assert scene_doc['revision'] == 'top20-8min-v3'
    account = read(OUT / 'account_readonly.json')
    cfg = read(ROOT / 'config/tts.json')
    original_script = SCRIPT.read_text(encoding='utf-8-sig')
    narration_section = original_script.split('## 낭독', 1)[1].split('## 화면 메모', 1)[0]
    script_lines = [line.strip() for line in narration_section.splitlines() if line.strip() and not line.startswith('### ')]
    source_lines = [sentence['text'] for scene in scene_doc['scenes'] for sentence in scene.get('sentences', [])]
    assert script_lines == source_lines, 'MD 원고와 장면 문장/순서 불일치'
    sentences, chunks, timings, timing_warnings = [], [], [], []
    dictionary = dict(scene_doc.get('pronunciation_dictionary', {}))
    scene_texts, scene_readings = [], []
    for scene in scene_doc['scenes']:
        sentence_rows = []
        for sentence in scene.get('sentences', []):
            reading, transforms = pronounce(sentence['text'])
            for tr in transforms:
                dictionary[tr['source_text']] = tr['spoken_text']
            row = {
                'sentence_id': sentence['sentence_id'], 'scene_id': scene['scene_id'],
                'original_text': sentence['text'], 'display_text': sentence['text'], 'reading_text': reading,
                'claim_ids': sentence.get('claim_ids', []), 'statement_type': sentence.get('statement_type'),
                'numerical_transformations': transforms, 'display_characters': len(sentence['text']),
                'reading_characters': len(reading), 'audio_revision': None, 'actual_listening': '미확인·음성 미생성',
            }
            sentences.append(row)
            sentence_rows.append(row)
        display = '\n'.join(row['display_text'] for row in sentence_rows)
        reading = '\n'.join(row['reading_text'] for row in sentence_rows)
        if sentence_rows:
            scene_texts.append(display)
            scene_readings.append(reading)
            filename = 'chunks/' + scene['scene_id'] + '.txt'
            text(OUT / filename, reading)
            hangul = sum('가' <= c <= '힣' for c in reading)
            chunks.append({
                'chunk_id': scene['scene_id'], 'scene_id': scene['scene_id'], 'path': filename,
                'sentence_ids': [row['sentence_id'] for row in sentence_rows],
                'text': reading, 'characters': len(reading), 'sha256': sha(OUT / filename),
                'hangul_syllables': hangul,
            })
            weights = [len(re.sub(r'\s', '', row['reading_text'])) for row in sentence_rows]
            total_weight = sum(weights)
            elapsed = float(scene['start_s'])
            for i, (row, weight) in enumerate(zip(sentence_rows, weights)):
                end = float(scene['end_s']) if i == len(sentence_rows) - 1 else elapsed + scene['duration_s'] * weight / total_weight
                row['estimated_start_s'] = round(elapsed, 4)
                row['estimated_end_s'] = round(end, 4)
                row['timing_basis'] = 'writer_scene_estimate_reading_length_allocation_not_audio_aligned'
                elapsed = end
            rate = hangul / scene['duration_s']
            if rate > 8.5:
                timing_warnings.append({'scene_id': scene['scene_id'], 'estimated_hangul_syllables_per_second': round(rate, 2), 'issue': '글자량 대비 잠정 구간이 짧을 수 있음. 실제 오디오 후 재배분; 속도 강제 변경 금지.'})
        timings.append({
            'scene_id': scene['scene_id'], 'start_s': scene['start_s'], 'end_s': scene['end_s'],
            'duration_s': scene['duration_s'], 'timing_basis': 'writer_v3_estimate_not_audio_aligned',
            'confidence': 'low', 'audio_revision': None, 'is_estimate': True,
            'measured_duration_s': None, 'timing_locked': False,
        })
    assert len({row['sentence_id'] for row in sentences}) == len(sentences)
    display_body = '\n\n'.join(scene_texts)
    reading_body = '\n\n'.join(scene_readings)
    text(OUT / 'display_sentences.txt', display_body)
    text(OUT / 'reading_text.txt', reading_body)
    save(OUT / 'sentences.json', {'task_id': 'top20-narration-prep-v1', 'script_revision': scene_doc['revision'], 'sentences': sentences})
    save(OUT / 'pronunciation_dictionary.json', {'source': 'writer v3 발음사전 + 값 보존 숫자 변환', 'entries': dictionary, 'proper_names': {name: name for name in ['원미구', '중랑구', '미추홀구', '권선구', '영통구', '경춘선숲길', '진관동', '삼송로', '서해구', '검단구', '청라호수공원', '석촌호수']}, 'actual_audio_pronunciation_checked': False})
    input_versions = {
        'writer/top20-8min-v2/script_v3.md': {'sha256': sha(SCRIPT), 'revision': 'top20-8min-v3'},
        'writer/top20-8min-v2/scene_proposals_v3.json': {'sha256': sha(SCENES), 'revision': scene_doc['revision']},
        'config/tts.json': {'sha256': sha(ROOT / 'config/tts.json'), 'usage': 'Jun 예산 후보 설정'},
    }
    characters = sum(chunk['characters'] for chunk in chunks)
    hangul = sum(chunk['hangul_syllables'] for chunk in chunks)
    punctuation_pause = len(sentences) * 0.25 + reading_body.count(',') * 0.12
    lower = round(hangul / 8.5 + punctuation_pause + 3, 1)
    upper = round(hangul / 6.5 + punctuation_pause + 3, 1)
    speed = (account.get('voice') or {}).get('settings', {}).get('speed')
    manifest = {
        'task_id': 'top20-narration-prep-v1', 'created_at_utc': STAMP,
        'script_revision': 'top20-8min-v3', 'audio_revision': None, 'input_versions': input_versions,
        'script_acceptance_basis': '최신 task packet: 직전 제시한 로컬 TOP20 원고 수락; 총괄이 공통 승인 기록 반영',
        'budget_approval_status': '유효한 해당 버전 예산 응답 대기', 'generation_started': False,
        'sentence_count': len(sentences), 'spoken_scene_count': len(chunks), 'total_scene_count': len(timings),
        'display_characters_sum_sentences': sum(row['display_characters'] for row in sentences),
        'display_normalized_characters': len('\n'.join(row['display_text'] for row in sentences)),
        'display_body_file_characters': len(display_body),
        'input_characters': characters, 'characters_sum_sentences': sum(row['reading_characters'] for row in sentences),
        'reading_body_file_characters': len(reading_body),
        'character_count_method': 'Unicode code points; chunks/*.txt 각 파일 전체·공백·문장 사이 LF 포함, BOM·말미 LF 없음. 요청 text에 ID·메모·제목·전체 합본의 장면 사이 빈 줄 제외.',
        'provider': cfg['provider'], 'voice_name': cfg['voice_name'], 'voice_id': cfg['voice_id'], 'model': cfg['model'],
        'style_description': cfg['style'], 'current_voice_speed': speed,
        'supported_request_settings': {k: v for k, v in (account.get('voice') or {}).get('settings', {}).items() if k in ['stability', 'similarity_boost', 'speed']},
        'unsupported_stored_settings': {'style': '현재 모델 can_use_style=false; 요청에 넣지 않음', 'use_speaker_boost': '현재 모델 can_use_speaker_boost=false; 요청에 넣지 않음'},
        'chunks': chunks,
        'shorts_audio_scope': '본편 생성 음성의 문장 ID를 편집 재사용하면 추가 생성 0. 별도 새 쇼츠 문장은 입력 미제공으로 이 견적에 미포함; 별도 문자수·예산 필요.',
    }
    save(OUT / 'narration_manifest.json', manifest)
    save(OUT / 'timing_proposals.json', {
        'script_revision': 'top20-8min-v3', 'audio_revision': None,
        'target_duration_s': 480, 'total_estimated_duration_s': 480, 'measured_duration_s': None,
        'timing_locked': False, 'duration_is_actual': False,
        'method': 'writer v3 장면별 구간 유지; 문장별 구간은 읽기문 공백 제외 길이 비례. 음성 기반 정렬 아님.',
        'independent_text_only_duration_heuristic': {'hangul_syllables': hangul, 'syllables_per_second_range': [6.5, 8.5], 'sentence_pause_s': 0.25, 'comma_pause_s': 0.12, 'end_hold_s': 3, 'estimated_range_s': [lower, upper], 'basis': '계획용 가정; Jun 실측/보장/속도 변경 지시 아님'},
        'scenes': timings, 'timing_warnings': timing_warnings,
        'changed_scene_ids': [], 'timing_delta_s': None, 'change_note': '새 오디오 미생성으로 실제 길이·변경 문장·델타 없음. 편집·총괄은 실측 후 시간표 갱신.',
    })
    local_windows = read(OUT / 'local_windows_voices.json')
    local = {
        'checked_at_utc': STAMP, 'python_executable': sys.executable,
        'python_modules': {name: bool(importlib.util.find_spec(name)) for name in ['edge_tts', 'pyttsx3', 'kokoro', 'TTS', 'piper', 'torch']},
        'executables': {name: shutil.which(name) for name in ['edge-tts', 'piper', 'espeak']},
        'windows': local_windows,
        'assessment': 'SAPI COM에서 Microsoft Heami Desktop 한국어 음성 열거 성공. 추가 API 비용 없는 오프라인 대안 후보. 실제 합성·파일 출력·청취 품질 미검증.',
        'edge_tts': {'available_in_checked_python': bool(importlib.util.find_spec('edge_tts')), 'network_required': True, 'service_endpoint_tested': False, 'installation_performed': False, 'assessment': '현재 확인한 Python에 미설치. 설치 후 연결·이용조건 확인 필요; 오프라인 엔진으로 표시하지 않음.'},
        'generation_invoked': False, 'paid_endpoints_invoked': False,
    }
    save(OUT / 'free_fallback_availability.json', local)
    rates = (account.get('model') or {}).get('model_rates') or {}
    voice_rate = (account.get('voice') or {}).get('sharing_rate')
    complete_rates = all(isinstance(x, (int, float)) and x > 0 for x in [rates.get('character_cost_multiplier'), rates.get('cost_discount_multiplier'), voice_rate])
    multiplier = Decimal(str(rates['character_cost_multiplier'])) * Decimal(str(rates['cost_discount_multiplier'])) * Decimal(str(voice_rate)) if complete_rates else None
    estimate = int((Decimal(characters) * multiplier).to_integral_value(rounding=ROUND_CEILING)) if multiplier else None
    plus20_cap = int((Decimal(estimate) * Decimal('1.20')).to_integral_value(rounding=ROUND_CEILING)) if estimate is not None else None
    # Latest parent packet: budget question already uses 6,000; never silently replace it.
    cap = 6000
    if estimate is not None:
        assert estimate <= cap, '정확한 예상 사용량이 총괄이 제시한 6000 상한을 초과함; 총괄 통보 필요'
    balance = (account.get('subscription') or {}).get('included_remaining')
    fits = balance >= cap if balance is not None and cap is not None else None
    budget = {
        'task_id': 'top20-narration-prep-v1', 'created_at_utc': STAMP,
        'status': 'prepared_awaiting_valid_budget_response', 'generation_authorized': False, 'generation_started': False,
        'episode_id': EP.name, 'script_revision': 'top20-8min-v3', 'script_sha256': sha(SCRIPT),
        'narration_manifest_sha256': sha(OUT / 'narration_manifest.json'), 'account_snapshot': 'account_readonly.json',
        'provider': cfg['provider'], 'voice_id': cfg['voice_id'], 'voice_name': cfg['voice_name'], 'model': cfg['model'],
        'input_characters': characters, 'paragraph_requests': len(chunks), 'sentence_count': len(sentences),
        'character_count_method': manifest['character_count_method'],
        'model_character_cost_multiplier': rates.get('character_cost_multiplier'), 'model_cost_discount_multiplier': rates.get('cost_discount_multiplier'), 'voice_rate': voice_rate,
        'effective_credits_per_character': str(multiplier) if multiplier else None,
        'estimated_credits': estimate, 'headroom_percent': 20,
        'estimated_plus_20_percent_cap': plus20_cap, 'included_credit_cap': cap,
        'cap_basis': '최신 총괄 packet: 사용자에게 6000크레딧 상한으로 예산 질의함. 이 상한의 응답 대기; 20% 산술 상한과 구분.',
        'budget_question_status': '총괄이 async 질의 전달; 응답 대기라고 통보받음. 본 담당이 응답·전송 원장을 직접 확인한 것은 아님.',
        'rounding': '20% 산술 기준=ceil(estimated_credits × 1.20); 사용자 응답 대상 최대상한=6000', 'included_remaining': balance,
        'balance_checked_at_utc': account.get('checked_at_utc'), 'cap_fits_included': fits,
        'remaining_after_estimate': balance - estimate if balance is not None and estimate is not None else None,
        'remaining_after_full_cap': balance - cap if balance is not None and cap is not None else None,
        'account_checks_passed': account.get('status') == 'read_only_checks_passed',
        'additional_cash_usd_estimate': 0, 'additional_cash_usd_cap': 0, 'additional_cash_krw_cap': 0,
        'cash_basis': '기존 포함 크레딧만 사용 제안. 구독료 환산·새 결제·환율 추정 없음.',
        'topup_or_overage_authorized': False, 'automatic_retry': False,
        'paid_generation_calls_this_task': 0,
        'scope': {'main': '26개 본편 장면 읽기문 1회 생성 제안', 'promo_short': '본편 오디오 재사용 시 추가 생성 0', 'content_short': '본편 오디오 재사용 시 추가 생성 0', 'new_short_sentences': '미포함; 별도 확정 원고와 견적 필요', 'private_uploads': '사용자 지시 3개 PRIVATE 범위 확인; 업로드 실행은 담당 총괄·편집 범위'},
        'approval_requirements': [
            '해당 episode·top20-8min-v3·script SHA·narration manifest SHA·Jun/eleven_v4·크레딧 상한·추가결제0에 연결된 유효한 사용자 예산 응답',
            '무료 Heami/Edge 선택은 별도 명시. 미응답·대기·과거 타 편 승인은 Jun 생성 승인 아님',
            '생성 직전 동일 원고/읽기문/voice 설정과 실제 잔액 재검증. 상한 초과·계정 조회 실패·요율 변경이면 중단',
            '실패·시간초과·결과 불명은 자동 재시도 금지; 요청 영수증·사용량 확인 후 총괄 판단. 20% 여유도 자동 재생성 허가 아님',
            '새 문장·설정 변경은 새 버전/견적으로 연결',
        ],
        'evidence_sources': [
            {'url': 'https://elevenlabs.io/docs/help-center/product/voices/voice-library/what-are-custom-rates-and-credit-multipliers', 'usage': '음성별 배수 존재 설명; 실제 요율은 account_readonly.json GET 결과 우선'},
            {'url': 'https://elevenlabs.io/docs/overview/models', 'usage': '모델 공식 문서; 계정별 실측 GET 결과와 구분'},
        ],
    }
    save(OUT / 'budget_proposal.json', budget)
    prompt = f"TOP20 v3 Jun 음성 예산 제안: 정확한 입력 {characters:,}자, 예상 {estimate:,}크레딧, 20% 여유 산술 기준 {plus20_cap:,}크레딧. 총괄이 사용자에게 질의한 최대상한 {cap:,}크레딧의 응답 대기. 현재 포함 잔액 {balance:,}크레딧. 추가 결제 0원·충전/초과과금 없음·자동 재시도 없음. 본편 생성분을 홍보/콘텐츠 쇼츠에 재사용하면 추가 음성 비용 0. 별도 새 쇼츠 문장 생성은 제외. 아직 생성하지 않았습니다."
    text(OUT / 'budget_prompt.txt', prompt + '\n\n' + '총괄 전달용: 해당 버전 Jun 상한 승인 또는 무료 Windows Heami 선택 응답에 연결하세요. 외부 메시지는 이 작업에서 보내지 않습니다.\n')
    save(OUT / 'preflight.json', {
        'task_id': 'top20-narration-prep-v1', 'scope': 'narration preparation only',
        'workflow_and_role_read': True, 'master_guide_relevant_sections': ['적용 순서', '체크리스트', '8.2 TTS', '8.3 원문/읽기문/표시문', '8.4 끝 발화 후3초', '10 검수 범위'],
        'episode_preflight_template_applied': True, 'episode_preflight_read': True,
        'latest_instruction_overrides_stale_shared_approval_status': True,
        'original_script_preserved': True, 'input_versions': input_versions,
        'voice': 'Jun은 예산 후보; 현재 편 유료 생성 승인 대기',
        'actual_audio': None, 'actual_listening_performed': False, 'continuous_playback_performed': False,
        'tts_generation_performed': False, 'external_audio_transfer_performed': False,
        'shared_files_modified': False,
    })
    save(OUT / 'execution_audit.json', {
        'initial_account_query': {'result': 'sandbox_network_EACCES', 'generation_calls': 0},
        'explicit_permission_mode_account_query': {'result': account['status'], 'reason': '사용자가 허용한 기존 helper GET 조회를 require_escalated로 1회 실행', 'requests': account['requests']},
        'automatic_retry_loop': False, 'synthesis_requests': 0, 'topup_requests': 0, 'account_modification_requests': 0,
    })
    save(OUT / 'provider_plan.json', {
        'status': 'plan_only_waiting_for_explicit_valid_response', 'generation_run': False,
        'task_id': 'top20-narration-prep-v1', 'input_script_revision': 'top20-8min-v3',
        'script_sha256': sha(SCRIPT), 'narration_manifest_sha256': sha(OUT / 'narration_manifest.json'),
        'pending_choice': ['Jun:6000 포함크레딧 최대상한·추가결제0·자동재시도없음 승인', '무료 Windows Heami 별도 선택'],
        'jun': {
            'provider': 'elevenlabs', 'model_id': cfg['model'], 'voice_id': cfg['voice_id'],
            'generation_endpoint_proposal': '/v1/text-to-speech/{voice_id}/with-timestamps',
            'request_text_source': 'narration_manifest.json의 chunks 순서와 chunks/*.txt의 정확한 bytes',
            'planned_initial_requests': len(chunks), 'input_characters': characters,
            'max_chunk_characters': max(c['characters'] for c in chunks),
            'live_model_maximum_text_length_per_request': (account.get('model') or {}).get('maximum_text_length_per_request'),
            'settings': manifest['supported_request_settings'],
            'settings_policy': '승인 설정 보존. can_use_style=false 및 can_use_speaker_boost=false인 필드는 전송하지 않음. 임의 가속·감속 없음.',
            'estimated_credits': estimate, 'plus20_reference_credits': plus20_cap,
            'pending_hard_credit_cap': cap, 'additional_cash_cap_krw': 0,
            'automatic_retries': False, 'topup': False, 'overage': False,
            'approval_guard': '총괄이 유효한 사용자 응답을 해당 episode/원고SHA/manifestSHA/Jun/v4/6000상한에 연결한 뒤에만 실행.',
            'pre_generation_checks': ['원고·manifest·chunk hash·설정 버전 동일성', '새 GET 잔액/배수·초과과금 비활성 상태', '6000상한과 다른 작업 사용분을 고려한 실제 잔여 예산'],
            'failure_policy': '실패·timeout·결과 불명 즉시 중단. 요청ID·안전한 영수증 보존; 사용량 확인 없이 재요청 금지. 여유 예산은 자동 재생성 권한 아님.',
            'expected_outputs_after_future_approval': ['장면별 음성 파일', '제공자 원본/정규화 문자 정렬', '요청별 크레딧·해시 영수증', '실제 길이와 문장ID 시간표', '숫자·고유명사 실제 청취 체크리스트'],
        },
        'free_fallback': {
            'candidate': 'Windows SAPI COM Microsoft Heami Desktop - Korean', 'api_cost': 0,
            'installed_and_enumerated': True, 'synthesis_and_wav_export_tested': False,
            'choice_required_before_generation': True, 'alignment': '제공자 문자 타임스탬프 없음. 실제 생성 후 로컬 정렬 또는 허용된 수동 검토 필요.',
            'edge_tts': '현재 Python 미설치; 별도 네트워크 서비스. 설치·연결·이용조건 미검증.',
        },
        'after_generation': ['제공자 정렬 보존·실제 오디오 decode/길이 측정', '문장 ID를 읽기문↔표시문 변환표로 연결', '실제 청취 가능 시 숫자/고유명사/호흡 검수; 불가 범위 미확인', 'changed_scene_ids·새 길이·변경 문장·timing delta를 editor/총괄에 전달', '본편 오디오에서 홍보/콘텐츠 Shorts2 문장 구간 재사용'],
        'private_upload_scope': '최신 사용자 packet에서 3개 PRIVATE 범위 전달. 이 담당은 업로드를 실행하지 않으며 음성 예산 승인으로 업로드를 대체하지 않음.',
    })
    save(OUT / 'issue_TOP20-BUDGET-GATE.json', {
        'issue_id': 'TOP20-BUDGET-GATE', 'scene_ids': [c['scene_id'] for c in chunks],
        'problem': '원고 수락은 최신 packet에 명시. 이번 버전 유료 Jun 예산 응답·무료 음성 선택은 대기.',
        'evidence': {'script_sha256': sha(SCRIPT), 'budget': 'budget_proposal.json', 'shared_state_directly_edited': False},
        'proposal': prompt, 'impact': '총괄·editor는 화면 준비를 계속하고 음성 생성/타임록은 유효한 응답 이후 진행.',
        'to': ['director', 'editor'], 'direct_peer_message_tool_available': False,
    })
    rows = [f"# TOP20 내레이션 준비 v1\n\n문장 {len(sentences)}개, 발화 장면 {len(chunks)}개. 원문·표시문은 writer v3 그대로이며 읽기문만 숫자·단위를 풀었습니다.\n\n{prompt}\n\n480초는 writer 계획값입니다. 음성·정렬·청취 검수는 수행하지 않았습니다. 마지막 3초는 발화 뒤 여백 계획값입니다. Jun speed={speed} 설정을 보존하며 길이에 맞춰 임의 가속하지 않습니다.\n\n무료 대안: Windows SAPI 한국어 Heami가 열거됐습니다. 실제 합성/청취 미검증입니다. edge-tts는 확인한 Python에 미설치이며 네트워크가 필요한 별도 대안입니다.\n\n`sentences.json`은 문장 ID와 원문/표시문/읽기문/숫자 변환 근거를 담고, `chunks/*.txt`만 미래 TTS 요청 text입니다. 전체 합본의 장면 사이 빈 줄은 요금 문자수에서 제외됩니다.\n\n## 문장별 대조\n"]
    for row in sentences:
        rows.append(f"\n{row['sentence_id']}\n\n표시: {row['display_text']}\n\n읽기: {row['reading_text']}\n")
    text(OUT / 'narration_reading.md', ''.join(rows))
    verify()
    files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'handoff.json']
    save(OUT / 'handoff.json', {
        'task_id': 'top20-narration-prep-v1', 'role': 'narration', 'status': 'prepared_budget_response_pending_no_generation',
        'input_revisions': input_versions,
        'outputs': [{'path': str(p.relative_to(EP)).replace('\\', '/'), 'sha256': sha(p)} for p in sorted(files)],
        'affected_scene_ids': [s['scene_id'] for s in scene_doc['scenes']],
        'checks': [{'check': '원문/문장 ID·숫자 값·입력 파일별 문자수', 'result': 'passed', 'evidence': 'verification.json'}, {'check': '계정 잔액·요율 GET 조회', 'result': account['status'], 'evidence': 'account_readonly.json'}, {'check': '실제 음성·길이·청취·독립 QA', 'result': 'not_performed', 'evidence': None}],
        'budget_summary': {'input_characters': characters, 'estimated_credits': estimate, 'included_credit_cap': cap, 'included_remaining': balance, 'additional_cash_krw_cap': 0, 'automatic_retry': False},
        'open_issue_ids': ['TOP20-BUDGET-GATE'], 'next_role': 'director→예산 응답 확인→narration→editor/qa',
        'changed_scene_ids': [], 'new_audio_duration_s': None, 'timing_delta_s': None,
        'unresolved': ['이번 버전 유효한 예산 응답/무료 음성 선택', 'Shorts 새 발화가 필요하면 별도 확정 입력과 예산', '실제 음성·타임록·청취·독립 검수'],
    })
    print(json.dumps({'status': 'prepared_no_generation', 'sentences': len(sentences), 'chunks': len(chunks), 'input_characters': characters, 'estimated_credits': estimate, 'cap': cap, 'balance': balance, 'cash_cap_krw': 0, 'duration_target_s': 480, 'text_heuristic_range_s': [lower, upper], 'folder': str(OUT)}, ensure_ascii=False))


def verify():
    rows = read(OUT / 'sentences.json')['sentences']
    manifest = read(OUT / 'narration_manifest.json')
    budget = read(OUT / 'budget_proposal.json')
    original = read(SCENES)
    expected = [(t['sentence_id'], s['scene_id'], t['text']) for s in original['scenes'] for t in s.get('sentences', [])]
    assert [(r['sentence_id'], r['scene_id'], r['display_text']) for r in rows] == expected
    assert all(r['original_text'] == r['display_text'] for r in rows)
    total = 0
    for chunk in manifest['chunks']:
        raw = (OUT / chunk['path']).read_bytes()
        assert not raw.startswith(b'\xef\xbb\xbf') and not raw.endswith(b'\n')
        assert raw.decode('utf-8') == chunk['text']
        assert sha(OUT / chunk['path']) == chunk['sha256']
        assert len(raw.decode('utf-8')) == chunk['characters']
        total += chunk['characters']
    assert total == manifest['input_characters'] == budget['input_characters']
    assert budget['narration_manifest_sha256'] == sha(OUT / 'narration_manifest.json')
    assert sha(SCRIPT) == EXPECTED_SCRIPT_SHA
    for row in rows:
        assert pronounce(row['original_text'])[0] == row['reading_text']
    times = read(OUT / 'timing_proposals.json')['scenes']
    assert times[0]['start_s'] == 0 and times[-1]['end_s'] == 480
    assert all(a['end_s'] == b['start_s'] for a, b in zip(times, times[1:]))
    assert all(t['audio_revision'] is None and t['is_estimate'] for t in times)
    save(OUT / 'verification.json', {
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'passed_local_text_and_budget_checks',
        'script_sha256': sha(SCRIPT), 'scene_proposals_sha256': sha(SCENES),
        'sentence_ids_count': len(rows), 'display_equals_original': True, 'script_md_matches_scene_sentences': True,
        'number_transformations_checked': sum(len(r['numerical_transformations']) for r in rows),
        'numeric_readings_independently_decoded': True, 'non_numeric_text_roundtrip_preserved': True,
        'chunk_hashes_and_character_counts_checked': len(manifest['chunks']), 'input_characters': total,
        'budget_cap_math_checked': budget['estimated_plus_20_percent_cap'] == int((Decimal(budget['estimated_credits']) * Decimal('1.20')).to_integral_value(rounding=ROUND_CEILING)),
        'parent_pending_budget_cap_preserved': budget['included_credit_cap'] == 6000,
        'exact_estimate_fits_pending_cap': budget['estimated_credits'] <= budget['included_credit_cap'],
        'estimated_timing_contiguous_0_to_480': True, 'actual_listening_performed': False, 'audio_generated': False,
        'independent_qa_performed': False, 'scope_note': '제작자 자체 텍스트·값·문자수 검사. 원자료 재집계·음성 품질·실제 정렬 검수 아님.',
    })


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify']:
        verify()
        print(json.dumps(read(OUT / 'verification.json'), ensure_ascii=False))
    else:
        assert not sys.argv[1:], 'No synthesis flags are supported'
        main()
