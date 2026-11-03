"""Compare selected tail cases with the survey index in the already acquired ZIP.

The two estimands differ. This is a sensitivity diagnostic, not a truth ranking,
not a replacement target, and not an additional forecast-model experiment.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re
from zipfile import ZipFile
import xml.etree.ElementTree as E
import pandas as pd
from diagnostics import OUT,save,sha,csv

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def cells(path):
    with ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(t.text or '' for t in si.findall('.//m:t',NS))
                    for si in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        root=E.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows={}
        for row in root.findall('m:sheetData/m:row',NS):
            values={}
            for c in row.findall('m:c',NS):
                v=c.find('m:v',NS)
                if c.get('t')=='inlineStr':value=''.join(t.text or '' for t in c.findall('.//m:t',NS))
                elif c.get('t')=='s':value=shared[int(v.text)] if v is not None else ''
                else:value=v.text if v is not None else ''
                values[re.sub(r'\d','',c.get('r'))]=value
            rows[int(row.get('r'))]=values
        return rows

def run():
    source=OUT.parent.parent/'research_notes/지역별 집값 예측 실패 진단/rental_data/rental_reb_monthly_2609.zip'
    member='02.주택_월간_아파트/01.매매가격지수/(월) 매매가격지수_아파트.xlsx'
    path=OUT/'official_sales_survey.xlsx'
    with ZipFile(source) as z:path.write_bytes(z.read(member))
    rows=cells(path);datecols={}
    for col,text in rows[4].items():
        match=re.search(r'(\d{4})\D*(\d{1,2})',text)
        if match and rows[5].get(col)=='지수' and rows[7].get(col)=='원자료':
            datecols[pd.Timestamp(f'{match[1]}-{int(match[2]):02d}-01')]=col
    if len(datecols)<200:raise ValueError('Unexpected official sheet header')
    cases=pd.read_csv(OUT/'worst_cases.csv',parse_dates=['origin'])
    comparison=[];unmatched=[]
    for case in cases.to_dict('records'):
        name=case['name'];tokens=name.split();area=tokens[-1]
        if tokens[0]=='세종':province=area='세종'
        else:province=tokens[0]
        matches=[(number,row) for number,row in rows.items()
                 if number>=8 and row.get('A')==province and row.get('D')==area]
        if len(matches)!=1:
            unmatched.append({'name':name,'origin':str(case['origin']),'matching_rows':len(matches)});continue
        number,row=matches[0]
        start=case['origin'].to_period('M').start_time;end=start+pd.DateOffset(months=6)
        if start not in datecols or end not in datecols:raise ValueError('Missing comparison month')
        first=row.get(datecols[start]);last=row.get(datecols[end])
        if not first or not last:
            unmatched.append({'name':name,'origin':str(case['origin']),'matching_rows':1,'missing_endpoint':True});continue
        change=(float(last)/float(first)-1)*100
        comparison.append({'level':case['level'],'name':name,'origin':case['origin'],
            'matched_trade_actual_pct':case['actual_pct'],'survey_actual_pct':change,
            'difference_pp':case['actual_pct']-change,'original_forecast_pct':case['prediction_pct'],
            'source_row':number,'start_cell':datecols[start]+str(number),'end_cell':datecols[end]+str(number),
            'source_hierarchy':' > '.join(row.get(col,'') for col in 'ABCD')})
    csv(pd.DataFrame(comparison),'target_crosscheck.csv')
    save(OUT/'target_crosscheck_manifest.json',{'zip_sha256':sha(source),'xlsx_sha256':sha(path),
         'source_member':member,'period_columns':len(datecols),'compared_cases':len(comparison),
         'selected_cases':'25 largest absolute baseline errors per administrative level',
         'comparison_is_tail_selected':True,'unmatched':unmatched,'target_replaced':False,
         'source_measure':'REB apartment sales SURVEY price index, original unadjusted series',
         'model_measure':'same complex/area matched trades; different estimand',
         'role':'measurement sensitivity only; no official index treated as universal ground truth'})
    print(pd.DataFrame(comparison).head(7).to_string(index=False))

if __name__=='__main__':run()
