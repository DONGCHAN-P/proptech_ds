import duckdb
c=duckdb.connect()
print(c.execute("SELECT apt_name_raw,apt_id,deal_date,area_m2,deal_amount,is_canceled FROM read_parquet('master/trade_events.parquet') WHERE apt_name_raw LIKE '%롯데캐슬%' AND deal_amount>=210000 AND sigungu_name LIKE '%화성%' ORDER BY deal_date DESC LIMIT 15").fetchall())
