from pathlib import Path
import xml.etree.ElementTree as ET,json,statistics,hashlib
root=Path(__file__).parent
names=['다산롯데캐슬','별내푸르지오','별내자이더스타','진접삼부르네상스더퍼스트']
rows=[]; files=[]
for m in ['07','08','09']:
 p=Path(f'raw/rtms_trade/2026/{m}/41360_2026{m}.xml');files.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 for e in ET.parse(p).findall('.//item'):
  x={k.tag:(k.text or '').strip() for k in e}
  if x['aptNm'] in names and 83<=float(x['excluUseAr'])<85 and int(x['floor'])>=5 and not x.get('cdealDay') and x.get('cdealType') not in ['O','Y']:
   rows.append({'name':x['aptNm'],'area':float(x['excluUseAr']),'floor':int(x['floor']),'build_year':int(x['buildYear']),'price_manwon':int(x['dealAmount'].replace(',','')),'date':f"{x['dealYear']}-{int(x['dealMonth']):02d}-{int(x['dealDay']):02d}",'transaction_type':x.get('dealingGbn'),'source_file':str(p),'aptSeq':x.get('aptSeq')})
groups=[]
for name in names:
 r=[x for x in rows if x['name']==name]
 groups.append({'name':name,'n':len(r),'median_manwon':statistics.median(x['price_manwon'] for x in r) if r else None,'range_manwon':[min(x['price_manwon'] for x in r),max(x['price_manwon'] for x in r)] if r else [],'build_year':r[0]['build_year'] if r else None,'dates':[min(x['date'] for x in r),max(x['date'] for x in r)] if r else []})
(root/'raw_verified_rows.json').write_text(json.dumps({'files':files,'groups':groups,'transactions':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(groups,ensure_ascii=True))
