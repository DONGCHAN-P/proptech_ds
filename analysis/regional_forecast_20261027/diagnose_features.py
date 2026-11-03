"""Exploratory controls / same-estimator ablation; never reselects the winner."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import pandas as pd
import numpy as np
from scipy.stats import rankdata
from threadpoolctl import threadpool_limits
import run_experiment as exp
from forecast import add_target,training_rows

R=exp.RESULT
p=pd.read_parquet(R/'feature_panel.parquet')
contract=json.loads((R/'feature_contract.json').read_text('utf-8'))
panel=add_target(p,6)
sample=training_rows(panel,pd.Timestamp('2023-12-27'))
sample=sample[sample.eligible&sample.level.eq('province')&sample.month.between('2018-01-01','2023-01-01')]
controls=['return_3','return_6','volume_yoy']
features=contract['price_features']+contract['external_features']+contract['policy_features']
rows=[]
for (region,name),g in sample.groupby(['region_code','name']):
    for feature in features:
        if feature in controls or '_region_' in feature: continue
        s=g[[feature,'target_log_return',*controls]].dropna()
        if len(s)<36 or s[feature].nunique()<3: continue
        x=np.column_stack([np.ones(len(s)),*[rankdata(s[c]) for c in controls]])
        a=rankdata(s[feature]);b=rankdata(s.target_log_return)
        ar=a-x@np.linalg.lstsq(x,a,rcond=None)[0]
        br=b-x@np.linalg.lstsq(x,b,rcond=None)[0]
        if np.std(ar)<1e-10 or np.std(br)<1e-10: continue
        rows.append({'region_code':region,'name':name,'feature':feature,'n':len(s),
                     'conditional_rank_correlation':float(np.corrcoef(ar,br)[0,1]),
                     'controls':','.join(controls),'window':'2018-01..2023-01; labels available by2023-12-27'})
pd.DataFrame(rows).to_csv(R/'conditional_correlations_exploratory.csv',index=False,encoding='utf-8-sig')
allrows=[]
# A diagnostic added after initial model design: explicitly not a new selection
# competition, nor independent confirmatory evidence. Same fixed HGB parameters.
specs={'diagnostic_boosting_price':('boost',exp.PRICE),
       'diagnostic_boosting_economy':('boost',exp.PRICE+contract['external_features'])}
with threadpool_limits(limits=4):
    for origin in exp.TEST:
        allrows.extend(exp.run_fold(panel,origin,6,specs,'diagnostic_holdout'))
        print(f'diagnostic ablation {origin.date()}',flush=True)
ab=pd.concat(allrows,ignore_index=True)
ab.to_csv(R/'diagnostic_ablation_predictions.csv',index=False,encoding='utf-8-sig')
summary=exp.metrics(ab)
summary.to_csv(R/'diagnostic_ablation_metrics.csv',index=False,encoding='utf-8-sig')
print(summary.to_string(index=False))
