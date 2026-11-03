from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
from artifacts import freeze_release
from score_release import score

def fixture(tmp_path):
    f=tmp_path/'future.csv'
    pd.DataFrame({'series_id':['p:11'],'name':['Seoul'],'region_code':['11'],'level':['province'],
                   'origin':['2026-10-27'],'model':['m'],'prediction_pct':[6.]}).to_csv(f,index=False)
    release=freeze_release(tmp_path/'releases',{'future_forecasts_6m.csv':f},{})
    panel=pd.DataFrame({'series_id':['p:11']*7,'month':pd.date_range('2026-10-01',periods=7,freq='MS'),
                       'log_change':[.01]*7})
    return release,panel

def test_future_actuals_in_input_do_not_allow_premature_scoring(tmp_path):
    release,panel=fixture(tmp_path)
    out=score(release,panel,'2027-06-27')
    assert out['status']=='pending_mature_actuals'
    assert out['metrics'][0]['scored_n']==0

def test_mature_release_is_scored_without_mutating_forecast(tmp_path):
    release,panel=fixture(tmp_path)
    before=(release/'future_forecasts_6m.csv').read_bytes()
    out=score(release,panel,'2027-07-27')
    assert out['status']=='scored' and out['metrics'][0]['scored_n']==1
    assert (release/'future_forecasts_6m.csv').read_bytes()==before


def test_single_region_unavailable_rank_is_valid_json_null(tmp_path):
    import json
    release,panel=fixture(tmp_path)
    out=score(release,panel,'2027-07-27')
    json.dumps(out,allow_nan=False)
    assert out['metrics'][0]['rank_spearman'] is None
