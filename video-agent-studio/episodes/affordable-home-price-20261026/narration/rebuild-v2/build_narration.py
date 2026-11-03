"""재제작 v2: 오프라인 준비, SHA 승인 후 무료 Edge TTS. 기존 파일은 읽기만 한다."""
import argparse
import array
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
import hashlib
from html import escape
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
BASE_PATH = HERE.parent / 'production_v1.py'
spec = importlib.util.spec_from_file_location('rebuild_readonly_helpers', BASE_PATH)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
VOICE = 'ko-KR-InJoonNeural'
RATE = '+0%'
HZ = 24000
CUT_GAP_S = 0.25
FINAL_HOLD_S = 3.0
FFMPEG = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
CONTRACT_PATH = HERE / 'build_contract.json'


class BuildError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BuildError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def owned(path):
    path = Path(path).resolve()
    require(path.is_relative_to(HERE) and path != HERE, '쓰기 범위는 narration/rebuild-v2/**뿐입니다.')
    return path


def save(path, value):
    path = owned(path)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def pins():
    return {relative(p): digest(p) for p in (
        Path(__file__), CONTRACT_PATH, BASE_PATH, base.OLD / 'production_narration.py')}


def dependencies():
    # Importing does not construct Communicate or make a network request.
    sys.path.insert(0, str(base.DEPS))
    import edge_tts
    require(edge_tts.__version__ == '7.3.1', '읽기 전용 edge_tts 7.3.1이 필요합니다.')
    require('boundary' in inspect.signature(edge_tts.Communicate).parameters, 'WordBoundary 미지원')
    require(FFMPEG.is_file(), '기존 로컬 FFmpeg가 없습니다.')
    return {'edge_tts': edge_tts.__version__, 'deps_path': relative(base.DEPS),
            'ffmpeg_path': relative(FFMPEG), 'ffmpeg_sha256': digest(FFMPEG),
            'python': sys.version.split()[0], 'WordBoundary_supported': True,
            'network_calls': 0, 'installation_performed': False}


def cardinal(number):
    number = int(number)
    require(0 <= number < 10**16, '큰 숫자는 별도 발음 사전 검토가 필요합니다.')
    if not number:
        return '영'
    result = ''
    for power, unit in ((12, '조'), (8, '억'), (4, '만'), (0, '')):
        part, number = divmod(number, 10**power)
        if not part:
            continue
        section = ''
        for scale, small in ((1000, '천'), (100, '백'), (10, '십'), (1, '')):
            n, part = divmod(part, scale)
            if n:
                section += ('' if n == 1 and scale > 1 else '영일이삼사오육칠팔구'[n]) + small
        result += section + unit
    return result


def number_spoken(raw):
    parts = raw.replace(',', '').split('.')
    return cardinal(parts[0]) + ('점' + ''.join('영일이삼사오육칠팔구'[int(c)] for c in parts[1]) if len(parts) == 2 else '')


def unicode_integrity(text):
    count = len(re.findall(r'[가-힣]', text))
    require(count > 0, '한글 문자 수 0: 인코딩 손상/잘못된 낭독문')
    require(not re.search(r'\?{2,}|(?:\?\s*){3,}|\ufffd|[\ud800-\udfff]', text), '연속 ?/대체문자/서로게이트: UTF-8 복원 필요')
    require(number_spoken('0.75') == '\uc601\uc810\uce60\uc624'
            and number_spoken('4,902') == '\uc0ac\ucc9c\uad6c\ubc31\uc774'
            and number_spoken('176.4') == '\ubc31\uce60\uc2ed\uc721\uc810\uc0ac',
            '숫자 발음 사전 Python 리터럴 유니코드 손상')
    return count


