from pathlib import Path
import sys,json,re,csv,hashlib
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/stats_deps'))
import pandas as pd
O=Path(__file__).parent;C=O/'extracted';C.mkdir(exist_ok=True);inventory=[]
for name in ['completions_01.xlsx','completions_02.xlsx','starts_01.xlsx','permits_00.xlsx','unsold_00.xlsx','migration_2025.xlsx','census_2024.xls']:
 p=O/'raw'/name;x=pd.ExcelFile(p)
 for i,sh in enumerate(x.sheet_names):
  df=pd.read_excel(x,sheet_name=sh,header=None);out=f'{p.stem}_sheet{i:02}.csv';df.to_csv(C/out,index=False,header=False,encoding='utf-8-sig');inventory.append({'source':name,'sheet':sh,'rows':len(df),'columns':len(df.columns),'csv':out,'preview':df.head(5).fillna('').astype(str).values.tolist()})
 print(name,len(x.sheet_names),'sheets')
(O/'sheet_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf8')
s=(O/'raw/bok_base_rate.html').read_text(encoding='utf8')
# Read actual table rows, not commented chart code.
from html import unescape
rows=[]
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
 cells=[unescape(re.sub('<[^>]+>','',a)).strip() for a in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',tr,re.S)]
 if cells:rows.append(cells)
with (C/'bok_base_rate_table.csv').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
print('rate table rows',len(rows));print(rows[:5]);print('census sheets',[i['sheet'] for i in inventory if i['source']=='census_2024.xls'])
