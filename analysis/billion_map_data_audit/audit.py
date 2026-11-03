from pathlib import Path
import pandas as pd,json
out=Path('analysis/billion_map_data_audit')
df=pd.read_parquet('master/trade_events.parquet',columns=['apt_id','deal_date','sigungu_code','deal_amount','area_m2','floor','build_year','is_canceled','deal_hash'])
g=pd.read_parquet('master/apt_id_map.parquet'); df['region']=df.sigungu_code.str[:2].map({'11':'서울','28':'인천','41':'경기'});df['year']=df.deal_date.dt.year
valid=df[(~df.is_canceled.fillna(False))&df.deal_amount.gt(0)&df.area_m2.ge(83)&df.area_m2.lt(85)&df.region.notna()]
geo=g[g.lat.between(33,39)&g.lng.between(124,132)]
v=valid.assign(has_geo=valid.apt_id.isin(geo.apt_id))
by=v.groupby(['region','year']).agg(transactions=('apt_id','size'),complexes=('apt_id','nunique'),geo_transactions=('has_geo','sum')).reset_index()
by.to_csv(out/'annual_region_coverage.csv',index=False,encoding='utf-8-sig')
agg=v.groupby(['apt_id','year']).deal_amount.agg(['median','count']).reset_index(); agg['has_geo']=agg.apt_id.isin(geo.apt_id)
annual=agg.groupby('year').agg(complexes=('apt_id','size'),geo_complexes=('has_geo','sum'),below_or_equal_1bn=('median',lambda s:int((s<=100000).sum())),single_trade_complexes=('count',lambda s:int((s==1).sum()))).reset_index()
annual.to_csv(out/'annual_complex_summary.csv',index=False,encoding='utf-8-sig')
raw=list(Path('raw').rglob('*.xml')); names=[str(p) for p in raw[:4]]
r={'checked_on':'2026-10-17','source_rows':len(df),'source_bytes':Path('master/trade_events.parquet').stat().st_size,'all_date_min':str(df.deal_date.min()),'all_date_max':str(df.deal_date.max()),'all_region_counts':df.region.value_counts(dropna=False).to_dict(),'canceled_rows':int(df.is_canceled.sum()),'duplicate_deal_hash_rows':int(df.deal_hash.duplicated().sum()),'eligible_rows':len(v),'eligible_complexes':v.apt_id.nunique(),'eligible_geocoded_complexes':v.loc[v.has_geo,'apt_id'].nunique(),'eligible_missing_geo_complexes':v.loc[~v.has_geo,'apt_id'].nunique(),'geo_master_rows':len(g),'geo_valid_rows':len(geo),'raw_xml_count':len(raw),'raw_xml_bytes':sum(p.stat().st_size for p in raw),'raw_sample_paths':names,'annual_regions':by.to_dict('records'),'annual_complexes':annual.to_dict('records')}
(out/'audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in r.items() if k not in ['annual_regions','annual_complexes']},ensure_ascii=False));print(annual.to_string(index=False));print(by.groupby('region').agg(first=('year','min'),last=('year','max'),rows=('transactions','sum')).to_string())
