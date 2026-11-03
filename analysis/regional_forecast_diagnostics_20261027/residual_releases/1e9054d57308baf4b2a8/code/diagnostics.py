"""Post-hoc failure diagnostics; never supplies future-dependent training tags."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'regional_forecast_iteration_20261027'))
import hashlib
import json
import numpy as np
import pandas as pd
from evaluation import point_metrics,direction,balanced_mae

OUT=Path(__file__).resolve().parent
PREV=OUT.parent/'regional_forecast_iteration_20261027'
WINDOWS={'all_regimes':('2017-01-27','2026-01-27'),'early':('2017-01-27','2019-12-31'),
         'boom':('2020-01-01','2021-12-31'),'turn':('2022-01-01','2023-12-31'),
         'recent':('2024-01-01','2026-01-27')}
MODELS={'A':'v3_hgb','B':'hgb_full_120m','C':'hgb_t2_law','D':'hgb_t2_120m'}
INPUTS=['return_3','return_6','return_12','volatility_6','observed_recent_min_matches',
        'observed_recent_mean_matches','observed_recent_volume','price_input_month','as_of',
        'mortgage_rate_new_business_pct_change_3','unsold_housing_total_change_12',
        'resident_registered_households_change_12','housing_completions_all_change_12']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text('utf-8'))
def save(path,data):
    # pandas normalizes NaN, nullable values and timestamps for strict JSON.
    if isinstance(data,pd.DataFrame):text=data.to_json(orient='records',force_ascii=False,date_format='iso')
    else:text=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False,default=str)
    Path(path).write_text(text+'\n','utf-8')
def csv(data,name):data.to_csv(OUT/name,index=False,encoding='utf-8-sig')

def require_common_targets(rows,models):
    reference=None
    for model in models:
        g=rows[rows.model.eq(model)]
        if g.duplicated(['origin','series_id']).any():raise ValueError('Duplicate cohort')
        target=g.set_index(['origin','series_id']).actual_pct.sort_index()
        if reference is not None and (not target.index.equals(reference.index) or not np.allclose(
            target.to_numpy(),reference.to_numpy(),equal_nan=True,rtol=1e-12,atol=1e-12)):
            raise ValueError('Different cohort or target')
        if target.empty or g.prediction_pct.isna().any():raise ValueError('Missing predictions')
        reference=target

def balanced_weights(rows):
    out=rows.copy();out['weight']=0.
    for _,indices in out.groupby(['model','level']).groups.items():
        g=out.loc[indices];valid=g[g.actual_pct.notna()&g.prediction_pct.notna()]
        count=valid.groupby(['origin','region_code']).series_id.transform('size')
        regions=valid.groupby('origin').region_code.transform('nunique')
        out.loc[valid.index,'weight']=1/count/regions/valid.origin.nunique()
    out['ae_pp']=(out.prediction_pct-out.actual_pct).abs()
    out['error_pp']=out.prediction_pct-out.actual_pct
    out['mae_contribution_pp']=out.ae_pp.fillna(0)*out.weight
    return out

def factor_decomposition(values):
    a,b,c,d=[float(values[k]) for k in 'ABCD']
    return dict(A=a,B=b,C=c,D=d,total_gain_pp=a-d,lag_at_base_pp=a-c,
                training_at_t3_pp=a-b,interaction_pp=b+c-a-d,
                lag_shapley_pp=.5*((a-c)+(b-d)),training_shapley_pp=.5*((a-b)+(c-d)))

def attach_inputs(rows,features):
    out=rows.copy();out['input_key_month']=pd.to_datetime(out.origin).dt.to_period('M').dt.start_time
    cols=[c for c in INPUTS if c in features]
    inputs=features[['series_id','month']+cols].rename(columns={'month':'input_key_month'})
    out=out.drop(columns=[c for c in cols if c in out],errors='ignore')
    out=out.merge(inputs,on=['series_id','input_key_month'],how='left',validate='many_to_one')
    if out.as_of.isna().any():raise ValueError('Missing input snapshot')
    if (pd.to_datetime(out.as_of)>pd.to_datetime(out.origin)).any() or (
        pd.to_datetime(out.price_input_month)>out.input_key_month).any():raise ValueError('Future input')
    return out

def read_sources():
    main=PREV/load(PREV/'latest_release.json')['directory']
    timing=Path(load(PREV/'results_timeliness/release_pointer.json')['directory'])
    sources={}
    for release in [main,timing]:
        manifest=load(release/'release.json')
        for name in ['history.parquet','future_forecasts_6m.csv']:
            assert sha(release/name)==manifest['files'][name]
        sources[str(release.relative_to(PREV))]=sha(release/'release.json')
    f=PREV/'results/feature_panel.parquet'
    assert sha(f)==load(main/'release.json')['metadata']['feature_panel_sha256']
    sources['feature_panel.parquet']=sha(f)
    hist=pd.read_parquet(main/'history.parquet')
    timing_hist=pd.read_parquet(timing/'history.parquet')
    rows=pd.concat([hist[hist.model.isin([MODELS['A'],MODELS['B']])],
                    timing_hist[timing_hist.model.isin([MODELS['C'],MODELS['D']])]],ignore_index=True)
    rows=rows[rows.origin.ge('2017-01-27')].copy()
    require_common_targets(rows,MODELS.values())
    return rows,pd.read_parquet(f),sources,main,timing

def run():
    rows,features,sources,main,timing=read_sources()
    scored=attach_inputs(rows,features)
    scored['regime']=np.select([scored.origin.dt.year<=2019,scored.origin.dt.year<=2021,
        scored.origin.dt.year<=2023],['early','boom','turn'],default='recent')
    observed=direction(np.expm1(scored.return_6)*100)
    truth=direction(scored.actual_pct)
    scored['realized_reversal']=scored.actual_pct.notna()&(observed*truth<0)
    scored['past_direction']=observed
    scored['actual_direction']=np.where(scored.actual_pct.notna(),truth,np.nan)
    scored['thin_matches']=scored.observed_recent_min_matches.lt(10)
    scored['low_volume']=scored.observed_recent_volume.lt(500)
    scored['predicted_direction']=direction(scored.prediction_pct)
    scored['sign_miss']=scored.actual_pct.notna()&scored.predicted_direction.ne(scored.actual_direction)
    scored=balanced_weights(scored)
    scored['large_error_5pp']=scored.ae_pp.ge(5.)
    # All rows—including 81 unscorable outcomes per model—remain in the ledger.
    scored.to_parquet(OUT/'error_ledger.parquet',index=False)
    factors=[];region_factors=[]
    for window,(a,b) in WINDOWS.items():
        sub=scored[scored.origin.between(a,b)]
        for level,g in sub.groupby('level'):
            values={key:balanced_mae(g[g.model.eq(model)]) for key,model in MODELS.items()}
            factors.append({'window':window,'level':level,**factor_decomposition(values)})
            for code,h in g.groupby('region_code'):
                values={key:balanced_mae(h[h.model.eq(model)]) for key,model in MODELS.items()}
                region_factors.append({'window':window,'level':level,'region_code':code,**factor_decomposition(values)})
    csv(pd.DataFrame(factors),'factor_decomposition.csv')
    csv(pd.DataFrame(region_factors),'factor_by_province.csv')
    base=scored[scored.model.eq('v3_hgb')].copy()
    records=[]
    for level,g in base.groupby('level'):
        total=g.mae_contribution_pp.sum()
        assert np.isclose(total,balanced_mae(g),atol=1e-12)
        for regime,h in g.groupby('regime'):
            m=point_metrics(h)
            records.append({'level':level,'regime':regime,**m,
                'full_period_mae_contribution_pp':h.mae_contribution_pp.sum(),
                'error_share':h.mae_contribution_pp.sum()/total,
                'observed_reversal_n':int(h.realized_reversal.sum())})
    csv(pd.DataFrame(records),'regime_diagnostics.csv')
    regional=[];subgroups=[]
    for (level,sid),g in base.groupby(['level','series_id']):
        regional.append({'level':level,'series_id':sid,'name':g['name'].iloc[0],
            'region_code':g.region_code.iloc[0],**point_metrics(g),
            'mae_contribution_pp':g.mae_contribution_pp.sum(),
            'reversal_scored_n':int(g.realized_reversal.sum()),'large_error_n':int(g.large_error_5pp.sum())})
    csv(pd.DataFrame(regional),'regional_diagnostics.csv')
    for level,g in base.groupby('level'):
        for tag in ['realized_reversal','thin_matches','low_volume','sign_miss']:
            for value,h in g.groupby(tag):
                subgroups.append({'level':level,'tag':tag,'value':bool(value),**point_metrics(h),
                    'mae_contribution_pp':h.mae_contribution_pp.sum()})
    csv(pd.DataFrame(subgroups),'subgroup_diagnostics.csv')
    outcomes=[]
    base['realized_move_band']=np.select([base.actual_pct.gt(10),base.actual_pct.lt(-10),
        base.actual_pct.notna()],['rise_above10','fall_below_minus10','within10'],default='unscored')
    for (level,band),g in base.groupby(['level','realized_move_band']):
        outcomes.append({'level':level,'realized_move_band':band,**point_metrics(g),
             'actual_mean_pct':g.actual_pct.mean(),'predicted_mean_pct':g.prediction_pct.mean(),
             'mae_contribution_pp':g.mae_contribution_pp.sum()})
    csv(pd.DataFrame(outcomes),'outcome_band_diagnostics.csv')
    columns=['level','name','origin','actual_pct','prediction_pct','error_pp','ae_pp',
        'realized_reversal','past_direction','predicted_direction','price_input_month','return_6',
        'observed_recent_min_matches','observed_recent_mean_matches','observed_recent_volume',
        'thin_matches','low_volume','mortgage_rate_new_business_pct_change_3',
        'unsold_housing_total_change_12']
    worst=pd.concat([g.nlargest(25,'ae_pp') for _,g in base.groupby('level')])
    csv(worst[columns],'worst_cases.csv')
    time=[]
    for (level,origin),g in base.groupby(['level','origin']):
        time.append({'level':level,'origin':origin,**point_metrics(g),
                     'mae_contribution_pp':g.mae_contribution_pp.sum()})
    csv(pd.DataFrame(time),'origin_diagnostics.csv')
    validity={'models':list(MODELS.values()),'common_cohort_targets_verified':True,
        'forecast_rows_per_model':len(base),'scored_rows_per_model':int(base.actual_pct.notna().sum()),
        'unscored_rows_per_model':int(base.actual_pct.isna().sum()),
        'origins':int(base.origin.nunique()),'feature_snapshot_sha256':sources['feature_panel.parquet'],
        'balanced_contribution_sum_verified':True,'all_diagnostics_post_hoc':True,
        'historical_first_vintages_verified':False,
        'training_factor':'A/C: cumulative since2009; B/D: up to120months since2007; includes start-year difference',
        'lag_factor':'post2020May t2 sensitivity includes quality fallback; revised snapshots',
        'as_of':'2026-10-27','sources':sources}
    save(OUT/'diagnostic_manifest.json',validity)
    print(pd.DataFrame(factors).to_string(index=False))
    print(pd.DataFrame(records)[['level','regime','mae_pp','bias_pp','error_share']].to_string(index=False))

if __name__=='__main__':run()
