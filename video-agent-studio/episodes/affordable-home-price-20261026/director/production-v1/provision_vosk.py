"""Fetch the official free Vosk Korean model into this episode only."""
import hashlib
import json
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
OUT = EP / 'qa/audio-v1/vosk-v1'
OUT.mkdir(exist_ok=True)
DEPS = OUT / 'deps'
CACHE = OUT / 'model-cache'
CACHE.mkdir(exist_ok=True)
URL = 'https://alphacephei.com/vosk/models/vosk-model-small-ko-0.22.zip'
archive = CACHE / 'vosk-model-small-ko-0.22.zip'
receipt = OUT / 'provision_receipt.json'
assert not archive.exists() and not receipt.exists(), 'Preserve prior download; do not silently repeat.'
proc = subprocess.run([sys.executable, '-B', '-m', 'pip', 'install', '--target', str(DEPS),
    '--cache-dir', str(OUT / 'pip-cache'), '--disable-pip-version-check', '--no-input',
    '--retries', '0', '--no-build-isolation', 'vosk==0.3.45'], capture_output=True, text=True, encoding='utf-8', errors='replace')
(OUT / 'pip.log').write_text(proc.stdout + '\n' + proc.stderr, encoding='utf-8')
assert proc.returncode == 0, 'Isolated package installation failed; inspect pip.log.'
request = urllib.request.Request(URL, headers={'User-Agent':'RealestateVideoQA/1.0'})
with urllib.request.urlopen(request, timeout=90) as response, archive.open('xb') as target:
    final_url = response.geturl()
    assert final_url.startswith('https://alphacephei.com/')
    count = 0
    while block := response.read(1024 * 1024):
        count += len(block)
        assert count < 130 * 1024 * 1024
        target.write(block)
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert sum(z.file_size for z in bundle.infolist()) < 400 * 1024 * 1024
    for member in bundle.infolist():
        target = (CACHE / member.filename).resolve()
        assert target.is_relative_to(CACHE.resolve()), 'Unsafe archive member.'
    bundle.extractall(CACHE)
sys.path.insert(0, str(DEPS))
import importlib.metadata
import vosk
versions = {d.metadata['Name']:d.version for d in importlib.metadata.distributions(path=[str(DEPS)])}
assert versions['vosk'] == '0.3.45'
data = {'status':'official_model_and_isolated_package_ready', 'at_utc':datetime.now(timezone.utc).isoformat(),
    'url':URL, 'final_url':final_url, 'archive_bytes':archive.stat().st_size,
    'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
    'model_path':str(CACHE / 'vosk-model-small-ko-0.22'), 'deps_path':str(DEPS), 'packages':versions,
    'primary_catalog':'https://alphacephei.com/vosk/models', 'model_license':'Apache-2.0',
    'HTTPS_and_ZIP_CRC_checked':True, 'publisher_checksum_available':False,
    'TTS_calls':0, 'audio_uploaded':False, 'inference_performed':False, 'cash_charge_krw':0}
receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k:data[k] for k in ['status','archive_bytes','archive_sha256','packages','cash_charge_krw']}))
