import pathlib,json,re,sys,statistics,hashlib
p=pathlib.Path(__file__).parent;p.mkdir(exist_ok=True);ep=p.parent.parent;src=ep/'research/map-led-v5'
summary=[]
for name in ['w1_a1','w1_b17','w2_a1','w2_a3']:
 text=(src/(name+'_notice.txt')).read_text(encoding='utf-8');sections=[]
 for m in re.finditer(r'=== PAGE (\d+) ===',text):
  end=text.find('=== PAGE',m.end());s=text[m.end():end if end!=-1 else len(text)]
  for term in ['거주의무','전매제한','전매 제한','거주의무 안내','주택우선매입']:
   hits=list(re.finditer(term,s))
   if hits:sections.append({'page':int(m.group(1)),'term':term,'excerpts':[s[max(0,h.start()-90):h.start()+400]for h in hits[:3]]})
 summary.append({'id':name,'source_file':'research/map-led-v5/'+name+'_notice.pdf','sections':sections})
(p/'restriction_source_excerpts.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
v=json.loads((ep/'research/alternatives-v5/raw_verified_rows.json').read_text(encoding='utf-8'));groups=[]
for g in v['groups']:
 rows=[r for r in v['transactions']if r['name']==g['name']];prices=[r['price_manwon']for r in rows]
 if not rows:continue
 groups.append(dict(name=g['name'],n=len(rows),median_manwon=statistics.median(prices),minimum_manwon=min(prices),maximum_manwon=max(prices),area_min=min(r['area']for r in rows),area_max=max(r['area']for r in rows),floor_min=min(r['floor']for r in rows),date_min=min(r['date']for r in rows),date_max=max(r['date']for r in rows),source_basis='preserved MLIT raw XML collected2026-10-13; 2026Jul-Sep83<=area<85/floor>=5/cancel-excluded as recorded',rows=rows))
(p/'price_rows_rechecked.json').write_text(json.dumps({'groups':groups,'source_files':v['files'],'checked_on':'2026-10-15','limits':['No fresh MLIT API fetch; cancellation updates after collection unknown','Not spot asking price or valuation','Same 83<=area<85 range, exact area/build year/location differ']},ensure_ascii=False,indent=2),encoding='utf-8')
print([(g['name'],g['n'],g['median_manwon'])for g in groups])
