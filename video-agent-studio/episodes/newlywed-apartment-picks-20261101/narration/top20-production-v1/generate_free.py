"""Generate only the explicitly selected free Edge TTS. Never loads credentials."""
import asyncio
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave

DIR = Path(__file__).resolve().parent
ROOT = DIR.parents[4]
sys.path.insert(0, str(DIR / 'deps'))
import edge_tts

VOICE = 'ko-KR-InJoonNeural'
RATE = '+0%'
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.resolve().relative_to(DIR)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def duration(p):
    with wave.open(str(p), 'rb') as w:
        return {'duration_s': w.getnframes() / w.getframerate(), 'frames': w.getnframes(), 'sample_rate': w.getframerate(), 'channels': w.getnchannels(), 'sample_width_bytes': w.getsampwidth()}


async def generate(chunk, semaphore):
    async with semaphore:
        scene = chunk['scene_id']
        out = DIR / 'free-edge-v1'
        out.mkdir(exist_ok=True)
        receipt_path = out / (scene + '.receipt.json')
        if receipt_path.exists():
            old = read(receipt_path)
            if old['status'] == 'complete' and old['input_sha256'] == chunk['sha256']:
                for key in ['mp3', 'wav', 'metadata']:
                    assert sha(DIR / old[key]['path']) == old[key]['sha256']
                return old
            raise RuntimeError('Existing incomplete attempt; explicit free retry required: ' + scene)
        body = (DIR / chunk['path']).read_text(encoding='utf8')
        assert body == chunk['text'] and sha(DIR / chunk['path']) == chunk['sha256']
        mp3 = out / (scene + '.mp3')
        wav = out / (scene + '.wav')
        metadata = out / (scene + '.boundaries.json')
        receipt = {'scene_id': scene, 'started_at_utc': stamp(), 'status': 'in_progress', 'provider': 'microsoft_edge_consumer_tts', 'voice': VOICE, 'rate': RATE, 'input_sha256': chunk['sha256'], 'input_characters': len(body), 'charge_usd': 0, 'paid_api_calls': 0, 'automatic_retry': False, 'boundary_requested': 'WordBoundary'}
        save(receipt_path, receipt)
        boundaries = []
        try:
            comm = edge_tts.Communicate(body, VOICE, rate=RATE, volume='+0%', pitch='+0Hz', boundary='WordBoundary', connect_timeout=15, receive_timeout=35)
            with mp3.open('wb') as audio:
                async for item in comm.stream():
                    if item['type'] == 'audio':
                        audio.write(item['data'])
                    elif item['type'] in ['WordBoundary', 'SentenceBoundary']:
                        boundaries.append({k: v for k, v in item.items() if k != 'data'})
            assert mp3.stat().st_size > 1000, 'Empty audio'
            save(metadata, {'provider': receipt['provider'], 'scene_id': scene, 'units': '100ns ticks; seconds=ticks/10000000', 'boundaries': boundaries})
            result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-i', str(mp3), '-ac', '1', '-ar', '44100', '-c:a', 'pcm_s16le', '-y', str(wav)], capture_output=True, text=True)
            assert result.returncode == 0, 'Audio decode failed'
            stats = duration(wav)
            assert stats['duration_s'] > 0 and boundaries, 'Missing duration or provider boundaries'
            receipt.update(status='complete', completed_at_utc=stamp(), **stats, boundary_count=len(boundaries), boundary_type=sorted(set(b['type'] for b in boundaries)), actual_listening_performed=False)
            for key, p in [('mp3', mp3), ('wav', wav), ('metadata', metadata)]:
                receipt[key] = {'path': str(p.relative_to(DIR)).replace('\\', '/'), 'sha256': sha(p), 'bytes': p.stat().st_size}
            save(receipt_path, receipt)
            print(json.dumps({'scene_id': scene, 'status': 'complete', 'duration_s': round(stats['duration_s'], 3), 'boundaries': len(boundaries)}, ensure_ascii=False), flush=True)
            # This file is a partial audio handoff, not a timing lock.
            completed = [read(p) for p in sorted(out.glob('*.receipt.json')) if read(p).get('status') == 'complete']
            save(DIR / 'partial_audio_handoff.json', {'updated_at_utc': stamp(), 'audio_revision': 'free-edge-injoon-v1', 'status': 'partial_audio_ready_alignment_pending', 'provider': receipt['provider'], 'voice': VOICE, 'completed_scene_count': len(completed), 'scene_count_expected': 26, 'scenes': [{'scene_id': x['scene_id'], 'duration_s': x['duration_s'], 'audio_path': str((DIR / x['wav']['path']).relative_to(ROOT)).replace('\\', '/'), 'boundary_path': str((DIR / x['metadata']['path']).relative_to(ROOT)).replace('\\', '/')} for x in completed], 'actual_listening_performed': False, 'paid_api_calls': 0})
            return receipt
        except Exception as e:
            receipt.update(status='failed', completed_at_utc=stamp(), error={'type': type(e).__name__, 'reason': '무료 Edge 연결/생성/디코드 실패; 비밀값·URL 쿼리 제외', 'os_error': getattr(e, 'errno', None)}, bytes_received=mp3.stat().st_size if mp3.exists() else 0)
            save(receipt_path, receipt)
            print(json.dumps({'scene_id': scene, 'status': 'failed', 'error_type': type(e).__name__, 'os_error': getattr(e, 'errno', None), 'bytes_received': receipt['bytes_received']}, ensure_ascii=False), flush=True)
            raise


async def main():
    manifest = read(DIR / 'narration_manifest.json')
    assert sum(c['characters'] for c in manifest['chunks']) == 4281
    assert sha(ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101/writer/top20-8min-v2/script_v3.md') == '4cc70ef2ae3cabda13b560104dd96ef0df0fe1f815a5f1372ac680e729d3be17'
    save(DIR / 'authorization_free.json', {'at_utc': stamp(), 'user_reply': '무료 TTS로 진행', 'source': '최신 총괄 task packet이 전달한 명시적 사용자 선택', 'scope': '무료 Edge InJoon 우선·차단 시 Windows Heami 대체·본편26장면·Shorts 본편 재사용', 'new_paid_generation_authorized': False, 'cash_cap_krw': 0, 'elevenlabs_calls_authorized': False, 'script_sha256': manifest['input_versions']['writer/top20-8min-v2/script_v3.md']['sha256'], 'reading_manifest_sha256': sha(DIR / 'narration_manifest.json'), 'edge_voice': VOICE, 'edge_rate': RATE})
    selected = manifest['chunks']
    if sys.argv[1:]:
        selected = [c for c in selected if c['scene_id'] in sys.argv[1:]]
    assert selected
    semaphore = asyncio.Semaphore(2)
    results = await asyncio.gather(*(generate(c, semaphore) for c in selected), return_exceptions=True)
    failures = [type(r).__name__ for r in results if isinstance(r, BaseException)]
    print(json.dumps({'requested': len(selected), 'completed': len(results) - len(failures), 'failures': failures, 'provider': 'microsoft_edge_consumer_tts', 'voice': VOICE, 'edge_tts_version': edge_tts.__version__, 'paid_api_calls': 0}, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
