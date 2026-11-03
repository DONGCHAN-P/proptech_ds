"""Verify saved inputs, script sections and user-facing hardlinks after shelf refresh."""
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OUT = EP/'outputs/growth-explanation-v1'
facts = json.loads((OUT/'facts.json').read_text(encoding='utf-8'))
for relative, digest in facts['input_sha256'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest, relative
checks = json.loads((OUT/'checks.json').read_text(encoding='utf-8'))
script = (OUT/'script_growth_v2.md').read_text(encoding='utf-8')
assert len(re.findall(r'^## [0-9]+\.', script, re.M)) == 10
assert '다음 시간에는 내 종자돈과 월소득을 기준으로 매매하기에 적절한 금액대를 계산해보겠습니다.' in script
for shelf in ('매매전월세', 'housing-choice'):
    assert os.path.samefile(ROOT/'영상'/shelf/'대본_보강안.md', OUT/'script_growth_v2.md')
    assert os.path.samefile(ROOT/'영상'/shelf/'집값상승률_보강.md', OUT/'보강대본.md')
state = json.loads((EP/'state.json').read_text(encoding='utf-8'))
assert (ROOT/state['script_path']).samefile(OUT/'script_growth_v2.md')
assert state['growth_supplement']['integrated_into_video'] is False
print(json.dumps(dict(original_input_hashes_verified=len(facts['input_sha256']),
                      period_calculations_verified=facts['validation']['regional_periods_checked'],
                      unchanged_sections=checks['unchanged_sections'],
                      changed_sections=checks['changed_sections'],
                      shelf_hardlinks_verified=4,
                      voice_and_video='unchanged; script review only'), ensure_ascii=False))
