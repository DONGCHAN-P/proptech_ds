import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import duckdb
from metrics.filters import trades_cte
c=duckdb.connect()
print(c.execute("DESCRIBE SELECT * FROM read_parquet('master/trade_events.parquet')").fetchall())
print(c.execute("SELECT min(deal_date),max(deal_date),count(*) FROM read_parquet('master/trade_events.parquet')").fetchall())
print(c.execute(trades_cte('master/trade_events.parquet')+" SELECT apt_name_raw, apt_id, sigungu_name,legal_dong_name,count(*) FROM trades WHERE apt_name_raw LIKE '%롯데캐슬%' AND sigungu_name='화성동탄구'  GROUP BY ALL").fetchall())



