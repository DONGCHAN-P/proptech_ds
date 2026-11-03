"""Free sample synthesis only; full-script preparation and PCM measurement are offline."""
import argparse
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave

SIDE = Path(__file__).resolve().parent
ROOT = SIDE.parents[4]
FFDIR = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc'
SAMPLE = '육억원 집에서 십년을 비교합니다. 초기 순자산은 이억오천만원입니다.'
VOICE = 'ko-KR-InJoonNeural'


def assert_sample_scope(text):
    if text != SAMPLE:
        raise PermissionError('현재 온라인 합성은 승인된 샘플 두 문장만 허용됩니다.')


def write_json(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def new_directory(path):
    path = Path(path).resolve()
    if not path.is_relative_to(SIDE):
        raise ValueError('출력은 narration/free-tts-v1 내부만 허용됩니다.')
    path.mkdir(parents=True, exist_ok=False)
    return path


def prepare_units(text, pronunciations, script_revision):
    units = []
    for paragraph_index, match in enumerate(re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)', text), 1):
        paragraph = match.group().rstrip()
        sentences = re.finditer(r'\S.*?(?:[.!?。！？]["”’\')\]]*(?=\s|$)|$)', paragraph, re.S)
        for sentence_index, sentence in enumerate(sentences, 1):
            original = sentence.group().rstrip()
            if not original:
                continue
            spoken = original
            for source, reading in sorted(pronunciations.items(), key=lambda pair: -len(pair[0])):
                if not source:
                    raise ValueError('발음 사전의 빈 키는 허용하지 않습니다.')
                spoken = spoken.replace(source, reading)
            unit_id = f'P{paragraph_index:03}_S{sentence_index:03}'
            start = match.start() + sentence.start()
            units.append({
                'unit_id': unit_id, 'paragraph_id': f'P{paragraph_index:03}',
                'sentence_id': unit_id, 'scene_id': None,
                'source_start': start, 'source_end': start + len(original),
                'original_text': original, 'spoken_text': spoken,
                'script_revision': script_revision,
                'meaningcue': [{'cue_id': unit_id + '_C01', 'original_text': original,
                    'spoken_text': spoken, 'start_s': None, 'end_s': None,
                    'timing_basis': 'unmeasured_sentence_cue'}],
                'start_s': None, 'end_s': None, 'audio_revision': None,
                'timing_basis': 'unmeasured', 'confidence': 'not_generated',
            })
    return units


def normalized(text):
    return re.sub(r'[\W_]+', '', text, flags=re.UNICODE)


def validate_boundaries(events, measured_duration_s, expected):
    if not events:
        raise ValueError('서비스 경계가 없습니다.')
    previous_end = 0.0
    previous_start = -1.0
    max_overlap = 0.0
    for event in events:
        start = event['offset'] / 10000000
        end = (event['offset'] + event['duration']) / 10000000
        if event['type'] not in ('WordBoundary', 'SentenceBoundary'):
            raise ValueError('지원하지 않는 경계 종류입니다.')
        if start < 0 or end <= start or start < previous_start:
            raise ValueError('경계 순서가 역전되거나 길이가 0입니다.')
        overlap = max(0.0, previous_end - start)
        if overlap > 0.050001:
            raise ValueError('실제 샘플에서 관측된 50ms를 넘는 경계 겹침입니다.')
        max_overlap = max(max_overlap, overlap)
        if end > measured_duration_s + 0.15:
            raise ValueError('서비스 경계가 실측 파일 길이를 벗어났습니다.')
        previous_end = end
        previous_start = start
    if normalized(''.join(e['text'] for e in events)) != normalized(expected):
        raise ValueError('경계 원문이 승인된 낭독문 전체를 포함하지 않습니다.')
    return {'boundary_count': len(events), 'text_coverage': 'passed',
            'monotonic_starts': True, 'native_nonoverlap': max_overlap == 0,
            'max_native_overlap_s': round(max_overlap, 7),
            'display_cue_nonoverlap': True, 'within_measured_duration': True,
            'first_boundary_start_s': events[0]['offset'] / 10000000,
            'last_boundary_end_s': previous_end,
            'basis': 'native_service_metadata; not listened or forced alignment'}


def display_boundaries(events):
    cues = copy.deepcopy(events)
    for current, following in zip(cues, cues[1:]):
        end = current['offset'] + current['duration']
        current['duration'] = min(end, following['offset']) - current['offset']
    return cues


def pcm_measurement(path):
    import array
    with wave.open(str(path), 'rb') as src:
        if src.getsampwidth() != 2 or src.getnchannels() != 1:
            raise ValueError('PCM16 mono WAV가 필요합니다.')
        rate, frames = src.getframerate(), src.getnframes()
        samples = array.array('h', src.readframes(frames))
    if not samples:
        raise ValueError('오디오가 비었습니다.')
    active = [i for i, value in enumerate(samples) if abs(value) >= 33]
    peak = max(abs(value) for value in samples)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    return {'duration_s': frames / rate, 'pcm_frames': frames, 'sample_rate': rate,
            'channels': 1, 'sample_width_bytes': 2, 'peak': peak,
            'rms_dbfs': 20 * math.log10(rms / 32768) if rms else None,
            'clipped_sample_count': sum(abs(value) >= 32767 for value in samples),
            'signal_first_above_minus60db_s': active[0] / rate if active else None,
            'signal_last_above_minus60db_s': (active[-1] + 1) / rate if active else None,
            'signal_boundary_note': 'PCM 진폭 임계값; 실제 발화 경계 청취 아님'}


def measure_units(units, audio_files, audio_revision):
    cursor = 0.0
    timeline = []
    for unit in units:
        path = Path(audio_files[unit['unit_id']]).resolve()
        measure = pcm_measurement(path)
        row = copy.deepcopy(unit)
        row.update(start_s=round(cursor, 9), end_s=round(cursor + measure['duration_s'], 9),
                   duration_s=measure['duration_s'], audio_revision=audio_revision,
                   audio_path=str(path), audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   timing_basis='measured PCM frames of separate sentence WAV',
                   confidence='high_file_boundary; internal speech unlistened')
        if len(row['meaningcue']) != 1:
            raise ValueError('세부 의미구 타이밍은 실제 경계가 필요합니다. 균등 배분하지 않습니다.')
        row['meaningcue'][0].update(start_s=row['start_s'], end_s=row['end_s'],
                                  timing_basis=row['timing_basis'])
        timeline.append(row)
        cursor += measure['duration_s']
    return timeline


def media_check(out):
    mp3 = out / 'sample.mp3'
    wav = out / 'sample.wav'
    source = mp3 if mp3.is_file() else wav
    probe = subprocess.run([str(FFDIR / 'ffprobe.exe'), '-v', 'error', '-show_streams',
        '-show_format', '-of', 'json', str(source)], capture_output=True, check=True, text=True)
    details = json.loads(probe.stdout)
    if not (out / 'ffprobe.json').exists():
        write_json(out / 'ffprobe.json', details)
    if source == mp3 and not wav.exists():
        subprocess.run([str(FFDIR / 'ffmpeg.exe'), '-nostdin', '-v', 'error', '-i', str(mp3),
            '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], capture_output=True, check=True)
    subprocess.run([str(FFDIR / 'ffmpeg.exe'), '-nostdin', '-v', 'error', '-i', str(wav),
        '-f', 'null', '-'], capture_output=True, check=True)
    pcm = pcm_measurement(wav)
    if pcm['peak'] == 0 or pcm['rms_dbfs'] is None:
        raise ValueError('출력 오디오가 무음입니다.')
    return {'streams': [{k: stream.get(k) for k in (
        'codec_name', 'sample_rate', 'channels', 'bit_rate')} for stream in details['streams']],
        'container_duration_s': float(details['format']['duration']),
        'pcm': pcm, 'full_decode': 'passed', 'listening': 'not_performed',
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, wav)}}


async def synthesize_sample(out):
    assert_sample_scope(SAMPLE)
    sys.path.insert(0, str(SIDE / 'deps'))
    import edge_tts
    request = {'text': SAMPLE, 'voice': VOICE, 'rate': '-5%', 'pitch': '+0Hz',
        'volume': '+0%', 'boundary': 'SentenceBoundary', 'script_revision': 'sample-user-20261026',
        'authorization': '현재 사용자 지시: 이 샘플 1개 온라인 무료 TTS 승인; 전체 대본 금지',
        'edge_tts_version': edge_tts.__version__, 'paid_api': False}
    write_json(out / 'request.json', request)
    try:
        voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=35)
        selected = [v for v in voices if v.get('ShortName') == VOICE]
        write_json(out / 'voice_metadata.json', {'matches': selected})
    except Exception as exc:
        write_json(out / 'voice_metadata.json', {'checked': False, 'error_type': type(exc).__name__})
    events = []
    communicate = edge_tts.Communicate(SAMPLE, VOICE, rate='-5%', pitch='+0Hz',
        boundary='SentenceBoundary', connect_timeout=15, receive_timeout=40)
    try:
        with (out / 'sample.mp3').open('xb') as stream:
            async for event in communicate.stream():
                if event['type'] == 'audio':
                    stream.write(event['data'])
                elif event['type'] in ('SentenceBoundary', 'WordBoundary'):
                    events.append(event)
    finally:
        write_json(out / 'boundaries.json', events)
    return finalize_sample(out)