def normalize(scene, dictionary):
    text = scene['narration']
    edits = []
    # Only decimal/comma numbers and abbreviations: ordinary 6억/9억/12억 stay as supplied.
    for match in re.finditer(r'(?<![\d,.])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+)(?![\d,.])', text):
        raw = match.group()
        require(Decimal(raw.replace(',', '')) >= 0, '음수 발음 검토 필요')
        edits.append((match.start(), match.end(), number_spoken(raw), '소수/쉼표 숫자 발음층'))
    for match in re.finditer(r'(?<![A-Za-z])(?:DSR|LTV|DTI)(?![A-Za-z])', text):
        spoken = {'DSR': '디 에스 알', 'LTV': '엘 티 브이', 'DTI': '디 티 아이'}[match.group()]
        edits.append((match.start(), match.end(), spoken, '약어 명료 발음'))
    # Optional explicit scene+span overrides must be reviewed as part of prepared SHA.
    for item in dictionary:
        if item['scene_id'] != scene['id']:
            continue
        a, b = item['source_start'], item['source_end']
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(text), '발음 사전 span 오류')
        require(text[a:b] == item['original'] and isinstance(item['spoken'], str) and item['spoken'].strip(), '발음 사전 원문 불일치')
        require(item.get('reason'), '발음 치환 이유 필요')
        require(not any(a < y and b > x and not (a <= x and y <= b) for x, y, _, _ in edits), '발음 치환 일부 겹침')
        edits = [e for e in edits if not (a <= e[0] and e[1] <= b)]
        edits.append((a, b, item['spoken'], item['reason']))
    result, atoms, transforms = [], [], []
    cursor = spoken_cursor = 0
    for a, b, spoken, reason in sorted(edits):
        require(a >= cursor, '발음 치환이 중복됩니다.')
        if a > cursor:
            literal = text[cursor:a]
            atoms.append({'source_start': cursor, 'source_end': a, 'spoken_start': spoken_cursor,
                          'spoken_end': spoken_cursor + len(literal), 'kind': 'literal'})
            result.append(literal)
            spoken_cursor += len(literal)
        atom = {'source_start': a, 'source_end': b, 'spoken_start': spoken_cursor,
                'spoken_end': spoken_cursor + len(spoken), 'kind': 'pronunciation',
                'original': text[a:b], 'spoken': spoken}
        atoms.append(atom)
        transforms.append({**atom, 'reason': reason})
        result.append(spoken)
        cursor, spoken_cursor = b, spoken_cursor + len(spoken)
    if cursor < len(text):
        literal = text[cursor:]
        atoms.append({'source_start': cursor, 'source_end': len(text), 'spoken_start': spoken_cursor,
                      'spoken_end': spoken_cursor + len(literal), 'kind': 'literal'})
        result.append(literal)
    spoken = ''.join(result)
    require(''.join(text[a['source_start']:a['source_end']] for a in atoms) == text, '원문 매핑 누락')
    require(''.join(spoken[a['spoken_start']:a['spoken_end']] for a in atoms) == spoken, '발음 매핑 누락')
    for atom in atoms:
        if atom['kind'] == 'literal':
            require(text[atom['source_start']:atom['source_end']] == spoken[atom['spoken_start']:atom['spoken_end']], '미기록 치환')
    return spoken, atoms, transforms


def protection(text, atoms):
    ranges = list(base.protected_ranges(text, []))
    # Protect a complete number+unit expression, including mixed Korean place values.
    number = r'\d[\d,]*(?:\.\d+)?'
    pattern = number + r'(?:\s*[조억만천백십]\s*(?:' + number + r')?)*(?:\s*(?:원|퍼센트\s*포인트|%포인트|%p|pp|%|㎡|제곱미터|개월|년|월|일|세대|가구|회|세|배|단지))?'
    ranges += [m.span() for m in re.finditer(pattern, text)]
    ranges += [(a['source_start'], a['source_end']) for a in atoms if a['kind'] == 'pronunciation']
    return sorted(set(ranges))


def sentence_spans(text):
    result, start = [], 0
    for match in re.finditer(r'[.!?。！？](?:[”’\"\']?)(?=\s|$)', text):
        end = match.end()
        if text[start:end].strip():
            a = start + len(text[start:end]) - len(text[start:end].lstrip())
            result.append((a, end))
        start = end
    if text[start:].strip():
        a = start + len(text[start:]) - len(text[start:].lstrip())
        result.append((a, len(text.rstrip())))
    require(result and base.compact(''.join(text[a:b] for a, b in result)) == base.compact(text), '문장 분할 원문 손실')
    return result


def anchor_spans(scene, q):
    result = []
    for beat in scene['beats']:
        anchor = beat['anchor']
        require(isinstance(anchor, str) and anchor.strip(), f"{scene['id']}: 빈 anchor")
        matches = list(re.finditer(re.escape(anchor), q['text']))
        require(len(matches) == 1, f"{scene['id']}: anchor 없음/중복: {anchor!r}; 원문 유일 구절 필요")
        a, b = matches[0].span()
        # When an anchor intersects a replacement, use that entire replacement span.
        # Provider word edges will cover the span; no time is interpolated within it.
        def edge(position, right=False):
            for atom in q['display_mapping']:
                if atom['source_start'] < position < atom['source_end'] and atom['kind'] != 'literal':
                    return atom['spoken_end'] if right else atom['spoken_start']
            return base.position(q, position)
        sa, sb = edge(a), edge(b, True)
        require(base.norm(q['spoken_text'][sa:sb]), f"{scene['id']}: anchor에 발화문자가 없습니다.")
        result.append({**beat, 'source_start': a, 'source_end': b, 'spoken_start': sa, 'spoken_end': sb})
    return result


