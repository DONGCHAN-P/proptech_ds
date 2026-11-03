"""Read frozen inputs; write only this QA directory. Never import/run producer code."""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from statistics import median, fmean
import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import pyarrow
import pyarrow.parquet as pq

ROOT = Path('C:/projects/realestate_reco')
OUT = Path(__file__).resolve().parent
DATA = ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
EP = OUT.parents[1]
END = 2026*4+1
REGIONS = ['서울', '경기', '인천', '부산', '대구', '대전', '세종']
CODE_REGION = {'11':'서울', '41':'경기', '28':'인천', '26':'부산', '27':'대구', '47':'대구', '30':'대전', '29':'광주', '36':'세종'}

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def qnum(value):
    return int(value[:4])*4+int(value[-1])-1

def qstr(value):
    return f'{value//4}Q{value%4+1}'

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

discrepancies = []
comparisons = []
def compare(scope, region, field, actual, expected, tolerance=1e-9):
    if expected == '' or isinstance(expected, float) and math.isnan(expected):
        expected = None
    if isinstance(actual, (int, float)) and not isinstance(actual, bool) and expected is not None:
        expected = float(expected)
        delta = float(actual)-expected
        ok = math.isfinite(actual) and abs(delta) <= tolerance
    else:
        delta = None
        ok = actual == expected
    result = dict(scope=scope, region=region, field=field, actual=actual, expected=expected, difference=delta, passed=ok)
    comparisons.append(result)
    if not ok:
        discrepancies.append(result)

manifest = load(OUT/'input_manifest.json')
context_changes = []
for key, expected in manifest.items():
    current = (ROOT/key).stat()
    if current.st_size != expected['bytes'] or current.st_mtime_ns != expected['mtime_ns']:
        if key.endswith(('/state.json','/brief.json')):
            context_changes.append({'path':key,'note':'Other owner updated mutable episode context; not used for numerical calculations. Initial context version preserved in manifest.'})
            continue
        raise RuntimeError(f'Frozen input changed: {key}')
result = load(DATA/'results.json')
normalization = load(DATA/'normalization.json')
coverage = load(EP/'research/regional-coverage-v1/coverage.json')
paths = rows(DATA/'quarterly_index.csv')
summaries_csv = {r['region']:r for r in rows(DATA/'regional_summary.csv')}
summaries_json = {r['region']:r for r in result['summaries']}
sens = rows(DATA/'sensitivity.csv')
byregion = defaultdict(dict)
path_checks = []
for row in paths:
    region, quarter, value = row['region'], qnum(row['quarter']), float(row['index'])
    if quarter in byregion[region] or not math.isfinite(value) or value <= 0:
        raise ValueError(f'Duplicate/invalid path row: {row}')
    byregion[region][quarter] = (value, None if row['matched_complexes']=='' else int(float(row['matched_complexes'])))
