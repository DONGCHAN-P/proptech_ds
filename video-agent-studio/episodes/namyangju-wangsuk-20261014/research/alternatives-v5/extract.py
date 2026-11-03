from pathlib import Path
import duckdb,json
root=Path(__file__).parent
c=duckdb.connect()
q="""select legal_dong_name,apt_name_raw,build_year,count(*) n,median(deal_amount) median_manwon,min(deal_amount) min_manwon,max(deal_amount) max_manwon,min(deal_date) first_date,max(deal_date) last_date from read_parquet('master/trade_events.parquet') where sigungu_code='41360' and deal_date between '2026-07-01' and '2026-10-08' and area_m2>=83 and area_m2<85 and floor>=5 and not is_canceled and build_year>=2010 group by all order by legal_dong_name,n desc"""
df=c.sql(q).df()
df.to_json(root/'all_candidates.json',orient='records',force_ascii=False,date_format='iso',indent=2)
print(df.to_string(index=False))
