"""Scoped QA: import the illustrative model; never run its file-writing main."""
import csv
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
EP = OUT.parents[1]
ROOT = EP.parents[2]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

paths = [EP / p for p in [
    "outputs/cost-wording-v3/script_cost_v3.md", "outputs/growth-explanation-v1/facts.json",
    "research/illustrative_model.py", "research/illustrative_model_note.md", "research/illustrative_results.json",
    "qa/regional-analysis-v1/findings.json", "qa/regional-analysis-v1/validation_receipt.json",
    "qa/regional-analysis-v1/input_manifest.json", "qa/regional-analysis-v1/sensitivity_review.json",
    "director/two-episode-production-v1/authorization.json"]]
paths += [ROOT / ("analysis/housing_growth_2006/regional_expansion_v1/" + p)
          for p in ["quarterly_index.csv", "regional_summary.csv", "sensitivity.csv", "results.json"]]
before = {p.relative_to(ROOT).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size} for p in paths}
facts = read(EP / "outputs/growth-explanation-v1/facts.json")
stored = read(EP / "research/illustrative_results.json")
spec = importlib.util.spec_from_file_location("illustrative_model_independent_qa", EP / "research/illustrative_model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
fixtures = model.fixtures()
cases = {"기본": {},
         "집0%_주식2%": dict(house_growth=0, stock_return=.02),
         "집4%_주식2%": dict(house_growth=.04, stock_return=.02),
         "집0%_주식8%": dict(house_growth=0, stock_return=.08),
         "집4%_주식8%": dict(house_growth=.04, stock_return=.08),
         "전세금리2%_매수6%": dict(rate=.06, jeonse_loan_rate=.02),
         "전세금리6%_매수2%": dict(rate=.02, jeonse_loan_rate=.06),
         "차액투자0%": dict(execution=0), "차액투자50%": dict(execution=.5),
         "월예산10만원_불가능": dict(budget=100_000),
         "집4%_주식6%": dict(house_growth=.04), "집6%_주식6%": dict(house_growth=.06),
         "월세120만원": dict(monthly_rent=1_200_000)}
runs = {name: model.simulate(**kwargs) for name, kwargs in cases.items()}
checks = []

def check(label, actual, expected, tolerance=.01):
    if actual is None or expected is None:
        passed = actual is expected
        error = None
    else:
        error = abs(actual - expected)
        passed = error <= tolerance
    checks.append(dict(check=label, actual=actual, expected=expected, absolute_error=error,
                       tolerance=tolerance, result="pass" if passed else "fail"))

# Independent closed forms: ending debt and annuity-due timing expressed as ordinary monthly deposits.
closed_forms = []
ledger_rows = 0
for name, run in runs.items():
    a = run["assumptions"]
    for label, v in run["paths"].items():
        if name in stored["cases"]:
            original = stored["cases"][name]["paths"][label]
            for field in ["initial_invested", "housing_asset", "debt", "invested", "cash", "continuing_networth", "liquidation_networth"]:
                check(f"저장값/{name}/{label}/{field}", v[field], original[field])
        if not v["feasible"]:
            assert v["continuing_networth"] is None and v["monthly_ledger"] == []
            continue
        n = a["months"]
        r = a["stock_return"]
        monthly = math.expm1(math.log1p(r) / 12)
        factor = math.exp(n * math.log1p(r) / 12)
        annuity = math.expm1(n * math.log1p(r) / 12) / monthly if monthly else n
        debt = 200_000_000 if label == "전세" else 20_000_000
        if label == "매매":
            lr = a["rate"] / 12
            cf_pay = 360_000_000 * lr / (-math.expm1(-360*math.log1p(lr))) if lr else 1_000_000
            check(f"독립상환액/{name}", v["mortgage_payment"], cf_pay)
            debt = 360_000_000 * (1 + lr) ** n - cf_pay * ((1 + lr) ** n - 1) / lr if lr else 360_000_000 - n * cf_pay
            housing = 600_000_000 * (1 + a["house_growth"]) ** 10
            initial = 250_000_000 - 240_000_000 - a["entry_buy"]
            surplus = a["budget"] - cf_pay - a["owner_cost"]
        else:
            housing = 400_000_000 if label == "전세" else 100_000_000
            initial = 250_000_000 - (housing-debt) - a["entry_rent"]
            loan_rate = a["jeonse_loan_rate"] if label == "전세" else a["rent_loan_rate"]
            surplus = a["budget"] - debt*loan_rate/12 - a["rent_cost"] - (a["monthly_rent"] if label == "월세" else 0)
        invested = initial * factor + surplus * a["execution"] * annuity
        cash = surplus * (1-a["execution"]) * n
        for field, actual, expected in [("invested", v["invested"], invested), ("debt", v["debt"], debt),
                                         ("housing", v["housing_asset"], housing),
                                         ("networth", v["continuing_networth"], housing + invested + cash - debt)]:
            check(f"독립닫힌식/{name}/{label}/{field}", actual, expected)
        prev = v["initial_networth_after_entry"]
        old_invested, old_house = v["initial_invested"], 600_000_000 if label == "매매" else housing
        errors = []
        for row in v["monthly_ledger"]:
            rent = a["monthly_rent"] if label == "월세" else 0
            ongoing = a["owner_cost"] if label == "매매" else a["rent_cost"]
            expected_gain = a["budget"] - row["interest"] - ongoing - rent + old_invested * monthly + row["housing_asset"] - old_house
            errors.append(abs(row["networth"] - prev - expected_gain))
            prev, old_invested, old_house = row["networth"], row["invested"], row["housing_asset"]
        ledger_rows += len(errors)
        check(f"월장부보존식/{name}/{label}", max(errors), 0)
        closed_forms.append(dict(case=name, path=label, continuing_networth_krw=v["continuing_networth"],
                                 ending_invested_krw=v["invested"], ending_cash_krw=v["cash"],
                                 ending_debt_krw=v["debt"], max_ledger_identity_error_krw=max(errors)))

base = runs["기본"]["paths"]
spoken = []

def claim(section, description, actual, displayed, rounding_unit):
    row = dict(section=section, description=description, actual_krw=actual, spoken_krw=displayed,
               rounding_unit_krw=rounding_unit, absolute_error_krw=abs(actual-displayed),
               result="pass" if abs(actual-displayed) <= rounding_unit/2+.01 else "fail")
    spoken.append(row)

for label, start, ending, fin in [("매매", 4_000_000, 614_000_000, 167_000_000),
                                 ("전세", 49_000_000, 659_000_000, 459_000_000),
                                 ("월세", 169_000_000, 689_000_000, 609_000_000)]:
    p = base[label]
    claim(3, label+" 초기투자금", p["initial_invested"], start, 1)
    claim(7, label+" 기말순자산", p["continuing_networth"], ending, 1_000_000)
    claim(7, label+" 기말금융자산", p["invested"], fin, 1_000_000)
for label, outflow, contribution in [("매매", 2_020_000, 980_000), ("전세", 720_000, 2_280_000), ("월세", 1_120_000, 1_880_000)]:
    first = base[label]["monthly_ledger"][0]
    claim(4, label+" 월주거지출", first["housing_cash_outflow"], outflow, 10_000)
    claim(4, label+" 월투자금", first["invest_contribution"], contribution, 10_000)
claim(4, "매매 월원리금", base["매매"]["mortgage_payment"], 1_720_000, 10_000)
claim(5, "매매 첫달원금", base["매매"]["monthly_ledger"][0]["principal"], 520_000, 10_000)
claim(5, "첫달후대출", base["매매"]["monthly_ledger"][0]["debt"], 359_500_000, 100_000)
claim(5, "10년상환원금", base["매매"]["total_principal"], 76_000_000, 1_000_000)
claim(5, "10년후대출", base["매매"]["debt"], 284_000_000, 1_000_000)
claim(7, "기말주택평가액", base["매매"]["housing_asset"], 731_000_000, 1_000_000)
claim(7, "월세매매격차", base["월세"]["continuing_networth"]-base["매매"]["continuing_networth"], 74_000_000, 1_000_000)
claim(7, "월세전세격차", base["월세"]["continuing_networth"]-base["전세"]["continuing_networth"], 30_000_000, 1_000_000)
for name, values, unit in [("집4%_주식6%", {"매매":770_000_000},10_000_000),
                           ("집6%_주식6%", {"매매":960_000_000},10_000_000),
                           ("집4%_주식2%", {"매매":740_000_000},10_000_000),
                           ("집4%_주식2%", {"전세":562_000_000,"월세":536_000_000},1_000_000),
                           ("집0%_주식8%", {"매매":502_000_000,"전세":717_000_000,"월세":784_000_000},1_000_000),
                           ("전세금리2%_매수6%", {"전세":713_000_000,"매매":525_000_000},1_000_000),
                           ("전세금리6%_매수2%", {"매매":698_000_000},1_000_000),
                           ("월세120만원", {"월세":656_000_000},1_000_000),
                           ("차액투자50%", {"매매":594_000_000,"월세":649_000_000},1_000_000),
                           ("차액투자50%", {"전세":610_000_000},10_000_000)]:
    for label, shown in values.items():
        claim(9 if name == "차액투자50%" else 8, name+"/"+label, runs[name]["paths"][label]["continuing_networth"], shown, unit)
check("집0%_주식2%에서전세최대", int(runs["집0%_주식2%"]["winner"] == "전세"), 1)
for scenario in facts["sensitivity"]:
    run = model.simulate(house_growth=scenario["house_growth_pct"]/100)
    check("facts/집기말/"+str(scenario["house_growth_pct"]), run["paths"]["매매"]["housing_asset"], scenario["house_end_krw"])
    for label, val in scenario["networth_krw"].items():
        check("facts/민감도/"+str(scenario["house_growth_pct"])+"/"+label, run["paths"][label]["continuing_networth"], val)
check("환율과총수익복리21%", (1.1*1.1-1)*100, 21, 1e-12)
check("레버리지2%가격변화", 600_000_000*.02, facts["leverage_example"]["asset_value_change_krw"])
check("레버리지자기자금비율5%", 600_000_000*.02/240_000_000*100, 5, 1e-12)
for example in facts["cumulative_examples"]:
    check("facts/누적수익률예시", ((1+example["gain_pct"]/100)**(1/example["years"])-1)*100, example["cagr_pct"], 1e-10)
for key, val in facts["constant_model_inputs"].items():
    check("facts/기본가정/"+key, runs["기본"]["assumptions"][key], val, 1e-12)

def rows(name):
    with (ROOT / "analysis/housing_growth_2006/regional_expansion_v1" / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def qi(q):
    return int(q[:4])*4+int(q[-1])-1

index_rows = rows("quarterly_index.csv")
lookup = {(r["region"],r["quarter"]):r for r in index_rows}
summary = {r["region"]:r for r in rows("regional_summary.csv")}
periods = []
for region in facts["regional"]:
    reg = region["region"]
    for period in region["periods"]:
        start, end = period["start"], period["end"]
        years = (qi(end)-qi(start))/4
        value = (float(lookup[reg,end]["index"])/float(lookup[reg,start]["index"]))**(1/years)*100-100
        check("지역CAGR/"+reg+"/"+start, value, period["cagr_pct"], 1e-10)
        check("지역기간/"+reg+"/"+start, years, period["years"], 1e-12)
        if years in (3,5,10):
            check("지역기존요약/"+reg+"/"+start, value, float(summary[reg][f"cagr_{int(years)}y_pct"]), 1e-10)
        links = [r for r in index_rows if r["region"]==reg and qi(start)<qi(r["quarter"])<=qi(end)]
        assert len(links) == int(years*4)
        counts = [int(float(r["matched_complexes"])) for r in links]
        periods.append(dict(region=reg, start=start, end=end, years=years, cagr_pct=value,
                            links=len(links), min_matched_complexes=min(counts), max_matched_complexes=max(counts),
                            latest_matched_complexes=counts[-1],
                            minimum_count_quarters=[r["quarter"] for r,c in zip(links,counts) if c==min(counts)]))

facts_hashes = []
for name, expected in facts["input_sha256"].items():
    p = ROOT / name.replace("\\", "/")
    actual = digest(p)
    facts_hashes.append(dict(path=p.relative_to(ROOT).as_posix(), expected_sha256=expected, actual_sha256=actual, matches=actual==expected))
old_manifest = read(EP / "qa/regional-analysis-v1/input_manifest.json")
prior_input_matches = []
for name, old in old_manifest.items():
    if name in before:
        prior_input_matches.append(dict(path=name, expected_sha256=old["sha256"], current_sha256=before[name]["sha256"], matches=old["sha256"]==before[name]["sha256"]))
after = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
unchanged = all(before[k]["sha256"]==after[k] for k in before)
failures = [x for x in checks+spoken if x["result"]=="fail"]
result = dict(task_id="private-production-v1-content-qa", checked_at=datetime.now(timezone.utc).isoformat(),
              status="pass" if not failures and unchanged and all(x["matches"] for x in facts_hashes+prior_input_matches) else "fail",
              producer_main_executed=False, bytecode_writes_disabled=True, raw_trade_reaggregation=False,
              fixtures=fixtures, numerical_check_count=len(checks), spoken_amount_check_count=len(spoken),
              ledger_rows_independently_checked=ledger_rows, regional_period_count=len(periods), failures=failures,
              input_manifest=before, input_unchanged_after_import=unchanged, facts_input_hash_checks=facts_hashes,
              selected_prior_qa_input_hash_checks=prior_input_matches,
              prior_qa_scope_note="기존 검수 중 선택한 소형 집계 입력 해시만 대조. 원거래·parquet·최신 연결비를 이번에 재집계하거나 재검수하지 않음.",
              checks=checks, spoken_amount_checks=spoken, scenarios=closed_forms)
save("numeric_audit.json", result)
save("regional_period_crosscheck.json", dict(periods=periods, existing_sensitivity_rows=rows("sensitivity.csv"),
     sensitivity_scope="2/3/5건 표의 기존 수치와 결측 경로 검토. 최소3/5건 경로 자체 재구축·원거래 재집계 미수행."))
print(json.dumps({k:result[k] for k in ["status","numerical_check_count","spoken_amount_check_count","ledger_rows_independently_checked","regional_period_count","input_unchanged_after_import","failures"]},ensure_ascii=False))
assert result["status"] == "pass"
