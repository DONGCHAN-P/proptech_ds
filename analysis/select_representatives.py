import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R))
import duckdb
from metrics.filters import trades_cte
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet')
queries=[('광교',"apt_name_raw='자연앤힐스테이트' AND legal_dong_name='이의동'"),('동탄2',"apt_name_raw='동탄역롯데캐슬'"),('파주 운정',"apt_name_raw='한울마을1단지운정신도시IPARK'"),('김포 한강',"sigungu_name='김포시' AND apt_name_raw LIKE '%센트럴자이1%'"),('양주 옥정',"sigungu_name='양주시' AND apt_name_raw LIKE '%레이크시티1%'")]
out={'definition':'시장 대표성·생활권·비교 가능한 국평 거래를 기준으로 선정. 전용83~85㎡ 연도별 중위가격.','towns':[]}
for town,where in queries:
 rows=c.execute(cte+f" SELECT apt_id,apt_name_raw,count(*) FROM trades WHERE {where} GROUP BY ALL ORDER BY 3 DESC").fetchall()
 if len(rows)!=1: print(town,rows);raise RuntimeError('Resolve complex IDs')
 aid,name,n=rows[0]
 annual=c.execute(cte+" SELECT year(deal_date),count(*),median(deal_amount),max(deal_amount) FROM trades WHERE apt_id=? AND area_m2>=83 AND area_m2<85 GROUP BY 1 ORDER BY 1",[aid]).fetchall()
 peak=c.execute(cte+" SELECT deal_amount,area_m2,deal_date FROM trades WHERE apt_id=? AND area_m2>=83 AND area_m2<85 ORDER BY deal_amount DESC,deal_date DESC LIMIT 1",[aid]).fetchone()
 out['towns'].append(dict(town=town,apt_id=aid,name=name,peak_manwon=peak[0],peak_area=peak[1],peak_date=str(peak[2].date()),annual=[dict(year=y,n=n,median_manwon=m,max_manwon=mx) for y,n,m,mx in annual]))
(R/'output/metrics_representatives_20261013.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=True))

