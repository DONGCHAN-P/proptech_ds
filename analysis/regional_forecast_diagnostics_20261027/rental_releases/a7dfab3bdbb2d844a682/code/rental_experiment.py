"""One controlled rental-feature block on the fixed HGB/cohort/target contract."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import inspect
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from diagnostics import OUT,PREV,WINDOWS,read_sources,sha,save,csv,require_common_targets
import experiment as e
from forecast import join_released,add_target
from evaluation import point_metrics
from artifacts import freeze_release,digest_frame

FEATURES=['jeonse_return_3','jeonse_return_12','jeonse_supply_demand','jeonse_demand_change_3']
SOURCE=OUT.parent.parent/'research_notes/지역별 집값 예측 실패 진단/rental_data/rental_normalized.csv'

def rental_features(panel,raw):
    """Assume availability on month t+3's first day, matching the old buffer.

    Canonical source release dates remain blank; this is an explicit experiment
    assumption. Price-index rebasing cancels from log ratios. No price level is
    passed to the model. Province features are broadcast to its districts.
    """
    source=raw.copy();source['month']=pd.to_datetime(source.month)
    source['region_code']=source.region_code.astype(str)
    if source.duplicated(['region_code','variable','month']).any():raise ValueError('Duplicate rental observations')
    source['available_date']=source.month+pd.DateOffset(months=3)
    derived=[]
    for (code,variable),group in source.groupby(['region_code','variable']):
        g=group.sort_values('month').copy();g['value']=pd.to_numeric(g.value,errors='coerce')
        lookup=g.set_index('month')
        if variable=='reb_apt_jeonse_price_index':
            for lag in [3,12]:
                old=lookup.value.reindex(g.month-pd.DateOffset(months=lag)).to_numpy()
                h=g.copy();h['value']=np.log(g.value.where(g.value>0)/np.where(old>0,old,np.nan))
                h['variable']=f'jeonse_return_{lag}';derived.append(h)
        elif variable=='reb_apt_jeonse_supply_demand_index':
            h=g.copy();h['variable']='jeonse_supply_demand';derived.append(h)
            old=lookup.value.reindex(g.month-pd.DateOffset(months=3)).to_numpy()
            h=g.copy();h['value']=g.value-old;h['variable']='jeonse_demand_change_3';derived.append(h)
    inputs=pd.concat(derived,ignore_index=True)
    # Every endpoint has the same monotone t+3 assumption, so the newer operand's
    # information date is also the maximum information date of both operands.
    inputs=inputs[inputs.value.notna()&inputs.region_code.isin(panel.region_code.astype(str).unique())]
    out=join_released(panel[['region_code','as_of']],inputs,max_age_months=6)
    for col in FEATURES:
        if col not in out:out[col]=np.nan
    return out[FEATURES]

def run():
    _,features,_,main,_=read_sources()
    frozen=OUT/'rental_source_snapshot.csv'
    if frozen.exists():
        if sha(frozen)!=sha(SOURCE):raise ValueError('New rental vintage requires a new experiment version')
    else:frozen.write_bytes(SOURCE.read_bytes())
    raw=pd.read_csv(frozen,dtype={'region_code':str})
    enriched=features.copy()
    added=rental_features(features,raw)
    for col in FEATURES:enriched[col]=added[col]
    assert digest_frame(features)==digest_frame(enriched[features.columns])
    panel=add_target(enriched,6)
    original=add_target(features,6)
    all_baseline=pd.read_parquet(main/'history.parquet')
    baseline=all_baseline[all_baseline.model.eq('v3_hgb')].copy()
    origins=sorted(baseline.origin.unique())
    spec={**e.SPECS['v3_hgb'],'features':e.SPECS['v3_hgb']['features']+FEATURES}
    metadata={'source_sha256':sha(frozen),'original_feature_sha256':sha(PREV/'results/feature_panel.parquet'),
         'spec':spec,'features':FEATURES,'origins':[str(d) for d in origins],
         'feature_builder_sha256':sha(Path(__file__)),
         'training_helper_sha256':sha(PREV/'experiment.py'),
         'availability_assumption':'reference month+3 months, FIRST day; distinct from source research month-end sensitivity',
         'historical_first_vintages_verified':False,'new_blind_evaluation':False}
    cache=OUT/'rental_cache';cache.mkdir(exist_ok=True)
    identity=digest_frame(enriched)+sha(frozen)+sha(Path(__file__))+sha(PREV/'experiment.py')
    previous=cache/'identity.txt'
    if previous.exists() and previous.read_text('utf-8')!=identity:raise ValueError('Rental producer changed; use a new version')
    previous.write_text(identity,'utf-8')
    records=[]
    for origin in origins:
        origin=pd.Timestamp(origin)
        cohort=e.cohort_at(original,origin)
        current=panel[panel.month.eq(origin.to_period('M').start_time)&panel.series_id.isin(cohort.series_id)].copy()
        current=current.set_index('series_id').loc[cohort.series_id].reset_index()
        path=cache/f'{origin:%Y%m}.parquet'
        if path.exists():rows=pd.read_parquet(path)
        else:
            values,_,n,last=e.fit_predict(panel,origin,current,spec)
            rows=baseline[baseline.origin.eq(origin)].set_index('series_id').loc[cohort.series_id].reset_index().copy()
            rows['model']='v3_hgb_rental';rows['prediction_pct']=values
            rows['train_n']=n;rows['train_latest_label_available']=last
            for col in ['lower_80','upper_80','lower_95','upper_95']:rows[col]=np.nan
            rows.to_parquet(path,index=False)
        records.append(rows)
        print(f'rental block {origin.date()} rows={len(rows)}',flush=True)
    candidate=pd.concat(records,ignore_index=True)
    both=pd.concat([baseline,candidate],ignore_index=True)
    require_common_targets(both,['v3_hgb','v3_hgb_rental'])
    # Same-rule earlier mature OOS errors only. Warm-up is included but not scored.
    calibrated=[]
    for origin,g in both.groupby('origin',sort=True):calibrated.append(e.add_intervals(g,both[both.origin<origin],origin))
    both=pd.concat(calibrated,ignore_index=True)
    both.to_parquet(OUT/'rental_predictions.parquet',index=False)
    score=[]
    for window,(a,b) in WINDOWS.items():
        for (model,level),g in both[both.origin.between(a,b)].groupby(['model','level']):
            score.append({'window':window,'model':model,'level':level,**point_metrics(g)})
    score=pd.DataFrame(score);csv(score,'rental_scorecard.csv')
    results=score[score.window.eq('all_regimes')]
    ratio=[];p90=[]
    for level,g in results.groupby('level'):
        g=g.set_index('model');ratio.append(g.loc['v3_hgb_rental','balanced_mae_pp']/g.loc['v3_hgb','balanced_mae_pp'])
        p90.append(g.loc['v3_hgb_rental','p90_ae_pp']/g.loc['v3_hgb','p90_ae_pp'])
    passed=bool(np.mean(ratio)<=.95 and max(ratio)<=1 and max(p90)<=1.1)
    save(OUT/'rental_decision.json',{'mean_balanced_mae_ratio':float(np.mean(ratio)),
        'improvement_pct':float((1-np.mean(ratio))*100),'geography_ratios':list(map(float,ratio)),
        'max_p90_ratio':float(max(p90)),'retrospective_numeric_gate_passed':passed,
        'operating_rule':'v3_hgb','automatic_operating_change':False,
        'reason':'conditional revised-vintage block; preserve and test on new observations',**metadata})
    cohort=e.cohort_at(original,e.ASOF)
    current=panel[panel.month.eq(e.ASOF.to_period('M').start_time)&panel.series_id.isin(cohort.series_id)].copy()
    current=current.set_index('series_id').loc[cohort.series_id].reset_index()
    values,model,n,last=e.fit_predict(panel,e.ASOF,current,spec)
    current.to_parquet(OUT/'rental_current_features.parquet',index=False)
    joblib.dump(model,OUT/'rental_current_model.joblib',compress=3)
    future=pd.read_csv(main/'future_forecasts_6m.csv',dtype={'region_code':str},parse_dates=['origin'])
    future=future[future.model.eq('v3_hgb')].set_index('series_id').loc[current.series_id].reset_index()
    future['model']='v3_hgb_rental';future['prediction_pct']=values
    future['train_n']=n;future['train_latest_label_available']=last
    future=e.add_intervals(future,both,e.ASOF)
    csv(future,'rental_future_forecasts.csv')
    missing=current.groupby('level')[FEATURES].apply(lambda g:g.isna().mean()).reset_index()
    csv(missing,'rental_current_missing.csv')
    files={name:OUT/name for name in ['rental_source_snapshot.csv','rental_predictions.parquet','rental_scorecard.csv',
        'rental_decision.json','rental_future_forecasts.csv','rental_current_features.parquet','rental_current_model.joblib']}
    files.update({f'code/{name}':OUT/name for name in ['rental_experiment.py','diagnostics.py']})
    files.update({f'code/{name}':PREV/name for name in ['experiment.py','evaluation.py','artifacts.py']})
    files['code/forecast.py']=PREV.parent/'regional_forecast_20261027/forecast.py'
    release=freeze_release(OUT/'rental_releases',files,{'as_of':'2026-10-27','baseline_release':main.name,
              'source_sha256':sha(frozen),'role':'conditional rental-block research candidate'})
    save(OUT/'rental_release_pointer.json',{'release_id':release.name,'directory':str(release.relative_to(OUT))})
    print(results[['model','level','mae_pp','balanced_mae_pp','p90_ae_pp']].to_string(index=False),flush=True)
    print(f'Numeric gate={passed}; improvement={(1-np.mean(ratio))*100:.3f}%',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=4):run()
