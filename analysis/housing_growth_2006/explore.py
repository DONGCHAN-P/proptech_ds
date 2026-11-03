from pathlib import Path
import json,numpy as np,pandas as pd,pyarrow.parquet as pq
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent/'exploration';O.mkdir(exist_ok=True)
d=pq.read_table(R/'master/trade_events.parquet',columns=['apt_id','area_m2_key','deal_date','sigungu_code','deal_amount','area_m2','is_canceled','deal_hash']).to_pandas()
d=d[~d.is_canceled.fillna(False)&(d.deal_amount>0)&(d.area_m2>0)].drop_duplicates('deal_hash').copy();d['region']=d.sigungu_code.str[:2].map({'11':'서울','41':'경기','28':'인천'});d=d[d.region.notna()];d['q']=d.deal_date.dt.to_period('Q');d=d[(d.q>='2006Q1')&(d.q<='2026Q3')];d['ppm']=d.deal_amount/d.area_m2
volume=d.groupby(['region','q']).agg(transactions=('ppm','size'),complexes=('apt_id','nunique'),p10=('ppm',lambda x:x.quantile(.1)),median=('ppm','median'),p90=('ppm',lambda x:x.quantile(.9))).reset_index();volume['q']=volume.q.astype(str);volume.to_csv(O/'quarterly_volume_distribution.csv',index=False,encoding='utf-8-sig')
results=[];peaks=[];sensitivity=[]
for minimum in [2,3,5]:
 g=d.groupby(['region','q','apt_id','area_m2_key']).agg(p=('ppm','median'),n=('ppm','size')).reset_index();g=g[g.n>=minimum];prev=g.copy();prev.q+=1;m=g.merge(prev,on=['region','q','apt_id','area_m2_key'],suffixes=('','_prev'));m['lr']=np.log(m.p/m.p_prev)
 b=m.groupby(['region','q','apt_id']).lr.mean().reset_index();stats=b.groupby(['region','q']).agg(lr=('lr','mean'),matched=('apt_id','size'),r10=('lr',lambda x:np.expm1(x.quantile(.1))*100),r90=('lr',lambda x:np.expm1(x.quantile(.9))*100)).reset_index()
 for region,s in stats.groupby('region'):
  s=s.sort_values('q'); idx=100.;series=[{'region':region,'q':'2006Q1','index':100.,'change':None,'matched':None,'r10':None,'r90':None}]
  for row in s.itertuples():
   if row.matched<1:raise ValueError('No matches')
   idx*=np.exp(row.lr);series.append(dict(region=region,q=str(row.q),index=idx,change=np.expm1(row.lr)*100,matched=int(row.matched),r10=row.r10,r90=row.r90))
  expected=len(pd.period_range('2006Q1','2026Q3',freq='Q'));assert len(series)==expected,(region,len(series))
  z=pd.DataFrame(series);window=z[z.q.between('2020Q1','2022Q4')];pk=window.loc[window['index'].idxmax()];after=z[z.q>=pk.q];tr=after.loc[after['index'].idxmin()];recovery=z[(z.q>tr.q)&(z['index']>=pk['index'])];rec=None if recovery.empty else recovery.iloc[0].q
  record=dict(region=region,min_trades=minimum,peak_quarter=pk.q,trough_quarter=tr.q,drawdown_pct=(tr['index']/pk['index']-1)*100,recovery_quarter=rec,latest_quarter=z.iloc[-1].q,latest_vs_peak_pct=(z.iloc[-1]['index']/pk['index']-1)*100,min_matched=int(s.matched.min()))
  sensitivity.append(record)
  if minimum==2:results.extend(series);peaks.append(record)
pd.DataFrame(results).to_csv(O/'quarterly_matched_index.csv',index=False,encoding='utf-8-sig');pd.DataFrame(peaks).to_csv(O/'peak_recovery.csv',index=False,encoding='utf-8-sig');pd.DataFrame(sensitivity).to_csv(O/'sensitivity.csv',index=False,encoding='utf-8-sig')
(O/'results.json').write_text(json.dumps({'peaks':peaks,'sensitivity':sensitivity},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(peaks,ensure_ascii=False,indent=2))


