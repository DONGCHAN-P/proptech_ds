from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd,pyarrow.parquet as pq
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/stats_deps'));O=Path(__file__).parent
f=O/'raw/histretSP.xls';sp=pd.read_excel(f,sheet_name='Returns by year',header=None);sp=sp[pd.to_numeric(sp[0],errors='coerce').between(2006,2025)].copy();sp['year']=sp[0].astype(int);stock=dict(zip(sp.year,sp[1].astype(float)))
raw=pd.read_excel(f,sheet_name='S&P 500 & Raw Data',header=None);raw=raw[pd.to_numeric(raw[0],errors='coerce').between(2006,2025)].copy();prices=dict(zip(raw[0].astype(int),raw[1].astype(float)))
d=pq.read_table(R/'master/trade_events.parquet',columns=['apt_id','area_m2_key','deal_date','sigungu_code','deal_amount','area_m2','is_canceled','deal_hash']).to_pandas();d=d[~d.is_canceled.fillna(False)&(d.deal_amount>0)&(d.area_m2>0)&d.apt_id.notna()&d.sigungu_code.str[:2].isin(['11','28','41'])].drop_duplicates('deal_hash');d['year']=d.deal_date.dt.year;d=d[d.year.between(2006,2025)];d['ppm']=d.deal_amount/d.area_m2
g=d.groupby(['year','apt_id','area_m2_key']).agg(p=('ppm','median'),n=('ppm','size')).reset_index();g=g[g.n>=5];prev=g.copy();prev.year+=1;m=g.merge(prev,on=['year','apt_id','area_m2_key'],suffixes=('','_prev'));m['lr']=np.log(m.p/m.p_prev);z=m.groupby(['year','apt_id']).lr.mean().reset_index();house=z.groupby('year').agg(lr=('lr','mean'),matched_complexes=('apt_id','size'));assert len(house)==19
annual=[]
for y in range(2007,2026):annual.append({'year':y,'housing_return':float(np.expm1(house.loc[y,'lr'])),'matched_complexes':int(house.loc[y,'matched_complexes']),'sp_price_return':prices[y]/prices[y-1]-1,'sp_dividend_included_return':stock[y]})
pd.DataFrame(annual).to_csv(O/'annual_returns.csv',index=False,encoding='utf-8-sig')
summary=[];paths={}
for start in [2006,2015,2020,2022]:
 a=[r for r in annual if r['year']>start];n=2025-start;assert len(a)==n
 for key,label in [('housing_return','수도권 아파트 가격'),('sp_price_return','S&P500 가격 · USD'),('sp_dividend_included_return','S&P500 배당 포함 · USD')]:
  vals=[r[key] for r in a];end=float(np.prod([1+v for v in vals]));summary.append({'start':start,'end':2025,'years':n,'series':label,'cagr_pct':(end**(1/n)-1)*100,'arithmetic_mean_pct':float(np.mean(vals)*100),'cumulative_pct':(end-1)*100})
 paths[str(start)]=[{'year':start,'house':100,'price':100,'total':100}];h=p=t=100
 for r in a:
  h*=1+r['housing_return'];p*=1+r['sp_price_return'];t*=1+r['sp_dividend_included_return'];paths[str(start)].append({'year':r['year'],'house':h,'price':p,'total':t})
pd.DataFrame(summary).to_csv(O/'comparison_summary.csv',index=False,encoding='utf-8-sig');out={'summary':summary,'paths':paths,'source':{'sp':'https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html','sp_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'house':'master/trade_events.parquet'},'limitations':['House = annual-median matched sample chain; stocks = year-end endpoints; timing is not identical','All returns nominal, unlevered, before taxes/costs; house excludes rent/use value','S&P dividend-included series is Damodaran dataset calculation, not identical to official SPTR reinvestment methodology','USD stock returns, KRW housing; FX not available: FRED download returned maintenance HTML','Do not substitute retrospective returns for future expected returns']};(O/'comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(pd.DataFrame(summary)[['start','series','cagr_pct']].to_string(index=False))
