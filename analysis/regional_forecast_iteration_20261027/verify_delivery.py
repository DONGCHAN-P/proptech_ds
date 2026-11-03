"""Verify issued artifacts without fitting or selecting another model."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hashlib
import json
import re
from urllib.parse import unquote
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import experiment as e
from artifacts import sha,require_complete_grid
from score_release import score

ROOT=Path(__file__).resolve().parent


def verify_manifest(release):
    manifest=json.loads((release/'release.json').read_text('utf-8'))
    identity={k:manifest[k] for k in ['metadata','files']}
    identifier=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    assert manifest['release_id']==identifier and release.name==identifier[:20]
    assert manifest['complete']
    for name,expected in manifest['files'].items():assert sha(release/name)==expected,name
    return len(manifest['files'])


def compare(left,right,columns):
    keys=['model','series_id']
    if 'origin' in left and 'origin' in right:keys=['origin']+keys
    a=left.set_index(keys).sort_index();b=right.set_index(keys).sort_index()
    assert a.index.equals(b.index)
    for c in columns:
        assert np.allclose(a[c],b[c],rtol=1e-10,atol=1e-9,equal_nan=True),c


def run():
    result={}
    main_pointer=json.loads((ROOT/'latest_release.json').read_text('utf-8'))
    main=ROOT/main_pointer['directory']
    timing_pointer=json.loads((ROOT/'results_timeliness/release_pointer.json').read_text('utf-8'))
    timing=Path(timing_pointer['directory'])
    manifests={}
    for collection in ['releases','timeliness_releases']:
        for path in sorted((ROOT/collection).iterdir()):
            if path.is_dir():manifests[f'{collection}/{path.name}']=verify_manifest(path)
    result['immutable_manifests_verified']=manifests
    result['main_release']=main.name;result['timeliness_release']=timing.name
    bank=e.load_bank(pd.read_parquet(e.RESULT/'feature_panel.parquet'))
    require_complete_grid(bank,e.ORIGINS,e.SPECS)
    cohort_blocks=0
    for origin,group in bank.groupby('origin'):
        base=group[group.model.eq('v3_hgb')].set_index('series_id').actual_pct.sort_index()
        for _,g in group.groupby('model'):
            candidate=g.set_index('series_id').actual_pct.sort_index()
            assert candidate.index.equals(base.index)
            assert np.allclose(candidate,base,equal_nan=True,rtol=1e-12,atol=1e-12)
            assert (pd.to_datetime(g.train_latest_label_available)<=origin).all()
            cohort_blocks+=1
    result['same_target_cohort_blocks']=cohort_blocks
    result['candidate_models']=bank.model.nunique();result['origins']=bank.origin.nunique()
    for filename in ['selection_trace.json','prospective_selection_trace.json']:
        for event in json.loads((e.RESULT/filename).read_text('utf-8')):
            weights=list(event['weights'].values())
            assert min(weights)>=0 and abs(sum(weights)-1)<1e-12
            if event['latest_known_label']:
                assert pd.Timestamp(event['latest_known_label'])<=pd.Timestamp(event['origin'])
    result['selection_dates_and_weights_verified']=True

    current=pd.read_parquet(main/'current_features.parquet')
    issued=pd.read_csv(main/'future_forecasts_6m.csv',parse_dates=['origin'],dtype={'region_code':str})
    replay=[]
    for name,spec in e.SPECS.items():
        kind=spec['kind']
        if kind=='zero':pred=np.zeros(len(current))
        elif kind=='momentum6':pred=current.return_6.to_numpy()*spec['multiplier']
        elif kind=='momentum3':pred=current.return_3.to_numpy()*2
        elif kind=='momentum_blend':pred=.5*current.return_6.to_numpy()+current.return_3.to_numpy()
        else:
            model=joblib.load(main/'models'/f'{name}.joblib')
            if isinstance(model,dict):
                pred=np.empty(len(current))
                for level,local in model.items():
                    mask=current.level.eq(level).to_numpy();pred[mask]=local.predict(current.loc[mask])
            else:pred=model.predict(current)
        replay.append(pd.DataFrame({'series_id':current.series_id,'model':name,'prediction_pct':100*np.expm1(pred)}))
    compare(pd.concat(replay),issued[issued.model.isin(e.SPECS)],['prediction_pct'])
    history=pd.read_parquet(main/'history.parquet')
    strategies,_=e.strategy_predictions(history,issued[issued.model.isin(e.SPECS)],e.ASOF)
    compare(strategies,issued[issued.model.isin(e.STRATEGIES)],['prediction_pct'])
    intervals=e.add_intervals(issued,history,e.ASOF)
    compare(intervals,issued,['lower_80','upper_80','lower_95','upper_95'])
    result['main_replayed_points']=len(issued)

    fresh=pd.read_parquet(timing/'current_features.parquet').set_index('series_id')
    original=pd.read_parquet(timing/'original_current_features.parquet').set_index('series_id')
    tf=pd.read_csv(timing/'future_forecasts_6m.csv',parse_dates=['origin','price_input_month','train_latest_label_available'])
    assert tf.train_n.gt(0).all() and (tf.train_latest_label_available<=e.ASOF).all()
    replay=[]
    fallback=joblib.load(timing/'models/fallback_v3_hgb.joblib')
    for name,g in tf.groupby('model'):
        values=pd.Series(index=g.series_id,dtype=float)
        good=g[~g.fallback_to_t3];bad=g[g.fallback_to_t3]
        if len(good):
            fitted=joblib.load(timing/'models'/f'{name}.joblib')
            values.loc[good.series_id]=100*np.expm1(fitted.predict(fresh.loc[good.series_id]))
            assert good.effective_predictor.eq(name).all()
            assert good.price_input_month.eq(pd.Timestamp('2026-08-01')).all()
        if len(bad):
            values.loc[bad.series_id]=100*np.expm1(fallback.predict(original.loc[bad.series_id]))
            assert bad.effective_predictor.eq('v3_hgb').all()
            assert bad.price_input_month.eq(pd.Timestamp('2026-07-01')).all()
        replay.append(pd.DataFrame({'model':name,'series_id':g.series_id,'prediction_pct':g.series_id.map(values)}))
    compare(pd.concat(replay),tf,['prediction_pct'])
    th=pd.read_parquet(timing/'history.parquet')
    ti=e.add_intervals(tf,th,e.ASOF)
    compare(ti,tf,['lower_80','upper_80','lower_95','upper_95'])
    result['timeliness_replayed_points']=len(tf)
    for _,g in th.groupby(['origin','model']):
        assert (pd.to_datetime(g.train_latest_label_available)<=pd.Timestamp(g.origin.iloc[0])).all()
    fallback_rows=th[th.model.isin(['hgb_t2_law','hgb_t2_120m'])&th.fallback_to_t3.fillna(False)]
    for origin,g in fallback_rows.groupby('origin'):
        truth=bank[bank.origin.eq(origin)&bank.model.eq('v3_hgb')].set_index('series_id')
        assert g.train_n.eq(g.series_id.map(truth.train_n)).all()
        assert g.train_latest_label_available.eq(g.series_id.map(truth.train_latest_label_available)).all()
    result['fallback_provenance_rows_verified']=len(fallback_rows)
    before=pd.read_parquet(ROOT/'timeliness_numerical_before_review.parquet')
    compare(before,th,['prediction_pct','actual_pct','lower_80','upper_80','lower_95','upper_95'])
    result['timeliness_numerical_regression_unchanged']=True
    regional=pd.read_csv(ROOT/'results_timeliness/by_region.csv')
    assert regional[regional.level.eq('district')].series_id.nunique()>100
    result['individual_district_diagnostics']=regional[regional.level.eq('district')].series_id.nunique()
    supply=json.loads((e.RESULT/'supply_update.json').read_text('utf-8'))
    assert sha(ROOT/'supply_supplement_snapshot.csv')==supply['sha256']
    assert json.loads((e.RESULT/'historical_feature_invariance.json').read_text('utf-8'))['passed']
    result['supply_snapshot_and_historical_invariance_verified']=True
    for release in [main,timing]:
        evaluation=score(release,pd.read_parquet(e.OLD/'data/monthly_panel.parquet'),'2026-10-27')
        assert evaluation['status']=='pending_mature_actuals'
        assert sum(m['scored_n'] for m in evaluation['metrics'])==0
    result['future_actuals_status']='pending_mature_actuals'
    report=ROOT.parent.parent/'reports/지역별 집값 예측 반복 검증.md'
    linked=0
    for document in [ROOT/'README.md',report]:
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',document.read_text('utf-8')):
            if link.startswith(('https://','http://','#')):continue
            target=(document.parent/unquote(link.split('#')[0])).resolve()
            assert target.exists(),f'{document.name}: missing {link}'
            linked+=1
    result['local_document_links_verified']=linked
    result['passed']=True
    e.save(ROOT/'delivery_verification.json',result)
    selected=['README.md','PLAN.md','delivery_verification.json','latest_release.json',
              'results/scorecard.csv','results/promotion_decisions.csv','results/campaign_summary.json',
              'results/trial_history.csv','results/scores_overview.png','results/regime_errors.png',
              'results/interval_calibration.png','results_timeliness/scorecard.csv',
              'results_timeliness/release_pointer.json','review3.md','review_timeliness_followup.md',
              'test_result.txt','experiment.py','evaluation.py','timeliness_experiment.py','score_release.py',
              'artifacts.py','render_report.py','verify_delivery.py']
    delivery={n:sha(ROOT/n) for n in selected}
    delivery['../../reports/'+report.name]=sha(report)
    e.save(ROOT/'delivery_manifest.json',{'as_of':str(e.ASOF),'files':delivery,
           'releases':{'main':main.name,'conditional_timeliness':timing.name},'tests_passed':41})
    print(json.dumps(result,ensure_ascii=False,default=str,indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=4):run()
