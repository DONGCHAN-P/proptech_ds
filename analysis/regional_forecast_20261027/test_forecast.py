import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forecast as f


def test_unknown_future_statistic_is_not_visible_at_origin():
    rows = pd.DataFrame({'region_code':['11','11'], 'month':['2020-01','2020-02'],
                         'variable':['rate','rate'], 'value':[1.,999.],
                         'available_date':['2020-02-20','2020-03-20']})
    origins = pd.DataFrame({'region_code':['11','11'], 'as_of':pd.to_datetime(['2020-03-01','2020-03-21'])})
    out = f.join_released(origins, rows)
    assert out['rate'].tolist() == [1.,999.]


def test_no_backfill_of_pre_release_values_and_national_broadcast():
    rows = pd.DataFrame({'region_code':['00'], 'month':['2020-01'], 'variable':['rate'],
                         'value':[1.], 'available_date':['2020-02-20']})
    origins = pd.DataFrame({'region_code':['11','26'], 'as_of':pd.to_datetime(['2020-02-01','2020-03-01'])})
    out=f.join_released(origins,rows)
    assert np.isnan(out.rate.iloc[0])
    assert out.rate.iloc[1] == 1.


def test_stale_public_statistics_are_not_indefinitely_reused():
    rows=pd.DataFrame({'region_code':['00'],'month':['2020-01'],'variable':['supply'],
                       'value':[123.],'available_date':['2020-03-01']})
    origins=pd.DataFrame({'region_code':['11','11'],'as_of':pd.to_datetime(['2020-03-27','2021-03-27'])})
    out=f.join_released(origins,rows,max_age_months=6)
    assert out.supply.iloc[0]==123.
    assert np.isnan(out.supply.iloc[1])


def test_target_requires_exact_six_month_endpoint_and_all_intermediate_months():
    d=pd.DataFrame({'series_id':['a']*8,'month':pd.date_range('2020-01-01',periods=8,freq='MS'),
                    'log_change':[np.nan]+[.01]*7})
    d.loc[3,'log_change']=np.nan
    out=f.add_target(d,6)
    assert np.isnan(out.target_log_return.iloc[0])
    assert np.isnan(out.target_log_return.iloc[2])
    d.loc[3,'log_change']=.01
    out=f.add_target(d,6)
    assert np.isclose(out.target_log_return.iloc[0],.06)
    assert np.isnan(out.target_log_return.iloc[2])


def test_training_labels_end_and_publish_before_test_origin():
    d=pd.DataFrame({'month':pd.to_datetime(['2019-11-01','2019-12-01','2020-01-01']),
                    'label_available':pd.to_datetime(['2020-07-01','2020-08-01','2020-09-01']),
                    'target_log_return':[1.,2.,3.]})
    out=f.training_rows(d,pd.Timestamp('2020-08-01'))
    assert out.month.tolist() == [pd.Timestamp('2019-11-01'),pd.Timestamp('2019-12-01')]


def test_policy_known_announcement_can_be_used_but_later_news_cannot():
    origins=pd.DataFrame({'region_code':['11','26'], 'district_code':['11680','26110'],
                          'as_of':pd.to_datetime(['2020-06-20']*2)})
    events=[{'announcement_date':'2020-06-17','effective_date':'2020-07-01',
              'affected_prefixes':['11'],'direction':1.,'event_id':'known'},
             {'announcement_date':'2020-07-10','effective_date':'2020-07-10',
              'affected_prefixes':['11'],'direction':1.,'event_id':'future'}]
    out=f.policy_features(origins,events)
    assert out.policy_recent_6m.tolist()==[1.,0.]


