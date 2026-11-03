"""Versioned, cached six-month forecast campaign with causal error feedback.

All 2024+ evaluation dates were previously inspected: this is retrospective
iteration, never a claim to a new blind test. Labels and eligibility are fixed.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
OLD=Path(__file__).resolve().parent.parent/'regional_forecast_20261027'
sys.path.insert(1,str(OLD))
import argparse
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from lightgbm import LGBMRegressor
from threadpoolctl import threadpool_limits
from forecast import add_target,training_rows,evaluation_cohort,join_released,lagged_change
from evaluation import point_metrics,balanced_mae,known_errors,loss_weights

OUT=Path(__file__).resolve().parent
RESULT=OUT/'results'
RESULT.mkdir(exist_ok=True)
CACHE=OUT/'cache'
CACHE.mkdir(exist_ok=True)
ASOF=pd.Timestamp('2026-10-27')
ORIGINS=list(pd.date_range('2015-01-01','2026-01-01',freq='6MS')+pd.Timedelta(days=26))
START_SCORE=pd.Timestamp('2017-01-27')
PRICE=json.loads((OLD/'results_v3/feature_contract.json').read_text('utf-8'))['price_features']
FULL=json.loads((OLD/'results_v3/feature_contract.json').read_text('utf-8'))
CAT=['region_code','level']
COMPACT_PRICE=['return_1','return_3','return_6','return_12','volatility_6','volatility_12',
               'volume_vs_12','volume_yoy','province_return_3','province_return_6',
               'relative_return_6','acceleration','market_return_3','market_return_6',
               'capital_return_6','season_sin','season_cos']
ECON=['bok_policy_rate_eom_pct','bok_policy_rate_eom_pct_change_3','bok_policy_rate_eom_pct_change_12',
      'mortgage_rate_new_business_pct','mortgage_rate_new_business_pct_change_3',
      'mortgage_rate_new_business_pct_change_12','unsold_housing_total_change_3','unsold_housing_total_change_12',
      'resident_registered_households_change_3','resident_registered_households_change_12',
      'resident_registered_population_change_12','annual_net_migration_rate_pct',
      'housing_completions_all_change_12','housing_starts_all_change_12','housing_permits_all_change_12',
      'unsold_per_1000_households','completions_per_1000_households','policy_recent_6m','policy_announcements_6m']
CORE=COMPACT_PRICE+ECON
SPECS={
 'v3_hgb':dict(kind='hgb',features=PRICE+FULL['external_features']+FULL['policy_features'],start='2009-01-01'),
 'zero':dict(kind='zero',features=[]),
 'damped_momentum':dict(kind='momentum6',features=[],multiplier=.5),
 'momentum6':dict(kind='momentum6',features=[],multiplier=1.),
 'momentum3':dict(kind='momentum3',features=[]),
 'momentum_blend':dict(kind='momentum_blend',features=[]),
 'ridge_compact_expanding':dict(kind='ridge',features=CORE),
 'ridge_compact_72m':dict(kind='ridge',features=CORE,window=72),
 'ridge_compact_120m':dict(kind='ridge',features=CORE,window=120),
 'ridge_compact_decay36':dict(kind='ridge',features=CORE,half_life=36),
 'ridge_price_72m':dict(kind='ridge',features=COMPACT_PRICE,window=72),
 'ridge_interaction_120m':dict(kind='ridge',features=CORE+['rate_momentum_interaction','rate_capital_interaction'],window=120),
 'ridge_full_120m':dict(kind='ridge',features=PRICE+FULL['external_features']+FULL['policy_features'],window=120),
 'hgb_compact_expanding':dict(kind='hgb',features=CORE),
 'hgb_compact_72m':dict(kind='hgb',features=CORE,window=72),
 'hgb_compact_120m':dict(kind='hgb',features=CORE,window=120),
 'lgbm_compact_120m':dict(kind='lgbm',features=CORE,window=120),
 'hgb_price_120m':dict(kind='hgb',features=COMPACT_PRICE,window=120),
}
STRATEGIES=['fixed_blend','online_best','online_ensemble','online_bias_corrected']

def save(path,value):
    def default(x):
        if isinstance(x,(np.integer,np.floating)): return x.item()
        if isinstance(x,(pd.Timestamp,Path)): return str(x)
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=default,allow_nan=False)+'\n','utf-8')

def csv(df,name): df.to_csv(RESULT/name,index=False,encoding='utf-8-sig')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_supply(p):
    source=OUT.parents[1]/'research_notes/지역별 집값 예측 반복 검증/data/supplement.csv'
    frozen=OUT/'supply_supplement_snapshot.csv'
    expected='24b6bc067466c0ba67b73746ef902d38ff495ed1df4c2dc96d10bca87c5d2bcb'
    if not frozen.exists():
        assert sha(source)==expected
        frozen.write_bytes(source.read_bytes())
    assert sha(frozen)==expected
    original=pd.read_csv(OLD/'data/monthly_exogenous_snapshot.csv',dtype={'region_code':str})
    supplement=pd.read_csv(frozen,dtype={'region_code':str})
    variables=['housing_completions_all','housing_starts_all','housing_permits_all']
    base=original[original.variable.isin(variables)].copy()
    # Limit the deployment update to six provinces with long historical supply.
    # National totals are never broadcast as missing regional supply; new regions
    # without a comparable historical supply series are retained in research only.
    codes=sorted(base.region_code.unique())
    extra=supplement[supplement.region_code.isin(codes)&supplement.variable.isin(variables)].copy()
    combined=pd.concat([base,extra],ignore_index=True)
    combined['month']=pd.to_datetime(combined.month)
    assert not combined.duplicated(['region_code','variable','month']).any()
    combined['value']=pd.to_numeric(combined.value,errors='coerce')
    combined.loc[combined.value<0,'value']=np.nan
    derivatives=[]
    for (_,var),g in combined.groupby(['region_code','variable']):
        for lag in [3,12]:
            h=lagged_change(g,lag,log_growth=True)
            h['variable']=var+f'_change_{lag}'
            derivatives.append(h)
    combined=pd.concat([combined,*derivatives],ignore_index=True)
    combined=combined[combined.value.notna()]
    cols=sorted(combined.variable.unique())
    current=p.month.eq(ASOF.to_period('M').start_time)&p.level.eq('province')&p.region_code.isin(codes)
    before=int(p.loc[current,cols].isna().sum().sum())
    joined=join_released(p[['region_code','as_of']],combined,max_age_months=6)
    for col in cols:
        p[col]=joined[col] if '_change_' in col else np.log1p(joined[col])
    after=int(p.loc[current,cols].isna().sum().sum())
    save(RESULT/'supply_update.json',{'sha256':expected,'all_collected_rows':len(supplement),
          'integrated_rows':len(extra),'regions':codes,'variables':cols,
          'current_missing_before':before,'current_missing_after':after,
          'first_new_release':str(pd.to_datetime(extra.available_date).min()),
          'not_credited_as_historical_accuracy_gain':True,
          'other_regions_deferred_until_comparable_history':True})
    return p

def features():
    p=pd.read_parquet(OLD/'results_v3/feature_panel.parquet').sort_values(['series_id','month']).reset_index(drop=True)
    p['relative_return_6']=p.return_6-p.province_return_6
    p['acceleration']=p.return_3*2-p.return_6
    province=p[p.level.eq('province')]
    for w in [3,6]:
        market=province.groupby('month')[f'return_{w}'].mean()
        p[f'market_return_{w}']=p.month.map(market)
    capital=province[province.region_code.isin(['11','28','41'])].groupby('month').return_6.mean()
    p['capital_return_6']=p.month.map(capital)
    p['rate_momentum_interaction']=p.mortgage_rate_new_business_pct_change_3*p.return_6
    p['rate_capital_interaction']=p.mortgage_rate_new_business_pct_change_3*p.region_code.isin(['11','28','41'])
    p=update_supply(p)
    for src,dst in [('unsold_housing_total','unsold_per_1000_households'),
                    ('housing_completions_all','completions_per_1000_households')]:
        p[dst]=1000*np.expm1(p[src])/np.expm1(p.resident_registered_households).where(lambda s:s>0)
    p=p.replace([np.inf,-np.inf],np.nan)
    previous=OUT/'candidate_feature_history.parquet'
    if previous.exists():
        old=pd.read_parquet(previous)
        new=p[p.month<=pd.Timestamp('2026-01-01')][old.columns].reset_index(drop=True)
        pd.testing.assert_frame_equal(old.reset_index(drop=True),new,check_exact=False,rtol=1e-12,atol=1e-12)
        save(RESULT/'historical_feature_invariance.json',{'passed':True,'rows':len(old),
             'latest_evaluation_origin':'2026-01','tolerance':1e-12,
             'statement':'2026 supply integration does not change any historical evaluation feature'})
    p.to_parquet(RESULT/'feature_panel.parquet',index=False)
    return p

def model_for(spec):
    pre=ColumnTransformer([
        ('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                             ('scale',StandardScaler())]),spec['features']),
        ('region',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])
    if spec['kind']=='ridge': estimator=Ridge(alpha=100.)
    elif spec['kind']=='hgb':
        estimator=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=12,min_samples_leaf=80,
                 l2_regularization=10.,learning_rate=.05,early_stopping=False,random_state=20261027)
    else:
        estimator=LGBMRegressor(n_estimators=140,num_leaves=15,min_child_samples=80,reg_lambda=20.,
                 learning_rate=.04,n_jobs=4,verbosity=-1,random_state=20261027,deterministic=True,force_col_wise=True)
    return Pipeline([('pre',pre),('model',estimator)])

def fit_predict(panel,asof,cohort,spec):
    train=training_rows(panel,asof)
    train=train[train.eligible&train.month.ge(spec.get('start','2007-01-01'))]
    if spec.get('window'):
        # Window measured at the latest mature training origin, not asof, so it
        # retains exactly 6/10 years of trainable observations despite label lag.
        earliest=train.month.max()-pd.DateOffset(months=spec['window']-1)
        train=train[train.month>=earliest]
    kind=spec['kind']
    if kind=='zero': pred=np.zeros(len(cohort));model=None
    elif kind=='momentum6': pred=cohort.return_6.to_numpy()*spec['multiplier'];model=None
    elif kind=='momentum3': pred=cohort.return_3.to_numpy()*2;model=None
    elif kind=='momentum_blend': pred=.5*cohort.return_6.to_numpy()+cohort.return_3.to_numpy();model=None
    else:
        model=model_for(spec)
        counts=train.groupby(['month','level','region_code']).series_id.transform('size').to_numpy()
        w=1./counts
        if spec.get('half_life'):
            age=(train.month.max().year-train.month.dt.year)*12+train.month.max().month-train.month.dt.month
            w*=np.power(.5,age/spec['half_life'])
        w/=w.mean()
        model.fit(train,train.target_log_return,model__sample_weight=w)
        pred=model.predict(cohort)
    assert train.label_available.max()<=asof
    return np.expm1(pred)*100,model,len(train),train.label_available.max()

def cohort_at(panel,origin):
    # Fixed common cohort from the original study, independent of future labels.
    train=training_rows(panel,origin)
    train=train[train.eligible&train.month.ge('2009-01-01')]
    counts=train.groupby('series_id').month.nunique()
    return panel[panel.month.eq(origin.to_period('M').start_time)&panel.eligible&panel.series_id.isin(counts[counts>=60].index)].copy()

def bank(p):
    panel=add_target(p,6)
    base=pd.read_csv(OLD/'results_v3/backtest_predictions.csv',dtype={'region_code':str},
                     parse_dates=['origin','month','target_month','label_available','train_latest_label_available'])
    base=base[base.model.eq('boosting_full')&base.horizon.eq(6)]
    historical=p[p.month<=pd.Timestamp('2026-01-01')]
    # Feature changes after the last evaluation origin cannot change past fits.
    fingerprint=hashlib.sha256(pd.util.hash_pandas_object(historical,index=True).values.tobytes()+
                json.dumps(SPECS,sort_keys=True).encode()+sha(Path(__file__)).encode()).hexdigest()
    records=[]
    for origin in ORIGINS:
        dest=CACHE/f'bank_{origin:%Y%m}.parquet'
        meta=dest.with_suffix('.json')
        if dest.exists() and meta.exists() and json.loads(meta.read_text('utf-8'))['fingerprint']==fingerprint:
            records.append(pd.read_parquet(dest));print(f'cached {origin.date()}',flush=True);continue
        cohort=cohort_at(panel,origin)
        if cohort.empty: continue
        block=[]
        for name,spec in SPECS.items():
            existing=base[base.origin.eq(origin)]
            if name=='v3_hgb' and not existing.empty:
                # Never cherry-pick baseline rows: exact cohort equality required.
                assert set(existing.series_id)==set(cohort.series_id)
                rows=existing.copy()
                rows['model']=name
            else:
                pred,_,n,last=fit_predict(panel,origin,cohort,spec)
                rows=cohort[['series_id','name','region_code','level','month','target_month','label_available','volatility_6']].copy()
                rows['prediction_pct']=pred
                rows['actual_pct']=np.expm1(cohort.target_log_return)*100
                rows['origin']=origin
                rows['model']=name
                rows['train_n']=n
                rows['train_latest_label_available']=last
            block.append(rows)
        combined=pd.concat(block,ignore_index=True)
        assert not combined.duplicated(['model','series_id']).any()
        combined.to_parquet(dest,index=False)
        save(meta,{'fingerprint':fingerprint,'origin':origin,'rows':len(combined),'models':len(SPECS)})
        records.append(combined)
        print(f'bank {origin.date()} {len(cohort)} regions x {len(SPECS)} candidates',flush=True)
    result=pd.concat(records,ignore_index=True)
    result.to_parquet(RESULT/'candidate_predictions.parquet',index=False)
    return result

def historical_scores(history,level,asof):
    known=known_errors(history,asof,lookback_months=60)
    known=known[known.level.eq(level)&known.model.isin(SPECS)]
    if known.origin.nunique()<3: return None,known
    losses={}
    for name,g in known.groupby('model'):
        # Penalize large errors without letting a populous province dominate.
        m=point_metrics(g)
        losses[name]=m['balanced_mae_pp']+.2*m['p90_ae_pp']+.2*abs(m['bias_pp'])
    return pd.Series(losses),known

def strategy_predictions(history,rows,origin):
    blocks=[];logs=[]
    for level,current in rows.groupby('level'):
        wide=current.pivot(index='series_id',columns='model',values='prediction_pct')
        assert wide.notna().all().all()
        meta=current.drop_duplicates('series_id').set_index('series_id').loc[wide.index].copy()
        losses,known=historical_scores(history,level,origin)
        if losses is None:
            ensemble=pd.Series(0.,index=wide.columns);ensemble['v3_hgb']=1.
            best=ensemble.copy()
        else:
            ensemble=loss_weights(losses).reindex(wide.columns,fill_value=0.)
            best=pd.Series(0.,index=wide.columns);best[losses.idxmin()]=1.
        for strategy in STRATEGIES:
            w=ensemble if strategy!='online_best' else best
            if strategy=='fixed_blend':
                w=pd.Series(0.,index=wide.columns);w['v3_hgb']=.5;w['damped_momentum']=.5
            pred=wide.to_numpy()@w.to_numpy()
            # Bias correction uses only prior causal strategy forecasts whose
            # outcomes have already been published. It cannot train on itself.
            correction=np.zeros(len(meta))
            if strategy=='online_bias_corrected':
                past=known_errors(history,origin,lookback_months=36)
                past=past[past.level.eq(level)&past.model.eq(strategy)]
                if past.origin.nunique()>=3:
                    past=past.copy();past['residual']=past.actual_pct-past.prediction_pct
                    global_bias=float(past.groupby(['origin','region_code']).residual.mean().mean())
                    for j,(_,row) in enumerate(meta.iterrows()):
                        s=past[past.region_code.eq(row.region_code)]
                        n=s.origin.nunique();local=float(s.residual.mean()) if len(s) else global_bias
                        correction[j]=.5*np.clip((n*local+8*global_bias)/(n+8),-5,5)
                pred+=correction
            out=meta.copy();out['model']=strategy;out['prediction_pct']=pred
            blocks.append(out.reset_index())
            logs.append({'origin':str(origin.date()),'level':level,'strategy':strategy,
                         'known_origins':int(known.origin.nunique()),
                         'latest_known_label':str(known.label_available.max()) if len(known) else None,
                         'weights':{k:float(v) for k,v in w.items() if v>0},
                         'bias_correction_mean_pp':float(correction.mean())})
    return pd.concat(blocks,ignore_index=True),logs

def add_intervals(current,history,origin):
    out=current.copy()
    for coverage in [80,95]:
        out[f'lower_{coverage}']=np.nan;out[f'upper_{coverage}']=np.nan
    for (model,level),indices in out.groupby(['model','level']).groups.items():
        known=known_errors(history,origin,lookback_months=60)
        known=known[known.model.eq(model)&known.level.eq(level)]
        if known.origin.nunique()<3: continue
        residual=known.actual_pct-known.prediction_pct
        for coverage in [80,95]:
            alpha=1-coverage/100
            lo=float(residual.quantile(alpha/2));hi=float(residual.quantile(1-alpha/2))
            out.loc[indices,f'lower_{coverage}']=out.loc[indices,'prediction_pct']+lo
            out.loc[indices,f'upper_{coverage}']=out.loc[indices,'prediction_pct']+hi
    return out

def evaluate(predictions):
    history=predictions.iloc[:0].copy()
    allrows=[];logs=[]
    for origin,rows in predictions.groupby('origin',sort=True):
        strategies,events=strategy_predictions(history,rows,origin)
        current=pd.concat([rows,strategies],ignore_index=True)
        current=add_intervals(current,history,origin)
        allrows.append(current);logs.extend(events)
        history=pd.concat([history,current],ignore_index=True)
    result=pd.concat(allrows,ignore_index=True)
    result.to_parquet(RESULT/'all_predictions.parquet',index=False)
    save(RESULT/'selection_trace.json',logs)
    csv(result,'all_predictions.csv')
    summary=[]
    windows={'all_regimes':(pd.Timestamp('2017-01-27'),ASOF),
             'early':(pd.Timestamp('2017-01-27'),pd.Timestamp('2019-12-31')),
             'boom':(pd.Timestamp('2020-01-01'),pd.Timestamp('2021-12-31')),
             'turn':(pd.Timestamp('2022-01-01'),pd.Timestamp('2023-12-31')),
             'recent':(pd.Timestamp('2024-01-01'),ASOF)}
    for window,(start,end) in windows.items():
        for (model,level),g in result[result.origin.between(start,end)].groupby(['model','level']):
            summary.append({'window':window,'model':model,'level':level,'origins':g.origin.nunique(),**point_metrics(g)})
    summary=pd.DataFrame(summary)
    for ref in ['v3_hgb','damped_momentum','zero']:
        reference=summary[summary.model.eq(ref)].set_index(['window','level']).mae_pp
        summary[f'skill_vs_{ref}']=1-summary.mae_pp/pd.MultiIndex.from_frame(summary[['window','level']]).map(reference)
    csv(summary,'scorecard.csv')
    detail=[]
    for (model,level,region),g in result[result.origin>=START_SCORE].groupby(['model','level','region_code']):
        detail.append({'model':model,'level':level,'region_code':region,**point_metrics(g)})
    csv(pd.DataFrame(detail),'by_region.csv')
    bytime=[]
    for (model,level,origin),g in result[result.origin>=START_SCORE].groupby(['model','level','origin']):
        bytime.append({'model':model,'level':level,'origin':origin,**point_metrics(g)})
    csv(pd.DataFrame(bytime),'by_origin.csv')
    baseline=summary[summary.window.eq('all_regimes')&summary.model.eq('v3_hgb')].set_index('level')
    decisions=[]
    for name in [*SPECS,*STRATEGIES]:
        m=summary[summary.window.eq('all_regimes')&summary.model.eq(name)].set_index('level')
        if len(m)!=2: continue
        ratio=m.balanced_mae_pp/baseline.balanced_mae_pp
        tail=m.p90_ae_pp/baseline.p90_ae_pp
        passed=bool(ratio.mean()<=.95 and (ratio<=1).all() and (tail<=1.1).all())
        decisions.append({'model':name,'mean_balanced_mae_ratio':float(ratio.mean()),
                          'province_ratio':float(ratio.get('province',np.nan)),
                          'district_ratio':float(ratio.get('district',np.nan)),
                          'max_p90_ratio':float(tail.max()),'eligible_for_promotion':passed})
    decision=pd.DataFrame(decisions).sort_values('mean_balanced_mae_ratio')
    csv(decision,'promotion_decisions.csv')
    # Primary adaptive rule declared before scores. Offline best is diagnostic,
    # never described as a past model that was selected without future knowledge.
    primary='online_ensemble'
    passed=bool(decision.set_index('model').loc[primary,'eligible_for_promotion'])
    save(RESULT/'campaign_summary.json',{'primary_rule':primary,'primary_passed_promotion_gate':passed,
         'prospective_rule':primary if passed else 'v3_hgb',
         'exploratory_offline_best':str(decision.iloc[0].model),
         'candidate_count':len(SPECS),'strategy_count':len(STRATEGIES),'origin_count':len(ORIGINS),
         'evaluation_start':str(START_SCORE.date()),'as_of':str(ASOF.date()),
         'new_blind_holdout':False,'source_vintage':'same revised snapshot; release lags partly assumed',
         'promotion_gate':'balanced MAE mean>=5% improvement; neither geography worse; p90<=10%worse',
         'future_reference_month_observed':False})
    return result,summary

def forecast(p,history):
    panel=add_target(p,6)
    cohort=cohort_at(panel,ASOF)
    rows=[]
    models=RESULT/'models';models.mkdir(exist_ok=True)
    for name,spec in SPECS.items():
        pred,model,n,last=fit_predict(panel,ASOF,cohort,spec)
        record=cohort[['series_id','name','region_code','level','month','target_month','label_available']].copy()
        record['origin']=ASOF;record['model']=name;record['prediction_pct']=pred;record['actual_pct']=np.nan
        record['train_n']=n;record['train_latest_label_available']=last
        if model is not None:joblib.dump(model,models/f'{name}.joblib',compress=3)
        rows.append(record)
    current=pd.concat(rows,ignore_index=True)
    strategies,trace=strategy_predictions(history,current,ASOF)
    current=pd.concat([current,strategies],ignore_index=True)
    current=add_intervals(current,history,ASOF)
    csv(current,'future_forecasts_6m.csv')
    save(RESULT/'prospective_selection_trace.json',trace)
    save(RESULT/'forecast_freeze.json',{'as_of':ASOF,'target_month':'2027-04',
         'forecast_sha256':sha(RESULT/'future_forecasts_6m.csv'),
         'feature_panel_sha256':sha(RESULT/'feature_panel.parquet'),
         'all_historical_errors_available_at_freeze':str(known_errors(history,ASOF).label_available.max()),
         'note':'Freeze this release; evaluate after target labels mature. Empirical intervals are not guaranteed coverage.'})
    print(f'Frozen future forecasts: {len(cohort)} regions x {len(SPECS)+len(STRATEGIES)} rules',flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['all','bank','evaluate','forecast'],default='all')
    args=ap.parse_args()
    save(OUT/'campaign_config.json',{'as_of':ASOF,'origins':ORIGINS,'specs':SPECS,'strategies':STRATEGIES,
         'primary_rule':'online_ensemble','neutral_band_pct':1.,'label_reporting_lag_months':3,
         'score_start':START_SCORE,'history_loss_lookback_months':60,
         'evidence':'retrospective repeated use of historical data; no new blind holdout'})
    p=features()
    with threadpool_limits(limits=4):
        if args.mode in ['all','bank']:pred=bank(p)
        else:pred=pd.read_parquet(RESULT/'candidate_predictions.parquet')
        if args.mode in ['all','evaluate']:history,summary=evaluate(pred)
        elif args.mode=='forecast':history=pd.read_parquet(RESULT/'all_predictions.parquet')
        else:return
        if args.mode in ['all','forecast']:forecast(p,history)
    print('Campaign complete',flush=True)

if __name__=='__main__':main()
