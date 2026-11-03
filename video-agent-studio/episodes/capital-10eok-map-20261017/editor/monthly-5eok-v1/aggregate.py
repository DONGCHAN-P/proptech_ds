from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;E=P.parent.parent;S=E/'research/source-completion-v1';R=E/'research/monthly-5eok-v1';coords=json.loads((E/'research/annual-map-v2/map_packet_v2.json').read_text(encoding='utf8'));df=pd.read_parquet(S/'episode_84_source_rows.parquet',columns=['complex_id','deal_date','deal_amount','included_price_analysis','area_m2','is_canceled','cancel_date']);v=df[df.included_price_analysis].copy();assert len(v)==1626292 and v.area_m2.ge(83).all() and v.area_m2.lt(85).all() and not v.is_canceled.fillna(False).any();v['month']=v.deal_date.dt.strftime('%Y-%m');months=pd.period_range('2006-01','2026-10',freq='M').astype(str).tolist();assert len(months)==250 and v.month.isin(months).all();agg=v.groupby(['complex_id','month']).deal_amount.agg(median_manwon='median',n='size').reset_index();assert agg.n.sum()==len(v);agg.to_parquet(R/'all_monthly_prices.parquet',index=False);ids=sorted(v.complex_id.unique());first=v.groupby('complex_id').month.min().to_dict();mapped={c['complex_id']:c for c in coords['complexes']};assert len(mapped)==8288 and len(ids)==9172;idx={cid:i for i,cid in enumerate(sorted(mapped))};status=np.full((250,8288),3,dtype=np.uint8);prices=np.full((250,8288),np.nan);ns=np.zeros((250,8288),dtype=np.int32);month_index={s:i for i,s in enumerate(months)}
for cid,i in idx.items():
 first_i=month_index[first[cid]];status[first_i:,i]=2
ma=agg[agg.complex_id.isin(mapped)].copy()
for a in ma.itertuples():
 m=month_index[a.month];i=idx[a.complex_id];status[m,i]=0 if a.median_manwon<=50000 else 1;prices[m,i]=a.median_manwon;ns[m,i]=a.n
summary=[]
for mi,month in enumerate(months):
 c=np.bincount(status[mi],minlength=4);a=agg[agg.month.eq(month)];s={'month':month,'month_label':month.replace('-','.'),'map_catalog':8288,'all_catalog':9172,'unlinked_catalog':884,'map_observed':int(c[0]+c[1]),'map_under':int(c[0]),'map_over':int(c[1]),'map_no_trade':int(c[2]),'map_not_yet_observed':int(c[3]),'map_n':int(ns[mi].sum()),'all_observed':len(a),'all_under':int(a.median_manwon.le(50000).sum()),'all_over':int(a.median_manwon.gt(50000).sum()),'all_n':int(a.n.sum()),'ratio_percent':float(c[0]/(c[0]+c[1])*100) if c[0]+c[1] else None,'partial_month':month=='2026-10'};assert sum(c)==8288 and s['map_under']+s['map_over']==s['map_observed'];assert s['map_observed']>0;summary.append(s)
exact=int(np.sum(prices==50000));assert np.all(status[prices==50000]==0);reappear=0;adj=0
for i in range(8288):
 last=None
 for m in range(250):
  st=int(status[m,i])
  if m and status[m-1,i]==1 and st==0:adj+=1
  if st in [0,1]:
   if last==1 and st==0:reappear+=1
   last=st
cs=[]
for cid,i in idx.items():
 c=mapped[cid];cs.append({'complex_id':cid,'name':c['name'],'x_5179':c['x_5179'],'y_5179':c['y_5179'],'HSMP_INNB':c['HSMP_INNB'],'first_valid_trade_month':first[cid]})
np.savez_compressed(R/'monthly_arrays.npz',status=status,median_manwon=prices,n=ns);pd.DataFrame(summary).to_csv(R/'monthly_summary.csv',index=False,encoding='utf-8-sig');(R/'monthly_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');(R/'complex_catalog.json').write_text(json.dumps(cs,ensure_ascii=False,separators=(',',':')),encoding='utf8');ratios=[s['ratio_percent'] for s in summary];lo=max(0,int(min(ratios)//10)*10);hi=min(100,int(np.ceil(max(ratios)/10))*10);hi=100 if hi==lo else hi
inputs=[S/'episode_84_source_rows.parquet',E/'research/annual-map-v2/map_packet_v2.json'];validation={'valid_source_rows':len(v),'all_month_n_sum':int(agg.n.sum()),'mapped_month_n_sum':int(ns.sum()),'month_count':250,'map_catalog':8288,'all_catalog':9172,'exactly_5eok_map_complex_months':exact,'reappearances_after_over_including_no_trade_gaps':reappear,'adjacent_month_over_to_under':adj,'first_observation_before_hidden':True,'status_code':{'under':0,'over':1,'no_trade':2,'not_yet_observed':3},'all_month_count_identities_verified':True,'threshold_manwon':50000,'threshold_operator':'<=50000 shown; >50000 hidden','minimum_observed_ratio':min(ratios),'maximum_observed_ratio':max(ratios),'chart_axis_percent':[lo,hi],'partial_last_month':'2026-10','latest_contract_date':str(v.deal_date.max().date()),'inputs':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],'new_api_calls':0,'paid_calls':0};(R/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:validation[k] for k in ['valid_source_rows','month_count','map_catalog','exactly_5eok_map_complex_months','reappearances_after_over_including_no_trade_gaps','chart_axis_percent']},ensure_ascii=False))
