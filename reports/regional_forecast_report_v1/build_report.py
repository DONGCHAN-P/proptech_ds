"""Build an offline HTML report from the frozen forecast experiment artifacts."""
from pathlib import Path
import sys
import hashlib
import json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
NEW=ROOT/'analysis/regional_forecast_iteration_20261027'
OLD=ROOT/'analysis/regional_forecast_20261027'
sys.path.insert(0,str(NEW))
from evaluation import point_metrics

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text('utf-8'))
def records(frame):return json.loads(frame.to_json(orient='records',force_ascii=False,date_format='iso'))

main=NEW/load(NEW/'latest_release.json')['directory']
timing=Path(load(NEW/'results_timeliness/release_pointer.json')['directory'])
for release in [main,timing]:
    manifest=load(release/'release.json')
    for name,expected in manifest['files'].items():assert sha(release/name)==expected,name
evaluation=load(NEW/'results/evaluation_manifest.json')
assert sha(NEW/'results/scorecard.csv')==evaluation['scorecard_sha256']

main_scores=pd.read_csv(NEW/'results/scorecard.csv')
timing_scores=pd.read_csv(timing/'scorecard.csv')
scores=pd.concat([main_scores,timing_scores[timing_scores.model.str.startswith('hgb_t2')]],ignore_index=True)
windows={'all_regimes':('2017-01-27','2026-01-27'),'boom':('2020-01-01','2021-12-31'),
         'turn':('2022-01-01','2023-12-31'),'recent':('2024-01-01','2026-01-27')}
scores=scores[scores.window.isin(windows)]
history=pd.read_parquet(timing/'history.parquet')
keep=['v3_hgb','hgb_t2_120m']
regional=[]
for window,(a,b) in windows.items():
    sub=history[history.origin.between(a,b)&history.model.isin(keep)]
    for (model,level,sid),g in sub.groupby(['model','level','series_id']):
        m=point_metrics(g)
        regional.append(dict(window=window,model=model,level=level,series_id=sid,name=g['name'].iloc[0],
                             region_code=str(g.region_code.iloc[0]),origins=g.origin.nunique(),
                             **{key:m.get(key,np.nan) for key in ['forecast_n','scored_n','unscored_n','mae_pp',
                                 'p90_ae_pp','bias_pp','balanced_direction_accuracy','interval_coverage_80']}))

time=[]
for (origin,model,level),g in history[history.model.isin(keep)&history.origin.ge('2017-01-27')].groupby(['origin','model','level']):
    time.append(dict(origin=origin.strftime('%Y-%m-%d'),model=model,level=level,mae_pp=point_metrics(g).get('mae_pp')))

correlations=pd.read_csv(OLD/'results_v3/feature_correlations_by_region.csv')
corr=[]
for key,label in [('volume_yoy','거래량 전년 대비 변화'),('unsold_housing_total_change_12','미분양 12개월 변화'),
                  ('mortgage_rate_new_business_pct_change_12','주담대 금리 12개월 변화'),('return_6','과거 6개월 가격 변화')]:
    group=correlations[correlations.feature.eq(key)]
    corr.append(dict(feature=key,label=label,rho=group.spearman.median(),regions=len(group),
                     n_min=int(group.n.min()),n_max=int(group.n.max()),
                     first=group.first_origin.min(),last=group.last_origin.max()))

all_timing=timing_scores[timing_scores.window.eq('all_regimes')]
p=all_timing.pivot(index='model',columns='level',values='balanced_mae_pp')
gain=100*(1-(p.loc['hgb_t2_120m']/p.loc['v3_hgb']).mean())
audit=load(OLD/'panel_audit.json')
issued=pd.read_csv(main/'future_forecasts_6m.csv',dtype={'region_code':str})
issued=issued[issued.model.eq('v3_hgb')]
conditional=pd.read_csv(timing/'future_forecasts_6m.csv',dtype={'region_code':str})
conditional=conditional[conditional.model.eq('hgb_t2_120m')]
forecasts=issued[['series_id','name','level','region_code','prediction_pct','lower_80','upper_80']].rename(
    columns={'prediction_pct':'baseline_pct','lower_80':'baseline_lower_80','upper_80':'baseline_upper_80'}).merge(
    conditional[['series_id','prediction_pct','lower_80','upper_80','price_input_month']].rename(
    columns={'prediction_pct':'conditional_pct','lower_80':'conditional_lower_80','upper_80':'conditional_upper_80'}),
    on='series_id',validate='one_to_one')
