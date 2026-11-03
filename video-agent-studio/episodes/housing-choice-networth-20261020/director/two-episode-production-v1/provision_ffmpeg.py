"""Verify a project-local, full FFmpeg build for canonical audio analysis."""
import array
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

EP = Path(__file__).resolve().parents[2]
ROOT = EP.parents[2]
OUT = EP / 'outputs/private-production-v1'
source = OUT / 'ffmpeg-deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
target = OUT / 'media-bin/ffmpeg.exe'
target.parent.mkdir(exist_ok=True)
shutil.copy2(source, target)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source) == sha(target)
assets = json.loads((EP / 'director/two-episode-production-v1/media_assets.json').read_text(encoding='utf-8'))
music = ROOT / next(a['path'] for a in assets['assets'] if a['asset_id'] == 'existing_channel_bgm')
voice = EP / 'narration/free-tts-v1/samples/injoon-20261026-v1/sample.wav'
checks = []
for audio in (music, voice):
    result = subprocess.run([str(target), '-v', 'error', '-i', str(audio), '-vn', '-t', '0.25', '-ac', '1', '-ar', '48000', '-f', 'f32le', 'pipe:1'], capture_output=True, check=True)
    values = array.array('f', result.stdout)
    assert len(values) == 12000 and all(math.isfinite(v) for v in values)
    assert max(abs(v) for v in values) > 0
    checks.append({'source': str(audio.relative_to(ROOT)).replace('\\', '/'), 'samples': len(values), 'finite': True, 'peak': max(abs(v) for v in values)})
version = subprocess.run([str(target), '-version'], capture_output=True, check=True, text=True).stdout
receipt = {'status': 'f32le_decode_pass', 'package': 'imageio-ffmpeg==0.6.0', 'binary': str(target.relative_to(ROOT)).replace('\\', '/'), 'binary_sha256': sha(target), 'version': version, 'checks': checks, 'global_install': False}
(Path(__file__).parent / 'ffmpeg_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': receipt['status'], 'binary': receipt['binary'], 'checks': len(checks)}))
