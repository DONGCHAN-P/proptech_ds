from pathlib import Path
import json,hashlib
import pandas as pd,numpy as np
Q=Path(__file__).resolve().parent;EP=Q.parents[1];R=EP/'research/monthly-5eok-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
vld=read(R/'validation.json')
for f in vld['inputs']:assert sha(Path(f['path']))==f['sha256']
source=pd.read_parquet(EP/'research/source-completion-v1/episode_84_source_rows.parquet',columns=['complex_id','deal_date','deal_amount','included_price_analysis','area_m2','is_canceled','cancel_date'])
v=source[source.included_price_analysis].copy();assert len(v)==1626292 and v.area_m2.ge(83).all() and v.area_m2.lt(85).all() and not(v.is_canceled.fillna(False)|v.cancel_date.notna()).any()
v['month']=v.deal_date.dt.to_period('M').astype(str);expected=v.groupby(['complex_id','month']).deal_amount.agg(['median','size']).reset_index();stored=pd.read_parquet(R/'all_monthly_prices.parquet')
j=expected.merge(stored,on=['complex_id','month'],how='outer',indicator=True,validate='one_to_one');assert j['_merge'].eq('both').all() and j['median'].eq(j.median_manwon).all() and j['size'].eq(j.n).all();assert int(j.n.sum())==len(v)
months=pd.period_range('2006-01','2026-10',freq='M').astype(str).tolist();cs=read(R/'complex_catalog.json');ids=[c['complex_id'] for c in cs];assert len(ids)==len(set(ids))==8288 and ids==sorted(ids)
pkt=read(EP/'research/annual-map-v2/map_packet_v2.json');prior={c['complex_id']:c for c in pkt['complexes']};assert set(ids)==set(prior)
first=v.groupby('complex_id').month.min()
for c in cs:
 old=prior[c['complex_id']];assert c['x_5179']==old['x_5179'] and c['y_5179']==old['y_5179'] and c['HSMP_INNB']==old['HSMP_INNB'] and c['first_valid_trade_month']==first[c['complex_id']]
index=pd.MultiIndex.from_product([months,ids],names=['month','complex_id']);e=expected.set_index(['month','complex_id']).reindex(index);p=e['median'].to_numpy().reshape((250,8288));n=e['size'].fillna(0).to_numpy(dtype='int32').reshape((250,8288));status=np.where(n>0,np.where(p<=50000,0,1),np.where(np.array(months)[:,None]<np.array([first[i] for i in ids])[None,:],3,2)).astype('uint8');a=np.load(R/'monthly_arrays.npz')
assert np.array_equal(p,a['median_manwon'],equal_nan=True) and np.array_equal(n,a['n']) and np.array_equal(status,a['status'])
summary=read(R/'monthly_summary.json');assert len(summary)==250 and [s['month'] for s in summary]==months
for mi,s in enumerate(summary):
 counts=np.bincount(status[mi],minlength=4);raw=expected[expected.month.eq(months[mi])]
 assert s['map_under']==counts[0] and s['map_over']==counts[1] and s['map_no_trade']==counts[2] and s['map_not_yet_observed']==counts[3] and s['map_observed']==counts[0]+counts[1] and sum(counts)==8288
 assert s['map_n']==int(n[mi].sum()) and s['all_n']==int(raw['size'].sum()) and s['all_observed']==len(raw) and s['all_under']==int(raw['median'].le(50000).sum())
 assert abs(s['ratio_percent']-100*counts[0]/(counts[0]+counts[1]))<1e-10
assert summary[-1]['partial_month'] and not any(s['partial_month'] for s in summary[:-1])
exact=int((p==50000).sum());assert exact==3454 and np.all(status[p==50000]==0)
reappear=0;adj=int(((status[:-1]==1)&(status[1:]==0)).sum());last=np.full(8288,-1,dtype='int8')
for row in status:
 reappear+=int(((last==1)&(row==0)).sum());obs=row<2;last[obs]=row[obs]
assert reappear==7148 and adj==3640
assert np.all(np.isnan(p[n==0])) and np.all(status[n==0]>=2)
samples=[]
for group in [j[j['median'].eq(50000)],j[j['median'].gt(50000)].sort_values('median'),j[j['size'].eq(2)]]:
 row=group.iloc[0];values=sorted(v[(v.complex_id==row.complex_id)&(v.month==row.month)].deal_amount.tolist());samples.append({'complex_id':row.complex_id,'month':row.month,'n':len(values),'raw_values_manwon':values,'median':float(row['median'])})
inputs=[R/f for f in ['all_monthly_prices.parquet','monthly_arrays.npz','complex_catalog.json','monthly_summary.csv','monthly_summary.json','validation.json']]
report={'monthly_price_review_ready':True,'valid_source_rows':len(v),'all_monthly_n_sum':int(stored.n.sum()),'observed_complex_month_groups':len(stored),'mapped_n_sum':int(n.sum()),'month_count':250,'first_month':months[0],'last_month':months[-1],'mapped_catalog':8288,'unlinked':884,'exact_5eok_under_groups':exact,'all_observed_reappearances':reappear,'adjacent_reappearances':adj,'all_2072000_status_median_n_cells_match_independent_source_grouping':True,'no_price_carry_or_interpolation':True,'first_observed_month_rules_match':True,'native_coordinate_join_match':True,'sample_raw_to_median':samples,'partial_last_month':'2026-10','latest_contract_date':str(v.deal_date.max().date()),'file_hashes':[{'file':str(f),'sha256':sha(f),'bytes':f.stat().st_size}for f in inputs],'render_review_ready':False,'actual_video_review':False,'limits':['기존검증원문스냅샷의월집계이며최신모든신고의전수완결보증아님.','무거래와첫관측전은가격없음. 이후알파모션은별도전환표현이며월가격을보간한것이아님.']}
(Q/'monthly_data_independent_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:report[k] for k in ['monthly_price_review_ready','valid_source_rows','month_count','mapped_n_sum','exact_5eok_under_groups','all_observed_reappearances','adjacent_reappearances']}))
