from pathlib import Path
import json,sys
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R))
import duckdb
from metrics.filters import trades_cte
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet').replace('WITH trades AS','WITH filtered AS')+", trades AS (SELECT * FROM filtered WHERE deal_date<=DATE '2026-10-06')\n"
leaders=json.loads((R/'video/public/pilot-v8/representatives.json').read_text(encoding='utf8'));report=[]
for t in leaders['towns']:
 for key,part in [('monthly',"date_trunc('month',deal_date)"),('quarterly',"date_trunc('quarter',deal_date)")]:
  rows=c.execute(cte+f" SELECT {part} p,count(*),median(deal_amount) FROM trades WHERE apt_id=? AND area_m2>=83 AND area_m2<85 GROUP BY 1 ORDER BY 1",[t['apt_id']]).fetchall()
  t[key]=[dict(period=str(d.date() if hasattr(d,'date') else d),year=d.year,quarter=(d.month-1)//3+1,month=d.month,n=n,median_manwon=m,partial=d.year==2026 and d.month>=10) for d,n,m in rows]
 stats={}
 for key in ['monthly','quarterly']:
  rows=[r for r in t[key] if r['year']>=2021 and not r['partial']];start=min((r['year']*12+r['month']-1 for r in rows),default=2021*12);end=2026*12+8;expected=(end-start+1) if key=='monthly' else (end-start)//3+1
  stats[key]=dict(observed=len(rows),expected=expected,empty=max(0,expected-len(rows)),below3=sum(r['n']<3 for r in rows),median_count=sorted(r['n'] for r in rows)[len(rows)//2] if rows else 0)
 report.append(dict(name=t['name'],town=t['town'],stats=stats,selected=[r for r in t['quarterly'] if not r['partial'] and (r['year'],r['quarter']) in [(2016,4),(2021,4),(2023,1),(2023,4),(2026,3)]]))
out=R/'video/public/pilot-v10';out.mkdir(exist_ok=True);(out/'periods.json').write_text(json.dumps(leaders,ensure_ascii=False,indent=2),encoding='utf8');(out/'period-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