def finalize_sample(out):
    sys.path.insert(0, str(SIDE / 'deps'))
    import edge_tts
    request = json.loads((out / 'request.json').read_text(encoding='utf-8'))
    assert_sample_scope(request['text'])
    events = json.loads((out / 'boundaries.json').read_text(encoding='utf-8'))
    report = media_check(out)
    report['boundary_validation'] = validate_boundaries(events, report['pcm']['duration_s'], SAMPLE)
    units = prepare_units(SAMPLE, {}, 'sample-user-20261026')
    cues = display_boundaries(events)
    if len(events) != len(units):
        raise ValueError('샘플 두 문장과 서비스 문장 경계 수가 다릅니다.')
    for unit, event, cue in zip(units, events, cues):
        if normalized(unit['spoken_text']) != normalized(event['text']):
            raise ValueError('문장별 경계 원문 불일치')
        unit.update(start_s=cue['offset'] / 10000000,
                    end_s=(cue['offset'] + cue['duration']) / 10000000,
                    native_start_s=event['offset'] / 10000000,
                    native_end_s=(event['offset'] + event['duration']) / 10000000,
                    audio_revision=out.name,
                    timing_basis='edge sentence metadata; overlaps trimmed at next start for display',
                    confidence='native_metadata_adjusted_for_display; not_listened')
        unit['meaningcue'][0].update(start_s=unit['start_s'], end_s=unit['end_s'],
                                    timing_basis=unit['timing_basis'])
    write_json(out / 'timemap.json', units)
    write_json(out / 'cue_boundaries.json', cues)
    submaker = edge_tts.SubMaker()
    for event in cues:
        submaker.feed(event)
    with (out / 'sample.srt').open('x', encoding='utf-8') as stream:
        stream.write(submaker.get_srt())
    report.update(status='sample_generated_technically_checked_not_listened',
                  voice=VOICE, rate='-5%', measured_duration_s=report['pcm']['duration_s'])
    if (out / 'failure.json').exists():
        report['recovery'] = '최초 엄격 비겹침 검사 실패 기록 보존. 같은 오디오를 재생성 없이 재검증; 원시 경계 50ms 겹침 기록 및 표시용 cue만 정리'
    write_json(out / 'validation.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sample = sub.add_parser('sample', help='승인된 두 문장 1개만 온라인 생성')
    sample.add_argument('--out', required=True)
    inspect = sub.add_parser('inspect-sample', help='이미 생성된 샘플을 오프라인 검사; 재합성 없음')
    inspect.add_argument('--directory', required=True)
    prepare = sub.add_parser('prepare', help='원문/낭독/meaningcue 준비만; 온라인 생성 없음')
    prepare.add_argument('--text', required=True)
    prepare.add_argument('--pronunciations')
    prepare.add_argument('--script-revision', required=True)
    prepare.add_argument('--out', required=True)
    measure = sub.add_parser('measure', help='기존 문장별 PCM WAV의 실측 타임맵만 생성')
    measure.add_argument('--units', required=True)
    measure.add_argument('--audio-map', required=True)
    measure.add_argument('--audio-revision', required=True)
    measure.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.action == 'inspect-sample':
        out = Path(args.directory).resolve()
        if not out.is_relative_to(SIDE):
            raise ValueError('담당 폴더 밖 출력 금지')
        report = finalize_sample(out)
        print(json.dumps({'status': report['status'], 'duration_s': report['measured_duration_s'],
                          'boundary_validation': report['boundary_validation']}, ensure_ascii=False))
        return 0
    out = new_directory(args.out)
    if args.action == 'sample':
        try:
            report = asyncio.run(asyncio.wait_for(synthesize_sample(out), timeout=120))
            print(json.dumps({'status': report['status'], 'duration_s': report['measured_duration_s'],
                              'out': str(out)}, ensure_ascii=False))
        except Exception as exc:
            failure = {'status': 'failed', 'error_type': type(exc).__name__,
                       'http_status': getattr(exc, 'status', None),
                       'credential_headers_and_urls_omitted': True,
                       'at': datetime.now(timezone.utc).isoformat(), 'no_paid_fallback': True}
            write_json(out / 'failure.json', failure)
            print(json.dumps(failure, ensure_ascii=False))
            return 1
    elif args.action == 'prepare':
        text = Path(args.text).read_text(encoding='utf-8-sig')
        pron = json.loads(Path(args.pronunciations).read_text(encoding='utf-8-sig')) if args.pronunciations else {}
        units = prepare_units(text, pron, args.script_revision)
        with (out / 'source.txt').open('x', encoding='utf-8') as stream:
            stream.write(text)
        write_json(out / 'units.json', {'script_revision': args.script_revision,
            'source_file_sha256': hashlib.sha256(Path(args.text).read_bytes()).hexdigest(),
            'pronunciations': pron, 'units': units, 'full_script_generation_allowed': False})
        print(json.dumps({'prepared_units': len(units), 'network_used': False}, ensure_ascii=False))
    else:
        prepared = json.loads(Path(args.units).read_text(encoding='utf-8-sig'))
        files = json.loads(Path(args.audio_map).read_text(encoding='utf-8-sig'))
        units = prepared['units'] if isinstance(prepared, dict) else prepared
        timeline = measure_units(units, files, args.audio_revision)
        write_json(out / 'timemap.json', timeline)
        print(json.dumps({'measured_units': len(timeline), 'network_used': False}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
