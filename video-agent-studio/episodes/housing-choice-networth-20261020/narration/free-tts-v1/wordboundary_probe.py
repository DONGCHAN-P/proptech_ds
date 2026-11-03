"""One explicitly authorized fixed Korean sample; never reads a full script."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys

SIDE = Path(__file__).resolve().parent
sys.path.insert(0, str(SIDE))
sys.path.insert(0, str(SIDE / 'deps'))
import edge_tts
from tts_pipeline import SAMPLE, media_check, normalized, write_json


async def run():
    out = SIDE / 'samples/injoon-wordboundary-20261026-v1'
    out.mkdir(exist_ok=False)
    write_json(out / 'request.json', {'text': SAMPLE, 'voice': 'ko-KR-InJoonNeural',
        'rate': '-5%', 'pitch': '+0Hz', 'boundary': 'WordBoundary',
        'authorization': '현재 사용자: 실제 WordBoundary 추가 작은 샘플 1회 승인',
        'edge_tts_version': edge_tts.__version__, 'full_script_generated': False})
    events = []
    try:
        communicate = edge_tts.Communicate(SAMPLE, 'ko-KR-InJoonNeural', rate='-5%',
            boundary='WordBoundary', connect_timeout=15, receive_timeout=40)
        with (out / 'sample.mp3').open('xb') as audio:
            async for event in communicate.stream():
                if event['type'] == 'audio':
                    audio.write(event['data'])
                elif event['type'] in ('WordBoundary', 'SentenceBoundary'):
                    events.append(event)
        write_json(out / 'boundaries.json', events)
        report = media_check(out)
        assert events and all(event['type'] == 'WordBoundary' for event in events)
        assert normalized(''.join(event['text'] for event in events)) == normalized(SAMPLE)
        starts = [event['offset'] / 1e7 for event in events]
        ends = [(event['offset'] + event['duration']) / 1e7 for event in events]
        assert starts == sorted(starts) and all(b > a for a, b in zip(starts, ends))
        assert max(ends) <= report['pcm']['duration_s'] + 0.15
        overlaps = [max(0, b-a) for b, a in zip(ends, starts[1:])]
        report.update(status='wordboundary_verified_not_listened', event_count=len(events),
            normalized_text_coverage='passed', max_native_overlap_s=max(overlaps, default=0),
            wordboundary_supported=True, full_script_generated=False,
            last_native_word_end_s=ends[-1], last_pcm_signal_end_s=report['pcm']['signal_last_above_minus60db_s'])
        write_json(out / 'validation.json', report)
        print(json.dumps({k:report[k] for k in ('status','event_count','wordboundary_supported','last_native_word_end_s','last_pcm_signal_end_s')}, ensure_ascii=False))
    except Exception as exc:
        if not (out / 'boundaries.json').exists():
            write_json(out / 'boundaries.json', events)
        write_json(out / 'failure.json', {'error_type': type(exc).__name__, 'http_status':getattr(exc,'status',None),
            'status':'failed','request_urls_and_headers_omitted':True,'automatic_retry':False})
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(asyncio.wait_for(run(), timeout=90))
