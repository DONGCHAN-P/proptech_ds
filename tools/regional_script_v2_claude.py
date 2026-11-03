"""Run an explicitly requested Claude collaborator, with no file/shell tools."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/script-review-v2'
COLLAB = OUT / 'collaboration'
COLLAB.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1'
results = json.loads((DATA / 'results.json').read_text(encoding='utf-8'))
packet = {
    'endpoint': '2026Q2',
    'regions': results['summaries'],
    'periods': {'3y': '2023Q2-2026Q2', '5y': '2021Q2-2026Q2', '10y': '2016Q2-2026Q2'},
    'method': 'Our exploratory quarterly matched apartment index, not an official index or an investment return. Same complex and area rounded to 0.01 square meters, median price/m2, at least 2 transactions in BOTH quarters per area; log-average within complex then equal-weight complexes. At least 30 complexes per link, no filling gaps. Metro 2006Q1+, Sejong contiguous 2015Q1+; no Sejong 2006 history. Gunwi excluded from Daegu for fixed boundary. Gwangju unavailable (API all-zero anomaly, not zero market transactions). Cancelled transactions excluded.',
    'peak_definition': 'For each region, maximum quarter in 2020Q1-2022Q4. Drawdown: that peak to subsequently observed minimum through 2026Q2. Latest vs trough is cumulative, NOT annual. First recovery: first observed quarter after trough >= that peak, NOT a guarantee of sustained recovery.',
    'sensitivity': 'Gyeonggi latest vs its own 2020-2022 peak: min2 -4.078994%; min3 -0.58%; min5 +5.24% with a different peak 2022Q2 and first recovery 2026Q1. Changing threshold changes the sample AND peak. This is not a confidence interval, min5 is not inherently truer. Other min5 region cycles lack coverage, cannot extrapolate. Avoid ONLY SEOUL recovered as an unqualified headline.',
    'limits': 'Changing matched samples, no floor/renovation controls, historical metro and new collection different vintages. Small sample minima Seoul43 Sejong35; show match counts on-screen. Average region does not imply all apartments recover. Broad regions do not support district or specific complex conclusions.',
    'external_factors': 'Collected official supply and migration descriptions exist but causal tests not complete; age migration/households/jobs long panels not yet aligned with prices. Do not claim jobs, population or construction caused a regional path; present 3 testable hypotheses: post-peak supply burden/recovery delay, households+young adult movement+jobs versus total population, region-specific response to common rates. No new external numerical claims in this draft without verified packet.',
    'next_episode': 'Housing-choice buy/jeonse/monthly rent uses 2% home appreciation and 6% investment as illustrative scenarios, not empirical future forecasts. Keep at most a brief bridge, do not make this regional episode a buy/rent ranking.',
}
packet_path = COLLAB / 'verified_facts.json'
packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
prompt = '''한국어 부동산 데이터 해설 유튜브 채널 '데이터로 보는 부동산'의 구성·대본 작가로 작업하세요.
사용자가 요청한 실제 Claude 최대 추론 협업입니다. 외부 도구는 제공하지 않습니다. 아래 검증 사실 패킷만 사용하고 숫자/인과/출처를 새로 만들지 마세요.

목표: 7개 지역 아파트 실거래의 고점·하락·반등·회복 차이를 차트로 보여주며 인사이트를 찾는 독립 영상의 대본 v2. 이전 매매/전세/월세 편의 전단계 영상입니다.
가제 추천: '집값 다 올랐다는데, 왜 내 지역은 아직일까? | 7개 지역 고점과 회복'
약 10~12분을 목표로 하되 음성 길이는 추정입니다. 낭독 3,800~5,000 한글 음절 정도로 충분히 설명하세요. 질문만 던지고 끝내지 말고 실제 데이터에서 확인한 3가지 결론을 끝에 회수하세요.
톤: 단정하고 친근한 구어체, 초반 5초에 흥미로운 실제 차이. 선정성 대신 관측된 격차로 긴장감. 행정 절차/연구 과제 목록/면책 조항으로 장황하게 만들지 마세요. 가정과 한계를 구체적인 사례 안에서 설명하세요.
구성 예시: 서울과 대구 고점 대비 간극 훅 → 이전 고점의 정의·비교법 짧게 → 반등과 회복은 다름(인천/세종) → 수도권 내 서울/경기/인천 차이와 경기 민감도 바로 인접해서 설명 → 부산/대구/대전/세종의 다른 시간 경로 → 3년/5년/10년 시작점 차이(세종 및 대구 주요 숫자, 나머지는 화면표로) → 수요·공급·금리 3가설을 이번 편 결론과 구별 → 오늘의 확인한 인사이트, 구체적 다음 편과 CTA.
방법론은 짧고 명확하게, 세부 조건은 화면과 별첨으로. 2006 자료 활용은 장기 차트에서 보여주되 세종은 2015부터, 장기 공통 비교는 2015로. 3/5/10년은 반드시 동분기 연환산 복리 수치. 서울10년 수치가 큰 것은 임의로 고치지 말고 자체 지수로 정확히 제한. 수치 낭독은 필요한 대표값 1자리 반올림, 거의0인 대구3년은 '거의 제자리'.

출력은 Markdown 한 문서. 맨 위 추천 제목과 대안2개, 핵심 한 문장, 예상 길이(실제 음성 미확정). S001...S014 안팎의 장면별로 `### S001 ...`, `**낭독**` 다음 자연스러운 2~4개 문단, `**화면**` 아래 핵심 자료와 강조 동작 1~2문장. 낭독에 내부 담당/검수/파일 경로나 작업 지시를 넣지 마세요. 마지막에 짧은 편집 메모(필수 각주/추가검증/다음 편)만 붙이세요. 실제 영상 제작은 하지 않습니다.

검증 사실 패킷:\n''' + json.dumps(packet, ensure_ascii=False, indent=2)
review = '--review' in sys.argv
if review:
    draft_text = (OUT/'script_v2.md').read_text(encoding='utf-8')
    prompt = '''당신은 한국어 데이터 해설 영상의 구성·대본 총괄 편집자입니다. 사용자가 7개 지역 집계와 대본 초안을 Claude Opus(max)에 전달해 검토하도록 명시 승인했습니다. 외부 도구 없이 아래 사실 패킷과 대본만 검토하세요.
목표: 더 흥미롭고 이해하기 쉬운 지역별 고점·회복 영상. 집값/금리/인구의 원인이나 미래 수익을 만들어내지 마세요. 이 자체지수는 공식 시장 대표값 검증 전인 탐색 결과입니다. 경기 표본 민감도, 세종2015시작, 광주미확보 등 핵심 조건을 유지하세요.
요청: 1) 수치·논리에서 반드시 고칠 사항이 있는지, 없으면 없다고 명시. 2) 흥미와 호흡을 개선할 상위3개만, 장면ID와 정확한 대체 문장을 제시. 3) S001 도입과 S012 결론의 개선 낭독문을 각각 완결된 한국어로 작성. 4) 후속 공급·이동 조사에 어떤 자료 한 개를 가장 먼저 붙일지와 이유.
현재11~14분목표를 유지하고 방법론/한계 설명은 구체 사례에 붙이세요. 권장 분량은 한글 약1500~2500자. 전체 대본을 다시 출력하지 마세요. 사실에 없는 수치/인용/지역별 원인단정 금지. Markdown으로 출력하세요.
검증된 집계 패킷:\n''' + json.dumps(packet, ensure_ascii=False, indent=2) + '\n\n검토 대상 Codex 대본 v2:\n' + draft_text
prompt_path = COLLAB / ('claude_review_prompt_v2.txt' if review else 'claude_prompt_v2.txt')
prompt_path.write_text(prompt, encoding='utf-8')
env = os.environ.copy()
for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY'):
    env.pop(key, None)
cmd = [str(Path.home() / '.local/bin/claude.exe'), '-p', '--model', 'opus', '--effort', 'max', '--output-format', 'json', '--tools', '', '--permission-mode', 'dontAsk', '--disable-slash-commands', '--no-chrome', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--setting-sources', '', '--no-session-persistence', '--max-budget-usd', '5', '--system-prompt', 'You are a careful Korean nonfiction script editor. Use only the supplied facts. Follow the requested review format. No tools or outside research are available.']
started = dt.datetime.now(dt.timezone.utc).isoformat()
t0 = time.monotonic()
proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=COLLAB, env=env, timeout=1000)
raw = proc.stdout
(COLLAB / ('claude_review_result_v2.json' if review else 'claude_result_v2.json')).write_text(raw, encoding='utf-8')
# Never copy environment, credentials or debug logs into the receipt.
receipt = {'started_at_utc': started, 'duration_seconds': round(time.monotonic()-t0, 2), 'exit_code': proc.returncode, 'requested_model': 'opus', 'requested_effort': 'max', 'auth_method_verified_before_run': 'claude.ai', 'cli_subscription_type_before_run': 'pro', 'api_key_env_removed': True, 'tools': [], 'mcp': [], 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'stderr_characters': len(proc.stderr)}
receipt.update(mode='editorial_review' if review else 'draft', payload_authorization='explicit user reply: 집계 수치와 대본 전달 승인' if review else 'initial request to use Claude maximum setting', api_budget_guard_usd=5)
try:
    response = json.loads(raw)
    receipt.update({k: response.get(k) for k in ('is_error', 'subtype', 'num_turns', 'duration_api_ms', 'total_cost_usd', 'usage')})
    receipt['actual_model_usage'] = response.get('modelUsage', {})
    draft = response.get('result', '')
    (OUT / ('claude_editorial_review_v2.md' if review else 'claude_draft_v2.md')).write_text(draft + '\n', encoding='utf-8')
    receipt['draft_characters'] = len(draft)
except json.JSONDecodeError:
    receipt['parse_error'] = True
    receipt['safe_error_excerpt'] = raw[:300] if 'token' not in raw.lower() else 'See local response; not printed.'
if proc.stderr and not raw:
    receipt['safe_error_kind'] = 'CLI stderr; inspect without credentials'
(COLLAB / 'claude_execution_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False, indent=2))
raise SystemExit(proc.returncode or (1 if receipt.get('is_error') or receipt.get('parse_error') else 0))
