import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import duckdb
from metrics.filters import trades_cte
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet')
scopes={'광교':('수원영통구',['이의동','원천동']),'동탄2':('화성동탄구',['청계동','영천동','산척동','목동','오산동','신동','송동','방교동','장지동','여울동'])}
for name,(sgg,dongs) in scopes.items():
 where="sigungu_name='"+sgg+"' AND legal_dong_name IN ("+','.join("'"+d+"'" for d in dongs)+')'
 for area in ["pyeong_bucket='30P'","area_m2>=83 AND area_m2<85"]:
  print(name,area,c.execute(cte+f' SELECT count(*),median(deal_amount),quantile_cont(deal_amount,.25),quantile_cont(deal_amount,.75) FROM trades WHERE year(deal_date)=2026 AND ({area}) AND ({where})').fetchone())