def semantic_spans(q, events=None):
    # Same inherited grammar/line policy; allow a complete short sentence anywhere,
    # including a short 감사합니다. after a longer closing sentence.
    text = q['text']
    native_ends = None
    if events is not None:
        validate_events(q, events)
        cursor, native_ends = 0, {0}
        for event in events:
            cursor += len(base.norm(event['text']))
            native_ends.add(cursor)
    def allowed(index):
        return base.safe_cut(q, index) and (native_ends is None or len(base.norm(q['spoken_text'][:base.position(q, index)])) in native_ends)
    sentences, start = [], 0
    for match in re.finditer(r'[.!?。！？](?:\s+|$)', text):
        end = match.start()+1
        if allowed(end):
            sentences.append((start, end))
            start = match.end()
    if start < len(text):
        sentences.append((start, len(text)))
    result = []
    for start, end in sentences:
        if base.lines(q, start, end):
            result.append((start, end))
            continue
        cuts = [(start, start)] + [(start+m.start(), start+m.end()) for m in re.finditer(r'\s+', text[start:end])
                                  if allowed(start+m.start()) and allowed(start+m.end())] + [(end, end)]
        @lru_cache(None)
        def solve(i):
            best = None
            for j in range(i+1, len(cuts)):
                a, b = cuts[i][1], cuts[j][0]
                part = text[a:b]
                if len(base.compact(part)) <= 9 or not base.lines(q, a, b):
                    continue
                remaining = solve(j) if j < len(cuts)-1 else (0, [])
                if remaining is None:
                    continue
                score = remaining[0]-180-abs(len(part)-50)/2
                if j < len(cuts)-1:
                    grammar = base.phrase_score(part, text[cuts[j][1]:end])
                    if grammar < 0:
                        continue
                    score += grammar
                candidate = (score, [(a, b)]+remaining[1])
                if best is None or candidate[0] > best[0]:
                    best = candidate
            return best
        found = solve(0)
        require(found is not None, '의미 단위 분할 검토 필요: '+q['scene_id']+' '+text[start:end])
        result += found[1]
    require(base.compact(''.join(text[a:b] for a, b in result)) == base.compact(text), '의미 단위 원문 손실')
    return result