compare('path_region_set', '전체', 'seven_regions', sorted(byregion), sorted(REGIONS))
metrics = []
for region in REGIONS:
    points = byregion[region]
    quarters = sorted(points)
    if quarters != list(range(quarters[0], END+1)):
        raise ValueError(f'Noncontiguous or wrong endpoint: {region}')
    if points[quarters[0]][0] != 100 or points[quarters[0]][1] is not None:
        raise ValueError(f'Wrong baseline: {region}')
    if any(points[q][1] is None or points[q][1] < 30 for q in quarters[1:]):
        raise ValueError(f'Unsupported link: {region}')
    window = [q for q in quarters if 2020*4 <= q <= 2022*4+3]
    assert len(window) == 12
    peak_q = max(window, key=lambda q:points[q][0])
    trough_q = min((q for q in quarters if q>=peak_q), key=lambda q:points[q][0])
    peak, trough, latest = points[peak_q][0], points[trough_q][0], points[END][0]
    recovered = [q for q in quarters if q>trough_q and points[q][0]>=peak]
    calculated = dict(region=region, min_trades=2, first_contiguous_quarter=qstr(quarters[0]), last_quarter=qstr(END),
                      peak_quarter=qstr(peak_q), trough_quarter=qstr(trough_q), drawdown_pct=100*(trough/peak-1),
                      first_recovery_quarter=qstr(recovered[0]) if recovered else None,
                      latest_vs_peak_pct=100*(latest/peak-1), latest_vs_trough_pct=100*(latest/trough-1),
                      min_matched_complexes=min(points[q][1] for q in quarters[1:]), latest_matched_complexes=points[END][1])
    for years in (3,5,10):
        start = END-4*years
        calculated[f'cagr_{years}y_pct'] = math.expm1(math.log(latest/points[start][0])/years)*100 if start in points else None
    for source, expected in [('regional_summary.csv', summaries_csv[region]), ('results.json/summaries',summaries_json[region]),
                             ('sensitivity.csv/minimum2',next(r for r in sens if r['region']==region and r['min_trades']=='2'))]:
        for field, value in calculated.items():
            if field != 'region':
                compare(source,region,field,value,expected[field])
    metrics.append({**calculated, 'peak_index':peak, 'trough_index':trough, 'latest_index':latest,
                    'path_rows':len(points), 'cagr_start_quarters':{str(y):qstr(END-y*4) for y in (3,5,10)}})
    path_checks.append(dict(region=region, rows=len(points), contiguous=True, positive=True, baseline=100, minimum_complex_threshold=30))
save('recalculated_metrics.json', {'definition':{'peak_window':'2020Q1–2022Q4', 'trough_window':'reference peak through 2026Q2',
    'recovery':'first observed quarterly crossing at/above reference peak after observed trough; not sustained recovery',
    'CAGR':'(2026Q2 index / same-quarter index 3/5/10 years earlier)^(1/years)-1'}, 'rows':metrics, 'path_checks':path_checks})
print('Quarterly metric recalculation completed.', flush=True)

# Restrict parquet IO to the two contract-date quarters; cancellation records share contract dates.
# Group cancellation flags by exact stored hash BEFORE dedup, then independently aggregate in Python.
frames = []
source_audit = []
columns = ['apt_id','area_m2_key','deal_date','sigungu_code','deal_amount','area_m2','is_canceled','deal_hash']
for source in (ROOT/'master/trade_events.parquet', DATA/'expansion_normalized.parquet'):
    frame = pd.read_parquet(source, columns=columns,
        filters=[('deal_date','>=',datetime(2026,1,1)),('deal_date','<',datetime(2026,7,1))])
    source_audit.append(dict(source=source.relative_to(ROOT).as_posix(), rows=len(frame)))
    frames.append(frame)
latest_frame = pd.concat(frames, ignore_index=True)
input_counts = Counter(latest_frame.sigungu_code.str[:2].map(CODE_REGION))
hash_groups = latest_frame.groupby('deal_hash', dropna=False).is_canceled.agg(['size','min','max'])
conflicts = hash_groups[(hash_groups['min']!=hash_groups['max'])]
cancel_hashes = set(hash_groups[hash_groups['max']].index)
hash_nulls = int(latest_frame.deal_hash.isna().sum())
assert hash_nulls == 0
duplicate_hash_rows = int(latest_frame.duplicated('deal_hash').sum())
filtered = latest_frame[~latest_frame.deal_hash.isin(cancel_hashes)].drop_duplicates('deal_hash').copy()
filtered = filtered[(filtered.deal_amount>0)&(filtered.area_m2>0)&filtered.apt_id.notna()].copy()
gunwi = filtered[filtered.sigungu_code.isin(['27720','47720'])]
gunwi_excluded = gunwi.sigungu_code.value_counts().to_dict()
filtered = filtered[~filtered.sigungu_code.isin(['27720','47720'])].copy()
area_cache = {a:int(Decimal(str(a)).quantize(Decimal('0.01'),rounding=ROUND_HALF_EVEN)*100) for a in filtered.area_m2.unique()}
decimal_keys = filtered.area_m2.map(area_cache)
pandas_keys = (filtered.area_m2.round(2)*100).round().astype('int64')
rounding_mismatches = int((decimal_keys!=pandas_keys).sum())
rounding_examples = filtered.loc[decimal_keys!=pandas_keys,['sigungu_code','area_m2']].copy()
rounding_examples['decimal_cents'] = decimal_keys[decimal_keys!=pandas_keys]
rounding_examples['binary_cents'] = pandas_keys[decimal_keys!=pandas_keys]
rounding_examples = rounding_examples.groupby(['sigungu_code','area_m2','decimal_cents','binary_cents']).size().reset_index(name='rows')
save('area_rounding_diagnostic.json', {'rows_affected':rounding_mismatches,'examples':rounding_examples.to_dict('records'),
     'interpretation':'Decimal(str(area)).quantize(0.01, HALF_EVEN) can differ from producer binary pandas round(2); main comparison follows the explicit producer round(2) definition.'})
