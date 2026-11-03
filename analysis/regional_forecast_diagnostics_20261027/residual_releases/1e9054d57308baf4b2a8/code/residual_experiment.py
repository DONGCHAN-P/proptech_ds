"""One predeclared structural alternative: fixed momentum offset plus residual HGB."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from diagnostics import OUT,PREV,WINDOWS,read_sources,save,csv,sha,require_common_targets
import experiment as e
from forecast import add_target
from evaluation import point_metrics
from artifacts import freeze_release

def residual_target(panel):
    out=panel.copy();out['target_log_return']=out.target_log_return-.5*out.return_6
    return out

def combine_predictions(residual_pct,observed_return_6):
    return 100*np.expm1(np.log1p(residual_pct/100)+.5*observed_return_6)

def run():
    _,features,_,main,_=read_sources()
    original=add_target(features,6);panel=residual_target(original)
    h=pd.read_parquet(main/'history.parquet');baseline=h[h.model.eq('v3_hgb')].copy()
    spec=e.SPECS['v3_hgb'].copy()
    cache=OUT/'residual_cache';cache.mkdir(exist_ok=True)
    identity=sha(Path(__file__))+sha(PREV/'results/feature_panel.parquet')+sha(PREV/'experiment.py')
    p=cache/'identity.txt'
    if p.exists() and p.read_text('utf-8')!=identity:raise ValueError('Changed producer requires a new version')
    p.write_text(identity,'utf-8')
    records=[]
    for origin in sorted(baseline.origin.unique()):
        origin=pd.Timestamp(origin);cohort=e.cohort_at(original,origin)
        path=cache/f'{origin:%Y%m}.parquet'
        if path.exists():rows=pd.read_parquet(path)
        else:
            residual,_,n,last=e.fit_predict(panel,origin,cohort,spec)
            rows=baseline[baseline.origin.eq(origin)].set_index('series_id').loc[cohort.series_id].reset_index().copy()
            rows['model']='hgb_momentum_residual'
            rows['prediction_pct']=combine_predictions(residual,cohort.return_6.to_numpy())
            rows['train_n']=n;rows['train_latest_label_available']=last
            for col in ['lower_80','upper_80','lower_95','upper_95']:rows[col]=np.nan
            rows.to_parquet(path,index=False)
        records.append(rows);print(f'residual {origin.date()} rows={len(rows)}',flush=True)
    candidate=pd.concat(records,ignore_index=True)
    both=pd.concat([baseline,candidate],ignore_index=True)
    require_common_targets(both,['v3_hgb','hgb_momentum_residual'])
    both=pd.concat([e.add_intervals(g,both[both.origin<origin],origin)
                    for origin,g in both.groupby('origin',sort=True)],ignore_index=True)
    both.to_parquet(OUT/'residual_predictions.parquet',index=False)
    score=[]
    for window,(a,b) in WINDOWS.items():
        for (model,level),g in both[both.origin.between(a,b)].groupby(['model','level']):
            score.append({'window':window,'model':model,'level':level,**point_metrics(g)})
    score=pd.DataFrame(score);csv(score,'residual_scorecard.csv')
    results=score[score.window.eq('all_regimes')];ratios={};p90=[]
    for level,g in results.groupby('level'):
        g=g.set_index('model');ratios[level]=float(g.loc['hgb_momentum_residual','balanced_mae_pp']/g.loc['v3_hgb','balanced_mae_pp'])
        p90.append(g.loc['hgb_momentum_residual','p90_ae_pp']/g.loc['v3_hgb','p90_ae_pp'])
    passed=bool(np.mean(list(ratios.values()))<=.95 and max(ratios.values())<=1 and max(p90)<=1.1)
    save(OUT/'residual_decision.json',{'geography_ratios':ratios,
        'mean_balanced_mae_ratio':float(np.mean(list(ratios.values()))),
        'improvement_pct':float((1-np.mean(list(ratios.values())))*100),
        'max_p90_ratio':float(max(p90)),'retrospective_numeric_gate_passed':passed,
        'operating_rule':'v3_hgb','automatic_operating_change':False,
        'offset_log_return':'0.5 * observed t3-lagged return_6',
        'features_and_hgb_parameters':spec,'source_release':main.name,
        'historical_first_vintages_verified':False,'new_blind_evaluation':False})
    current=e.cohort_at(original,e.ASOF)
    residual,model,n,last=e.fit_predict(panel,e.ASOF,current,spec)
    current.to_parquet(OUT/'residual_current_features.parquet',index=False)
    joblib.dump(model,OUT/'residual_current_model.joblib',compress=3)
    future=pd.read_csv(main/'future_forecasts_6m.csv',dtype={'region_code':str},parse_dates=['origin'])
    future=future[future.model.eq('v3_hgb')].set_index('series_id').loc[current.series_id].reset_index()
    future['model']='hgb_momentum_residual';future['prediction_pct']=combine_predictions(residual,current.return_6.to_numpy())
    future['train_n']=n;future['train_latest_label_available']=last
    csv(e.add_intervals(future,both,e.ASOF),'residual_future_forecasts.csv')
    files={name:OUT/name for name in ['residual_predictions.parquet','residual_scorecard.csv','residual_decision.json',
            'residual_future_forecasts.csv','residual_current_features.parquet','residual_current_model.joblib']}
    files.update({f'code/{name}':OUT/name for name in ['residual_experiment.py','diagnostics.py']})
    files.update({f'code/{name}':PREV/name for name in ['experiment.py','evaluation.py','artifacts.py']})
    files['code/forecast.py']=PREV.parent/'regional_forecast_20261027/forecast.py'
    release=freeze_release(OUT/'residual_releases',files,{'as_of':'2026-10-27','baseline_release':main.name,
            'role':'one fixed-offset residual research alternative'})
    save(OUT/'residual_release_pointer.json',{'release_id':release.name,'directory':str(release.relative_to(OUT))})
    print(results[['model','level','mae_pp','balanced_mae_pp','p90_ae_pp']].to_string(index=False),flush=True)
    print(f'Numeric gate={passed}; balanced gain={(1-np.mean(list(ratios.values())))*100:.3f}%',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=4):run()
