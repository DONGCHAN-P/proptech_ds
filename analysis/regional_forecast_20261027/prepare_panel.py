"""Build an isolated monthly matched-cell panel from immutable local inputs."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import duckdb
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from forecast import matched_changes

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
DATA=OUT/'data'
DATA.mkdir(exist_ok=True)
REGIONS={'11':'서울','26':'부산','27':'대구','28':'인천','29':'광주','30':'대전',
         '31':'울산','36':'세종','41':'경기','43':'충북','44':'충남'}
GROUPS={'gwangju':'29','ulsan':'31','chungbuk':'43','chungnam':'44'}
GJ={'12210':'29110','12240':'29140','12270':'29155','12300':'29170','12330':'29200'}
# Stable aggregates avoid forecasting boundary-code jumps as market moves.
ALIASES={**GJ,**{x:'41190' for x in ['41192','41194','41196']},
         **{x:'41590' for x in ['41591','41593','41595','41597']},
         **{x:'28100' for x in ['28110','28140','28125','28155']},
         **{x:'28260' for x in ['28275','28290']},
         **{x:'43110' for x in ['43111','43112','43113','43114','43710']},
         **{x:'44130' for x in ['44131','44133']},'44830':'44270'}
SPECIAL_NAMES={'41190':'부천시','41590':'화성시','28100':'옛 중·동구 통합권',
               '28260':'옛 서구 통합권','43110':'청주·청원 통합권','44130':'천안시','44270':'당진시'}

def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n','utf-8')

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def normalize_extra():
    base=ROOT/'raw/rtms_trade_expansion/additional_20261023'
    status=json.loads((base/'batch_status.json').read_text('utf-8'))
    paths=[]
    for group,region in GROUPS.items():
        if group not in status.get('finished_groups',[]):
            continue
        dest=DATA/f'additional_{group}.parquet'
        meta=DATA/f'additional_{group}_sources.json'
        if dest.exists() and meta.exists():
            paths.append(dest)
            continue
        rows=[]
        sources=[]
        skipped_alias_rows=0
        for mp in sorted((base/group).glob('*/*.meta.json')):
            m=json.loads(mp.read_text('utf-8'))
            if not m.get('complete') or m.get('stored_rows')!=m.get('totalCount'):
                continue
            prefix=mp.name.removesuffix('.meta.json')
            files=sorted(mp.parent.glob(prefix+'.page*.xml'))
            if not files:
                raise ValueError(f'Missing complete page {mp}')
            n=0
            for path in files:
                content=path.read_bytes()
                sources.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(content).hexdigest()})
                tree=ET.fromstring(content)
                if tree.findtext('.//resultCode') not in ('000','00','0'):
                    raise ValueError(f'Bad API result {path}')
                for item in tree.findall('.//items/item'):
                    n+=1
                    v={child.tag:(child.text or '').strip() for child in item}
                    code=v.get('sggCd') or prefix
                    if code=='44730':
                        skipped_alias_rows+=1
                        continue  # Yeongi cannot be assigned to today's Chungnam without parcel crosswalk.
                    date=pd.Timestamp(year=int(v['dealYear']),month=int(v['dealMonth']),day=int(v['dealDay']))
                    area=float(v['excluUseAr'])
                    amount=int(v['dealAmount'].replace(',',''))
                    apt=v.get('aptSeq') or '|'.join([code,v.get('umdNm',''),v.get('jibun',''),v.get('aptNm',''),v.get('buildYear','')])
                    key='|'.join([apt,str(date.date()),str(area),str(amount),v.get('floor',''),v.get('aptDong','')])
                    rows.append({'apt_id':'api:'+apt,'sigungu_code':code,'sigungu_name':v.get('estateAgentSggNm',''),
                                 'deal_date':date,'area_m2':area,'deal_amount':amount,
                                 'is_canceled':v.get('cdealType','').upper() in ('O','Y','1') or bool(v.get('cdealDay')),
                                 'deal_hash':hashlib.sha256(key.encode()).hexdigest()})
            if n!=int(m['stored_rows']):
                raise ValueError(f'Incomplete page set {mp}: {n} != {m["stored_rows"]}')
        df=pd.DataFrame(rows)
        df['is_canceled']=df.groupby('deal_hash').is_canceled.transform('max')
        before=len(df)
        df=df.drop_duplicates('deal_hash')
        df.to_parquet(dest,index=False)
        save(meta,{'group':group,'rows':len(df),'duplicate_rows_removed':before-len(df),
                   'excluded_yeongi_rows':skipped_alias_rows,'source_files':sources,'parquet_sha256':sha(dest)})
        print(f'{group}: {len(df):,} normalized, {before-len(df):,} duplicate rows removed',flush=True)
        paths.append(dest)
        del df,rows
    return paths

def main():
    extra=normalize_extra()
    sources=[ROOT/'master/trade_events.parquet',
             ROOT/'analysis/housing_growth_2006/regional_expansion_v1/expansion_normalized.parquet',*extra]
    manifest=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources]
    save(OUT/'input_manifest.json',{'inputs':manifest,'boundary_aliases':ALIASES,
          'excluded_codes':['27720','47720','44730'],'sejong_start':'2013-01',
          'last_input_month':'2026-09','common_asof_buffer_months':3,
          'vintage_status':'revised_snapshot_with_assumed_reporting_buffer_not_true_realtime'})
    con=duckdb.connect()
    con.execute("SET threads=4")
    selects=[]
    for path in sources:
        selects.append(f"SELECT apt_id, sigungu_code, deal_date, area_m2, deal_amount, is_canceled, deal_hash FROM read_parquet('{path.as_posix()}')")
    alias_sql='CASE sigungu_code '+' '.join(f"WHEN '{k}' THEN '{v}'" for k,v in ALIASES.items())+' ELSE sigungu_code END'
    con.execute('CREATE TEMP VIEW source AS '+' UNION ALL '.join(selects))
    con.execute(f"""CREATE TEMP VIEW valid AS
       SELECT * EXCLUDE (sigungu_code), {alias_sql} AS district_code,
              substr({alias_sql},1,2) AS region_code,
              date_trunc('month',deal_date)::DATE AS month,
              round(area_m2,2) AS area_key, deal_amount/area_m2 AS ppm
       FROM source WHERE NOT coalesce(is_canceled,false) AND deal_amount>0
       AND area_m2 BETWEEN 10 AND 330 AND apt_id IS NOT NULL
       AND deal_date >= DATE '2006-01-01' AND deal_date < DATE '2026-10-01'
       AND sigungu_code NOT IN ('27720','47720','44730')
       AND (substr(sigungu_code,1,2)!='36' OR deal_date >= DATE '2013-01-01')
       QUALIFY row_number() OVER(PARTITION BY deal_hash ORDER BY deal_date)=1""")
    coverage=con.sql("""SELECT region_code,district_code,count(*) transactions,
                        min(deal_date) first_date,max(deal_date) last_date,
                        count(DISTINCT apt_id) complexes FROM valid GROUP BY 1,2 ORDER BY 1,2""").df()
    coverage.to_csv(OUT/'coverage.csv',index=False,encoding='utf-8-sig')
    # Province and district panels are kept separate during evaluation, not independent replicates.
    con.execute("CREATE TEMP VIEW expanded AS SELECT 'p:'||region_code series_id,* FROM valid UNION ALL SELECT 'd:'||district_code series_id,* FROM valid")
    cells=con.sql("SELECT series_id,month,apt_id,area_key,median(ppm) ppm FROM expanded GROUP BY 1,2,3,4").df()
    cells['month']=pd.to_datetime(cells.month)
    print(f'Matching {len(cells):,} complex-area-month cells',flush=True)
    changes=matched_changes(cells,min_complexes=5)
    stats=con.sql("""SELECT series_id,month,any_value(region_code) region_code,any_value(district_code) district_code,
                      count(*) volume,median(ppm) median_ppm,
                      median(area_m2) median_area FROM expanded GROUP BY 1,2""").df()
    stats['month']=pd.to_datetime(stats.month)
    stats.loc[stats.series_id.str.startswith('p:'),'district_code']=stats.region_code
    panel=stats.merge(changes,on=['series_id','month'],how='left',validate='one_to_one')
    grids=[]
    for sid,g in panel.groupby('series_id'):
        full=pd.date_range(g.month.min(),'2026-09-01',freq='MS')
        s=g.set_index('month').reindex(full).rename_axis('month').reset_index()
        s['series_id']=sid
        s['region_code']=g.region_code.iloc[0]
        s['district_code']=g.district_code.iloc[0]
        s['volume']=s.volume.fillna(0)
        grids.append(s)
    panel=pd.concat(grids,ignore_index=True).sort_values(['series_id','month'])
    names={}
    admin=json.loads((ROOT/'raw/rtms_trade_expansion/admin_codes_20261023/district_codes.json').read_text('utf-8'))
    for row in admin:
        code=ALIASES.get(row['code'],row['code'])
        names[code]=row['fields'][2]
    # Production master names are useful for older district codes absent in current registry.
    old=con.sql(f"SELECT sigungu_code,any_value(sigungu_name) n FROM read_parquet('{sources[0].as_posix()}') GROUP BY 1").df()
    names.update({k:v for k,v in zip(old.sigungu_code,old.n) if isinstance(v,str) and v})
    names.update(SPECIAL_NAMES)
    panel['region_name']=panel.region_code.map(REGIONS)
    panel['name']=[REGIONS.get(r,r) if sid.startswith('p:') else REGIONS.get(r,r)+' '+(names.get(d) or d)
                   for sid,r,d in zip(panel.series_id,panel.region_code,panel.district_code)]
    if panel.region_name.isna().any():
        raise ValueError('Unmapped region; review crosswalk')
    panel.to_parquet(DATA/'monthly_panel.parquet',index=False)
    audit={'valid_transactions':int(coverage.transactions.sum()),'regions':coverage.region_code.nunique(),
           'district_series':int(coverage.district_code.nunique()),'monthly_rows':len(panel),
           'supported_months':int(panel.log_change.notna().sum()),'matched_cell_count':len(cells),
           'matching_min_complexes':5,'change_estimator':'10pct_trimmed_mean_log_returns_equal_complex_weight',
           'panel_sha256':sha(DATA/'monthly_panel.parquet'),
           'floor_and_renovation_uncontrolled':True,'snapshot_vintage_limitation':True}
    save(OUT/'panel_audit.json',audit)
    print(json.dumps(audit,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    main()
