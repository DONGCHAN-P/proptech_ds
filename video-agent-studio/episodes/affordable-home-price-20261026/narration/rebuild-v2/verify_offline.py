"""오프라인 검사를 실행하고 UTF-8 로그·입력 SHA·검증 범위를 별도 버전에 저장한다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError('검증 출력은 narration/rebuild-v2/**만 허용합니다.')
    out.mkdir(parents=True, exist_ok=False)
    inputs = {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
              ('build_narration.py', 'build_contract.json', 'test_build_narration.py', 'verify_offline.py')}
    run = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(HERE/'test_build_narration.py')],
                         capture_output=True, encoding='utf8')
    log = run.stdout + run.stderr
    (out/'tests.log').write_text(log, encoding='utf8')
    found = re.search(r'Ran (\d+) tests?', log)
    passed = run.returncode == 0 and found is not None and log.rstrip().endswith('OK')
    receipt = {'status': 'passed' if passed else 'failed', 'exit_code': run.returncode,
               'test_count': int(found.group(1)) if found else None, 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
               'inputs_sha256': inputs, 'log_sha256': hashlib.sha256(log.encode('utf8')).hexdigest(),
               'scope': ['UTF-8/Hangul/damaged text rejection', 'minimal decimal/comma number pronunciation mapping',
                         'full source cue reassembly and number-unit protection', 'source array order and unique scene IDs',
                         'actual existing WordBoundary regression (one prior scene, read only)',
                         'synthetic covering-word anchor checks without interpolation',
                         'SHA/Claude/free-only/argv/attempt budget gate negative tests',
                         'two-scene synthesis mock: one call per scene, full PCM prefix preserved, actual local FFmpeg 48k conversion',
                         'natural internal pauses >0.35s accepted, fixed 0.25s cut gap and final 3s hold'],
               'new_script_consumed': False, 'real_new_TTS_calls': 0, 'paid_calls': 0,
               'external_network_connects_allowed_in_tests': False, 'loopback_for_Windows_asyncio_only': True,
               'actual_listening': False, 'actual_new_audio_timing_verified': False,
               'independent_QA_performed': False}
    (out/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'test_count': receipt['test_count'], 'receipt': str(out/'receipt.json'),
                      'new_TTS_calls': 0}, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
