"""Artifact-level checks beyond the unit tests, with saved-model replay."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
import joblib

OUT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--results',default='results_v3')
args=ap.parse_args()
R=(OUT/args.results).resolve()
assert R.is_relative_to(OUT.resolve())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((R/'run_summary.json').read_text('utf-8'))
contract=json.loads((R/'feature_contract.json').read_text('utf-8'))
sel=json.loads((R/'selection_frozen_before_holdout.json').read_text('utf-8'))
forecasts=pd.read_csv(R/'forecast_next_6_months.csv',parse_dates=['as_of','price_input_month','forecast_month'])
backtest=pd.read_csv(R/'backtest_predictions.csv',parse_dates=['origin','train_latest_label_available'])
assert (backtest.train_latest_label_available<=backtest.origin).all()
assert pd.Timestamp(sel['latest_selection_label_available'])<=pd.Timestamp(min(sel['holdout_origins']))
assert not forecasts.duplicated(['series_id','horizon']).any()
assert forecasts.prediction_pct.notna().all()
assert forecasts.horizon.between(1,6).all()
assert not forecasts.reference_month_observed.any()
assert (forecasts.price_input_month==pd.Timestamp('2026-07-01')).all()
for h,g in forecasts.groupby('horizon'):
    assert (g.forecast_month==pd.Timestamp('2026-10-01')+pd.DateOffset(months=int(h))).all()
assert sha(R/'forecast_next_6_months.csv')==summary['forecast_sha256']
assert sha(OUT/'data/monthly_exogenous_snapshot.csv')==contract['external_sha256']
panel=pd.read_parquet(R/'feature_panel.parquet')
replay=[]
for h in range(1,7):
    chosen=forecasts[forecasts.horizon.eq(h)]
    modelpath=R/'models'/f'{summary["winner"]}_{h}m.joblib'
    if not modelpath.exists(): continue
    model=joblib.load(modelpath)
    current=panel[panel.month.eq('2026-10-01')].set_index('series_id').loc[chosen.series_id].reset_index()
    actual=np.expm1(model.predict(current))*100
    delta=float(np.max(np.abs(actual-chosen.prediction_pct.to_numpy())))
    assert delta<1e-10
    replay.append({'horizon':h,'rows':len(chosen),'max_replay_difference_pp':delta,'model_sha256':sha(modelpath)})
coverage=pd.read_csv(R/'evaluation_coverage.csv')
cohort=coverage[coverage.stage.eq('holdout')&coverage.horizon.eq(6)&coverage.model.eq(summary['winner'])]
checks={'passed':True,'saved_model_replay':replay,'holdout_coverage':cohort.to_dict('records'),
        'missing_future_labels_preserved':int(cohort.unscored_n.sum()),
        'code_hashes':{p.name:sha(p) for p in OUT.glob('*.py')},
        'forecast_sha256':sha(R/'forecast_next_6_months.csv'),
        'not_verified':['historical true vintages','individual dwelling prices','future predictive coverage','causal policy impact']}
(R/'artifact_verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'passed':True,'replayed_models':len(replay),'unscored_holdout_forecasts':int(cohort.unscored_n.sum())}))
