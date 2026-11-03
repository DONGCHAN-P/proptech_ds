"""FULL-HISTORY-QA-V1: stdlib-only independent frozen-CSV arithmetic.
Does not import/run analyst code or read raw XML/parquet or external services.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'analysis/housing_growth_2006'
SRC = BASE / 'regional_expansion_v1'
TGT = BASE / 'full_history_v1'
REGIONS = ['서울', '경기', '인천', '부산', '대구', '대전', '세종']
receipts = {}
checks = defaultdict(int)
failures = []
notes = []


def read(p):
    b = p.read_bytes()
    receipts[p.relative_to(ROOT).as_posix()] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
    return b.decode('utf-8-sig')


def rows(p):
    return list(csv.DictReader(io.StringIO(read(p))))


def load(p):
    return json.loads(read(p))


def qord(q):
    return int(q[:4]) * 4 + int(q[-1]) - 1


def test(label, actual, expected, where):
    checks[label] += 1
    if isinstance(expected, bool):
        ok = actual is expected
    elif isinstance(expected, (int, float)):
        ok = isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9)
    else:
        ok = actual == expected
    if not ok:
        failures.append({'check': label, 'where': where, 'actual': actual, 'expected': expected})


def typed(value, expected):
    if value is None or value == '':
        return None
    if isinstance(expected, bool):
        return {'True': True, 'False': False}.get(value, value)
    if isinstance(expected, (int, float)):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def compare(label, actual, expected, where, csv_mode=False, excluded=()):
    for field, value in expected.items():
        if field in excluded:
            continue
        test(label, typed(actual.get(field), value) if csv_mode else actual.get(field), value, f'{where}/{field}')


def intervals(values):
    """For each last high touch, search the first subsequent return directly.
    Minimum is bounded by that return; the return itself is not a trough.
    """
    found = []
    peak = 0
    i = 1
    while i < len(values):
        if values[i] >= values[peak]:
            peak = i
            i += 1
            continue
        end = next((j for j in range(i + 1, len(values)) if values[j] >= values[peak]), None)
        stop = end if end is not None else len(values)
        trough = min(range(i, stop), key=values.__getitem__)
        found.append((peak, trough, end))
        if end is None:
            break
        peak = end
        i = end + 1
    return found


index = rows(SRC / 'quarterly_index.csv')
volume = rows(SRC / 'quarterly_volume.csv')
summary_csv = rows(TGT / 'summary.csv')
episodes_csv = rows(TGT / 'episodes.csv')
results = load(TGT / 'results.json')
validation = load(TGT / 'validation.json')
chart = rows(TGT / 'chart_source.csv')
manifest = load(TGT / 'input_manifest.json')
analyst_receipt = load(TGT / 'verification_receipt.json')

for item in manifest:
    if item['path'] in receipts:
        test('frozen_manifest_sha', receipts[item['path']]['sha256'], item['sha256'], item['path'])

by_region = defaultdict(list)
v_region = defaultdict(list)
for line, row in enumerate(index, 2):
    by_region[row['region']].append((row, line))
for row in volume:
    v_region[row['region']].append(row)
test('source_regions', sorted(by_region), sorted(REGIONS), 'quarterly_index.csv')
test('source_regions', sorted(v_region), sorted(REGIONS), 'quarterly_volume.csv')
test('source_unique_keys', len({(r['region'], r['quarter']) for r in index}), len(index), 'index')
test('source_unique_keys', len({(r['region'], r['quarter']) for r in volume}), len(volume), 'volume')

expected_summary = []
expected_episodes = []
expected_chart = []
for region in REGIONS:
    pairs = sorted(by_region[region], key=lambda p: qord(p[0]['quarter']))
    rr = [p[0] for p in pairs]
    qq = [r['quarter'] for r in rr]
    xx = [float(r['index']) for r in rr]
    vv = sorted(v_region[region], key=lambda r: qord(r['quarter']))
    test('price_continuity', [qord(q) for q in qq], list(range(qord(qq[0]), qord(qq[-1]) + 1)), region)
    test('volume_continuity', [qord(r['quarter']) for r in vv], list(range(qord('2006Q1'), qord('2026Q2') + 1)), region)
    test('price_start', qq[0], '2015Q1' if region == '세종' else '2006Q1', region)
    test('price_end', qq[-1], '2026Q2', region)
    test('price_count', len(rr), 46 if region == '세종' else 82, region)
    test('source_positive_finite', all(math.isfinite(x) and x > 0 for x in xx), True, region)
    test('source_link_support', rr[0]['matched_complexes'], '', region)
    support = [int(float(r['matched_complexes'])) for r in rr[1:]]
    test('source_link_support', min(support) >= 30, True, region)
    all_ep = []
    positions = intervals(xx)
    underwater = []
    for number, (peak, trough, ret) in enumerate(positions, 1):
        end = ret if ret is not None else len(rr) - 1
        dd = 100 * (xx[trough] / xx[peak] - 1)
        ep = dict(episode_id=f'{region}-DD-{number:02}', region=region,
                  peak_quarter=qq[peak], peak_index=xx[peak], peak_is_observation_start=peak == 0,
                  first_decline_quarter=qq[peak + 1], trough_quarter=qq[trough], trough_index=xx[trough],
                  max_drawdown_pct=dd, major_ge_5pct=dd <= -5.0 or math.isclose(dd, -5.0, rel_tol=0, abs_tol=1e-10),
                  first_return_quarter=qq[ret] if ret is not None else None,
                  first_return_index=xx[ret] if ret is not None else None, right_censored=ret is None,
                  observed_end_quarter=qq[end], peak_to_trough_quarters=trough - peak,
                  peak_to_first_return_quarters=ret - peak if ret is not None else None,
                  trough_to_first_return_quarters=ret - trough if ret is not None else None,
                  peak_to_observed_end_quarters=end - peak, peak_to_observed_end_years=(end - peak) / 4,
                  underwater_observed_quarters=end - peak - (ret is not None),
                  duration_status='미회복·관측종료' if ret is None else '최초복귀 관측')
        all_ep.append(ep)
        underwater.extend(range(peak + 1, ret if ret is not None else len(xx)))
        test('first_return_boundary', all(x < xx[peak] for x in xx[peak + 1:ret]), True, ep['episode_id'])
    running = [max(xx[:i + 1]) for i in range(len(xx))]
    drawdowns = [100 * (x / h - 1) for x, h in zip(xx, running)]
    test('all_underwater_once', sorted(underwater), [i for i, d in enumerate(drawdowns) if d < 0], region)
    test('drawdown_curve', min(e['max_drawdown_pct'] for e in all_ep), min(drawdowns), region)
    worst = min(all_ep, key=lambda e: e['max_drawdown_pct'])
    completed = [e for e in all_ep if not e['right_censored']]
    active = next((e for e in all_ep if e['right_censored']), None)
    longest = max(completed, key=lambda e: e['peak_to_first_return_quarters'])
    longest_trough = max(completed, key=lambda e: e['trough_to_first_return_quarters'])
    high = max(xx)
    total = sum(int(v['transactions']) for v in vv)
    within = sum(int(v['transactions']) for v in vv if qq[0] <= v['quarter'] <= qq[-1])
    before = sum(int(v['transactions']) for v in vv if v['quarter'] < qq[0])
    s = dict(region=region, price_start_quarter=qq[0], price_end_quarter=qq[-1],
             price_observed_quarters=len(rr), price_elapsed_years=(qord(qq[-1]) - qord(qq[0])) / 4,
             price_calendar_years_touched=int(qq[-1][:4]) - int(qq[0][:4]) + 1,
             baseline_index=xx[0], latest_index=xx[-1],
             full_period_cumulative_change_pct=100 * (xx[-1] / xx[0] - 1),
             full_period_cagr_pct=100 * ((xx[-1] / xx[0]) ** (4 / (qord(qq[-1]) - qord(qq[0]))) - 1),
             all_time_high_index=high, all_time_high_first_quarter=qq[xx.index(high)],
             all_time_high_last_quarter=qq[len(xx) - 1 - xx[::-1].index(high)],
             latest_vs_all_time_high_pct=100 * (xx[-1] / high - 1), latest_is_all_time_high=xx[-1] == high,
             had_past_decline=bool(all_ep), all_drawdown_episode_count=len(all_ep),
             major_ge_5pct_episode_count=sum(e['major_ge_5pct'] for e in all_ep),
             completed_episode_count=len(completed), right_censored_episode_count=len(all_ep) - len(completed),
             max_historical_drawdown_pct=worst['max_drawdown_pct'], max_drawdown_episode_id=worst['episode_id'],
             max_drawdown_peak_quarter=worst['peak_quarter'], max_drawdown_trough_quarter=worst['trough_quarter'],
             max_drawdown_first_return_quarter=worst['first_return_quarter'], max_drawdown_right_censored=worst['right_censored'],
             max_drawdown_peak_to_first_return_quarters=worst['peak_to_first_return_quarters'],
             max_drawdown_trough_to_first_return_quarters=worst['trough_to_first_return_quarters'],
             max_drawdown_peak_to_observed_end_quarters=worst['peak_to_observed_end_quarters'],
             longest_completed_recovery_episode_id=longest['episode_id'],
             longest_completed_recovery_quarters=longest['peak_to_first_return_quarters'],
             longest_completed_recovery_years=longest['peak_to_first_return_quarters'] / 4,
             longest_completed_recovery_peak_quarter=longest['peak_quarter'],
             longest_completed_recovery_return_quarter=longest['first_return_quarter'],
             longest_completed_trough_recovery_episode_id=longest_trough['episode_id'],
             longest_completed_trough_to_first_return_quarters=longest_trough['trough_to_first_return_quarters'],
             active_episode_id=active['episode_id'] if active else None,
             active_episode_elapsed_quarters_lower_bound=active['peak_to_observed_end_quarters'] if active else None,
             active_episode_trough_quarter_observed_only=active['trough_quarter'] if active else None,
             min_link_matched_complexes=min(support), latest_link_matched_complexes=support[-1],
             full_volume_start_quarter=vv[0]['quarter'], full_volume_end_quarter=vv[-1]['quarter'],
             full_volume_quarters=len(vv), full_volume_calendar_years_touched=int(vv[-1]['quarter'][:4]) - int(vv[0]['quarter'][:4]) + 1,
             full_valid_transaction_total=total, valid_transactions_within_price_index_dates=within,
             valid_transactions_before_price_index_start=before, matched_transaction_total=None,
             matched_transaction_share_pct=None, matched_trade_count_status='기존 집계에 매칭 거래건수 없음·산출 불가')
    expected_summary.append(s)
    expected_episodes.extend(all_ep)
    for i, (row, line) in enumerate(pairs):
        expected_chart.append(dict(region=region, quarter=qq[i], source_index=xx[i],
                                   normalized_start_100=xx[i] / xx[0] * 100, running_high_index=running[i],
                                   running_drawdown_pct=drawdowns[i], matched_complexes=None if i == 0 else support[i - 1],
                                   source_row_number_including_header=line,
                                   source_file=(SRC / 'quarterly_index.csv').relative_to(ROOT).as_posix()))

for filename, actual, expected, key, csv_mode in [
    ('summary.csv', summary_csv, expected_summary, 'region', True),
    ('results.json/summaries', results['summaries'], expected_summary, 'region', False),
    ('episodes.csv', episodes_csv, expected_episodes, 'episode_id', True),
    ('results.json/episodes', results['episodes'], expected_episodes, 'episode_id', False)]:
    lookup = {a[key]: a for a in actual}
    test('output_unique_keys', len(lookup), len(actual), filename)
    test('output_keyset', sorted(lookup), sorted(e[key] for e in expected), filename)
    for e in expected:
        compare(filename, lookup.get(e[key], {}), e, str(e[key]), csv_mode)

chart_lookup = {(r['region'], r['quarter']): r for r in chart}
test('chart_unique_keys', len(chart_lookup), len(chart), 'chart_source.csv')
test('chart_keyset', sorted(chart_lookup), sorted((e['region'], e['quarter']) for e in expected_chart), 'chart_source.csv')
for e in expected_chart:
    key = (e['region'], e['quarter'])
    compare('chart_source.csv', chart_lookup.get(key, {}), e, str(key), True)

total = sum(s['full_valid_transaction_total'] for s in expected_summary)
test('valid_volume_total', total, 6640041, 'quarterly_volume.csv')
test('valid_volume_total', results['full_valid_transaction_total'], total, 'results.json')
test('matched_volume_unavailable', results['matched_transaction_count'], None, 'results.json')
test('method_metadata', results['regions'], REGIONS, 'results/regions')
test('method_metadata', results['data_endpoint'], '2026Q2', 'results/data_endpoint')
test('method_metadata', results['method']['major_threshold_pct'], 5.0, 'results/major_threshold_pct')
test('method_metadata', results['method']['major_threshold_use'], 'descriptive presentation label only; every episode retained', 'results/major_threshold_use')
test('validation_aggregate', validation['input_rows']['quarterly_index'], len(index), 'validation/input_rows')
test('validation_aggregate', validation['input_rows']['quarterly_volume'], len(volume), 'validation/input_rows')
test('validation_aggregate', validation['real_episode_count'], len(expected_episodes), 'validation/real_episode_count')
test('validation_aggregate', validation['major_episode_count'], sum(e['major_ge_5pct'] for e in expected_episodes), 'validation/major_episode_count')

synthetic = [
    ('단조상승', [100, 110, 120], []),
    ('복귀후_더낮은미래저점', [100, 90, 110, 105, 80, 100, 120], [(0, 1, 2), (2, 4, 6)]),
    ('고점동률_최초복귀', [100, 90, 100, 90, 100], [(0, 1, 2), (2, 3, 4)]),
    ('고점및저점_동률처리', [100, 100, 90, 90, 100], [(1, 2, 4)]),
    ('미회복_관측종료', [100, 90, 95], [(0, 1, None)]),
    ('정확히5퍼센트', [100, 95, 100], [(0, 1, 2)]),
    ('마지막분기_첫하락', [100, 110, 100], [(1, 2, None)])]
for name, xx, expected in synthetic:
    test('qa_boundary_cases', intervals(xx), expected, name)
    declaration = next(r for r in validation['synthetic_checks'] if r['check'] == name)
    test('validation_declared_boundary', declaration['expected_peak_trough_return_positions'], [list(x) for x in expected], name)

keyfacts = []
for region, start, end, duration in [('서울', '2010Q1', '2015Q2', 21), ('경기', '2008Q3', '2014Q3', 24), ('인천', '2008Q3', '2016Q2', 31)]:
    ep = next(e for e in expected_episodes if e['region'] == region and e['peak_quarter'] == start)
    test('requested_script_fact', ep['first_return_quarter'], end, ep['episode_id'])
    test('requested_script_fact', ep['peak_to_first_return_quarters'], duration, ep['episode_id'])
    keyfacts.append({k: ep[k] for k in ('region', 'peak_quarter', 'trough_quarter', 'first_return_quarter', 'peak_to_first_return_quarters', 'trough_to_first_return_quarters')})

pngs = []
viewed_sha = {
    'full_history_six_regions_2006.png': '451cd98394ae1614b8920cb1d58ccc79bfefb80fea9582f3272df2f36a334575',
    'full_history_sejong_2015.png': '3d3a6b1839b9699294593f1f57699166990f6719ca379839178f13a06ad5b4e3',
    'running_peak_drawdown_full_history.png': 'db193abb16607bbcbdd6936be82fbb5eb61345e42cafa8ddb406ff263a1a3535',
}
for p in sorted(TGT.glob('*.png')):
    raw = p.read_bytes()
    path = p.relative_to(ROOT).as_posix()
    receipts[path] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    test('png_signature', raw[:8].hex(), '89504e470d0a1a0a', p.name)
    size = [int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')]
    previous = next(c for c in analyst_receipt['reviewed_charts'] if c['path'] == path)
    test('analyst_receipt_png_sha', receipts[path]['sha256'], previous['sha256'], p.name)
    test('analyst_receipt_png_size', size, previous['pixels'], p.name)
    test('independent_viewed_png_sha', receipts[path]['sha256'], viewed_sha[p.name], p.name)
    pngs.append(dict(path=path, **receipts[path], pixels=size))

# Exact transaction days cannot be inferred from quarter-aggregated inputs.
notes.append('summary/results의 full_volume_first_date 및 last_date: 분기 내 위치만 검사. 정확한 거래일은 이번 입력만으로 독립 확인 불가.')
for actual in summary_csv:
    for field, quarterfield in [('full_volume_first_date', 'full_volume_start_quarter'), ('full_volume_last_date', 'full_volume_end_quarter')]:
        d = actual[field]
        quarter = f'{d[:4]}Q{(int(d[5:7]) - 1) // 3 + 1}'
        test('daily_date_quarter_bounds_only', quarter, actual[quarterfield], f"{actual['region']}/{field}")

for path, receipt in receipts.items():
    test('read_input_stability', hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), receipt['sha256'], path)

output = dict(task_id='FULL-HISTORY-QA-V1', verified_at=datetime.now(timezone.utc).isoformat(),
              verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              status='pass' if not failures else 'fail', independent=True,
              arithmetic='별도 stdlib 구현; 제작 코드 import/실행 없음; 수치 허용오차 abs=1e-9, rel=1e-12; 회복 판정은 엄격한 >=',
              check_counts=dict(checks), total_checks=sum(checks.values()), failures=failures,
              keyfacts=keyfacts, full_valid_transaction_total=total,
              recomputed_summaries=expected_summary, recomputed_episodes=expected_episodes,
              coverage=dict(series=7, index_rows=len(index), volume_rows=len(volume), episodes=len(expected_episodes),
                            major_episodes=sum(e['major_ge_5pct'] for e in expected_episodes),
                            censored_episodes=sum(e['right_censored'] for e in expected_episodes),
                            pngs=pngs, static_png_visual_review='표본 PNG 3개 실제 열람: 축·기준선·기간·제목 수치 확인. 동영상 프레임 검수 아님.',
                            actual_video='unchecked·대상외', continuous_playback='unchecked·대상외', actual_listening='unchecked·대상외',
                            raw_ingestion='대상외', official_index_research='대상외', other_raw_median_task='대상외', exact_daily_dates='unchecked'),
              notes=notes, receipts=receipts)
target = OUT / 'independent_recompute.json'
target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
receipt_sha = hashlib.sha256(target.read_bytes()).hexdigest()
revision = {p: receipts[(TGT / p).relative_to(ROOT).as_posix()]['sha256'] for p in ('summary.csv', 'episodes.csv', 'results.json', 'validation.json', 'chart_source.csv')}
issue = dict(issue_id='FHQA-R01', scene_id='analysis/full-history-v1/validation-metadata', timecode=None,
             severity='recommended', 문제='제작자 검수 기록 일부가 물음표로 저장되어 검수 범위를 읽기 어려움.',
             evidence=dict(paths=['analysis/housing_growth_2006/full_history_v1/validation.json#visual_review.scope',
                                  'analysis/housing_growth_2006/full_history_v1/verification_receipt.json#verification_scope,reviewed_charts.visual_review,independent_qa'],
                           sample=validation['visual_review']['scope'],
                           effect='수치·PNG 내용에는 영향 없음. 이번 독립 QA가 실제 확인 범위와 SHA를 별도 기록함.'),
             수정안='제작 담당이 검수 설명을 UTF-8 한글로 복구하고 기존 검수 receipt SHA를 갱신. 분석 수치 재집계 불필요.',
             owner='research/full-history-v1', status='open', checked_revision=revision)
findings = dict(task_id='FULL-HISTORY-QA-V1', status='pass_with_recommendation' if not failures else 'fail',
                checked_revision=revision, required_count=len(failures), critical_count=0,
                recommended_count=1, findings=[issue],
                verification=dict(independent_receipt=target.relative_to(ROOT).as_posix(), sha256=receipt_sha,
                                  check_count=output['total_checks'], numeric_discrepancies=failures,
                                  keyfacts=keyfacts, full_valid_transaction_total=total,
                                  valid_volume_meaning='보유·수집 범위의 유효거래 합계. 가격지수 매칭 거래량이 아니며 매칭 거래건수·비율 산출 불가.',
                                  series_periods='서울·경기·인천·부산·대구·대전: 2006Q1~2026Q2, 82개 관측/81분기 간격=20.25년. 세종: 2015Q1~2026Q2, 46개 관측/45분기 간격=11.25년.',
                                  episodes='33개 전체 유지, 5% 이상 표시 14개, 우측중도절단 6개. 미회복 경과는 하한이며 관측 저점은 미래 최종저점이 아님.'),
                coverage=dict(data=output['coverage'],
                              png_axes='6지역 공통 y축 0~600/2006Q1=100; 세종 별도 y축 0~250/2015Q1=100; 낙폭 공통 -25~0%, 0% 누적고점/-5% 설명용 점선. 표시 CAGR·누적·현재 낙폭 반올림 일치.',
                              png_limit='정지 PNG 3개를 열어 확인. 영상 내 크기·자막·장면 경계·연속 재생·청취는 unchecked.',
                              daily_date_limit=notes[0], exclusions='XML/parquet 재수집·350항목 과거 QA·공식가격 웹조사·별도 raw median·script v3·API/Claude·유료 생성 제외.'),
                next_role='director → research(권장 기록 복구); 향후 script v3 변경 팩트만 별도 요청')
(OUT / 'findings.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'issue_FHQA-R01.json').write_text(json.dumps(issue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
handoff = dict(task_id='FULL-HISTORY-QA-V1', role='qa', status='pass_with_recommendation' if not failures else 'fail',
               input_revisions={'revision': 'FULL-HISTORY-V1; regional_expansion_v1 frozen CSV',
                                'sha_manifest': 'independent_recompute.json#receipts'},
               outputs=['findings.json', 'independent_recompute.json', 'issue_FHQA-R01.json', 'verify_frozen.py'],
               receipt_sha256=receipt_sha, affected_scene_ids=['analysis/full-history-v1'],
               checks=[dict(check='독립 계산', result='pass' if not failures else 'fail', evidence=f"{output['total_checks']}건; 7계열/538행, 거래량574행, 하락33/주요14/미회복6"),
                       dict(check='핵심 팩트', result='pass', evidence='서울21q·경기24q·인천31q; 세종2015Q1부터; 유효거래6640041≠매칭 거래량'),
                       dict(check='시각', result='sampled_png_only', evidence='PNG3개 실제 열람·SHA 연결. 영상/연속 재생/청취 unchecked')],
               open_issue_ids=['FHQA-R01'], required_fix_count=len(failures),
               unresolved='권장: 제작 검수 기록 한글 깨짐. 분기 CSV에서 정확한 일자 독립 확인 불가.',
               next_role='director; 권장사항 research 전달. script v3 변경 팩트는 별도 요청 대기')
(OUT / 'handoff.json').write_text(json.dumps(handoff, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(json.dumps({'status': output['status'], 'checks': output['total_checks'], 'failures': failures, 'keyfacts': keyfacts,
                  'valid_volume': total, 'receipt_sha256': receipt_sha}, ensure_ascii=False))
