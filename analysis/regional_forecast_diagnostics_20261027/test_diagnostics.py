from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import pytest
from diagnostics import require_common_targets,balanced_weights,factor_decomposition,attach_inputs


def fixture():
    return pd.DataFrame({'origin':pd.to_datetime(['2020-01-27']*3),'series_id':['a','b','c'],
        'region_code':['11','41','41'],'level':'district','prediction_pct':[0.,0.,0.],
        'actual_pct':[2.,4.,np.nan],'model':'A'})


def test_weights_equalize_regions_and_retain_unscored_rows():
    rows=fixture();out=balanced_weights(rows)
    assert len(out)==3 and out.weight.tolist()==[.5,.5,0.]
    assert np.isclose(out.mae_contribution_pp.sum(),3.)


def test_multiple_districts_in_one_province_do_not_increase_its_weight():
    rows=fixture();rows['actual_pct']=[2.,4.,6.]
    out=balanced_weights(rows)
    assert out.weight.tolist()==[.5,.25,.25]
    assert np.isclose(out.mae_contribution_pp.sum(),3.5)


def test_missing_or_changed_targets_cannot_silently_change_comparison():
    a=fixture();b=a.assign(model='B')
    require_common_targets(pd.concat([a,b]),['A','B'])
    for other in [b.iloc[:-1],b.assign(actual_pct=[2.,5.,np.nan])]:
        with pytest.raises(ValueError):require_common_targets(pd.concat([a,other]),['A','B'])


def test_factor_gains_sum_to_total_with_interaction():
    result=factor_decomposition({'A':10.,'B':8.,'C':9.,'D':6.})
    assert result['total_gain_pp']==4.
    assert result['lag_at_base_pp']==1. and result['training_at_t3_pp']==2.
    assert result['interaction_pp']==1.
    assert result['lag_shapley_pp']+result['training_shapley_pp']==4.


def test_input_join_uses_origin_month_only_and_refuses_future_input():
    rows=fixture();dates=pd.to_datetime(['2020-01-01','2020-01-01','2020-01-01'])
    f=pd.DataFrame({'series_id':['a','b','c'],'month':dates,'as_of':pd.Timestamp('2020-01-27'),
                    'price_input_month':pd.Timestamp('2019-10-01'),'return_6':.03,
                    'observed_recent_min_matches':8.,'observed_recent_mean_matches':12.,
                    'observed_recent_volume':300.,'volatility_6':.01})
    later=f.assign(month=pd.Timestamp('2020-02-01'),return_6=999.)
    out=attach_inputs(rows,pd.concat([f,later]))
    assert out.return_6.eq(.03).all() and len(out)==3
    f['price_input_month']=pd.Timestamp('2020-02-01')
    with pytest.raises(ValueError,match='Future'):attach_inputs(rows,f)


def test_fresh_issued_input_month_is_preserved_separately_from_reference():
    rows=pd.DataFrame({'series_id':['p:11'],'model':['hgb_t2_law'],'origin':[pd.Timestamp('2022-07-27')],
        'price_input_month':[pd.Timestamp('2022-05-01')],'fallback_to_t3':[False]})
    reference=pd.DataFrame({'series_id':['p:11'],'month':[pd.Timestamp('2022-07-01')],
        'as_of':[pd.Timestamp('2022-07-27')],'price_input_month':[pd.Timestamp('2022-04-01')],'return_6':[.01]})
    out=attach_inputs(rows,reference)
    assert out.price_input_month.iloc[0]==pd.Timestamp('2022-05-01')
    assert out.reference_price_input_month.iloc[0]==pd.Timestamp('2022-04-01')
    assert not out.fallback_to_t3.iloc[0]