def prepare_data(source, dictionary):
    require(isinstance(source.get('revision'), str) and source['revision'], 'revision 필요')
    require(isinstance(source.get('policy_as_of'), str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', source['policy_as_of']), 'policy_as_of YYYY-MM-DD 필요')
    chapters = source.get('chapters')
    require(isinstance(chapters, list) and chapters, 'chapters 필요')
    chapter_ids = [c['id'] for c in chapters]
    require(all(type(i) is int for i in chapter_ids) and len(chapter_ids) == len(set(chapter_ids)), 'chapter.id는 중복 없는 정수')
    require(all(isinstance(c['title'], str) and c['title'].strip() for c in chapters), 'chapter.title 필요')
    require(isinstance(source.get('scenes'), list) and source['scenes'], 'scenes 필요')
    ids, prepared = set(), []
    known_ids = {s['id'] for s in source['scenes']}
    require(all(d['scene_id'] in known_ids for d in dictionary), '사전에 알 수 없는 scene_id')
    for index, scene in enumerate(source['scenes'], 1):
        sid = scene['id']
        require(isinstance(sid, str) and re.fullmatch(r'R\d{3,}', sid) and sid not in ids, 'R001 형식의 유일 ID 필요')
        ids.add(sid)
        require(type(scene['chapter']) is int and scene['chapter'] in chapter_ids, f'{sid}: 알 수 없는 chapter')
        for key in ('title', 'narration'):
            require(isinstance(scene[key], str) and scene[key].strip(), f'{sid}: {key} 필요')
        hangul_count = unicode_integrity(scene['narration'])
        require(all(key in scene for key in ('graphic', 'visual_notes', 'source_ids', 'beats')), f'{sid}: schema 누락')
        require(isinstance(scene['beats'], list) and isinstance(scene['source_ids'], list), f'{sid}: beats/source_ids 배열 필요')
        require(all(isinstance(b.get('action'), str) and b['action'].strip() for b in scene['beats']), f'{sid}: beat action 필요')
        spoken, atoms, transforms = normalize(scene, dictionary)
        q = {'scene_id': sid, 'paragraph': index, 'chapter': scene['chapter'], 'title': scene['title'],
             'text': scene['narration'], 'spoken_text': spoken, 'display_mapping': atoms,
             'transforms': transforms, 'protected_ranges': protection(scene['narration'], atoms),
             'source_hangul_count': hangul_count, 'spoken_hangul_count': unicode_integrity(spoken)}
        q['beats'] = anchor_spans(scene, q)
        require(len(escape(spoken).encode('utf8')) <= 4096, f'{sid}: 문단이 provider 단일 요청 한도를 넘습니다. 부모에게 장면 분리 제안 필요')
        q['sentence_count'] = len(sentence_spans(q['text']))
        q['meaning_plan'] = [{'text': q['text'][x:y], 'display_lines': base.lines(q, x, y),
                             'source_start': x, 'source_end': y, 'start_s': None, 'end_s': None,
                             'timing_basis': 'unmeasured_semantic_plan'} for x, y in semantic_spans(q)]
        require(base.compact(''.join(c['text'] for c in q['meaning_plan'])) == base.compact(q['text']), f'{sid}: 전체 큐 원문 손실')
        prepared.append(q)
    require(set(chapter_ids) == {q['chapter'] for q in prepared}, '빈 chapter')
    return prepared


def prepare(script, out, dictionary=None):
    script, out = Path(script).resolve(), owned(out)
    frozen_root = EP / 'director/rebuild-v2'
    frozen_copy = (script.parent.parent == frozen_root and script.parent.name.startswith('frozen-script-'))
    require(script.suffix == '.json' and (script.is_relative_to(EP / 'writer/rebuild-v2') or frozen_copy),
            '새 입력은 writer/rebuild-v2 또는 총괄 frozen-script JSON이어야 합니다.')
    source = load(script)
    dictionary_path = Path(dictionary).resolve() if dictionary else None
    dictionary_items = load(dictionary_path)['transforms'] if dictionary_path else []
    scenes = prepare_data(source, dictionary_items)
    dep = dependencies()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'source.json').write_bytes(script.read_bytes())
    plan = {'status': 'offline_prepared_NOT_synthesized', 'episode_id': EP.name,
            'script_path': relative(script), 'script_sha256': digest(script), 'revision': source['revision'],
            'policy_as_of': source['policy_as_of'], 'chapters': source['chapters'], 'scenes': scenes,
            'voice': VOICE, 'rate': RATE, 'internal_pauses': 'provider_natural_measured_only', 'cut_gap_s': CUT_GAP_S,
            'inputs': {relative(script): digest(script)}, 'pipeline_inputs': pins(), 'dependencies': dep,
            'dictionary': dictionary_items, 'network_calls': 0, 'audio_measured': False, 'actual_listening': False}
    if dictionary_path:
        plan['inputs'][relative(dictionary_path)] = digest(dictionary_path)
    save(out / 'prepared.json', plan)
    save(out / 'text_mapping_checks.json', {
        'script_sha256': digest(script), 'scope': 'offline text checks only',
        'source_to_spoken_exact': True, 'all_cues_preserve_source_whitespace_normalized': True,
        'anchor_unique_source_spans': True, 'native_alignment_checked': False,
        'hangul_count': sum(q['source_hangul_count'] for q in scenes),
        'repeated_question_marks_rejected': True, 'numeric_dictionary_unicode_checked': True,
        'scenes': [{'id': q['scene_id'], 'transforms': q['transforms'], 'protected_ranges': q['protected_ranges'],
                    'source_hangul_count': q['source_hangul_count'], 'spoken_hangul_count': q['spoken_hangul_count'],
                    'cue_count': len(q['meaning_plan'])} for q in scenes]})
    return plan


def command_argv(prepared, lock, authorization, out):
    return [str(Path(sys.executable).resolve()), '-X', 'utf8', str(Path(__file__).resolve()), 'generate',
            '--prepared', str(Path(prepared).resolve()), '--lock', str(Path(lock).resolve()),
            '--authorization', str(Path(authorization).resolve()), '--out', str(Path(out).resolve())]


def check_gate(prepared, lock, authorization, out):
    prepared, lock, authorization, out = map(lambda p: Path(p).resolve(), (prepared, lock, authorization, out))
    owned(prepared)
    owned(out)
    require(lock.is_relative_to(EP / 'director') and authorization.is_relative_to(EP / 'director'), '승인 파일은 부모 director 소유여야 합니다.')
    require(lock.is_file() and authorization.is_file(), '부모 확정대본/무료 외부호출 승인 파일이 없습니다.')
    plan, frozen, auth = load(prepared), load(lock), load(authorization)
    require(plan['voice'] == VOICE and plan['rate'] == RATE and plan['pipeline_inputs'] == pins(), '코드/계약 변경: 새 prepare 필요')
    for name, pin in plan['inputs'].items():
        require(digest(ROOT / name) == pin, '준비 후 입력 변경: ' + name)
    require(digest(prepared.parent / 'source.json') == plan['script_sha256'], '준비 원문 변경')
    source = load(ROOT / plan['script_path'])
    require(plan['scenes'] == json.loads(json.dumps(prepare_data(source, plan['dictionary']), ensure_ascii=False)), 'prepared 내용이 현재 변환 로직과 다릅니다.')
    require(plan['chapters'] == source['chapters'] and plan['revision'] == source['revision'] and plan['policy_as_of'] == source['policy_as_of'], '준비 메타데이터 불일치')
    require(plan['script_sha256'] == digest(ROOT / plan['script_path']), '대본 SHA 불일치')
    for item in (frozen, auth):
        require(item.get('approved') is True and item.get('episode_id') == EP.name and item.get('script_sha256') == plan['script_sha256'] and item.get('script_revision') == plan['revision'], '대상 편/대본 revision/SHA 승인 불일치')
    require(frozen.get('script_path') == plan['script_path'] and frozen.get('claude_approved') is True and frozen.get('review_reference'), '부모 Claude 확정 증거 필요')
    expected = {'source': 'main_direct_instruction', 'network_tts_authorized': True,
                'provider': 'edge-tts', 'voice': VOICE, 'rate': RATE, 'external_payload': 'text_only',
                'cash_cap_krw': 0, 'paid_calls_authorized': False, 'credentials_allowed': False,
                'automatic_retries': 0, 'prepared_sha256': digest(prepared), 'lock_sha256': digest(lock),
                'command_argv': command_argv(prepared, lock, authorization, out),
                'allowed_scene_ids': [q['scene_id'] for q in plan['scenes']],
                'max_network_attempts': len(plan['scenes'])}
    for key, value in expected.items():
        require(type(auth.get(key)) is type(value) and auth[key] == value, '실행 승인 범위 불일치: ' + key)
    require(auth.get('instruction_reference'), '부모의 현재 실행 지시 참조 필요')
    require(not out.exists(), '기존 결과 경로 보존: 새 --out 필요')
    return plan, {'lock_path': relative(lock), 'lock_sha256': digest(lock),
                  'authorization_path': relative(authorization), 'authorization_sha256': digest(authorization),
                  'prepared_sha256': digest(prepared), 'script_sha256': plan['script_sha256']}


def pcm_read(path):
    with wave.open(str(path), 'rb') as w:
        require((w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, HZ), 'WAV24k mono16 필요')
        return array.array('h', w.readframes(w.getnframes()))


def pcm_write(path, samples):
    path = owned(path)
    require(not path.exists(), '기존 WAV 보존')
    with wave.open(str(path), 'wb') as w:
        w.setparams((1, 2, HZ, 0, 'NONE', 'not compressed'))
        w.writeframes(samples.tobytes())


def ffmpeg_convert(source, target, hz):
    target = owned(target)
    require(not target.exists(), '기존 변환본 보존')
    run = subprocess.run([str(FFMPEG), '-nostdin', '-n', '-v', 'error', '-i', str(source),
                          '-ac', '1', '-ar', str(hz), '-c:a', 'pcm_s16le', str(target)], capture_output=True)
    require(run.returncode == 0 and target.is_file() and target.stat().st_size > 44, 'FFmpeg 변환 실패')
    with wave.open(str(target), 'rb') as w:
        require((w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, hz), '변환 WAV 규격 오류')


def validate_events(q, events):
    require(events and all(e.get('type') == 'WordBoundary' for e in events), '실제 WordBoundary만 허용')
    require(base.norm(''.join(e['text'] for e in events)) == base.norm(q['spoken_text']), 'provider 발화문 불일치: 원문 정렬 추정 금지')
    previous = -1
    for e in events:
        require(e['offset'] >= previous and e['duration'] > 0 and base.norm(e['text']), 'WordBoundary 시각/문자 오류')
        previous = e['offset']


def align_sentence(q, events):
    validate_events(q, events)
    intervals, cursor = [], 0
    for e in events:
        end = cursor+len(base.norm(e['text']))
        intervals.append((cursor, end))
        cursor = end
    cues = []
    for a, b in semantic_spans(q, events):
        sa, sb = base.position(q, a), base.position(q, b)
        x, y = len(base.norm(q['spoken_text'][:sa])), len(base.norm(q['spoken_text'][:sb]))
        touched = [i for i, (u, v) in enumerate(intervals) if u < y and v > x]
        require(touched, '큐/provider 단어 연결 실패')
        first, last = touched[0], touched[-1]
        require(intervals[first][0] == x and intervals[last][1] == y, 'WordBoundary 중간 큐 분할 금지')
        begin = events[first]['offset']/1e7
        end = (events[last]['offset']+events[last]['duration'])/1e7
        cues.append({'id': q['scene_id']+f'Q{len(cues)+1:03}', 'scene_id': q['scene_id'],
                     'paragraph': q['paragraph'], 'text': q['text'][a:b],
                     'spoken_text': q['spoken_text'][sa:sb], 'display_lines': base.lines(q, a, b),
                     'source_start': a, 'source_end': b, 'spoken_start': sa, 'spoken_end': sb,
                     'start_s': begin, 'end_s': end, 'native_start_s': begin, 'native_end_s': end,
                     'first_word_index': first, 'last_word_index': last,
                     'timing_basis': 'actual_provider_WordBoundary_semantic_grouping_no_interpolation'})
    return cues


def align_beats(q, words):
    stream = base.norm(q['spoken_text'])
    require(base.norm(''.join(w['text'] for w in words)) == stream, '장면 전체 단어 보존 불일치')
    ranges, cursor = [], 0
    for w in words:
        end = cursor + len(base.norm(w['text']))
        ranges.append((cursor, end))
        cursor = end
    result = []
    for beat in q['beats']:
        x = len(base.norm(q['spoken_text'][:beat['spoken_start']]))
        y = len(base.norm(q['spoken_text'][:beat['spoken_end']]))
        touched = [i for i, (a, b) in enumerate(ranges) if a < y and b > x]
        require(touched, f"{q['scene_id']}: anchor와 provider 단어 연결 실패")
        first, last = touched[0], touched[-1]
        exact = ranges[first][0] == x and ranges[last][1] == y
        result.append({**beat, 'start_s': words[first]['start_s'], 'end_s': max(words[i]['end_s'] for i in touched),
                       'first_word_index': first, 'last_word_index': last,
                       'anchor_matches_word_edges': exact,
                       'timing_basis': 'actual_provider_WordBoundary_covering_anchor_no_interpolation'})
    return result


async def synthesize_scene(q, folder):
    folder.mkdir(exist_ok=False)
    save(folder / 'request.json', {'voice': VOICE, 'rate': RATE, 'text': q['spoken_text'], 'boundary': 'WordBoundary'})
    sys.path.insert(0, str(base.DEPS))
    import edge_tts
    import edge_tts.communicate
    # Disable the library's implicit 403 retry; one stream attempt per scene.
    def reject_retry(error):
        raise error
    edge_tts.communicate.DRM.handle_client_response_error = staticmethod(reject_retry)
    events = []
    unexpected = []
    try:
        stream = edge_tts.Communicate(q['spoken_text'], VOICE, rate=RATE, pitch='+0Hz',
                                     boundary='WordBoundary', connect_timeout=15, receive_timeout=60)
        chunks = list(stream.texts)
        require(len(chunks) == 1, 'provider 내부 다중 네트워크 청크 금지')
        stream.texts = iter(chunks)
        with (folder / 'original.mp3').open('xb') as output:
            async for event in stream.stream():
                if event['type'] == 'audio':
                    output.write(event['data'])
                elif event['type'] == 'WordBoundary':
                    events.append(event)
                else:
                    unexpected.append(event)
    finally:
        save(folder / 'WordBoundary.json', events)
        save(folder / 'other_events.json', unexpected)
    require(not unexpected, '예상 밖 provider 이벤트: 정렬 확인 필요')
    validate_events(q, events)
    ffmpeg_convert(folder / 'original.mp3', folder / 'original.wav', HZ)
    values = pcm_read(folder / 'original.wav')
    signal = [i for i, v in enumerate(values) if abs(v) >= 33]
    require(signal and max(map(abs, values)) < 32767, '무음/클리핑 PCM')
    first_native = math.floor(events[0]['offset'] / 1e7 * HZ)
    native_end = math.ceil(max(e['offset'] + e['duration'] for e in events) / 1e7 * HZ)
    require(native_end <= len(values) + round(0.15 * HZ), 'provider 끝이 실제 PCM과 과도하게 다릅니다.')
    # No PCM trimming, sentence splicing or forced pause changes.
    return values, events, {'source_pcm_frames': len(values),
        'signal_start_s': signal[0]/HZ, 'signal_end_s': (signal[-1]+1)/HZ,
        'first_word_start_s': first_native/HZ, 'last_word_end_s': native_end/HZ,
        'pcm_peak': max(map(abs, values)), 'pcm_preserved': True,
        'cues': align_sentence(q, events)}


def validate_scene(q, result):
    cues = result['cues']
    require(base.compact(''.join(c['text'] for c in cues)) == base.compact(q['text']), '전체 큐 원문 보존 실패')
    require(base.compact(''.join(c['spoken_text'] for c in cues)) == base.compact(q['spoken_text']), '전체 큐 발음문 보존 실패')
    require([i for c in cues for i in range(c['first_word_index'], c['last_word_index']+1)] == list(range(len(result['words']))), '단어/큐 누락 또는 중복')
    previous_source_end = 0
    for cue in cues:
        a, b = cue['source_start'], cue['source_end']
        require(0 <= previous_source_end <= a < b <= len(q['text']), '큐 원문 순서/중복 오류')
        require(not q['text'][previous_source_end:a].strip(), '큐 사이 원문 누락')
        previous_source_end = b
        require(q['text'][a:b] == cue['text'], '큐 원문 span 오류')
        require(1 <= len(cue['display_lines']) <= 2 and max(map(len, cue['display_lines'])) <= 40, '자막 2줄/40자 제한')
        require(' '.join(' '.join(cue['display_lines']).split()) == ' '.join(cue['text'].split()), '줄바꿈 원문 손실')
        require(0 <= cue['start_s'] < cue['end_s'] <= result['duration_s'] + 1e-7, '큐 시각 범위 오류')
    for a, b in q['protected_ranges']:
        matches = [c for c in cues if c['source_start'] <= a and b <= c['source_end']]
        require(len(matches) == 1 and any(q['text'][a:b] in line for line in matches[0]['display_lines']), '숫자/단위가 큐/줄 경계에서 분리됨: '+q['text'][a:b])
    require(all(a['end_s'] <= b['start_s'] + 1e-7 for a, b in zip(cues, cues[1:])), '자막 큐 겹침')
    require(all(0 <= w['start_s'] < w['end_s'] <= result['duration_s'] + 1e-7 for w in result['words']), '단어 시각 범위 오류')
    require(all(0 <= b['start_s'] < b['end_s'] <= result['duration_s'] + 1e-7 for b in result['beats']), 'beats 시각 범위 오류')
    original = pcm_read(ROOT/result['segments'][0]['original_wav_path'])
    delivered = pcm_read(ROOT/result['audio_path'])
    require(delivered[:len(original)] == original and not any(delivered[len(original):]), '원본 PCM 보존 실패')
    with wave.open(str(ROOT/result['audio_48k_path']), 'rb') as w:
        require(w.getnframes() == 2*len(delivered), '48k WAV 길이 불일치')
    return {'id': q['scene_id'], 'text_to_spoken_mapping': 'passed', 'all_source_cues_preserved': True,
            'all_spoken_cues_preserved': True, 'all_provider_words_used_once': True,
            'protected_numbers_and_units': True, 'cue_source_spans_exact': True,
            'native_beats_cover_source_anchor': True, 'complete_original_pcm_preserved': True,
            'wav48k_duration_matches': True, 'actual_listening': False}


async def generate(prepared, lock, authorization, out):
    plan, gate = check_gate(prepared, lock, authorization, out)
    dep = dependencies()
    require(dep == plan['dependencies'], '로컬 의존성 변경: 새 prepare 필요')
    out = owned(out)
    out.mkdir(parents=True, exist_ok=False)
    save(out / 'run_inputs.json', {'gate': gate, 'pipeline_inputs': pins(), 'dependencies': dep,
         'voice': VOICE, 'rate': RATE, 'command_argv': command_argv(prepared, lock, authorization, out)})
    limit = len(plan['scenes'])
    receipt = {'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(),
               'max_network_attempts': limit, 'network_attempts_started': 0, 'scene_attempts_succeeded': 0,
               'automatic_retries': 0, 'paid_calls': 0, 'registered_credentials_read': False,
               'external_payload': 'text_only', 'attempts': [], 'cache_reused': False}
    results, checks, cursor = [], [], 0.0
    current = None
    try:
        for q in plan['scenes']:
            current = q['scene_id']
            folder = out / current
            require(digest(lock) == gate['lock_sha256'] and digest(authorization) == gate['authorization_sha256'] and digest(prepared) == gate['prepared_sha256'], '실행 중 승인/준비 파일 변경')
            require(digest(ROOT / plan['script_path']) == plan['script_sha256'] and pins() == plan['pipeline_inputs'], '실행 중 대본/코드 변경')
            require(receipt['network_attempts_started'] < limit, '무료 요청 한도 초과')
            unicode_integrity(q['spoken_text'])
            attempt = {'scene_id': current, 'attempt': 1, 'status': 'started'}
            receipt['network_attempts_started'] += 1
            receipt['attempts'].append(attempt)
            save(out / f'attempt_{current}.json', {**attempt, 'started_utc': datetime.now(timezone.utc).isoformat()})
            samples, events, record = await asyncio.wait_for(synthesize_scene(q, folder), 180)
            receipt['scene_attempts_succeeded'] += 1
            attempt['status'] = 'succeeded'
            words = [{'text': e['text'], 'start_s': e['offset']/1e7, 'end_s': (e['offset']+e['duration'])/1e7,
                      'native_word_index': i, 'timing_basis': 'actual_provider_WordBoundary'} for i, e in enumerate(events)]
            cues = record.pop('cues')
            # Provider overlaps remain in words; presentation cues never overlap.
            for a, b in zip(cues, cues[1:]):
                a['end_s'] = min(a['end_s'], b['start_s'])
            last_speech = max(max(w['end_s'] for w in words), record['signal_end_s'])
            extra_hold = FINAL_HOLD_S if q is plan['scenes'][-1] else 0.0
            target_frames = max(len(samples), math.ceil((last_speech+extra_hold)*HZ))
            samples.extend([0]*max(0, target_frames-len(samples)))
            pcm_write(folder/'audio24.wav', samples)
            ffmpeg_convert(folder/'audio24.wav', folder/'audio48.wav', 48000)
            result = {'id': current, 'chapter': q['chapter'], 'title': q['title'],
                      'narration': q['text'], 'spoken_text': q['spoken_text'],
                      'audio_path': relative(folder/'audio24.wav'), 'audio_48k_path': relative(folder/'audio48.wav'),
                      'duration_s': len(samples)/HZ, 'last_speech_end_s': last_speech,
                      'last_speech_basis': 'max_native_word_end_and_PCM_abs_ge_33_unlistened',
                      'scene_start_s': cursor, 'scene_end_s': cursor+len(samples)/HZ,
                      'gap_after_s': CUT_GAP_S if q is not plan['scenes'][-1] else 0.0,
                      'cues': cues, 'beats': align_beats(q, words), 'words': words,
                      'transforms': q['transforms'], 'display_mapping': q['display_mapping'],
                      'segments': [{'source_start': 0, 'source_end': len(q['text']),
                                    'original_mp3_path': relative(folder/'original.mp3'),
                                    'original_wav_path': relative(folder/'original.wav'),
                                    'WordBoundary_path': relative(folder/'WordBoundary.json'), **record}],
                      'natural_word_gaps': [{'after_word_index': i, 'gap_s': b['start_s']-a['end_s']}
                                            for i, (a, b) in enumerate(zip(words, words[1:])) if b['start_s']-a['end_s'] >= 0.2],
                      'original_tail_from_last_speech_s': record['source_pcm_frames']/HZ-last_speech,
                      'tail_from_last_speech_s': len(samples)/HZ-last_speech, 'pcm_frames_24k': len(samples),
                      'audio_sha256': digest(folder/'audio24.wav'), 'audio_48k_sha256': digest(folder/'audio48.wav'),
                      'actual_listening': False}
            checks.append(validate_scene(q, result))
            save(folder/'scene_timing.json', result)
            results.append(result)
            cursor = result['scene_end_s']+result['gap_after_s']
        require(digest(lock) == gate['lock_sha256'] and digest(authorization) == gate['authorization_sha256']
                and digest(prepared) == gate['prepared_sha256'] and pins() == plan['pipeline_inputs']
                and digest(ROOT / plan['script_path']) == plan['script_sha256'], '완료 전 승인/입력 변경')
        timing = {'script_sha256': plan['script_sha256'], 'script_revision': plan['revision'],
                  'policy_as_of': plan['policy_as_of'], 'voice': VOICE, 'rate': RATE, 'scenes': results,
                  'audio_revision': relative(out), 'timing_scope': 'scene_local_cues_words_beats; scene_start_s_is_body_only',
                  'total_duration_s': cursor, 'total_scene_audio_s': sum(s['duration_s'] for s in results),
                  'total_cut_silence_s': CUT_GAP_S*max(0, len(results)-1), 'cut_gap_s': CUT_GAP_S,
                  'internal_pauses': 'provider_natural_measured_not_enforced', 'final_hold_from_last_speech_s': FINAL_HOLD_S,
                  'brand_and_chapter_cards_included': False, 'gate_evidence': gate,
                  'status': 'measured_pending_independent_QA', 'actual_listening': False, 'ASR_performed': False}
        save(out/'mapping_checks.json', {'script_sha256': plan['script_sha256'], 'scenes': checks,
             'source_to_spoken_exact': True, 'all_cues_preserved': True, 'actual_listening': False})
        save(out/'timing_proposals.json', {'audio_revision': relative(out), 'common_timing_locked': False,
             'scenes': [{'scene_id': s['id'], 'start_s': s['scene_start_s'], 'end_s': s['scene_end_s'],
                         'timing_basis': 'measured_WordBoundary_PCM_body_only', 'confidence': 'measured_not_listened',
                         'audio_revision': relative(out)} for s in results]})
        save(out/'changed_scenes.json', {'changed_scene_ids': [s['id'] for s in results],
             'scenes': [{'scene_id': s['id'], 'new_duration_s': s['duration_s'], 'changed_sentences': [q['text'][a:b] for a, b in sentence_spans(q['text'])],
                         'previous_duration_s': None, 'timing_delta_s': None,
                         'comparison_basis': 'new_script_R_ids_no_assumed_old_scene_correspondence'} for s, q in zip(results, plan['scenes'])],
             'next_roles': ['director', 'editor']})
        save(out/'final_timing.json', timing)
        receipt['status'] = 'measured_pending_independent_QA'
    except Exception as error:
        receipt.update(status='failed_partial_preserved', failed_scene_id=current,
                       error_type=type(error).__name__, http_status=getattr(error, 'status', None),
                       reason=str(error) if isinstance(error, (BuildError, AssertionError, ValueError)) else None)
        raise
    finally:
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(out/'run_receipt.json', receipt)
    return timing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('inspect-deps')
    p = sub.add_parser('prepare')
    p.add_argument('--script', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--dictionary')
    for action in ('check-gate', 'generate'):
        p = sub.add_parser(action)
        for key in ('prepared', 'lock', 'authorization', 'out'):
            p.add_argument('--'+key, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'inspect-deps':
            result = dependencies()
        elif args.action == 'prepare':
            plan = prepare(args.script, args.out, args.dictionary)
            result = {'status': plan['status'], 'script_sha256': plan['script_sha256'],
                      'scenes': len(plan['scenes']), 'network_calls': 0}
        elif args.action == 'check-gate':
            _, result = check_gate(args.prepared, args.lock, args.authorization, args.out)
        else:
            timing = asyncio.run(generate(args.prepared, args.lock, args.authorization, args.out))
            result = {'status': timing['status'], 'total_duration_s': timing['total_duration_s']}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({'status': 'blocked_or_failed', 'error_type': type(error).__name__,
                          'reason': str(error) if isinstance(error, (BuildError, FileNotFoundError, ValueError)) else None}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
