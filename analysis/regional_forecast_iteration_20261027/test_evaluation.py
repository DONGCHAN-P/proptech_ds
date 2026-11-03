from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import pytest
import evaluation as e
import experiment as x

def test_metrics_keep_unobserved_outcome_in_coverage():
    d=pd.DataFrame({'prediction_pct':[2.,3.,99.],'actual_pct':[1.,5.,np.nan]})
    m=e.point_metrics(d)
    assert m['forecast_n']==3 and m['scored_n']==2
    assert m['mae_pp']==1.5 and np.isclose(m['rmse_pp'],np.sqrt(2.5))
    assert m['bias_pp']==-.5

def test_neutral_forecast_is_a_real_class_not_always_wrong():
    d=pd.DataFrame({'prediction_pct':[0.,2.,-2.],'actual_pct':[.5,3.,-5.]})
    m=e.point_metrics(d)
    assert m['direction_accuracy']==1.
    assert m['balanced_direction_accuracy']==1.

def test_unreleased_error_never_enters_selector_or_calibration():
    d=pd.DataFrame({'origin':pd.to_datetime(['2020-01-27','2020-07-27']),
                    'label_available':pd.to_datetime(['2020-10-01','2021-04-01']),
                    'prediction_pct':[1.,999.],'actual_pct':[2.,0.]})
    out=e.known_errors(d,pd.Timestamp('2021-01-27'))
    assert out.prediction_pct.tolist()==[1.]
    d.loc[1,'actual_pct']=1e10
    assert e.known_errors(d,pd.Timestamp('2021-01-27')).actual_pct.tolist()==[2.]

def test_interval_score_penalizes_narrow_missed_range():
    score=e.interval_score(np.array([5.]),np.array([0.]),np.array([1.]),.2)
    assert score[0]==41.

def test_simplex_weights_are_nonnegative_and_sum_to_one():
    w=e.loss_weights(pd.Series({'a':1.,'b':2.,'c':100.}))
    assert all(w>=0) and np.isclose(w.sum(),1.)
    assert w['a']>w['b'] and w['c']==0.

def test_equal_geography_score_does_not_let_big_province_dominate():
    d=pd.DataFrame({'origin':['2020']*5,'region_code':['11']+['41']*4,
                    'prediction_pct':[0.]*5,'actual_pct':[10.,0.,0.,0.,0.]})
    assert e.balanced_mae(d)==5.

def test_available_but_missing_actual_is_not_a_known_error():
    d=pd.DataFrame({'origin':pd.to_datetime(['2020-01-27']),
                    'label_available':pd.to_datetime(['2020-10-01']),
                    'prediction_pct':[1.],'actual_pct':[np.nan]})
    assert e.known_errors(d,pd.Timestamp('2021-01-27')).empty

def strategy_fixture():
    rows=[]
    for date in ['2015-01-27','2015-07-27','2016-01-27']:
        for model,pred in [('v3_hgb',2.),('damped_momentum',0.),('online_ensemble',1.)]:
            origin=pd.Timestamp(date)
            rows.append(dict(series_id='p:11',level='province',region_code='11',origin=origin,
                             label_available=origin+pd.DateOffset(months=9),model=model,
                             prediction_pct=pred,actual_pct=1.))
    history=pd.DataFrame(rows)
    current=history[history.origin.eq('2016-01-27')&~history.model.eq('online_ensemble')].copy()
    current['origin']=pd.Timestamp('2017-01-27')
    current['actual_pct']=np.nan
    return history,current

def test_adaptive_rule_cannot_select_its_own_past_strategy_as_a_base_model():
    history,_=strategy_fixture()
    scores,_=x.historical_scores(history,'province',pd.Timestamp('2017-01-27'))
    assert not scores.index.isin(x.STRATEGIES).any()

def test_adaptive_forecasts_keep_region_ids_and_unit_weight_sum():
    history,current=strategy_fixture()
    out,trace=x.strategy_predictions(history,current,pd.Timestamp('2017-01-27'))
    assert 'series_id' in out
    assert out.series_id.tolist()==['p:11']*4
    assert all(np.isclose(sum(row['weights'].values()),1.) for row in trace)

def test_new_supply_does_not_reveal_a_2026_release_in_2025():
    origins=pd.DataFrame({'region_code':['11','11'],
                          'as_of':pd.to_datetime(['2025-12-27','2026-03-27'])})
    raw=pd.DataFrame({'region_code':['11'],'month':['2026-01'],'variable':['housing_starts_all'],
                      'value':[100.],'available_date':['2026-02-27']})
    joined=x.join_released(origins,raw,max_age_months=6)
    assert np.isnan(joined.housing_starts_all.iloc[0])
    assert joined.housing_starts_all.iloc[1]==100.

def test_region_report_keeps_two_districts_in_same_province():
    d=pd.DataFrame({'model':['m','m'],'level':['district']*2,'series_id':['d:a','d:b'],
                    'name':['A','B'],'region_code':['11']*2,'origin':['2020']*2,
                    'prediction_pct':[0.,0.],'actual_pct':[2.,5.]})
    out=e.regional_metrics(d)
    assert set(out.series_id)=={'d:a','d:b'}
    assert out.mae_pp.tolist()==[2.,5.]
