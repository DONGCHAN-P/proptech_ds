"""Reproducible rolling-origin forecasting, model selection and untouched holdout.

Run AFTER prepare_panel.py and official data collection. All transformations and
model fitting occur within each historical fold. Never uses current amenities as
historical features or realized future interest rates / policy changes.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hashlib
import argparse
import json
import warnings
import joblib
import numpy as np
import pandas as pd
import sklearn
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from forecast import (add_target,training_rows,join_released,policy_features,
                      lagged_change,assert_selection_available,evaluation_cohort)

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
NOTES=ROOT/'research_notes/지역별 집값 6개월 예측 연구'
ap=argparse.ArgumentParser()
ap.add_argument('--output',default='results_v3')
args=ap.parse_args()
RESULT=(OUT/args.output).resolve()
if not RESULT.is_relative_to(OUT.resolve()): raise ValueError('Results must stay inside the experiment')
RESULT.mkdir(exist_ok=True)
ASOF=pd.Timestamp('2026-10-27')
DEV=pd.date_range('2017-01-01','2023-01-01',freq='6MS')+pd.Timedelta(days=26)
TEST=pd.date_range('2024-01-01','2026-01-01',freq='6MS')+pd.Timedelta(days=26)
PRICE=['return_1','return_3','return_6','return_12','volatility_6','volatility_12',
       'volume_log','volume_vs_12','volume_yoy','median_area','area_change_12','price_log',
       'matched_complexes','province_return_3','province_return_6','province_return_12',
       'season_sin','season_cos']
CATEGORICAL=['region_code','level']

def save(path,obj):
    def default(x):
        if isinstance(x,(np.integer,np.floating)): return x.item()
        if isinstance(x,(pd.Timestamp,Path)): return str(x)
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=default,allow_nan=False)+'\n','utf-8')

def csv(df,name):
    df.to_csv(RESULT/name,index=False,encoding='utf-8-sig')

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rolling(panel,col,window,op):
    return panel.groupby('series_id',sort=False)[col].transform(lambda x:getattr(x.rolling(window,min_periods=window),op)())

def read_events():
    p=OUT/'data/policy_events_snapshot.json'
    if not p.exists(): return []
    raw=json.loads(p.read_text('utf-8'))
    events=raw if isinstance(raw,list) else raw.get('events',[])
    extra=OUT/'data/policy_2026_verified_snapshot.json'
    if extra.exists(): events+=json.loads(extra.read_text('utf-8'))
    return events

def build_features():
    p=pd.read_parquet(OUT/'data/monthly_panel.parquet').sort_values(['series_id','month']).reset_index(drop=True)
    # Extend calendar through ASOF so latest features can be carried by a strict
    # three-month SHIFT, never by filling unreported current price observations.
    parts=[]
    for sid,g in p.groupby('series_id',sort=False):
        full=pd.date_range(g.month.min(),ASOF.to_period('M').start_time,freq='MS')
        s=g.set_index('month').reindex(full).rename_axis('month').reset_index()
        for col in ['series_id','region_code','district_code','region_name','name']:
            s[col]=g[col].iloc[0]
        parts.append(s)
    p=pd.concat(parts,ignore_index=True).sort_values(['series_id','month']).reset_index(drop=True)
    for w in [1,3,6,12]:
        p[f'return_{w}']=rolling(p,'log_change',w,'sum')
    for w in [6,12]: p[f'volatility_{w}']=rolling(p,'log_change',w,'std')
    p['volume_log']=np.log1p(p.volume)
    vol12=rolling(p,'volume',12,'mean')
    p['volume_vs_12']=np.log((rolling(p,'volume',3,'mean')+1)/(vol12+1))
    p['volume_yoy']=np.log((p.volume+1)/(p.groupby('series_id').volume.shift(12)+1))
    p['area_change_12']=p.median_area-p.groupby('series_id').median_area.shift(12)
    p['price_log']=np.log(p.median_ppm)
    prov=p[p.series_id.str.startswith('p:')][['region_code','month','return_3','return_6','return_12']]
    prov=prov.rename(columns={f'return_{w}':f'province_return_{w}' for w in [3,6,12]})
    p=p.merge(prov,on=['region_code','month'],how='left',validate='many_to_one')
    p['observed_recent_min_matches']=rolling(p,'matched_complexes',12,'min')
    p['observed_recent_mean_matches']=rolling(p,'matched_complexes',12,'mean')
    p['observed_recent_volume']=rolling(p,'volume',12,'sum')
    price_shift=[c for c in PRICE if c not in ['season_sin','season_cos']]+[
        'observed_recent_min_matches','observed_recent_mean_matches','observed_recent_volume']
    p[price_shift]=p.groupby('series_id',sort=False)[price_shift].shift(3)
    p['price_input_month']=p.month-pd.DateOffset(months=3)
    p['as_of']=p.month+pd.Timedelta(days=26)
    p['season_sin']=np.sin(2*np.pi*p.month.dt.month/12)
    p['season_cos']=np.cos(2*np.pi*p.month.dt.month/12)
    p['level']=p.series_id.str[0].map({'p':'province','d':'district'})
    p['eligible']=(p.observed_recent_min_matches>=5)&(p.observed_recent_mean_matches>=10)&(p.observed_recent_volume>=200)
    extfile=OUT/'data/monthly_exogenous_snapshot.csv'
    ex=pd.read_csv(extfile,dtype={'region_code':str})
    needed=['region_code','month','variable','value','available_date']
    if not set(needed).issubset(ex.columns):
        raise ValueError(f'Official input schema missing: {set(needed)-set(ex.columns)}')
    ex['value']=pd.to_numeric(ex.value,errors='coerce')
    ex=ex[ex.value.notna()].copy()
    # Derive exogenous changes *within source series* and retain the release date
    # of the newest observation. Exact calendar joins avoid treating missing
    # source months as sequential observations.
    ex['month']=pd.to_datetime(ex.month)
    # Variables that only appeared during the holdout (or today) cannot be
    # validated as historical predictors. Preserve them in research source data.
    histories=ex[ex.month.lt('2024-01-01')].groupby('variable').month.nunique()
    included=histories[histories>=36].index
    deferred=sorted(set(ex.variable)-set(included))
    save(RESULT/'deferred_variables.json',{'reason':'fewer than 36 observed calendar months before holdout',
                                         'variables':deferred})
    ex=ex[ex.variable.isin(included)&ex.region_code.isin(['00',*p.region_code.unique()])].copy()
    count_vars=ex.variable.str.contains('complet|permit|start|unsold|household|population',case=False,regex=True)
    ex.loc[count_vars&ex.value.lt(0),'value']=np.nan
    transformed=[]
    for (region,var),g in ex.groupby(['region_code','variable'],sort=False):
        g=g.sort_values('month').copy()
        if g.month.duplicated().any(): raise ValueError(f'Duplicate official observation {region}/{var}')
        for lag in [3,12]:
            # Rate differences remain percentage-point changes; nonnegative
            # quantities use log growth to avoid comparing different city sizes.
            h=lagged_change(g,lag,log_growth=('rate' not in var and 'net_migration' not in var))
            h['variable']=var+f'_change_{lag}'
            transformed.append(h)
    ex_all=pd.concat([ex,*transformed],ignore_index=True)
    # Negative administrative flow corrections cannot be interpreted as negative
    # buildings: preserve them in source records, use missing model values.
    count_vars=ex_all.variable.str.contains('complet|permit|start|unsold|household|population',case=False,regex=True)&~ex_all.variable.str.contains('_change_')
    ex_all.loc[count_vars&ex_all.value.lt(0),'value']=np.nan
    ex_all=ex_all[ex_all.value.notna()]
    p=join_released(p,ex_all,max_age_months=6)
    external=sorted(ex_all.variable.unique())
    annualfile=OUT/'data/migration_annual_snapshot.csv'
    if annualfile.exists():
        annual=pd.read_csv(annualfile,dtype={'region_code':str})
        p=join_released(p,annual,max_age_months=18)
        if 'net_migration_annual_persons' in p:
            denominator=p.get('resident_registered_population',pd.Series(np.nan,index=p.index))
            p['annual_net_migration_rate_pct']=100*p.net_migration_annual_persons/denominator.where(denominator>0)
            external.append('annual_net_migration_rate_pct')
    # Convert count levels to log scale after the as-of join. Growth already log.
    for col in external:
        if '_change_' not in col and 'rate' not in col:
            p[col]=np.log1p(p[col].clip(lower=0))
    events=read_events()
    p=policy_features(p,events)
    policy=['policy_recent_6m','policy_announcements_6m'] if events else []
    # A province is partly exposed when a subset of districts is designated.
    # Treating province prefix 41 as unaffected by a 41xxx district policy would
    # silently miss Gyeonggi events. Weights use already-lagged 12m trade volume.
    if policy:
        districts=p[p.level.eq('district')].copy()
        districts['_weight']=districts.observed_recent_volume.fillna(0)
        denom=districts.groupby(['region_code','month'])._weight.sum()
        for col in policy:
            districts['_weighted']=districts[col]*districts._weight
            exposure=(districts.groupby(['region_code','month'])._weighted.sum()/denom.where(denom>0))
            idx=p.level.eq('province')
            key=pd.MultiIndex.from_frame(p.loc[idx,['region_code','month']])
            p.loc[idx,col]=exposure.reindex(key).to_numpy()
    # Province interactions let the same national rate have different fitted
    # associations; no hardcoded assertion about its causal sign.
    interaction=[]
    ratecols=[c for c in external if 'rate' in c and '_change_' not in c]
    for col in ratecols:
        for region in sorted(p.region_code.unique()):
            name=f'{col}_region_{region}'
            p[name]=p[col]*p.region_code.eq(region).astype(float)
            interaction.append(name)
    external+=interaction
    p=p.replace([np.inf,-np.inf],np.nan)
    current=p[p.month.eq(ASOF.to_period('M').start_time)&p.level.eq('province')]
    availability=[]
    for col in PRICE+external+policy:
        for _,row in current.iterrows():
            availability.append({'name':row['name'],'region_code':row.region_code,'feature':col,
                                 'available':bool(pd.notna(row[col]))})
    csv(pd.DataFrame(availability),'current_feature_availability.csv')
    p.to_parquet(RESULT/'feature_panel.parquet',index=False)
    save(RESULT/'feature_contract.json',{'price_features':PRICE,'external_features':external,'policy_features':policy,
        'categorical':CATEGORICAL,'price_reporting_lag_months':3,'origin_day':27,
        'forecast_as_of':str(ASOF.date()),'price_features_available_through':'2026-07',
        'forecast_reference_month':'2026-10','forecast_months':['2026-11','2026-12','2027-01','2027-02','2027-03','2027-04'],
        'current_reference_price_observed':False,'target':'future monthly matched-cell return relative to origin month; not won price',
        'external_sha256':hash_file(extfile),'policy_sha256':hash_file(OUT/'data/policy_events_snapshot.json') if events else None,
        'annual_migration_sha256':hash_file(annualfile) if annualfile.exists() else None,
        'policy_2026_sha256':hash_file(OUT/'data/policy_2026_verified_snapshot.json') if (OUT/'data/policy_2026_verified_snapshot.json').exists() else None,
        'policy_package_clustering':'announcement/package date and tightening/easing direction; at most one pulse per package per regional row',
        'unresolved_policy_geography':['41597 Dongtan cannot be assigned to whole canonical41590 Hwaseong; no broadened exposure'],
        'snapshot_backtest':'pseudo_real_time_revised_snapshot_not_historical_vintages'})
    return p,external,policy

def get_model(kind,features):
    num=Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())])
    pre=ColumnTransformer([('numeric',num,features),('region',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)])
    estimator=Ridge(alpha=100.) if kind=='ridge' else HistGradientBoostingRegressor(
        max_iter=100,max_leaf_nodes=12,min_samples_leaf=80,l2_regularization=10.,
        learning_rate=.05,early_stopping=False,random_state=20261027)
    return Pipeline([('pre',pre),('model',estimator)])

def weights(df):
    # Each level and each province get comparable mass at each monthly origin.
    count=df.groupby(['month','level','region_code']).series_id.transform('size')
    w=1./count.to_numpy()
    return w/w.mean()

def metrics(df):
    out=[]
    for (stage,horizon,model,level),g in df.groupby(['stage','horizon','model','level']):
        forecast_n=len(g)
        g=g[g.actual_pct.notna()]
        if g.empty: continue
        error=g.prediction_pct-g.actual_pct
        out.append({'stage':stage,'horizon':int(horizon),'model':model,'level':level,
                    'n':len(g),'forecast_n':forecast_n,'unscored_n':forecast_n-len(g),
                    'scored_coverage':len(g)/forecast_n,'origins':g.origin.nunique(),'mae_pp':float(error.abs().mean()),
                    'rmse_pp':float(np.sqrt(np.mean(error**2))),'bias_pp':float(error.mean()),
                    'direction_accuracy':float((np.sign(g.prediction_pct)==np.sign(g.actual_pct)).mean())})
    return pd.DataFrame(out)

def run_fold(panel,asof,horizon,specs,stage):
    train=training_rows(panel,asof)
    train=train[train.eligible & (train.month>=pd.Timestamp('2009-01-01'))]
    test=evaluation_cohort(panel,asof)
    nmonths=train.groupby('series_id').month.nunique()
    test=test[test.series_id.isin(nmonths[nmonths>=60].index)]
    if test.empty: return []
    assert train.label_available.max()<=asof
    result=[]
    for name,(kind,features) in specs.items():
        if kind=='zero': pred=np.zeros(len(test))
        elif kind=='momentum': pred=test.return_6.fillna(0).to_numpy()*horizon/6*.5
        else:
            model=get_model(kind,features)
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore',message='Skipping features without any observed values')
                model.fit(train,train.target_log_return,model__sample_weight=weights(train))
            pred=model.predict(test)
        rows=test[['series_id','name','region_code','level','month','target_month','label_available']].copy()
        rows['origin']=str(asof.date())
        rows['stage']=stage
        rows['horizon']=horizon
        rows['model']=name
        rows['prediction_pct']=np.expm1(pred)*100
        rows['actual_pct']=np.expm1(test.target_log_return.to_numpy())*100
        rows['train_n']=len(train)
        rows['train_latest_label_available']=str(train.label_available.max().date())
        result.append(rows)
    return result

def correlations(panel,features):
    # Descriptive relationships from development-era labels only; overlapping
    # 6m labels invalidate naive IID p-values, so deliberately do not report them.
    sample=training_rows(panel,pd.Timestamp('2023-12-27'))
    sample=sample[sample.eligible & sample.level.eq('province') & sample.month.ge('2009-01-01')]
    rows=[]
    for (region,name),g in sample.groupby(['region_code','name']):
        for feature in features:
            s=g[[feature,'target_log_return','month']].dropna()
            if len(s)<36 or s[feature].nunique()<3: continue
            rho=float(spearmanr(s[feature],s.target_log_return).statistic)
            if not np.isfinite(rho): continue
            rows.append({'region_code':region,'name':name,'feature':feature,'spearman':rho,'n':len(s),
                         'first_origin':str(s.month.min().date()),'last_origin':str(s.month.max().date())})
    detail=pd.DataFrame(rows)
    csv(detail,'feature_correlations_by_region.csv')
    agg=detail.groupby('feature').agg(regions=('spearman','size'),median_spearman=('spearman','median'),
                min_spearman=('spearman','min'),max_spearman=('spearman','max'),
                positive_share=('spearman',lambda x:float((x>0).mean()))).reset_index()
    agg['abs_median']=agg.median_spearman.abs()
    csv(agg.sort_values('abs_median',ascending=False),'feature_correlations_summary.csv')

def main():
    # Freeze external inputs before processing so parallel research updates can
    # never silently change data halfway through an experiment.
    for src,dst in [(NOTES/'collected/monthly_exogenous.csv',OUT/'data/monthly_exogenous_snapshot.csv'),
                    (NOTES/'collected/migration_annual_net_six_regions.csv',OUT/'data/migration_annual_snapshot.csv'),
                    (NOTES/'policy_events.json',OUT/'data/policy_events_snapshot.json'),
                    (NOTES/'policy_2026_verified_projection.json',OUT/'data/policy_2026_verified_snapshot.json')]:
        if src.exists() and not dst.exists(): dst.write_bytes(src.read_bytes())
    p,external,policy=build_features()
    macro=[c for c in external if 'rate' in c and 'migration' not in c]
    supply=[c for c in external if any(x in c for x in ['housing_','unsold_'])]
    demand=[c for c in external if any(x in c for x in ['population','household','migration'])]
    specs={'price_unchanged':('zero',[]),'damped_momentum':('momentum',[]),
           'ridge_price':('ridge',PRICE),'ridge_macro':('ridge',PRICE+macro),
           'ridge_supply':('ridge',PRICE+supply),'ridge_demand':('ridge',PRICE+demand),
           'ridge_economy':('ridge',PRICE+external),
           'ridge_full':('ridge',PRICE+external+policy),
           'boosting_full':('boost',PRICE+external+policy)}
    panel=add_target(p,6)
    correlations(panel,PRICE+external+policy)
    records=[]
    for origin in DEV:
        records.extend(run_fold(panel,origin,6,specs,'development'))
        print(f'development {origin.date()}',flush=True)
    dev=pd.concat(records,ignore_index=True)
    assert_selection_available(dev,min(TEST))
    devmetrics=metrics(dev)
    # Freeze the winner BEFORE evaluating 2024+ holdout. Province MAE is the
    # primary research metric; ties prefer the simpler earlier-listed model.
    scores=devmetrics[devmetrics.level.eq('province')].set_index('model').mae_pp
    winner=min(specs,key=lambda k:(scores.get(k,float('inf')),list(specs).index(k)))
    save(RESULT/'selection_frozen_before_holdout.json',{'winner':winner,'criterion':'development province 6m MAE',
          'development_origins':[str(x.date()) for x in DEV],'holdout_origins':[str(x.date()) for x in TEST],
          'development_scores':scores.to_dict(),'parameter_search':'none; one predeclared configuration per family',
          'selection_information_cutoff':min(TEST),'latest_selection_label_available':dev.label_available.max(),
          'feature_groups':{'macro':macro,'supply':supply,'demand':demand,'policy':policy}})
    print(f'Frozen winner: {winner}',flush=True)
    for origin in TEST:
        records.extend(run_fold(panel,origin,6,specs,'holdout'))
        print(f'holdout {origin.date()}',flush=True)
    backtest=pd.concat(records,ignore_index=True)
    # Calibrate 1..5m trajectories for the same preselected family; selecting a
    # different winner per future month on the holdout would be optimistic.
    chosen={winner:specs[winner]}
    for h in range(1,6):
        hp=add_target(p,h)
        for origin in TEST:
            records.extend(run_fold(hp,origin,h,chosen,'path_holdout'))
        print(f'path horizon={h}',flush=True)
    alltests=pd.concat(records,ignore_index=True)
    csv(alltests,'backtest_predictions.csv')
    coverage=alltests.groupby(['stage','origin','horizon','model','level']).actual_pct.agg(
        forecast_n='size',scored_n='count').reset_index()
    coverage['unscored_n']=coverage.forecast_n-coverage.scored_n
    coverage['scored_coverage']=coverage.scored_n/coverage.forecast_n
    csv(coverage,'evaluation_coverage.csv')
    summary=metrics(alltests)
    csv(summary,'backtest_metrics.csv')
    csv(backtest[backtest.stage.eq('holdout')].groupby(['model','level','region_code']).apply(
        lambda g:pd.Series({'forecast_n':len(g),'scored_n':int(g.actual_pct.notna().sum()),'mae_pp':(g.prediction_pct-g.actual_pct).abs().mean(),
                            'bias_pp':(g.prediction_pct-g.actual_pct).mean()}),include_groups=False).reset_index(),
        'holdout_by_region.csv')
    # Error range is empirical held-out residual spread, not an IID statistical
    # confidence interval: origins and geographic levels are dependent.
    residuals=alltests[alltests.model.eq(winner)&alltests.stage.isin(['holdout','path_holdout'])].copy()
    residuals['residual']=residuals.actual_pct-residuals.prediction_pct
    intervals={}
    for (h,level),g in residuals.groupby(['horizon','level']):
        intervals[(h,level)]=(float(g.residual.quantile(.1)),float(g.residual.quantile(.9)))
    forecasts=[]
    excluded=[]
    models=RESULT/'models'
    models.mkdir(exist_ok=True)
    for h in range(1,7):
        hp=add_target(p,h)
        train=training_rows(hp,ASOF)
        train=train[train.eligible&train.month.ge('2009-01-01')]
        nmonths=train.groupby('series_id').month.nunique()
        cur=hp[hp.month.eq(ASOF.to_period('M').start_time)].copy()
        valid=cur.eligible & cur.series_id.isin(nmonths[nmonths>=60].index)
        if h==6:
            for _,r in cur[~valid].iterrows():
                excluded.append({'series_id':r.series_id,'name':r['name'],
                    'reason':'insufficient continuous matched trades or fewer than 60 eligible training months',
                    'last_input_month':str(r.price_input_month.date())})
        cur=cur[valid]
        kind,features=specs[winner]
        if kind=='zero': pred=np.zeros(len(cur))
        elif kind=='momentum': pred=cur.return_6.fillna(0).to_numpy()*h/6*.5
        else:
            model=get_model(kind,features)
            model.fit(train,train.target_log_return,model__sample_weight=weights(train))
            pred=model.predict(cur)
            joblib.dump(model,models/f'{winner}_{h}m.joblib',compress=3)
        cur['horizon']=h
        cur['prediction_pct']=np.expm1(pred)*100
        cur['forecast_month']=cur.month+pd.DateOffset(months=h)
        cur['error_p10_pp']=[intervals.get((h,l),(np.nan,np.nan))[0] for l in cur.level]
        cur['error_p90_pp']=[intervals.get((h,l),(np.nan,np.nan))[1] for l in cur.level]
        cur['range_low_pct']=cur.prediction_pct+cur.error_p10_pp
        cur['range_high_pct']=cur.prediction_pct+cur.error_p90_pp
        cur['model']=winner
        cur['as_of']=ASOF
        cur['reference_index']=100.
        cur['forecast_index']=100+cur.prediction_pct
        cur['reference_month_observed']=False
        forecasts.append(cur[['series_id','name','region_code','level','as_of','price_input_month','forecast_month',
                              'horizon','prediction_pct','range_low_pct','range_high_pct','forecast_index',
                              'reference_index','reference_month_observed','observed_recent_mean_matches','model']])
        print(f'final {h}m {len(cur)} regions; {len(train):,} training rows',flush=True)
    future=pd.concat(forecasts,ignore_index=True)
    csv(future,'forecast_next_6_months.csv')
    save(RESULT/'excluded_series.json',excluded)
    save(RESULT/'run_summary.json',{'as_of':ASOF,'winner':winner,'feature_count':len(PRICE+external+policy),
          'price_features':len(PRICE),'external_features':len(external),'policy_features':len(policy),
          'province_forecasts':int(future[future.horizon.eq(6)&future.level.eq('province')].shape[0]),
          'district_forecasts':int(future[future.horizon.eq(6)&future.level.eq('district')].shape[0]),
          'excluded':len(excluded),'training_origin_start':'2009-01','price_input_end':'2026-07',
          'raw_history_start':'2006-01','sklearn':sklearn.__version__,
          'forecast_sha256':hash_file(RESULT/'forecast_next_6_months.csv'),
          'limitations':['revised historical snapshots','assumed transaction/statistical release lags where noted',
                         'matched complex/area does not control floor or renovation',
                         'partial policy registry; no policy-causal interpretation',
                         'unobserved origin-month price; forecasts are relative returns, not won prices',
                         'empirical error spread; dependent observations; no guaranteed coverage']})
    print(summary[summary.stage.eq('holdout')].to_string(index=False),flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=4):
        main()
