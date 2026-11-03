"""Two predeclared calibration alternatives; existing point forecasts stay fixed."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from diagnostics import OUT,PREV,WINDOWS,read_sources,attach_inputs,save,csv,sha
from evaluation import point_metrics,known_errors
from artifacts import freeze_release

METHODS=['baseline','symmetric','volatility_scaled']

def scale(rows):
    # An observed volatility proxy, not a claim that returns are independent.
    return (100*np.sqrt(6)*rows.volatility_6).clip(lower=1.).fillna(1.)

def calibrate(current,history,origin,method):
    if method not in METHODS:raise ValueError('Unknown interval method')
    out=current.copy()
    for coverage in [80,95]:out[f'lower_{coverage}']=np.nan;out[f'upper_{coverage}']=np.nan
    known=known_errors(history,origin,lookback_months=60)
    for level,indices in out.groupby('level').groups.items():
        prior=known[known.level.eq(level)]
        if prior.origin.nunique()<3:continue
        residual=prior.actual_pct-prior.prediction_pct
        for coverage in [80,95]:
            alpha=1-coverage/100
            if method=='symmetric':
                q=min(1.,np.ceil((len(prior)+1)*coverage/100)/len(prior))
                radius=float(residual.abs().quantile(q,interpolation='higher'))
                lower=-radius;upper=radius
            else:
                values=residual/scale(prior) if method=='volatility_scaled' else residual
                lower=float(values.quantile(alpha/2));upper=float(values.quantile(1-alpha/2))
                if method=='volatility_scaled':
                    lower=lower*scale(out.loc[indices]);upper=upper*scale(out.loc[indices])
            out.loc[indices,f'lower_{coverage}']=out.loc[indices,'prediction_pct']+lower
            out.loc[indices,f'upper_{coverage}']=out.loc[indices,'prediction_pct']+upper
    return out

def run():
    _,features,_,main,_=read_sources()
    history=pd.read_parquet(main/'history.parquet')
    history=attach_inputs(history[history.model.eq('v3_hgb')],features)
    historical=[]
    for origin,current in history.groupby('origin',sort=True):
        for method in METHODS:
            result=calibrate(current,history,origin,method)
            if method=='baseline':
                for c in ['lower_80','upper_80','lower_95','upper_95']:
                    assert np.allclose(current[c],result[c],rtol=1e-10,atol=1e-9,equal_nan=True),c
            result['calibration_rule']=method
            historical.append(result)
    allrows=pd.concat(historical,ignore_index=True)
    allrows.to_parquet(OUT/'interval_predictions.parquet',index=False)
    scores=[]
    for window,(a,b) in WINDOWS.items():
        for (method,level),g in allrows[allrows.origin.between(a,b)].groupby(['calibration_rule','level']):
            scores.append({'window':window,'calibration_rule':method,'level':level,**point_metrics(g)})
    scorecard=pd.DataFrame(scores);csv(scorecard,'interval_scorecard.csv')
    gate=[]
    for method in METHODS[1:]:
        comparisons=[]
        for level in ['province','district']:
            g=scorecard[scorecard.window.eq('all_regimes')&scorecard.level.eq(level)].set_index('calibration_rule')
            old=g.loc['baseline'];new=g.loc[method]
            comparisons.append(dict(method=method,level=level,coverage80=new.interval_coverage_80,
               interval_score_ratio=new.interval_score_80/old.interval_score_80,
               width_ratio=new.interval_width_80_pp/old.interval_width_80_pp,
               passed=bool(new.interval_coverage_80>=.75 and new.interval_score_80<=old.interval_score_80 and
                           new.interval_width_80_pp<=1.25*old.interval_width_80_pp)))
        passed=all(c['passed'] for c in comparisons)
        for row in comparisons:row['both_levels_passed']=passed
        gate.extend(comparisons)
    csv(pd.DataFrame(gate),'interval_decisions.csv')
    issued=pd.read_csv(main/'future_forecasts_6m.csv',dtype={'region_code':str},parse_dates=['origin'])
    issued=issued[issued.model.eq('v3_hgb')].copy()
    current=attach_inputs(issued,features)
    future=[]
    for method in METHODS:
        rows=calibrate(current,history,pd.Timestamp('2026-10-27'),method)
        assert np.allclose(rows.prediction_pct,current.prediction_pct,atol=1e-12)
        rows['calibration_rule']=method;future.append(rows)
    future=pd.concat(future,ignore_index=True)
    keep=['series_id','name','region_code','level','origin','target_month','model','calibration_rule',
          'prediction_pct','lower_80','upper_80','lower_95','upper_95','price_input_month','volatility_6']
    csv(future[keep],'interval_future_forecasts.csv')
    save(OUT/'interval_config.json',{'methods':METHODS,'past_error_lookback_months':60,
         'minimum_mature_origins':3,'label_maturity_months':3,'point_model':'v3_hgb',
         'source_release':str(main.relative_to(PREV)),
         'source_release_manifest_sha256':sha(main/'release.json'),
         'volatility_scale':'max(100*sqrt(6)*observed_volatility_6,1pp); missing1pp',
         'symmetric_quantile':'min(1,ceil((n+1)*coverage)/n), higher empirical quantile',
         'gate':'both levels all-regimes coverage80>=.75, score<=baseline,width<=1.25baseline',
         'historical_first_vintage_verified':False,'new_blind_evaluation':False,
         'operating_change':False,'role':'frozen research candidates; point forecasts unchanged'})
    files={name:OUT/name for name in ['interval_future_forecasts.csv','interval_predictions.parquet',
        'interval_scorecard.csv','interval_config.json','interval_decisions.csv']}
    files.update({f'code/{name}':OUT/name for name in ['interval_experiment.py','diagnostics.py']})
    files['code/evaluation.py']=PREV/'evaluation.py'
    files['source_release.json']=main/'release.json'
    release=freeze_release(OUT/'interval_releases',files,{'as_of':'2026-10-27','point_source':main.name,
            'role':'research interval sensitivity; no promotion to operation'})
    save(OUT/'interval_release_pointer.json',{'release_id':release.name,'directory':str(release.relative_to(OUT))})
    print(scorecard[scorecard.window.eq('all_regimes')][['calibration_rule','level','mae_pp',
          'interval_coverage_80','interval_width_80_pp','interval_score_80']].to_string(index=False))
    print(pd.DataFrame(gate).to_string(index=False))

if __name__=='__main__':run()
