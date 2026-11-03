from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
import numpy as np
import timeliness_experiment as t
from timeliness_experiment import refresh_price_features,PRICE_COLS

def fixture():
    months=pd.date_range('2018-01-01','2026-09-01',freq='MS')
    raw=pd.DataFrame({'series_id':'p:11','region_code':'11','month':months,
                       'log_change':np.arange(len(months))/1000,'volume':100.,'median_area':84.,
                       'median_ppm':100.,'matched_complexes':20.})
    dates=pd.to_datetime(['2020-04-01','2020-05-01','2026-10-01'])
    base=pd.DataFrame({'series_id':'p:11','region_code':'11','level':'province','month':dates,
                       'log_change':.01,'eligible':True,'price_input_month':dates-pd.DateOffset(months=3)})
    for col in PRICE_COLS:base[col]=0.
    return base,raw

def test_rule_does_not_apply_to_mixed_february_2020_contract_month():
    base,raw=fixture();out=refresh_price_features(base,raw)
    assert out.price_input_month.tolist()==list(pd.to_datetime(['2020-01-01','2020-03-01','2026-08-01']))
    assert out.return_1.iloc[0]==0. # Before rule, original predictor unchanged.

def test_unobservable_september_price_cannot_change_october_forecast_input():
    base,raw=fixture();first=refresh_price_features(base,raw)
    raw.loc[raw.month.eq('2026-09-01'),'log_change']=1000.
    second=refresh_price_features(base,raw)
    pd.testing.assert_frame_equal(first,second)


def fallback_fixture():
    origin=pd.Timestamp('2026-10-27')
    current=pd.DataFrame({'series_id':['p:11','d:11:x'],'fresh_eligible':[True,False]})
    fallback=pd.DataFrame({'series_id':current.series_id,'model':'v3_hgb',
                          'prediction_pct':[2.,3.],'train_n':999,
                          'train_latest_label_available':pd.Timestamp('2026-07-01')}).set_index('series_id')
    return origin,current,fallback


def test_mixed_fallback_keeps_effective_training_provenance(monkeypatch):
    origin,current,fallback=fallback_fixture()
    monkeypatch.setattr(t.e,'fit_predict',lambda *a: (np.array([4.]),'fresh-model',7,pd.Timestamp('2026-10-01')))
    rows,model=t.predict_with_fallback(None,origin,current,fallback,'fresh',{})
    assert rows.prediction_pct.tolist()==[4.,3.]
    assert rows.train_n.tolist()==[7,999]
    assert rows.effective_predictor.tolist()==['fresh','v3_hgb']
    assert rows.train_latest_label_available.tolist()==list(pd.to_datetime(['2026-10-01','2026-07-01']))
    assert rows.price_input_month.tolist()==list(pd.to_datetime(['2026-08-01','2026-07-01']))


def test_all_fallback_avoids_fit_and_keeps_metadata(monkeypatch):
    origin,current,fallback=fallback_fixture();current['fresh_eligible']=False
    def fail(*a):raise AssertionError('No fit when all rows use fallback')
    monkeypatch.setattr(t.e,'fit_predict',fail)
    rows,model=t.predict_with_fallback(None,origin,current,fallback,'fresh',{})
    assert rows.train_n.tolist()==[999,999] and model is None
    assert rows.fallback_to_t3.all()


def test_pre_rule_reuse_preserves_reused_model_provenance(monkeypatch):
    origin,current,fallback=fallback_fixture()
    reused=fallback.copy();reused['model']='hgb_full_120m';reused['train_n']=123
    rows,_=t.predict_with_fallback(None,pd.Timestamp('2020-01-27'),current,fallback,'fresh',{},reuse=reused)
    assert rows.train_n.tolist()==[123,123]
    assert rows.effective_predictor.eq('hgb_full_120m').all()
    assert rows.price_input_month.eq(pd.Timestamp('2019-10-01')).all()


def test_release_archives_interval_history_and_sources(tmp_path,monkeypatch):
    import json
    from artifacts import sha
    root=tmp_path/'working';root.mkdir();(root/'models').mkdir()
    for name in ['future_forecasts_6m.csv','current_features.parquet','original_current_features.parquet',
                 'assumption_manifest.json','scorecard.csv']:
        (root/name).write_text('fixture','utf-8')
    origins=pd.date_range('2023-01-01',periods=4,freq='6MS')
    history=pd.DataFrame({'origin':origins,'label_available':origins+pd.DateOffset(months=9),
                          'model':'fresh','level':'province','prediction_pct':[1.,2.,3.,4.],
                          'actual_pct':[2.,1.,5.,3.]})
    history.to_parquet(root/'predictions.parquet',index=False)
    current=pd.DataFrame({'model':['fresh'],'level':['province'],'prediction_pct':[2.]})
    expected=t.e.add_intervals(current,history,pd.Timestamp('2026-10-27'))
    monkeypatch.setattr(t,'R',root)
    release=t.freeze_outputs({'fresh':{}},release_root=tmp_path/'releases')
    (root/'predictions.parquet').write_bytes(b'working history overwritten')
    archived=pd.read_parquet(release/'history.parquet')
    actual=t.e.add_intervals(current,archived,pd.Timestamp('2026-10-27'))
    pd.testing.assert_frame_equal(expected,actual)
    manifest=json.loads((release/'release.json').read_text('utf-8'))
    for name in ['code/timeliness_experiment.py','code/experiment.py','code/evaluation.py',
                 'code/forecast.py','code/artifacts.py','resolved_config.json','bank_manifest.json']:
        assert sha(release/name)==manifest['files'][name]
