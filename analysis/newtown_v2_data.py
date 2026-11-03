import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import duckdb
from metrics.filters import trades_cte
from analysis.newtown import TOWNS,town_where
TOWNS['동탄2'][1].append('여울동')
c=duckdb.connect()
cte=trades_cte('master/trade_events.parquet')
result={"basis":"2006~2026 local RTMS, cancelled excluded, 2026 partial year through 2026-10-06","regions":[],"complexes":[]}
for town in TOWNS:
 r=c.execute(cte+f" SELECT count(*),median(deal_amount),count(*) FILTER(WHERE deal_amount>100000) FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P' AND ({town_where(town)})").fetchone()
 result["regions"].append(dict(name=town,count=r[0],median_manwon=r[1],over10_count=r[2],over10_pct=round(r[2]/r[0]*100,1) if r[0] else None))
queries=[("동탄역 롯데캐슬","sigungu_name='화성동탄구' AND apt_name_raw='동탄역롯데캐슬'"),("광교 자연앤힐스테이트","legal_dong_name IN ('이의동','원천동') AND apt_name_raw LIKE '%힐스테이트%'"),("김포 한강힐스테이트","sigungu_name='김포시' AND legal_dong_name='마산동' AND apt_name_raw='한강 힐스테이트'"),("옥정 어반센트럴","sigungu_name='양주시' AND apt_name_raw LIKE '%어반센트럴%'"),("운정 힐스테이트","sigungu_name='파주시' AND legal_dong_name='목동동' AND apt_name_raw='산내마을9단지힐스테이트운정'")]
for name,where in queries:
 ids=c.execute(cte+f" SELECT apt_id,apt_name_raw,legal_dong_name,count(*) FROM trades WHERE {where} GROUP BY ALL ORDER BY 4 DESC").fetchall()
 for aid,raw,dong,n in ids:
  rows=c.execute(cte+" SELECT year(deal_date),count(*),median(deal_amount),max(deal_amount) FROM trades WHERE apt_id=? AND area_m2>=83 AND area_m2<85 GROUP BY 1 ORDER BY 1",[aid]).fetchall()
  result["complexes"].append(dict(label=name,apt_id=aid,name=raw,dong=dong,annual84=[dict(year=y,n=n,median_manwon=m,max_manwon=mx) for y,n,m,mx in rows]))
r=c.execute(cte+f" SELECT count(*),median(deal_amount),count(*) FILTER(WHERE deal_amount>100000) FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P' AND (({town_where('동탄1')}) OR ({town_where('동탄2')}))" ).fetchone()
result['regions'].append(dict(name='동탄1·2',count=r[0],median_manwon=r[1],over10_count=r[2],over10_pct=round(r[2]/r[0]*100,1)))
out=ROOT/'output'/'metrics_newtown_v2_20261013.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=True))



