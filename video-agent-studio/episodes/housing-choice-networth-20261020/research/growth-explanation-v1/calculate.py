"""Frozen transaction aggregates and one-variable extensions of illustrative-v1."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OUT = EP / 'outputs/growth-explanation-v1'
OUT.mkdir(parents=True, exist_ok=True)


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def quarter_number(quarter):
    return int(quarter[:4])*4 + int(quarter[-1])-1


index_path = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1/quarterly_index.csv'
summary_path = index_path.with_name('regional_summary.csv')
history_path = ROOT / 'analysis/housing_growth_2006/full_history_v1/summary.csv'
model_path = EP / 'research/illustrative_model.py'
original_path = EP / 'research/illustrative_results.json'
original_script = EP / 'outputs/script-review-v1/script_v1.md'
inputs = [index_path, summary_path, history_path, model_path, original_path, original_script]
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}

indices = {}
for row in rows(index_path):
    region = indices.setdefault(row['region'], {})
    assert row['quarter'] not in region
    region[row['quarter']] = float(row['index'])
summaries = {r['region']: r for r in rows(summary_path)}
history = {r['region']: r for r in rows(history_path)}
regional = []
for name, series in indices.items():
    ordered = sorted(series, key=quarter_number)
    assert all(quarter_number(b)-quarter_number(a) == 1 for a, b in zip(ordered, ordered[1:]))
    end = ordered[-1]
    assert end == '2026Q2'
    periods = []
    for start in ['2023Q2', '2021Q2', '2016Q2', ordered[0]]:
        years = (quarter_number(end)-quarter_number(start))/4
        rate = ((series[end]/series[start])**(1/years)-1)*100
        reference = (float(summaries[name][f'cagr_{int(years)}y_pct']) if years in (3, 5, 10)
                     else float(history[name]['full_period_cagr_pct']))
        assert abs(rate-reference) < 1e-9
        periods.append(dict(start=start, end=end, years=years, cagr_pct=rate))
    regional.append(dict(region=name, periods=periods))

spec = importlib.util.spec_from_file_location('housing_illustrative', model_path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
fixture_checks = model.fixtures()
base = model.simulate()
saved = json.loads(original_path.read_text(encoding='utf-8'))['cases']['기본']
for name, path in base['paths'].items():
    assert abs(path['continuing_networth']-saved['paths'][name]['continuing_networth']) < .01

sensitivity = []
for growth in (0, .02, .04, .06):
    run = model.simulate(house_growth=growth)
    buy = run['paths']['매매']
    assert abs(buy['housing_asset']-600_000_000*(1+growth)**10) < .01
    assert buy['debt'] == base['paths']['매매']['debt']
    assert buy['invested'] == base['paths']['매매']['invested']
    for name in ('전세', '월세'):
        assert run['paths'][name] == base['paths'][name]
    sensitivity.append(dict(house_growth_pct=growth*100, house_end_krw=buy['housing_asset'],
                            networth_krw={k: v['continuing_networth'] for k, v in run['paths'].items()}))

facts = dict(version='growth-explanation-v1', data_cutoff='2026Q2',
             input_sha256=hashes, regional=regional, sensitivity=sensitivity,
             constant_model_inputs=base['assumptions'],
             cumulative_examples=[dict(gain_pct=gain, years=years,
                                       cagr_pct=((1+gain/100)**(1/years)-1)*100)
                                  for gain in (30, 50) for years in (5, 10)],
             leverage_example=dict(house_krw=600_000_000, own_equity_krw=240_000_000,
                                   loan_krw=360_000_000, price_change_pct=2,
                                   asset_value_change_krw=12_000_000,
                                   equity_change_before_costs_pct=5),
             validation=dict(regional_periods_checked=len(regional)*4,
                             scenario_checks='closed-form house values; fixed tenant paths; baseline reconciliation',
                             accounting_fixtures=fixture_checks),
             scope_notes=[
                 '기존 집계에서 재계산. 원거래 재집계·공식 지수 대조는 이번 작업 범위 밖이다.',
                 'Regional chain: matching complex/area, >=2 trades per quarter, >=30 complexes per link.',
                 'Sejong full period starts 2015Q1; other six regions start 2006Q1.',
                 '2% is a planning scenario, not an estimated historical average or forecast.',
                 'Original fees, fixed rents/deposits and other illustrative inputs are retained.',
                 'No paid generation, new voice, rendering or transmission performed.'
             ])
# Inputs remain unchanged, including the model's original main-program outputs.
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == digest for p, digest in hashes.items())
(OUT/'facts.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
lines = ['# 집값 상승률 보강 계산', '', '자료 종료: 2026Q2. 단위: 연복리 상승률(%).', '',
         '| 지역 | 최근 3년 | 최근 5년 | 최근 10년 | 전체 가용 기간 |',
         '|---|---:|---:|---:|---:|']
for region in regional:
    p = region['periods']
    lines.append('| '+region['region']+' | '+' | '.join(f"{v['cagr_pct']:.2f}" for v in p[:3])
                 +f" | {p[3]['cagr_pct']:.2f} ({p[3]['start']}–2026Q2) |")
lines += ['', '최근 3·5·10년 시작 분기는 각각 2023Q2·2021Q2·2016Q2다. 전체 이력은 6개 지역 20.25년, 세종 11.25년이다.', '',
          '## 집값 상승률만 변경', '',
          '기존 illustrative-v1. 투자 연 6%, 대출 연 4%, 10년, 임대료·보증금 고정. 단위: 억원.', '',
          '| 집값 연 상승률 | 10년 뒤 집값 | 매매 순자산 | 전세 순자산 | 월세 순자산 |',
          '|---|---:|---:|---:|---:|']
for row in sensitivity:
    values = [row['house_end_krw'], *row['networth_krw'].values()]
    lines.append(f"| {row['house_growth_pct']:.0f}% | "+' | '.join(f'{v/1e8:.4f}' for v in values)+' |')
lines += ['', '순자산은 계속거주 평가액이다. 주거 안정성에 임의의 현금 수익을 붙이지 않았다. 진입비 600만원 등 원 모형의 설명용 비용 가정을 유지했다.', '',
          '계산: CAGR=(종료 지수/시작 지수)^(1/경과 연수)−1. 입력 SHA와 검증 내역은 facts.json에 있다.']
(OUT/'계산근거.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps(dict(regional=regional[:3], sensitivity=sensitivity, checks=facts['validation']), ensure_ascii=False, indent=2))
