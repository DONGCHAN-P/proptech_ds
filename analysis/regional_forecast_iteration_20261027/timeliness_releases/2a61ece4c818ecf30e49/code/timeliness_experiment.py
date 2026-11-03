"""Conditional t-2 price-input sensitivity; not verified historical vintages.

Reporting-law evidence does NOT establish that final revised observations were
already available. Cohorts, targets and three-month label maturity stay fixed.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import experiment as e
from forecast import add_target
from evaluation import point_metrics,regional_metrics,known_errors
from artifacts import digest_frame,freeze_release

R=e.OUT/'results_timeliness';R.mkdir(exist_ok=True)
PRICE_COLS=[c for c in e.PRICE if c not in ['season_sin','season_cos']]
QUALITY=['observed_recent_min_matches','observed_recent_mean_matches','observed_recent_volume']
FIRST=pd.Timestamp('2020-05-01')

def refresh_price_features(base,raw):
    q=raw.sort_values(['series_id','month']).copy()
    def roll(col,window,how):
        return q.groupby('series_id')[col].transform(lambda v:getattr(v.rolling(window,min_periods=window),how)())
    for w in [1,3,6,12]: q[f'return_{w}']=roll('log_change',w,'sum')
    for w in [6,12]: q[f'volatility_{w}']=roll('log_change',w,'std')
    q['volume_log']=np.log1p(q.volume)
    q['volume_vs_12']=np.log((roll('volume',3,'mean')+1)/(roll('volume',12,'mean')+1))
    q['volume_yoy']=np.log((q.volume+1)/(q.groupby('series_id').volume.shift(12)+1))
    q['area_change_12']=q.median_area-q.groupby('series_id').median_area.shift(12)
    q['price_log']=np.log(q.median_ppm)
    q['observed_recent_min_matches']=roll('matched_complexes',12,'min')
    q['observed_recent_mean_matches']=roll('matched_complexes',12,'mean')
    q['observed_recent_volume']=roll('volume',12,'sum')
    for w in [3,6,12]:
        province=q[q.series_id.str.startswith('p:')].set_index(['region_code','month'])[f'return_{w}']
        idx=pd.MultiIndex.from_frame(q[['region_code','month']])
        q[f'province_return_{w}']=province.reindex(idx).to_numpy()
    out=base.copy()
    mask=out.month>=FIRST
    dates=out.loc[mask,'month']-pd.DateOffset(months=2)
    idx=pd.MultiIndex.from_arrays([out.loc[mask,'series_id'],dates])
    look=q.set_index(['series_id','month'])
    for col in PRICE_COLS+QUALITY:
        out.loc[mask,col]=look[col].reindex(idx).to_numpy()
    out.loc[mask,'price_input_month']=dates.to_numpy()
    out['fresh_eligible']=out.eligible
    out.loc[mask,'fresh_eligible']=(out.loc[mask,'observed_recent_min_matches']>=5)&(
        out.loc[mask,'observed_recent_mean_matches']>=10)&(out.loc[mask,'observed_recent_volume']>=200)
    out['fresh_eligible'] &= out[['return_3','return_6','return_12']].notna().all(axis=1)
    # These explanatory columns depend on the same currently known price inputs.
    out['relative_return_6']=out.return_6-out.province_return_6
    out['acceleration']=2*out.return_3-out.return_6
    province=out[out.level.eq('province')]
    for w in [3,6]: out[f'market_return_{w}']=out.month.map(province.groupby('month')[f'return_{w}'].mean())
    out['capital_return_6']=out.month.map(province[province.region_code.isin(['11','28','41'])].groupby('month').return_6.mean())
    if 'mortgage_rate_new_business_pct_change_3' in out:
        out['rate_momentum_interaction']=out.mortgage_rate_new_business_pct_change_3*out.return_6
    assert digest_frame(base[['series_id','month','log_change']])==digest_frame(out[['series_id','month','log_change']])
    pd.testing.assert_frame_equal(base[base.month<FIRST][PRICE_COLS].reset_index(drop=True),
                                  out[out.month<FIRST][PRICE_COLS].reset_index(drop=True))
    return out

def predict_with_fallback(panel,origin,current,fallback,name,spec,reuse=None):
    """Route each prediction together with its effective training provenance."""
    source=fallback if reuse is None else reuse
    rows=source.reindex(current.series_id).reset_index().copy()
    if rows.prediction_pct.isna().any():raise ValueError('Incomplete fallback cohort')
    rows['effective_predictor']=rows.model
    rows['model']=name
    rows['price_input_month']=origin.to_period('M').start_time-pd.DateOffset(months=3)
    rows['fallback_to_t3']=reuse is None
    model=None
    if reuse is None:
        good=current[current.fresh_eligible]
        if len(good):
            values,model,n,last=e.fit_predict(panel,origin,good,spec)
            assert last<=origin
            routed=rows.series_id.isin(good.series_id)
            values=pd.Series(values,index=good.series_id)
            rows.loc[routed,'prediction_pct']=rows.loc[routed,'series_id'].map(values).to_numpy()
            rows.loc[routed,'train_n']=n
            rows.loc[routed,'train_latest_label_available']=last
            rows.loc[routed,'effective_predictor']=name
            rows.loc[routed,'fallback_to_t3']=False
            rows.loc[routed,'price_input_month']=origin.to_period('M').start_time-pd.DateOffset(months=2)
    return rows,model


def freeze_outputs(variants,release_root=None):
    e.save(R/'resolved_config.json',{'variants':variants,'first_origin':str(FIRST),
          'as_of':str(e.ASOF),'evaluation_identity':e.evaluation_identity(),
          'price_columns':PRICE_COLS,'quality_columns':QUALITY,'label_maturity_months':3})
    names=['future_forecasts_6m.csv','current_features.parquet','original_current_features.parquet',
           'assumption_manifest.json','scorecard.csv','resolved_config.json']
    files={n:R/n for n in names}
    files['history.parquet']=R/'predictions.parquet'
    files['bank_manifest.json']=e.RESULT/'bank_manifest.json'
    files.update({f'models/{f.name}':f for f in (R/'models').glob('*.joblib')})
    files.update({f'code/{n}':e.OUT/n for n in ['timeliness_experiment.py','experiment.py','evaluation.py','artifacts.py']})
    files['code/forecast.py']=e.OLD/'forecast.py'
    return freeze_release(release_root or e.OUT/'timeliness_releases',files,
         {'as_of':str(e.ASOF),'assumption':'unverified vintage t-2',
          'historical_predictions_sha256':e.sha(R/'predictions.parquet')})


def run():
    base=pd.read_parquet(e.RESULT/'feature_panel.parquet')
    bank=e.load_bank(base)
    raw=pd.read_parquet(e.OLD/'data/monthly_panel.parquet')
    fresh=refresh_price_features(base,raw)
    fresh.to_parquet(R/'feature_panel.parquet',index=False)
    original=add_target(base,6)
    panel=add_target(fresh,6)
    panel['eligible']=panel.eligible&panel.fresh_eligible
    variants={'hgb_t2_law':dict(e.SPECS['v3_hgb']),
              'hgb_t2_120m':dict(e.SPECS['hgb_full_120m'])}
    records=[]
    for origin in e.ORIGINS:
        cohort=e.cohort_at(original,origin)
        fallback=bank[bank.model.eq('v3_hgb')&bank.origin.eq(origin)].set_index('series_id')
        assert set(cohort.series_id)==set(fallback.index)
        current=panel[panel.series_id.isin(cohort.series_id)&panel.month.eq(origin.to_period('M').start_time)]
        good=current[current.fresh_eligible]
        for name,spec in variants.items():
            past=None
            if origin.to_period('M').start_time<FIRST:
                previous='v3_hgb' if name=='hgb_t2_law' else 'hgb_full_120m'
                past=bank[bank.model.eq(previous)&bank.origin.eq(origin)].set_index('series_id')
            rows,_=predict_with_fallback(panel,origin,current,fallback,name,spec,reuse=past)
            rows['timing_assumption']='t-2 from2020-05; true historical availability unverified'
            records.append(rows)
        print(f'timeliness {origin.date()} {len(good)}/{len(cohort)} fresh-input eligible',flush=True)
    allrows=pd.concat(records,ignore_index=True)
    extra=bank[bank.model.isin(['v3_hgb','damped_momentum'])]
    allrows=pd.concat([extra,allrows],ignore_index=True)
    # Intervals use only errors of previously issued same-rule forecasts available
    # at the origin; no own-outcome calibration or shortened label maturity.
    issued=[]
    for origin,g in allrows.groupby('origin',sort=True):
        prior=allrows[allrows.origin<origin]
        issued.append(e.add_intervals(g,prior,origin))
    allrows=pd.concat(issued,ignore_index=True)
    allrows.to_parquet(R/'predictions.parquet',index=False)
    summary=[]
    windows={'all_regimes':('2017-01-27','2026-01-27'),'post_law':('2020-05-01','2026-01-27'),
             'boom':('2020-01-01','2021-12-31'),'turn':('2022-01-01','2023-12-31'),
             'recent':('2024-01-01','2026-01-27')}
    for window,(a,b) in windows.items():
        for (name,level),g in allrows[allrows.origin.between(a,b)].groupby(['model','level']):
            summary.append({'window':window,'model':name,'level':level,'origins':g.origin.nunique(),**point_metrics(g)})
    pd.DataFrame(summary).to_csv(R/'scorecard.csv',index=False,encoding='utf-8-sig')
    regional_metrics(allrows[allrows.origin>=e.START_SCORE]).to_csv(R/'by_region.csv',index=False,encoding='utf-8-sig')
    models=R/'models';models.mkdir(exist_ok=True)
    cohort=e.cohort_at(original,e.ASOF)
    pred,baseline_model,n,last=e.fit_predict(original,e.ASOF,cohort,e.SPECS['v3_hgb'])
    fallback=cohort.copy()
    fallback['prediction_pct']=pred;fallback['model']='v3_hgb'
    fallback['train_n']=n;fallback['train_latest_label_available']=last
    fallback=fallback.set_index('series_id')
    current=panel[panel.series_id.isin(cohort.series_id)&panel.month.eq(e.ASOF.to_period('M').start_time)].copy()
    future=[]
    for name,spec in variants.items():
        rows,model=predict_with_fallback(panel,e.ASOF,current,fallback,name,spec)
        if model is not None:joblib.dump(model,models/f'{name}.joblib',compress=3)
        rows['actual_pct']=np.nan;rows['origin']=e.ASOF
        future.append(rows)
    future=e.add_intervals(pd.concat(future,ignore_index=True),allrows,e.ASOF)
    keep=['series_id','name','region_code','level','origin','target_month','model','prediction_pct','price_input_month',
          'lower_80','upper_80','lower_95','upper_95','fallback_to_t3','effective_predictor',
          'train_n','train_latest_label_available']
    future[keep].to_csv(R/'future_forecasts_6m.csv',index=False,encoding='utf-8-sig')
    current.to_parquet(R/'current_features.parquet',index=False)
    cohort.to_parquet(R/'original_current_features.parquet',index=False)
    joblib.dump(baseline_model,models/'fallback_v3_hgb.joblib',compress=3)
    e.save(R/'assumption_manifest.json',{'first_whole_month_origin':'2020-05-27','price_lag_after':2,
          'label_maturity_months':3,'target_and_cohort_changed':False,'historical_vintages_verified':False,
          'role':'conditional timeliness sensitivity; no reporting-deadline finality guarantee',
          'new_blind_evaluation':False,'law_source':'https://www.korea.kr/news/policyNewsView.do?newsId=148869388',
          'raw_target_sha256':e.sha(e.OLD/'data/monthly_panel.parquet'),
          'freshness_code_sha256':e.sha(Path(__file__))})
    release=freeze_outputs(variants)
    e.save(R/'release_pointer.json',{'release_id':release.name,'directory':str(release)})
    print(pd.DataFrame(summary).query("window=='all_regimes'")[['model','level','mae_pp','balanced_mae_pp']].to_string(index=False),flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=4):run()
