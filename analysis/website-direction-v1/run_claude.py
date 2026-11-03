"""One bounded subscription-CLI design review; no provider API credentials."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
prompt = (HERE / 'claude_input.txt').read_text(encoding='utf-8')
env = os.environ.copy()
for key in list(env):
    if key.startswith(('ANTHROPIC_', 'CLAUDE_CODE_USE_')):
        env.pop(key, None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'] = '1'
command = [
    'C:/Users/e2ken/.local/bin/claude.exe', '-p', '--effort', 'low',
    '--output-format', 'json', '--tools', '', '--strict-mcp-config',
    '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence',
    '--disable-slash-commands', '--setting-sources', '',
    '--settings', '{"disableAllHooks":true}',
]
with (HERE / 'result.json').open('w', encoding='utf-8') as output, (HERE / 'stderr.log').open('w', encoding='utf-8') as error:
    result = subprocess.run(command, input=prompt, encoding='utf-8', env=env,
                            stdout=output, stderr=error, cwd=HERE, timeout=240)
receipt = dict(exit_code=result.returncode, input_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
               created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               tools_enabled=False, credential_environment_removed=True,
               external_paid_generation_calls=0)
if result.returncode == 0:
    data = json.loads((HERE / 'result.json').read_text(encoding='utf-8'))
    (HERE / 'claude_review.md').write_text(data.get('result', ''), encoding='utf-8')
    receipt.update(is_error=data.get('is_error'), usage=data.get('usage'),
                   reported_cli_estimate=data.get('total_cost_usd'),
                   billing_note='Subscription CLI estimate is not evidence of an added API charge.')
(HERE / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in receipt.items() if k != 'usage'}))
raise SystemExit(result.returncode)