data=dict(as_of='2026-10-27',main_release=main.name,timeliness_release=timing.name,
          balanced_gain_pct=gain,scores=records(scores),regional=records(pd.DataFrame(regional)),
          forecasts=records(forecasts),
          time=time,correlations=corr,trials=records(pd.read_csv(NEW/'results/trial_history.csv')),
          audit=audit,verification=load(NEW/'delivery_verification.json'),
          supply=load(NEW/'results/supply_update.json'),model_specs=load(NEW/'campaign_config.json')['specs'])
payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('</','<\\/')
template=(HERE/'template.html').read_text('utf-8')
baseline=scores[(scores.window=='all_regimes')&(scores.model=='v3_hgb')&(scores.level=='province')].iloc[0]
candidate=scores[(scores.window=='all_regimes')&(scores.model=='hgb_t2_120m')&(scores.level=='province')].iloc[0]
static_rows=''.join(f'<tr><th>{label}</th><td>{baseline[key]*scale:.3f}</td><td>{candidate[key]*scale:.3f}</td></tr>'
                    for key,label,scale in [('mae_pp','평균 절대오차 (%p)',1),('balanced_mae_pp','균형 MAE (%p)',1),
                         ('p90_ae_pp','p90 절대오차 (%p)',1),('balanced_direction_accuracy','방향 균형 정확도 (%)',100),
                         ('interval_coverage_80','80% 범위 포함률 (%)',100)])
output=template.replace('__REPORT_DATA__',payload).replace('__STATIC_ROWS__',static_rows)
output=output.replace('__GAIN__',f'{gain:.2f}')
province_forecasts=forecasts[forecasts.level.eq('province')].sort_values('region_code')
forecast_rows=''.join(f'<tr><th>{r["name"]}</th><td>{r["baseline_pct"]:+.2f}%</td>'
                f'<td>{r["conditional_pct"]:+.2f}%</td><td>{r["baseline_lower_80"]:+.2f}% ~ {r["baseline_upper_80"]:+.2f}%</td></tr>'
                for r in records(province_forecasts))
output=output.replace('__FORECAST_ROWS__',forecast_rows)
target=HERE.parent/'지역별 집값 예측 반복 검증.html'
target.write_text(output,'utf-8')
inputs=[NEW/'results/scorecard.csv',NEW/'results/evaluation_manifest.json',main/'release.json',
        timing/'release.json',timing/'history.parquet',timing/'scorecard.csv',
        OLD/'panel_audit.json',OLD/'results_v3/feature_correlations_by_region.csv',
        main/'future_forecasts_6m.csv',timing/'future_forecasts_6m.csv',
        NEW/'results/trial_history.csv',NEW/'results/campaign_summary.json',
        NEW/'delivery_verification.json',NEW/'results/supply_update.json',NEW/'campaign_config.json',
        ROOT/'reports/지역별 집값 예측 반복 검증.md',HERE/'template.html',Path(__file__)]
(HERE/'source_manifest.json').write_text(json.dumps(dict(as_of=data['as_of'],output='../'+target.name,
          output_sha256=sha(target),main_release=main.name,timeliness_release=timing.name,
          inputs={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in inputs}),
          ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(dict(output=str(target),bytes=target.stat().st_size,score_rows=len(scores),
                     regional_rows=len(regional),gain_pct=gain),ensure_ascii=False))
