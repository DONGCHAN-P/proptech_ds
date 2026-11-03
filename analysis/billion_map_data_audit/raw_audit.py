from pathlib import Path
import json,xml.etree.ElementTree as E,collections,pandas as pd
out=Path('analysis/billion_map_data_audit'); files=list(Path('raw/rtms_trade').rglob('*.xml')); rows=[]
for p in files:
 try:
  t=E.parse(p); n=len(t.findall('.//item')); total=int(t.findtext('.//totalCount') or n); rc=t.findtext('.//resultCode'); m=p.with_suffix('.meta.json'); meta=json.loads(m.read_text(encoding='utf8')) if m.exists() else {}
  rows.append({'path':str(p),'ym':p.stem.split('_')[-1],'code':p.stem.split('_')[0],'rows':n,'total':total,'truncated':n<total,'mock':meta.get('mock'),'result_code':rc})
 except Exception as e: rows.append({'path':str(p),'error':type(e).__name__})
r=pd.DataFrame(rows);r.to_csv(out/'raw_file_coverage.csv',index=False,encoding='utf-8-sig'); print('files',len(r),'bytes',sum(p.stat().st_size for p in files),'truncated',int(r.truncated.fillna(False).sum()),'mock',r.mock.value_counts(dropna=False).to_dict(),'errors',int(r.get('error',pd.Series(dtype=str)).notna().sum())); print(r[r.truncated.fillna(False)].head(8).to_string(index=False));print(r.assign(year=r.ym.str[:4]).groupby('year').agg(files=('path','size'),codes=('code','nunique'),rows=('rows','sum')).to_string())
summary={'files':len(r),'bytes':sum(p.stat().st_size for p in files),'truncated_files':int(r.truncated.fillna(False).sum()),'error_files':int(r.get('error',pd.Series(dtype=str)).notna().sum()),'mock_true_files':int(r.mock.eq(True).sum()),'mock_unknown_files':int(r.mock.isna().sum()),'distinct_codes':r.code.nunique(),'months':r.ym.nunique()};(out/'raw_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
