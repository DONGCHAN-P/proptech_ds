"""Preserve today's local input bytes without claiming historic publication vintages."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import pandas as pd
import pyarrow.parquet as pq
from diagnostics import OUT,PREV,sha,save
from artifacts import freeze_release

def audit_rent(rent_root):
    rent={};invalid=[]
    for path in sorted(Path(rent_root).rglob('*.parquet')):
        relative=path.relative_to(rent_root)
        month='/'.join(relative.parts[:2])
        block=rent.setdefault(month,{'files':0,'valid_files':0,'invalid_files':0,'rows':0,'bytes':0})
        block['files']+=1;block['bytes']+=path.stat().st_size
        try:
            count=pq.ParquetFile(path).metadata.num_rows
        except (OSError,ValueError):
            block['invalid_files']+=1;invalid.append(relative.as_posix());continue
        block['valid_files']+=1;block['rows']+=count
    return {'months':rent,'invalid_paths':invalid}

def run():
    root=OUT.parent.parent
    first_seen_path=root/'master/trade_events.parquet'
    tracking=pd.read_parquet(first_seen_path,columns=['deal_date','first_seen_date','first_seen_is_estimate'])
    groups=tracking.groupby('first_seen_is_estimate',dropna=False).agg(
        rows=('deal_date','size'),contract_min=('deal_date','min'),contract_max=('deal_date','max'),
        local_seen_min=('first_seen_date','min'),local_seen_max=('first_seen_date','max')).reset_index()
    save(OUT/'local_tracking_audit.json',{'scope':'local trade_events tracking file; not the entire11province model cohort',
        'source_sha256':sha(first_seen_path),'groups':json.loads(groups.to_json(orient='records',date_format='iso')),
        'nonestimated_rows':int(tracking.first_seen_is_estimate.eq(False).sum()),
        'total_rows':len(tracking),'local_seen_date_is_publication_date':False,
        'historical_publication_vintage_restored':False,'task_as_of':'2026-10-27'})
    rent_root=root/'staged/rent'
    rent=audit_rent(rent_root)
    save(OUT/'local_rental_audit.json',{**rent,'scope':'staged rental files; coverage from directory labels',
        'historical_model_ready':False,'reason':'single2026Augustmonth; cannot validate longhistorical extra predictive power',
        'raw_transactions_exported':False})
    old=PREV.parent/'regional_forecast_20261027'
    sources={'monthly_panel.parquet':old/'data/monthly_panel.parquet',
             'monthly_exogenous_snapshot.csv':old/'data/monthly_exogenous_snapshot.csv',
             'migration_annual_snapshot.csv':old/'data/migration_annual_snapshot.csv',
             'policy_events_snapshot.json':old/'data/policy_events_snapshot.json',
             'policy_2026_verified_snapshot.json':old/'data/policy_2026_verified_snapshot.json',
             'supply_supplement_snapshot.csv':PREV/'supply_supplement_snapshot.csv',
             'local_tracking_audit.json':OUT/'local_tracking_audit.json',
             'local_rental_audit.json':OUT/'local_rental_audit.json',
             'capture_inputs.py':Path(__file__)}
    snapshot=freeze_release(OUT/'input_snapshots',sources,{'task_as_of':'2026-10-27',
        'snapshot_kind':'copy of currently stored local inputs',
        'original_historical_publication_vintages_restored':False,
        'captured_date_does_not_relabel_underlying_collection_dates':True,
        'raw_transactions_copied':False,'automatic_scheduler_configured':False})
    save(OUT/'input_snapshot_pointer.json',{'snapshot_id':snapshot.name,'directory':str(snapshot.relative_to(OUT)),
        'size_bytes':sum(p.stat().st_size for p in sources.values())})
    print(groups.to_string(index=False))
    print(json.dumps({'rental_months':rent,'input_snapshot':snapshot.name,
                     'size_bytes':sum(p.stat().st_size for p in sources.values())},ensure_ascii=False))

if __name__=='__main__':run()