print(json.dumps({'area_rounding_rows':rounding_mismatches,'examples':rounding_examples.head(12).to_dict('records')},ensure_ascii=False),flush=True)
main_area_cache = dict(zip(filtered.area_m2, pandas_keys))
filtered['region'] = filtered.sigungu_code.str[:2].map(CODE_REGION)
assert filtered.region.notna().all()
assert not filtered.is_canceled.any()
assert filtered.deal_hash.is_unique
bycell = defaultdict(list)
for row in filtered.itertuples(index=False):
    quarter = 1 if row.deal_date.month <= 3 else 2
    bycell[(row.region, row.apt_id, main_area_cache[row.area_m2], quarter)].append(float(row.deal_amount)/float(row.area_m2))
links = []
cell_rows = []
for minimum in (2,3,5):
    per_complex = defaultdict(list)
    valid_cells = Counter()
    matched_cells = Counter()
    for (region,apt,area,q), prices in bycell.items():
        if len(prices)>=minimum:
            valid_cells[(region,q)] += 1
        if q != 1 or len(prices)<minimum:
            continue
        later = bycell.get((region,apt,area,2), [])
        if len(later)<minimum:
            continue
        prior_price, later_price = median(prices), median(later)
        lr = math.log(later_price/prior_price)
        per_complex[(region,apt)].append(lr)
        matched_cells[region] += 1
        if minimum == 2:
            cell_rows.append(dict(region=region, apt_id=apt, area_key_0_01m2=area, q1_n=len(prices),q2_n=len(later),
                                  q1_median_price_per_m2=prior_price,q2_median_price_per_m2=later_price,log_link=lr))
    for region in REGIONS:
        complex_links = [fmean(values) for (reg,apt),values in per_complex.items() if reg==region]
        ratio = math.exp(fmean(complex_links)) if len(complex_links)>=30 else None
        reference_ratio = byregion[region][END][0]/byregion[region][END-1][0] if minimum==2 else None
        record = dict(region=region, min_trades=minimum, input_rows=int(input_counts[region]),
                      eligible_q1_cells=valid_cells[(region,1)],eligible_q2_cells=valid_cells[(region,2)],
                      matched_area_cells=matched_cells[region],matched_complexes=len(complex_links),ratio=ratio,
                      log_link=fmean(complex_links),change_pct=100*(ratio-1) if ratio else None,
                      path_latest_ratio=reference_ratio,difference=None if reference_ratio is None else ratio-reference_ratio)
        links.append(record)
        if minimum==2:
            compare('latest_link',region,'ratio',ratio,reference_ratio,tolerance=1e-12)
            compare('latest_link',region,'matched_complexes',len(complex_links),byregion[region][END][1],tolerance=0)
        existing = next((r for r in sens if r['region']==region and int(r['min_trades'])==minimum),None)
        if existing:
            compare(f'sensitivity_latest_counts/minimum{minimum}',region,'latest_matched_complexes',len(complex_links),existing['latest_matched_complexes'],tolerance=0)
