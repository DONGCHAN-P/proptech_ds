from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
import numpy as np
from interval_experiment import calibrate

def fixture():
    origin=pd.Timestamp('2022-01-27')
    dates=pd.to_datetime(['2020-01-27','2020-07-27','2021-01-27'])
    hist=pd.DataFrame({'origin':dates,'label_available':dates+pd.DateOffset(months=9),
        'level':'province','prediction_pct':[1.,2.,3.],'actual_pct':[2.,0.,6.],'volatility_6':.01})
    current=pd.DataFrame({'origin':[origin],'level':'province','prediction_pct':[4.],'volatility_6':[.02]})
    return origin,hist,current

def test_future_and_immature_errors_do_not_change_intervals():
    origin,hist,current=fixture()
    forbidden=hist.iloc[:1].assign(origin=pd.Timestamp('2021-12-27'),label_available=pd.Timestamp('2022-09-01'),actual_pct=9999.)
    forbidden=pd.concat([forbidden,forbidden.assign(origin=pd.Timestamp('2023-01-27'),label_available=pd.Timestamp('2020-01-01'))])
    for method in ['baseline','symmetric','volatility_scaled']:
        a=calibrate(current,hist,origin,method)
        b=calibrate(current,pd.concat([hist,forbidden]),origin,method)
        pd.testing.assert_frame_equal(a,b)

def test_scaled_intervals_use_only_observed_volatility_and_keep_points():
    origin,hist,current=fixture()
    a=calibrate(current,hist,origin,'baseline')
    b=calibrate(current,hist,origin,'volatility_scaled')
    assert b.prediction_pct.iloc[0]==4.
    assert np.isclose(b.upper_80.iloc[0]-b.lower_80.iloc[0],2*(a.upper_80.iloc[0]-a.lower_80.iloc[0]))

def test_unready_history_keeps_missing_bounds_and_finite_zero_scale():
    origin,hist,current=fixture()
    current['volatility_6']=0.
    out=calibrate(current,hist.iloc[:2],origin,'volatility_scaled')
    assert out.lower_80.isna().all() and out.prediction_pct.eq(4.).all()

def test_symmetric_interval_is_centered_on_unchanged_point():
    origin,hist,current=fixture()
    out=calibrate(current,hist,origin,'symmetric')
    assert np.isclose(out.lower_80.iloc[0]+out.upper_80.iloc[0],8.)
