import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R))
import duckdb
from metrics.filters import trades_cte
from analysis.newtown import town_where
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet')
out={'definition':'수집된 해제 제외 거래 전체 기간·전체 면적의 최고 거래총액 단지. 추이 차트는 각 단지 최고가 면적형(면적 차이 0.05㎡ 미만)의 연도별 중위가격.','towns':[]}
for town in ['광교','동탄2','파주 운정','김포 한강','양주 옥정']:
 rows=c.execute(cte+f" SELECT apt_id,arg_max(apt_name_raw,deal_amount),max(deal_amount),arg_max(area_m2,deal_amount),arg_max(deal_date,deal_amount),count(*) FROM trades WHERE ({town_where(town)}) GROUP BY apt_id ORDER BY max(deal_amount) DESC LIMIT 3").fetchall()
 aid,name,peak,area,date,n=rows[0]
 annual=c.execute(cte+" SELECT year(deal_date),count(*),median(deal_amount),max(deal_amount) FROM trades WHERE apt_id=? AND abs(area_m2-?)<0.05 GROUP BY 1 ORDER BY 1",[aid,area]).fetchall()
 out['towns'].append(dict(town=town,apt_id=aid,name=name,peak_manwon=peak,peak_area=area,peak_date=str(date.date()),annual=[dict(year=y,n=n,median_manwon=m,max_manwon=mx) for y,n,m,mx in annual],top3=[dict(name=r[1],peak_manwon=r[2],area=r[3]) for r in rows]))
(R/'output/metrics_leaders_20261013.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=True))



