from pathlib import Path
import csv,re,json,sys
O=Path(__file__).parent;C=O/'extracted'
def read(n):return list(csv.reader((C/n).open(encoding='utf-8-sig')))
def write(n,h,rows):
 with (C/n).open('w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(h);w.writerows(rows)
rows=[]
for stem,kind in [('completions_01','completions'),('starts_01','starts'),('permits_00','permits')]:
 for p in sorted(C.glob(stem+'_sheet*.csv')):
  grid=read(p.name);y=re.search(r'[’\x27]?(\d{2})년',grid[0][0]);
  if not y:continue
  yr=int(y[1]);yr+=2000 if yr<50 else 1900
  for row in grid[3:]:
   region=row[0].strip() if row else ''
   if region not in ['서울','경기','인천','부산','대구','대전']:continue
   for month in range(1,13):
    try:v=float(row[month+1].replace(',',''))
    except (ValueError,IndexError):continue
    rows.append([kind,region,f'{yr}-{month:02}',v,p.name,'all_housing_not_apartments_only'])
write('supply_monthly_six_regions.csv',['measure','region','month','housing_units','source_grid','scope'],rows)
m=read('migration_2025_sheet03.csv');out=[];kind=''
for r in m[4:]:
 if r[0].strip():kind=r[0].strip()
 try:yr=int(float(r[1]))
 except (ValueError,IndexError):continue
 for j,reg in enumerate(m[2][2:],2):
  if reg.strip() not in ['서울','경기','인천','부산','대구','대전']:continue
  try:v=float(r[j].replace(',',''))
  except (ValueError,IndexError):continue
  out.append([kind,reg.strip(),yr,v])
write('migration_annual_six_regions.csv',['measure','region','year','persons'],out)
s=(O/'raw/bok_base_rate.html').read_text(encoding='utf8');s=re.sub(r'/\*.*?\*/','',s,flags=re.S);j=re.search(r'var\s+chartObj2_s\s*=\s*(\[.*?\]);',s,re.S)
if not j:raise ValueError('rate array not found')
r=json.loads(j[1].split(']]')[0]+']]');assert len(r)>20
write('bok_base_rate_changes.csv',['effective_date','base_rate_pct'],[[d.strip().replace('/','-'),v] for d,v in r])
print('supply',len(rows),'migration',len(out),'rate_changes',len(r))

