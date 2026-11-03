from pathlib import Path
import json, numpy as np, pandas as pd, pyarrow.parquet as pq
R=Path(__file__).resolve().parents[2]; O=Path(__file__).parent
cols=['apt_id','area_m2_key','deal_date','sigungu_code','deal_amount','area_m2','is_canceled','deal_hash']
d=pq.read_table(R/'master/trade_events.parquet',columns=cols).to_pandas(); raw=len(d)
d=d[~d.is_canceled.fillna(False)&(d.deal_amount>0)&(d.area_m2>0)&d.apt_id.notna()].copy(); before=len(d); d=d.drop_duplicates('deal_hash'); dup=before-len(d)
names={'11':'서울','26':'부산','27':'대구','28':'인천','29':'광주','30':'대전','31':'울산','36':'세종','41':'경기','42':'강원','43':'충북','44':'충남','45':'전북','46':'전남','47':'경북','48':'경남','50':'제주','51':'강원','52':'전북'}
d['region']=d.sigungu_code.str[:2].map(names); d['year']=d.deal_date.dt.year; d['ppm']=d.deal_amount/d.area_m2
coverage=d.groupby(['region','year']).agg(transactions=('ppm','size'),complexes=('apt_id','nunique'),median_per_m2=('ppm','median'),first_date=('deal_date','min'),last_date=('deal_date','max')).reset_index(); coverage.to_csv(O/'coverage.csv',index=False,encoding='utf-8-sig')
end=d.deal_date.max(); full=min(2025,end.year-1); a=d[(d.year>=2006)&(d.year<=full)]
g=a.groupby(['region','year','apt_id','area_m2_key']).agg(price=('ppm','median'),n=('ppm','size')).reset_index(); g=g[g.n>=5]
p=g.copy(); p.year+=1; pairs=g.merge(p,on=['region','year','apt_id','area_m2_key'],suffixes=('','_prev')); pairs['log_return']=np.log(pairs.price/pairs.price_prev)
rows=[]
for (reg,year),s in pairs.groupby(['region','year']):
 # Collapse areas within a complex first, then equal weight complexes.
 z=s.groupby('apt_id').log_return.mean(); rows.append(dict(region=reg,year=int(year),growth_pct=float(np.expm1(z.mean())*100),matched_complexes=len(z),matched_area_pairs=len(s),transactions=int(s.n.sum()+s.n_prev.sum()),q10=float(np.expm1(z.quantile(.1))*100),q90=float(np.expm1(z.quantile(.9))*100)))
r=pd.DataFrame(rows).sort_values(['region','year']); r.to_csv(O/'matched_annual_growth.csv',index=False,encoding='utf-8-sig')
summary=[]
for reg,s in r.groupby('region'):
 for years in [1,3,5,10,19]:
  q=s[(s.year>full-years)&(s.year<=full)]
  if len(q)==years and q.matched_complexes.min()>=30:
   growth=np.prod(1+q.growth_pct/100); summary.append(dict(region=reg,start=full-years,end=full,years=years,cumulative_pct=(growth-1)*100,annualized_pct=(growth**(1/years)-1)*100,min_matched_complexes=int(q.matched_complexes.min())))
pd.DataFrame(summary).to_csv(O/'period_growth.csv',index=False,encoding='utf-8-sig')
audit={'raw_rows':raw,'valid_deduplicated_rows':len(d),'duplicate_hashes_removed':dup,'first_date':str(d.deal_date.min()),'last_date':str(end),'regions':sorted(d.region.dropna().unique()),'last_full_year':full,'method':'Annual median price per m2 for identical apt_id and area_m2_key, >=5 trades in each year; average log return within complex, then equal complex weights. Chain annual matched returns. >=30 complexes each year for period summary.','limitations':['Not an official price index; changing matched sample, survivor and turnover bias','No adjustment for floor, renovation or within-year transaction timing','Source completeness and apt_id stability not independently established','2026 excluded from full-year chart; no extrapolation','Prices are in source deal_amount units; returns unit-invariant']}
(O/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
# Self-contained SVG chart: calendar-year returns, no inferred missing years.
regions=list(r.region.unique()); W=1250; H=100+len(regions)*49; svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#F6F4EF"/><g font-family="sans-serif" fill="#173348"><text x="25" y="30" font-size="21">동일 단지·면적 매칭 연간 가격변화 (%) · 자체 실거래 분석</text>']
for y in range(2007,full+1): svg.append(f'<text x="{110+(y-2007)*58}" y="65" font-size="12">{y}</text>')
for i,reg in enumerate(regions):
 yy=85+i*49; svg.append(f'<text x="20" y="{yy+23}" font-size="16">{reg}</text>')
 for y in range(2007,full+1):
  q=r[(r.region==reg)&(r.year==y)]; x=102+(y-2007)*58
  if len(q) and q.iloc[0].matched_complexes>=30:
   v=q.iloc[0].growth_pct; color='#286cda' if v>=0 else '#bc4d4d'; opacity=.18+min(abs(v)/25,1)*.65; label=f'{v:+.1f}'
  else: color='#888'; opacity=.08; label='—'
  svg.append(f'<rect x="{x}" y="{yy}" width="55" height="39" fill="{color}" fill-opacity="{opacity}" rx="3"/><text x="{x+27}" y="{yy+24}" text-anchor="middle" font-size="13">{label}</text>')
svg.append('</g></svg>'); (O/'annual_heatmap.svg').write_text(''.join(svg),encoding='utf8')
print(json.dumps(audit,ensure_ascii=False)); print(pd.DataFrame(summary).to_string(index=False))
