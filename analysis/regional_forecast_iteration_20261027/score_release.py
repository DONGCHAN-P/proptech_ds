"""Score an immutable issued forecast only after its targets are mature."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(1,str(Path(__file__).resolve().parent.parent/'regional_forecast_20261027'))
import argparse
import json
import numpy as np
import pandas as pd
from forecast import add_target
from evaluation import point_metrics
from artifacts import sha

def json_safe(value):
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,list):return [json_safe(v) for v in value]
    if isinstance(value,(float,np.floating)) and not np.isfinite(value):return None
    if isinstance(value,np.generic):return value.item()
    return value

def score(release,panel,as_of):
    release=Path(release)
    manifest=json.loads((release/'release.json').read_text('utf-8'))
    for name,expected in manifest['files'].items():
        if sha(release/name)!=expected: raise ValueError('Frozen release file changed')
    issued=pd.read_csv(release/'future_forecasts_6m.csv',dtype={'region_code':str})
    issued['month']=pd.to_datetime(issued.origin).dt.to_period('M').dt.start_time
    targets=add_target(panel,6)[['series_id','month','target_log_return','label_available']]
    issued=issued.drop(columns=['actual_pct'],errors='ignore')
    joined=issued.merge(targets,on=['series_id','month'],how='left',validate='many_to_one',suffixes=('','_scoring'))
    label='label_available_scoring' if 'label_available_scoring' in joined else 'label_available'
    truth=np.expm1(joined.target_log_return)*100
    joined['actual_pct']=truth.where(pd.to_datetime(joined[label])<=pd.Timestamp(as_of))
    rows=[]
    for (model,level),g in joined.groupby(['model','level']):
        rows.append({'model':model,'level':level,**point_metrics(g)})
    return json_safe({'status':'scored' if joined.actual_pct.notna().any() else 'pending_mature_actuals',
            'release_id':manifest['release_id'],'as_of':str(as_of),'metrics':rows})

def main():
    root=Path(__file__).resolve().parent
    ap=argparse.ArgumentParser();ap.add_argument('--release');ap.add_argument('--panel',
         default=str(root.parent/'regional_forecast_20261027/data/monthly_panel.parquet'))
    ap.add_argument('--as-of',required=True)
    a=ap.parse_args()
    if a.release:release=Path(a.release)
    else:
        pointer=json.loads((root/'latest_release.json').read_text('utf-8'))
        release=root/pointer['directory']
    result=score(release,pd.read_parquet(a.panel),a.as_of)
    result['actual_panel_sha256']=sha(a.panel)
    # Evaluations are versioned by date and actual-data snapshot; never replaces
    # an earlier release or assessment when transactions are later revised.
    target=root/'release_evaluations';target.mkdir(exist_ok=True)
    dest=target/f'{release.name}_{a.as_of}_{result["actual_panel_sha256"][:12]}.json'
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if not dest.exists():dest.write_text(payload,'utf-8')
    print(json.dumps({'status':result['status'],'release_id':result['release_id'],'evaluation':str(dest)},ensure_ascii=False))

if __name__=='__main__':main()
