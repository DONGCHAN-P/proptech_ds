"""Editorial review of approved aggregate data/draft, via logged-in Claude only."""
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import datetime as dt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/script-review-v3'
COLLAB=OUT/'collaboration'
COLLAB.mkdir(parents=True,exist_ok=True)
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

summary=rows(ROOT/'analysis/housing_growth_2006/full_history_v1/summary.csv')
episodes=rows(ROOT/'analysis/housing_growth_2006/full_history_v1/episodes.csv')
raw=rows(ROOT/'analysis/housing_growth_2006/full_transactions_v1/quarterly_all_valid_transactions.csv')
first_last=[]
for region in dict.fromkeys(r['region'] for r in raw):
    selected=sorted((r for r in raw if r['region']==region),key=lambda r:r['quarter'])
    first_last += [selected[0],selected[-1]]
packet={'endpoint':'2026Q2','full_history_summary':summary,'all_running_peak_drawdown_episodes':episodes,'all_valid_transaction_first_last_quarters':first_last,'total_valid_transactions':6640041,'definitions':'Sixregions2006Q1-2026Q2=81quarterintervals20.25years; Sejongmatching2015Q1-2026Q2=45intervals11.25years. RawSejongearlier36110historyisnotverifiedcomplete2006citycoverage. Raw medians use ALL validtrades and changingcomposition. Matchedpriceindex uses subsets samecomplex+rounded0.01sqm, bothquarters>=2trades, >=30complexlinks, equalcomplexlogaverage. Neither is officialconstant-qualitymarkettruth or investmentreturn. Full-historyrunninghighdrawdown episodescloseatFIRST>=priorhigh, nofuturetroughuntilthatreturn; rightcensoredreturnsNULL, do not forecastend. All33episodes saved; major5% threshold is presentationonly, notfilter. Gyeonggithreshold2/3/5 latestvsownpeak -4.08/-0.58/+5.24 differentpeaks2021Q4/2021Q4/2022Q2; onlybasic2timeseriesexists.','external_verified_example':'MOLITofficialall-housingDaegucompletions2023=31630,2024=29441, verified originalcellsT12/U12 in completions_02.xlsx and independentQA. SupplyispublishedcontemporaneousboundarywhereaspriceDaeguexcludesGunwi; no causaltest.','collection':'Gwangju/Ulsan/Chungbuk/ChungnamnewcollectioninprogressNOTin7regionfrozenanalysis; keepoutofpricefacts.'}
script=(OUT/'script_v3.md').read_text(encoding='utf8')
prompt='''한국어 부동산 데이터 영상 편집자로 이 검토 대본을 검토하세요. 사용자가 이전에 7개 지역 집계·대본의 Claude 전달을 명시 승인했고, 최신 요구는 2020년 이후 한 주기에서 2006년 이후 전체 거래·전체 역사로 범위를 넓히는 것입니다. 아래 집계와 초안만 사용하며 외부 도구는 없습니다.
요청: (1) 수치·기간·지표범위의 필수 오류를 장면ID와 정확한 교체문으로 지적. 특히 664만 원거래 전체와 매칭부분표본의 차이, 누적고점 기준 에피소드, 기간의81/45분기 간격, 세종역사포괄을 확인. (2) 전체2006역사를 시청자가 실제로본 느낌이 나는지와 최근주기편향을 점검. (3) 구성/호흡 개선은 상위2개만; S001훅 또는S012결론의 짧은 대체문을 제시. 원자료 없는 미래상승/인과/회복필연 단정 금지. (4) 원거래 중위값과 매칭지수가 다른 경로를 그릴 때 어떻게 설명하면 좋을지 한 문단. 1500~2200한글자 내외Markdown. 전체대본재출력금지. 확인할 수 없는 것은 정확히 못확인했다고 남기고, 단지 조건 설명을 반복 경고/면책투로 늘리지 마세요. 아래 행들은 개별거래가 아닌 집계입니다.
검증 집계:\n'''+json.dumps(packet,ensure_ascii=False,indent=2)+'\n\n검토 대본 v3:\n'+script
(COLLAB/'verified_aggregate_packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(COLLAB/'claude_review_prompt_v3.txt').write_text(prompt,encoding='utf8')
if '--prepare-only' in sys.argv:
    print(json.dumps({'state':'prepared_locally_only','regions':len(summary),'raw_summary_rows':len(first_last),'episodes':len(episodes),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'external_calls':0},ensure_ascii=False))
    raise SystemExit(0)
env=os.environ.copy()
for key in ('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY'):
    env.pop(key,None)
cmd=[str(Path.home()/'.local/bin/claude.exe'),'-p','--model','opus','--effort','max','--output-format','json','--tools','','--permission-mode','dontAsk','--disable-slash-commands','--no-chrome','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','','--no-session-persistence','--max-budget-usd','5','--system-prompt','You are a precise Korean data-video editor. Review only supplied aggregates and script. No tools. Distinguish descriptive medians, matched index and future claims.']
t0=time.monotonic()
proc=subprocess.run(cmd,input=prompt,text=True,encoding='utf8',errors='replace',capture_output=True,cwd=COLLAB,env=env,timeout=1000)
(COLLAB/'claude_result_v3.json').write_text(proc.stdout,encoding='utf8')
response=json.loads(proc.stdout)
receipt={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-t0,2),'exit_code':proc.returncode,'requested_model':'opus','requested_effort':'max','actual_model_usage':response.get('modelUsage',{}),'is_error':response.get('is_error'),'subtype':response.get('subtype'),'usage':response.get('usage'),'cli_cost_estimate_usd':response.get('total_cost_usd'),'api_key_env_removed':True,'tools':[],'mcp':[],'authorization':'Explicit current user reply: 새 집계·대본의 Claude 전달 승인; 2006-2026Q2 regional aggregates+draftv3 only; no individualtrades/credentials transmitted','prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'script_input_sha256':hashlib.sha256(script.encode()).hexdigest(),'stderr_characters':len(proc.stderr)}
(OUT/'claude_review_v3.md').write_text(response.get('result','')+'\n',encoding='utf8')
(COLLAB/'claude_execution_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
raise SystemExit(proc.returncode or int(bool(receipt['is_error'])))
