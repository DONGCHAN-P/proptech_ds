from pathlib import Path
import json,xml.etree.ElementTree as ET,statistics,hashlib,csv
out=Path(__file__).parent; rows=[];sources=[]
for ym in ['202607','202608','202609']:
 p=Path('raw/rtms_trade')/ym[:4]/ym[4:]/f'41450_{ym}.xml'
 fresh=out/'price_raw'/f'41450_{ym}.xml'
 if fresh.exists():p=fresh
 tree=ET.parse(p);items=tree.findall('.//item')
 sources.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'items':len(items),'total':tree.findtext('.//totalCount'),'metadata':json.loads(p.with_suffix('.meta.json').read_text(encoding='utf-8'))})
 for i,it in enumerate(items,1):
  r={x.tag:(x.text or '').strip() for x in it}
  try:
   if not (83<=float(r['excluUseAr'])<85 and int(r['floor'])>=5):continue
  except (KeyError,ValueError):continue
  if r.get('cdealType') or r.get('cdealDay'):continue
  r.update(source_file=str(p),item_index=i);rows.append(r)
groups={}
for r in rows:groups.setdefault((r.get('umdNm'),r['aptNm']),[]).append(r)
result=[]
for (dong,name),rs in groups.items():
 vals=[int(r['dealAmount'].replace(',','')) for r in rs]
 result.append({'dong':dong,'name':name,'n':len(vals),'median_manwon':statistics.median(vals),'min_manwon':min(vals),'max_manwon':max(vals)})
result.sort(key=lambda r:(r['dong'],r['name']))
(out/'existing_prices_all.json').write_text(json.dumps({'period':'2026Q3','area':'83<=exclusive sqm<85','floor':'>=5','type':'매매/중개·직거래 포함','statistic':'median','unit':'만원','cancel':'cdealType OR cdealDay nonblank excluded','dedup':'no dedup: preserve distinct official items','checked_on':'2026-10-19','warning':'월별 수집시점은 sources.metadata; 이후해제 미반영 가능; 현재호가·현재전수 아님','sources':sources,'results':result},ensure_ascii=False,indent=2),encoding='utf-8')
keys=sorted(set().union(*(r.keys() for r in rows)))
with (out/'existing_price_rows.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
print(json.dumps(result,ensure_ascii=False))
