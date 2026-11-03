"""Offline narrow presence check. No API, no credentials, no price statistics."""
import json
from pathlib import Path
import pyarrow.parquet as pq
import xml.etree.ElementTree as ET
BASE=Path(__file__).resolve().parents[4]
res={'checked_on':'2026-10-20','scope':'offline_presence_only','trade':[],'rent':[]}
cols=['apt_name_raw','sigungu_code','deal_date','area_m2','is_canceled']
d=pq.read_table(BASE/'master/trade_events.parquet',columns=cols).to_pandas()
for code,name,token in [('11710','잠실엘스','엘스'),('41117','광교자연앤힐스테이트','자연앤힐스테이트')]:
 s=d[(d.sigungu_code.astype(str)==code)&d.apt_name_raw.str.contains(token,regex=False,na=False)&(d.area_m2>=84)&(d.area_m2<85)]
 for ym in ['201601','202609']:
  t=s[s.deal_date.dt.strftime('%Y%m')==ym]
  res['trade'].append({'candidate':name,'month':ym,'source':'master/trade_events.parquet',
   'rows_including_cancelled':len(t),'cancel_flags':t.is_canceled.astype(str).value_counts().to_dict(),
   'area_m2_values':sorted(t.area_m2.unique().tolist()),'exact_names':t.apt_name_raw.unique().tolist()})
 p=BASE/'raw/rtms_rent/2026/08'/f'{code}_202608.xml'
 if p.exists():
  root=ET.parse(p).getroot(); rows=[]
  allrows=root.findall('.//item')
  for item in allrows:
   row={x.tag:(x.text or '').strip() for x in item}
   if token not in row.get('aptNm',''):continue
   try: area=float(row.get('excluUseAr',''))
   except ValueError:continue
   if 84<=area<85: rows.append({k:row.get(k) for k in ['aptNm','excluUseAr','dealYear','dealMonth','dealDay','deposit','monthlyRent','contractType']})
  res['rent'].append({'candidate':name,'month':'202608','source':str(p.relative_to(BASE)),
   'totalCount':root.findtext('.//totalCount'),'stored_rows':len(allrows),'matched_rows':rows,
   'note':'Stored source only; no live update. Different month from requested September.'})
res['limitations']=['84-85㎡ is an area band, not exact identical unit area.',
 'Presence only. No price statistics or long-run winner calculated.',
 'Existing master extraction timestamp and full source completeness not re-audited.']
p=Path(__file__).with_name('data_pilot_local_results.json');p.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'trade':res['trade'],'rent':[{'candidate':r['candidate'],'total':r['totalCount'],'stored':r['stored_rows'],'matched':len(r['matched_rows'])} for r in res['rent']]},ensure_ascii=False))
