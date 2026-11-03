from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R))
import duckdb
from metrics.filters import trades_cte
from analysis.newtown import TOWNS,town_where
if '여울동' not in TOWNS['동탄2'][1]:TOWNS['동탄2'][1].append('여울동')
c=duckdb.connect();cte=trades_cte('master/trade_events.parquet').replace('WITH trades AS','WITH filtered AS')+", trades AS (SELECT * FROM filtered WHERE deal_date<=DATE '2026-10-06')\n";out={'basis':'해제 제외; 지역 분포는 전용83~85㎡; 연도2026 수집표본;10월6일까지','regions':[],'complexes':[]}
for name in ['광교','동탄2','파주 운정','김포 한강','양주 옥정']:
 where=town_where(name)
 rows=c.execute(cte+f" SELECT deal_amount FROM trades WHERE year(deal_date)=2026 AND area_m2>=83 AND area_m2<85 AND ({where}) ORDER BY deal_amount").fetchall();values=[r[0] for r in rows]
 r=c.execute(cte+f" SELECT count(*),median(deal_amount),quantile_cont(deal_amount,.25),quantile_cont(deal_amount,.75),min(deal_amount),max(deal_amount) FROM trades WHERE year(deal_date)=2026 AND area_m2>=83 AND area_m2<85 AND ({where})").fetchone()
 bins=[{'from_eok':b,'to_eok':b+2,'n':sum(b*10000<=v<(b+2)*10000 for v in values)} for b in range(0,24,2)]
 monthly=c.execute(cte+f" SELECT month(deal_date),count(*),median(deal_amount) FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P' AND ({where}) GROUP BY 1 ORDER BY 1").fetchall()
 out['regions'].append(dict(name=name,n=r[0],median=r[1],q1=r[2],q3=r[3],min=r[4],max=r[5],bins=bins,monthly30=[dict(month=m,n=n,median=v) for m,n,v in monthly]))
leaders=json.loads((R/'output/metrics_representatives_20261013.json').read_text(encoding='utf8'))
for t in leaders['towns']:
 rows=c.execute(cte+" SELECT year(deal_date),count(*),median(deal_amount),max(deal_amount) FROM trades WHERE apt_id=? AND area_m2>=83 AND area_m2<85 GROUP BY 1 ORDER BY 1",[t['apt_id']]).fetchall()
 t['annual']=[dict(year=y,n=n,median_manwon=m,max_manwon=mx) for y,n,m,mx in rows]
 annual=t['annual'];by={r['year']:r for r in annual};t['change_2021_2026_pct']=round((by[2026]['median_manwon']/by[2021]['median_manwon']-1)*100,1) if 2021 in by else None
 t['change_2021_2023_pct']=round((by[2023]['median_manwon']/by[2021]['median_manwon']-1)*100,1) if 2021 in by and 2023 in by else None
 out['complexes'].append(t)
(R/'video/public/pilot-v8').mkdir(exist_ok=True)
(R/'video/public/pilot-v8/data.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
base=json.loads((R/'video/public/pilot-v2/metrics.json').read_text(encoding='utf8'));base['regions']=[]
for name in TOWNS:
 r=c.execute(cte+f" SELECT count(*),median(deal_amount),count(*) FILTER(WHERE deal_amount>100000) FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P' AND ({town_where(name)})").fetchone()
 base['regions'].append(dict(name=name,count=r[0],median_manwon=r[1],over10_count=r[2],over10_pct=round(r[2]/r[0]*100,1)))
r=c.execute(cte+f" SELECT count(*),median(deal_amount),count(*) FILTER(WHERE deal_amount>100000) FROM trades WHERE year(deal_date)=2026 AND pyeong_bucket='30P' AND (({town_where('동탄1')}) OR ({town_where('동탄2')}))").fetchone()
base['regions'].append(dict(name='동탄1·2',count=r[0],median_manwon=r[1],over10_count=r[2],over10_pct=round(r[2]/r[0]*100,1)))
(R/'video/public/pilot-v8/regional.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf8')
(R/'video/public/pilot-v8/representatives.json').write_text(json.dumps({'towns':out['complexes']},ensure_ascii=False,indent=2),encoding='utf8')
(R/'video/public/pilot-v8/scope.json').write_text(json.dumps({'cutoff':'2026-10-06','towns':TOWNS,'master_modified':str((R/'master/trade_events.parquet').stat().st_mtime),'note':'current collected snapshot; retrospective counts can differ from v7 frozen figures'},ensure_ascii=False,indent=2),encoding='utf8')
print('REGIONAL',json.dumps(base['regions'],ensure_ascii=False))
print(json.dumps({'regions':[dict(name=r['name'],n=r['n'],median=r['median'],q1=r['q1'],q3=r['q3']) for r in out['regions']],'complexes':[dict(name=t['name'],changes=[t['change_2021_2026_pct'],t['change_2021_2023_pct']]) for t in out['complexes']]},ensure_ascii=False))
