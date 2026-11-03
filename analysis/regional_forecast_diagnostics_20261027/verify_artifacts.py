"""Verify diagnostics, immutable derivatives and future replay without refitting."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import hashlib
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from diagnostics import OUT,PREV,sha,load,save,read_sources,require_common_targets,attach_inputs
from interval_experiment import calibrate
from residual_experiment import combine_predictions

def verify_release(path):
    manifest=load(path/'release.json')
    identity={key:manifest[key] for key in ['metadata','files']}
    digest=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    assert manifest['complete'] and manifest['release_id']==digest and path.name==digest[:20]
    for name,expected in manifest['files'].items():assert sha(path/name)==expected,name
    return len(manifest['files'])

def run():
    _,features,_,main,timing=read_sources()
    checks={}
    released={}
    for folder in ['rental_releases','residual_releases','interval_releases','input_snapshots']:
        for path in (OUT/folder).iterdir():
            if path.is_dir():released[f'{folder}/{path.name}']=verify_release(path)
    checks['immutable_files_verified']=released
    ledger=pd.read_parquet(OUT/'error_ledger.parquet')
    require_common_targets(ledger,['v3_hgb','hgb_full_120m','hgb_t2_law','hgb_t2_120m'])
    timing_history=pd.read_parquet(timing/'history.parquet')
    issued=timing_history[timing_history.origin.ge('2017-01-27')&timing_history.model.isin(['hgb_t2_law','hgb_t2_120m'])]
    joined=ledger[ledger.model.isin(['hgb_t2_law','hgb_t2_120m'])].merge(
        issued[['origin','series_id','model','price_input_month']],on=['origin','series_id','model'],suffixes=('','_issued'))
    assert joined.price_input_month.eq(joined.price_input_month_issued).all()
    assert 'reference_return_6' in ledger and 'reference_observed_recent_volume' in ledger
    checks['effective_t2_or_fallback_provenance_verified_rows']=len(joined)
    f=pd.read_csv(OUT/'factor_decomposition.csv')
    assert np.allclose(f.lag_at_base_pp+f.training_at_t3_pp+f.interaction_pp,f.total_gain_pp)
    assert np.allclose(f.lag_shapley_pp+f.training_shapley_pp,f.total_gain_pp)
    checks['factor_identities_verified']=True
    regime=pd.read_csv(OUT/'regime_diagnostics.csv')
    assert np.allclose(regime.groupby('level').error_share.sum(),1.)
    r=pd.read_csv(OUT/'regional_diagnostics.csv')
    assert np.allclose(r.groupby('level').mae_contribution_pp.sum().sort_index(),
                      regime.groupby('level').full_period_mae_contribution_pp.sum().sort_index())
    checks['balanced_contributions_verified']=True
    history=pd.read_parquet(main/'history.parquet')
    base=history[history.model.eq('v3_hgb')]
    replays={}
    for prefix,model in [('rental','v3_hgb_rental'),('residual','hgb_momentum_residual')]:
        both=pd.read_parquet(OUT/f'{prefix}_predictions.parquet')
        require_common_targets(both,['v3_hgb',model])
        assert (pd.to_datetime(both.train_latest_label_available)<=both.origin).all()
        control=both[both.model.eq('v3_hgb')].set_index(['origin','series_id']).sort_index()
        expected=base.set_index(['origin','series_id']).sort_index()
        assert np.allclose(control.prediction_pct,expected.prediction_pct)
        current=pd.read_parquet(OUT/f'{prefix}_current_features.parquet')
        pipeline=joblib.load(OUT/f'{prefix}_current_model.joblib')
        raw=pipeline.predict(current)
        pred=100*np.expm1(raw)
        if prefix=='residual':pred=combine_predictions(pred,current.return_6.to_numpy())
        future=pd.read_csv(OUT/f'{prefix}_future_forecasts.csv',dtype={'region_code':str})
        saved=future.set_index('series_id').loc[current.series_id]
        assert np.allclose(pred,saved.prediction_pct,atol=1e-9,rtol=1e-10)
        assert future.series_id.nunique()==130
        assert not load(OUT/f'{prefix}_decision.json')['retrospective_numeric_gate_passed']
        replays[prefix]=len(future)
    checks['point_model_replays']=replays
    ih=pd.read_parquet(OUT/'interval_predictions.parquet')
    for _,g in ih.groupby(['origin','level']):
        arrays=[v.prediction_pct.to_numpy() for _,v in g.groupby('calibration_rule')]
        assert all(np.allclose(arrays[0],a) for a in arrays[1:])
    future=pd.read_csv(OUT/'interval_future_forecasts.csv',dtype={'region_code':str},parse_dates=['origin'])
    source=attach_inputs(base,features)
    for method,g in future.groupby('calibration_rule'):
        inputs=attach_inputs(g,features)
        replay=calibrate(inputs,source,pd.Timestamp('2026-10-27'),method)
        for col in ['lower_80','upper_80','lower_95','upper_95']:
            assert np.allclose(replay[col],g[col],atol=1e-9,rtol=1e-10,equal_nan=True)
    checks['interval_replayed_forecasts']=len(future)
    checks['forecast_unscored_by_level']=ledger[ledger.model.eq('v3_hgb')].groupby('level').actual_pct.apply(lambda x:int(x.isna().sum())).to_dict()
    rental=pd.read_csv(OUT/'rental_source_snapshot.csv',dtype={'region_code':str})
    assert len(rental)==4533 and rental.region_code.nunique()==11
    assert rental.available_date.isna().all()
    checks['rental_rows']=len(rental)
    checks['rental_historical_release_dates_verified']=False
    checks['target_crosscheck_cases']=load(OUT/'target_crosscheck_manifest.json')['compared_cases']
    checks['target_crosscheck_tail_selected']=True
    checks['operating_model_changed']=False
    checks['new_independent_holdout']=False
    checks['passed']=True
    save(OUT/'artifact_verification.json',checks)
    print(json.dumps(checks,ensure_ascii=False,indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=4):run()
