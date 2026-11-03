import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import duckdb
from metrics.filters import trades_cte
from analysis.newtown import TOWNS,town_where
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet')
print(c.execute(cte+' SELECT max(deal_date) FROM trades').fetchone())
for town in ['광교','동탄2']:
 for filt in ["pyeong_bucket='30P'","area_m2>=83 AND area_m2<85"]:
  print(town,filt,c.execute(cte+f" SELECT count(*),median(deal_amount),quantile_cont(deal_amount,.25),quantile_cont(deal_amount,.75) FROM trades WHERE year(deal_date)=2026 AND deal_date<=DATE '2026-10-06' AND ({town_where(town)}) AND ({filt})").fetchone())