with (OUT/'latest_matched_cells.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer = csv.DictWriter(stream,fieldnames=list(cell_rows[0]))
    writer.writeheader()
    writer.writerows(cell_rows)
alternate_cells = defaultdict(list)
for row in filtered.itertuples(index=False):
    q = 1 if row.deal_date.month <= 3 else 2
    alternate_cells[(row.region,row.apt_id,area_cache[row.area_m2],q)].append(float(row.deal_amount)/float(row.area_m2))
alternate_complex = defaultdict(list)
for (reg,apt,area,q), prices in alternate_cells.items():
    next_prices = alternate_cells.get((reg,apt,area,2),[])
    if q==1 and len(prices)>=2 and len(next_prices)>=2:
        alternate_complex[(reg,apt)].append(math.log(median(next_prices)/median(prices)))
alternate_links = []
for reg in REGIONS:
    values = [fmean(v) for (r,a),v in alternate_complex.items() if r==reg]
    ratio = math.exp(fmean(values))
    main = next(r for r in links if r['region']==reg and r['min_trades']==2)
    alternate_links.append(dict(region=reg,decimal_ratio=ratio,binary_ratio=main['ratio'],
        ratio_difference=ratio-main['ratio'],decimal_matched_complexes=len(values),binary_matched_complexes=main['matched_complexes']))
rounding_report = load(OUT/'area_rounding_diagnostic.json')
rounding_report['alternate_latest_links'] = alternate_links
rounding_report['latest_link_changed_beyond_1e_12'] = any(abs(r['ratio_difference'])>1e-12 for r in alternate_links)
rounding_report['historical_rounding_alternate_path_checked'] = False
save('area_rounding_diagnostic.json',rounding_report)
save('latest_link_recalculation.json', {'source_quarter_rows':source_audit,'period':'2026Q1→2026Q2',
    'method':'0.01m² integer-cent keys from specified binary pandas round(2); >=N trades per identical complex/area in each quarter; median price/m²; area log links averaged within complex; equal complex means; >=30 complexes; exact stored-hash dedup; cancellation takes precedence for hash conflicts; Gunwi 27720/47720 excluded',
    'cancellation_duplicate_audit':{'null_hash_rows':hash_nulls,'duplicate_hash_rows':duplicate_hash_rows,
        'conflicting_cancel_hashes':len(conflicts),'canceled_hashes':len(cancel_hashes),
        'gunwi_excluded_latest_rows_by_code':{str(k):int(v) for k,v in gunwi_excluded.items()},
        'remaining_rows':len(filtered),'rounding_key_mismatches':rounding_mismatches},'rows':links})
print('Independent latest-quarter links completed.', flush=True)

# Reconcile metadata-recorded totals, without scanning raw XML. Counts before/after dedup differ by design.
metadata_rows = []
for city in coverage['cities']:
    region = city['name_ko']
    compare('coverage_raw_totals',region,'api_rows',normalization['api_rows'][region],city['metadata_stored_rows'],tolerance=0)
    compare('coverage_raw_totals',region,'api_rows_vs_totalCount',normalization['api_rows'][region],city['metadata_declared_totalCount'],tolerance=0)
    metadata_rows.append(dict(region=region,parsed_raw_rows=normalization['api_rows'][region],
        metadata_stored_rows=city['metadata_stored_rows'],metadata_totalCount=city['metadata_declared_totalCount'],
        zero_row_metadata_cells=city['zero_stored_rows_cells']))
raw_total = sum(normalization['api_rows'].values())
compare('coverage_raw_totals','전체','total_rows',raw_total,coverage['totals']['metadata_stored_rows'],tolerance=0)
compare('coverage_raw_totals','전체','xml_file_count',normalization['xml_files'],coverage['totals']['present_expected_xml_files'],tolerance=0)
normalized_path = DATA/'expansion_normalized.parquet'
normalized_rows = pq.ParquetFile(normalized_path).metadata.num_rows
compare('coverage_raw_totals','전체','normalized_plus_dedup',normalized_rows+normalization['duplicate_transaction_keys_removed'],raw_total,tolerance=0)
compare('combined_inputs','전체','raw_rows',normalized_rows+pq.ParquetFile(ROOT/'master/trade_events.parquet').metadata.num_rows,result['raw_rows'],tolerance=0)
flags = pd.read_parquet(normalized_path,columns=['is_canceled','parse_error','id_fallback','deal_hash','region'])
compare('normalization_flags','전체','canceled_after_dedup',int(flags.is_canceled.sum()),normalization['canceled_after_dedup'],tolerance=0)
compare('normalization_flags','전체','parse_errors',int(flags.parse_error.sum()),normalization['parse_errors'],tolerance=0)
compare('normalization_flags','전체','fallback_id_rows',int(flags.id_fallback.sum()),normalization['fallback_id_rows'],tolerance=0)
compare('normalization_flags','전체','duplicate_hashes',int(flags.deal_hash.duplicated().sum()),0,tolerance=0)
for row in metadata_rows:
    row['normalized_unique_rows'] = int((flags.region==row['region']).sum())
    row['raw_minus_unique_rows'] = row['parsed_raw_rows']-row['normalized_unique_rows']
cells = coverage.get('cells', [])
save('raw_totals_reconciliation.json', {'rows':metadata_rows,'parsed_raw_total':raw_total,'normalization_unique_rows':normalized_rows,
    'normalization_removed_duplicate_rows':normalization['duplicate_transaction_keys_removed'],
    'xml_file_count_reported':normalization['xml_files'],'metadata_file_count_reported':coverage['totals']['present_expected_xml_files'],
    'coverage_scope':coverage['scope_note'],
    'limitation':'Parsed raw totals are producer normalization audit values reconciled to metadata, plus independent parquet count/flag checks; full XML totals were not independently reparsed.',
    'coverage_interpretation_status':coverage.get('interpretation_status'),
    'coverage_interpretation_findings':coverage.get('interpretation_findings')})

# A bounded cancellation sample, selected by fixed city/month/code, not a full XML walk.
samples = [('three_cities','busan','202606','26710'),('three_cities','daegu','202606','27290'),
           ('three_cities','daejeon','202606','30200'),('gwangju_sejong','sejong','202606','36110'),
           ('gwangju_sejong','gwangju','202606','29200')]
xml_evidence = []
for dataset,city,month,code in samples:
    path = ROOT/f'raw/rtms_trade_expansion/{dataset}/{city}/{month}/{code}.page1.xml'
    if not path.exists():
        xml_evidence.append({'path':path.relative_to(ROOT).as_posix(),'status':'unchecked_missing_sample'})
        continue
    raw = path.read_bytes()
    tree = ET.fromstring(raw)
    marker_counts = Counter()
    canceled_hash_list = []
    agreement = 0
    present = 0
    for item in tree.findall('.//items/item'):
        data = {child.tag:(child.text or '').strip() for child in item}
        marker_counts[(data.get('cdealType',''),bool(data.get('cdealDay','')))] += 1
        canceled = data.get('cdealType','').upper() in ('O','Y','1') or bool(data.get('cdealDay'))
        if canceled:
            import hashlib
            contract = f"{int(data['dealYear']):04d}{int(data['dealMonth']):02d}{int(data['dealDay']):02d}"
            identity = '|'.join(['api:'+data['aptSeq'],contract,str(int(data['dealAmount'].replace(',',''))),
                str(float(data['excluUseAr'])),str(int(data.get('floor') or 0)),data.get('aptDong','')])
            digest = hashlib.sha256(identity.encode()).hexdigest()
            found = flags[flags.deal_hash==digest]
            if len(found):
                present += 1
                agreement += int(bool(found.is_canceled.all()))
            canceled_hash_list.append(digest)
    import hashlib
    entry = {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
             'status':'sample_parsed','resultCode':tree.findtext('.//resultCode'), 'response_totalCount':tree.findtext('.//totalCount'),
             'parsed_page_items':sum(marker_counts.values()),
             'marker_counts':[{'cdealType':k[0],'cdealDay_present':k[1],'count':v} for k,v in marker_counts.items()],
             'canceled_marker_items':len(canceled_hash_list),'canceled_hashes_found_in_normalized':present,
             'normalized_canceled_agreements':agreement}
    xml_evidence.append(entry)
    compare('sample_xml_cancellations',city,'all_canceled_samples_found',present,len(canceled_hash_list),tolerance=0)
    compare('sample_xml_cancellations',city,'all_found_samples_canceled',agreement,present,tolerance=0)
save('xml_cancellation_samples.json', {'coverage':'5 fixed page1 files; cancellation markers and normalized canceled-flag matching only; no full XML scan', 'samples':xml_evidence})

sensitivity_summary = []
for region in REGIONS:
    record = {'region':region,'minimums':{}}
    for minimum in (2,3,5):
        row = next((r for r in sens if r['region']==region and int(r['min_trades'])==minimum),None)
        gap = next((r for r in result['gaps'] if r['region']==region and r['min_trades']==minimum),None)
        record['minimums'][str(minimum)] = {'supported_cycle_summary':row is not None,
            'first_recovery_quarter':row['first_recovery_quarter'] or None if row else None,
            'latest_vs_peak_pct':float(row['latest_vs_peak_pct']) if row else None,
            'peak_quarter':row['peak_quarter'] if row else None,
            'first_contiguous_quarter':row['first_contiguous_quarter'] if row else gap.get('first_contiguous_quarter') if gap else None,
            'gap':gap,'historical_sensitivity_recalculated':minimum==2,
            'latest_link_independently_recalculated':True}
    sensitivity_summary.append(record)
save('sensitivity_review.json', {'coverage':'Reviewed producer sensitivity.csv and results.json/gaps; independently recalculated main2 path metrics and minimum2/3/5 endpoint counts/links only; historical minimum3/5 paths not independently reconstructed.',
    'rows':sensitivity_summary,'main2_available_regions':7,'minimum3_cycle_available_regions':5,'minimum5_cycle_available_regions':1,
    'required_notes':['경기 minimum2: 미회복(-4.0789939863%); minimum3: 미회복(-0.5811950167%); minimum5: 2026Q1 최초 회복(+5.2416639586%). 회복 여부는 표본 문턱에 민감함.',
    'minimum3 서울·세종, minimum5 경기 외 6개 지역은 2020–2022 고점 전체 구간을 지지하는 연속 경로 없음. 누락을 수익률 0 또는 강건성 통과로 해석 금지.',
    '광주는 수집 응답·메타·정규화 원시 합계 0이므로 분석 불가. 실제 거래 부재나 수집 내용 정확성이 검증된 것은 아님.',
    '세종 main2 경로는 2015Q1부터; 다른 6개 지역은 2006Q1부터. 각 자체 기준값 100은 지역 간 가격 수준 비교가 아님.']})
save('comparison_details.json', {'numeric_tolerance_percentage_points':1e-9,'latest_ratio_tolerance':1e-12,'comparisons':comparisons,'discrepancies':discrepancies})
receipt = {'task_id':'regional-analysis-v1-independent-qa','status':'arithmetic_pass_with_interpretation_caveats' if not discrepancies else 'discrepancies_found',
    'classification':'exploratory_custom_index_not_official_or_investment_return',
    'checked_at':datetime.now().astimezone().isoformat(),'python':sys.version,'pandas':pd.__version__,'pyarrow':pyarrow.__version__,
    'producer_code_imported_or_executed':False,'full_xml_scan_performed':False,
    'compared_field_count':len(comparisons),'discrepancy_count':len(discrepancies),'discrepancies':discrepancies,
    'mutable_context_changes':context_changes,
    'main2_latest_links':[r for r in links if r['min_trades']==2]}
save('validation_receipt.json',receipt)
for key, expected in manifest.items():
    current = (ROOT/key).stat()
    if current.st_size != expected['bytes'] or current.st_mtime_ns != expected['mtime_ns']:
        if key.endswith(('/state.json','/brief.json')):
            continue
        raise RuntimeError(f'Input changed during audit: {key}')
print(json.dumps({'status':receipt['status'],'comparisons':len(comparisons),'discrepancies':discrepancies,
    'latest_links':[{k:r[k] for k in ('region','ratio','path_latest_ratio','matched_complexes','difference')} for r in links if r['min_trades']==2],
    'sample_xml_files':len(xml_evidence),'metadata_raw_rows':raw_total},ensure_ascii=False,indent=2))
