from pathlib import Path
import json, hashlib
import numpy as np
Q=Path(__file__).resolve().parent; E=Q.parents[1]
R=E/'research/monthly-5eok-permanent-v2'
old=np.load(E/'research/monthly-5eok-v1/monthly_arrays.npz'); a=np.load(R/'monthly_arrays.npz')
for k in ['median_manwon','n']: assert np.array_equal(a[k],old[k],equal_nan=True)
assert np.array_equal(a['original_status'],old['status'])
p=a['median_manwon']; n=a['n']; observed=np.logical_or.accumulate(n>0,axis=0)
breached=np.logical_or.accumulate((n>0)&(p>50000),axis=0)
expected=np.where(breached,1,np.where(observed,0,3)).astype('uint8')
assert np.array_equal(expected,a['status']) and np.array_equal(observed,a['cumulative_observed']) and np.array_equal(breached,a['ever_breached'])
lit=expected==0
assert not np.any(breached&lit)
assert not np.any((expected[:-1]==1)&(expected[1:]!=1))
assert np.all(expected[~observed]==3)
hold=(n[1:]==0)&lit[:-1]; assert np.all(lit[1:][hold])
exact=(p==50000)&~breached; assert np.all(lit[exact])
first_over=(n>0)&(p>50000)&~np.vstack([np.zeros((1,8288),bool),breached[:-1]])
assert np.all(expected[first_over]==1)
s=json.loads((R/'monthly_summary.json').read_text(encoding='utf-8-sig'))
for i,row in enumerate(s):
 assert row['map_under']==int(lit[i].sum()) and row['map_over']==int(breached[i].sum()) and row['map_observed']==int(observed[i].sum())
 assert row['map_not_yet_observed']==int((~observed[i]).sum()) and row['map_no_trade']==0
 assert row['map_under']+row['map_over']==row['map_observed']
 assert abs(row['ratio_percent']-100*lit[i].sum()/observed[i].sum())<1e-10
def sample(mask):
 i,j=np.argwhere(mask)[0]; return {'month_index':int(i),'complex_index':int(j),'median_manwon':float(p[i,j]),'n':int(n[i,j]),'state':int(expected[i,j])}
report={'data_review_ready':True,'months':250,'catalog':8288,'cells_checked':int(expected.size),'original_monthly_prices_n_unchanged':True,'original_monthly_source_review':'qa/monthly-5eok-v1/monthly_data_independent_review.json','independent_cumulative_state_exact':True,'no_reappearance_after_breach':True,'no_trade_lit_hold_cells':int(hold.sum()),'exact_50000_before_breach_lit_cells':int(exact.sum()),'first_breach_complexes':int(first_over.sum()),'final_lit':int(lit[-1].sum()),'final_breached':int(breached[-1].sum()),'final_cumulative_observed':int(observed[-1].sum()),'samples':{'exact_5eok':sample(exact),'first_breach':sample(first_over)},'counter_same_population':True,'actual_video_review':False,'input_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file()},'limits':['누적 최초 초과 이력 지도이며 현재 거래가격이나 현재 매수가능 단지 목록이 아니다.','기존 원문 월중위값 검증을 승계하며 추가 API 호출은 없다.']}
(Q/'data_independent_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['input_hashes','limits','samples']}))
