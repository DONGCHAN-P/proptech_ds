from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path('C:/projects/realestate_reco')
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1'
EP = OUT.parents[1]
paths = [DATA / n for n in ('results.json', 'quarterly_index.csv', 'regional_summary.csv', 'sensitivity.csv', 'normalization.json', 'expansion_normalized.parquet')]
paths += [DATA.with_suffix('.py'), ROOT/'master/trade_events.parquet', EP/'research/regional-coverage-v1/coverage.json', EP/'state.json', EP/'brief.json']
manifest = {}
for path in paths:
    digest = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    s = path.stat()
    manifest[path.relative_to(ROOT).as_posix()] = dict(sha256=digest, bytes=s.st_size, mtime_ns=s.st_mtime_ns)
(OUT/'input_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

coverage = json.loads((EP/'research/regional-coverage-v1/coverage.json').read_text(encoding='utf-8-sig'))
summary = {'python':sys.version, 'pandas':pd.__version__, 'coverage_keys':list(coverage), 'coverage_totals':coverage.get('totals')}
summary['coverage_cities'] = [{k:v for k,v in c.items() if k not in ('by_code', 'cells', 'files', 'month_cells')} for c in coverage['cities']]
summary['parquet'] = {}
for path in (DATA/'expansion_normalized.parquet', ROOT/'master/trade_events.parquet'):
    pf = pq.ParquetFile(path)
    brief = {'rows':pf.metadata.num_rows,'row_groups':pf.num_row_groups,'schema':str(pf.schema_arrow)}
    columns = ['sigungu_code', 'is_canceled', 'deal_date']
    if 'region' in pf.schema_arrow.names:
        columns += ['region', 'parse_error', 'id_fallback']
    frame = pd.read_parquet(path, columns=columns)
    brief['code_counts'] = {str(k):int(v) for k,v in frame.sigungu_code.str[:2].value_counts(dropna=False).items()}
    brief['null_counts'] = frame.isna().sum().to_dict()
    brief['cancel_values'] = frame.is_canceled.value_counts(dropna=False).astype(int).to_dict()
    brief['date_min'] = str(frame.deal_date.min())
    brief['date_max'] = str(frame.deal_date.max())
    if 'region' in frame:
        brief['region_counts'] = frame.region.value_counts().astype(int).to_dict()
    summary['parquet'][path.relative_to(ROOT).as_posix()] = brief
(OUT/'input_inspection.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str)+'\n',encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, default=str, indent=2))