def test_same_month_quality_matching_excludes_unmatched_luxury_composition():
    # Doubling the price of the same unit and adding a luxury building must mean +100%,
    # rather than the increase in the raw median transaction price.
    g=pd.DataFrame({'series_id':['a']*3,'month':pd.to_datetime(['2020-01-01','2020-02-01','2020-02-01']),
                    'apt_id':['x','x','luxury'],'area_key':[84.,84.,84.], 'ppm':[100.,200.,1000.]})
    out=f.matched_changes(g,min_complexes=1)
    row=out[out.month==pd.Timestamp('2020-02-01')].iloc[0]
    assert np.isclose(row.log_change,np.log(2))
    assert row.matched_complexes==1


def test_matching_does_not_treat_nonadjacent_months_as_one_month_return():
    g=pd.DataFrame({'series_id':['a']*2,'month':pd.to_datetime(['2020-01-01','2020-03-01']),
                    'apt_id':['x']*2,'area_key':[84.]*2,'ppm':[100.,200.]})
    out=f.matched_changes(g,min_complexes=1)
    assert out.log_change.isna().all()


def test_month_gap_in_panel_invalidates_calendar_target_even_with_six_later_rows():
    months=pd.date_range('2020-01-01',periods=9,freq='MS').delete(3)
    d=pd.DataFrame({'series_id':['a']*8,'month':months,'log_change':[.01]*8})
    out=f.add_target(d,6)
    assert np.isnan(out.target_log_return.iloc[0])


def test_releases_after_origin_cannot_change_features():
    origins=pd.DataFrame({'region_code':['11'],'as_of':pd.to_datetime(['2020-06-27'])})
    rows=pd.DataFrame({'region_code':['11','11'],'month':['2020-03','2020-07'],
                       'variable':['units','units'],'value':[123.,1.],
                       'available_date':['2020-05-01','2020-09-01']})
    before=f.join_released(origins,rows).units.iloc[0]
    rows.loc[1,'value']=999999999.
    after=f.join_released(origins,rows).units.iloc[0]
    assert before==after==123.


def test_selection_cannot_use_label_published_after_first_holdout():
    assert hasattr(f,'assert_selection_available')
    records=pd.DataFrame({'label_available':pd.to_datetime(['2024-04-01'])})
    with pytest.raises(ValueError,match='selection'):
        f.assert_selection_available(records,pd.Timestamp('2024-01-27'))


def test_change_is_released_only_after_both_operands():
    assert hasattr(f,'lagged_change')
    rows=pd.DataFrame({'month':pd.to_datetime(['2020-01-01','2020-04-01']),
                       'value':[999.,4.],'available_date':pd.to_datetime(['2020-08-01','2020-05-01'])})
    out=f.lagged_change(rows,3,log_growth=False)
    assert out.value.iloc[1]==-995.
    assert out.available_date.iloc[1]==pd.Timestamp('2020-08-01')
    assert np.isnan(out.value.iloc[0])


def test_forecast_cohort_keeps_region_with_unobserved_future_outcome():
    assert hasattr(f,'evaluation_cohort')
    panel=pd.DataFrame({'series_id':['a','a'],'month':pd.to_datetime(['2019-01-01','2020-01-01']),
                        'label_available':pd.to_datetime(['2019-10-01','2020-10-01']),
                        'target_log_return':[.01,np.nan],'eligible':[True,True]})
    cohort=f.evaluation_cohort(panel,pd.Timestamp('2020-01-27'),min_training_months=1)
    assert cohort.series_id.tolist()==['a']
    assert cohort.target_log_return.isna().all()


def test_same_policy_package_submeasures_count_as_one_signal():
    origins=pd.DataFrame({'region_code':['11'],'district_code':['11680'],
                          'as_of':pd.to_datetime(['2020-06-27'])})
    base={'announcement_date':'2020-06-17','effective_date':'2020-07-01',
          'affected_prefixes':['11'],'direction':1.}
    events=[{**base,'event_id':'designation'},{**base,'event_id':'lending_rule'}]
    out=f.policy_features(origins,events)
    assert out.policy_recent_6m.iloc[0]==1.
    assert out.policy_announcements_6m.iloc[0]==1.
