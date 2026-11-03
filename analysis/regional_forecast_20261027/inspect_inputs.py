"""Read-only input inventory for the isolated forecasting experiment."""
from pathlib import Path
import json
import duckdb
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
c = duckdb.connect()
def query(sql):
    return c.sql(sql).df().astype(object).where(lambda d: d.notna(), None).to_dict('records')

sources = {}
for name, rel in [('master','master/trade_events.parquet'), ('expansion','analysis/housing_growth_2006/regional_expansion_v1/expansion_normalized.parquet')]:
    p = ROOT / rel
    if not p.exists():
        continue
    path = p.as_posix()
    schema = pq.ParquetFile(p).schema_arrow.names
    info = {'path':rel, 'columns':schema, 'bytes':p.stat().st_size,
            'regions':query(f"SELECT substr(sigungu_code,1,2) region_code, count(*) n, min(deal_date)::varchar first_date, max(deal_date)::varchar last_date FROM read_parquet('{path}') GROUP BY 1 ORDER BY 1")}
    if 'first_seen_is_estimate' in schema:
        info['availability'] = query(f"SELECT first_seen_is_estimate, count(*) n, min(first_seen_date)::varchar first_seen_min, max(first_seen_date)::varchar first_seen_max FROM read_parquet('{path}') GROUP BY 1")
    sources[name] = info
status = {}
for p in (ROOT/'raw/rtms_trade_expansion').glob('*/batch_status.json'):
    v=json.loads(p.read_text('utf-8'))
    status[p.parent.name]={k:v.get(k) for k in ['state','finished_groups','current_group','updated','reason']}
summ = {'sources':sources,'additional_collection_status':status}
(OUT/'input_inventory.json').write_text(json.dumps(summ, ensure_ascii=False, indent=2)+'\n','utf-8')
print(json.dumps(summ,ensure_ascii=False,indent=2))
