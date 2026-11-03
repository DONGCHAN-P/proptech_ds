import duckdb
c=duckdb.connect()
print(c.execute("SELECT apt_name_raw,apt_id,sigungu_name,legal_dong_name,area_m2,deal_amount,deal_date,is_canceled FROM read_parquet('master/trade_events.parquet') WHERE year(deal_date)=2026 AND deal_amount=222500 AND area_m2 BETWEEN 83 AND 85").fetchall())
print(c.execute("SELECT apt_name_raw,apt_id,sigungu_name,legal_dong_name,count(*) FROM read_parquet('master/trade_events.parquet') WHERE apt_name_raw LIKE '%롯데%' AND (legal_dong_name='오산동' OR legal_dong_name='여울동') GROUP BY ALL").fetchall())

