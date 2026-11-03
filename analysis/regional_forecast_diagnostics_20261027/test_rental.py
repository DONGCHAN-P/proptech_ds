from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rental_experiment import rental_features

def fixture():
    dates=pd.date_range('2024-01-01','2026-09-01',freq='MS')
    rows=pd.DataFrame({'region_code':'11','month':dates,'variable':'reb_apt_jeonse_price_index',
                       'value':100*np.exp(np.arange(len(dates))*.01)})
    demand=rows.assign(variable='reb_apt_jeonse_supply_demand_index',value=110.)
    panel=pd.DataFrame({'series_id':['p:11','d:11110'],'region_code':'11','as_of':pd.Timestamp('2026-10-27')})
    return panel,pd.concat([rows,demand],ignore_index=True)

def test_future_rental_values_cannot_change_current_inputs():
    panel,raw=fixture();a=rental_features(panel,raw)
    raw.loc[raw.month.gt('2026-07-01'),'value']=99999.
    b=rental_features(panel,raw)
    pd.testing.assert_frame_equal(a,b)
    assert np.allclose(a.jeonse_return_3,.03)
    assert np.allclose(a.jeonse_return_12,.12)

def test_price_index_rebasing_cancels_from_return_features():
    panel,raw=fixture();a=rental_features(panel,raw)
    raw.loc[raw.variable.eq('reb_apt_jeonse_price_index'),'value']*=1000
    b=rental_features(panel,raw)
    np.testing.assert_allclose(a.jeonse_return_3,b.jeonse_return_3,atol=1e-12)
    np.testing.assert_allclose(a.jeonse_return_12,b.jeonse_return_12,atol=1e-12)

def test_missing_region_stays_missing_and_no_national_broadcast():
    panel,raw=fixture();panel.loc[1,'region_code']='99'
    raw=pd.concat([raw,raw.assign(region_code='00')],ignore_index=True)
    out=rental_features(panel,raw)
    assert out.loc[1,['jeonse_return_3','jeonse_return_12','jeonse_supply_demand','jeonse_demand_change_3']].isna().all()
