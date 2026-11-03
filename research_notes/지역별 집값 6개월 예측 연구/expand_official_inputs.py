"""Supplemental key-free downloads and extraction; no transaction parsing."""
from collect_official_inputs import *
import zipfile, xml.etree.ElementTree as ET, io, html

def book(path):
    z=zipfile.ZipFile(path);ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
    rels={x.attrib['Id']:x.attrib['Target'] for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for sh in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns):
        rid=sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'];target=rels[rid];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        cells={}
        for c in ET.fromstring(z.read(target)).findall('.//s:sheetData/s:row/s:c',ns):
            v=c.find('s:v',ns);value=v.text if v is not None else ''
            if c.attrib.get('t')=='s':value=strings[int(value)] if value else ''
            elif c.attrib.get('t')=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
            cells[c.attrib['r']]=value or ''
        yield sh.attrib['name'],cells

def download_extras():
    jobs=[('employment_202609_xlsx','https://mods.go.kr/boardDownload.es?bid=210&list_no=447479&seq=4','employment_202609.xlsx')]
    for y,endmo in [(2008,12),(2026,9)]:
        params=dict(searchYearMonth='month',xlsStats='1',sltOrgType='1',sltOrgLvl1='A',sltOrgLvl2='',gender='gender',genderPer='genderPer',generation='generation',sltUndefType='',searchYearStart=str(y),searchMonthStart='01',searchYearEnd=str(y),searchMonthEnd=f'{endmo:02}',sltOrderType='1',sltOrderValue='ASC',category='month')
        jobs.append((f'mois_population_{y}','https://jumin.mois.go.kr/downloadCsv.do?'+urllib.parse.urlencode(params),f'mois_population_{y}.csv'))
    # Public ECOS demonstration endpoint, inspected once; never reads user credentials.
    jobs.append(('ecos_sample_mortgage_probe','https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/121Y006/M/200601/200610/BECBLA03','ecos_sample_mortgage_probe.json'))
    jobs.append(('bok_rate_press_list','https://www.bok.or.kr/portal/bbs/B0000501/list.do?menuNo=201264&searchCnd=1&searchKwd='+urllib.parse.quote('금융기관 가중평균금리'),'bok_rate_press_list.html'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        for e in pool.map(fetch,jobs):save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')),flush=True)

def inspect():
    p=OLD/'raw/unsold_00.xlsx'
    for sn,c in book(p):
        print('UNSOLD',sn)
        for row in sorted({int(re.search(r'\d+',k)[0]) for k in c}):
            line=[f'{col}{row}={c.get(f"{col}{row}","")}' for col in ['A','B','C','D','E','F']]
            if any(x.split('=',1)[1] for x in line):print(' | '.join(line))
            if row>120:break
        break
    p=OUT/'employment_202609.xlsx'
    if p.exists():
        for sn,c in book(p):
            print('EMPLOYMENT',sn,[(k,v) for k,v in c.items() if v][:10])
    for y in [2008,2026]:
        p=OUT/f'mois_population_{y}.csv'
        if p.exists():
            b=p.read_bytes()
            for enc in ['utf-8-sig','cp949']:
                try:s=b.decode(enc);break
                except UnicodeDecodeError:pass
            print('MOIS',y,s[:800])

def fetch_history():
    jobs=[]
    for y in range(2009,2026):
        params=dict(searchYearMonth='month',xlsStats='1',sltOrgType='1',sltOrgLvl1='A',sltOrgLvl2='',gender='gender',genderPer='genderPer',generation='generation',sltUndefType='',searchYearStart=str(y),searchMonthStart='01',searchYearEnd=str(y),searchMonthEnd='12',sltOrderType='1',sltOrderValue='ASC',category='month')
        jobs.append((f'mois_population_{y}','https://jumin.mois.go.kr/downloadCsv.do?'+urllib.parse.urlencode(params),f'mois_population_{y}.csv'))
    jobs += [('ecos_lending_items','https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/1/100/121Y006','ecos_lending_items.json'),('ecos_lending_table_metadata','https://ecos.bok.or.kr/api/StatisticTableList/sample/json/kr/1/10/121Y006','ecos_lending_table_metadata.json')]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for e in pool.map(fetch,jobs):save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')),flush=True)

def fetch_definitions():
    jobs=[('ecos_lending_items_10','https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/1/10/121Y006','ecos_lending_items_10.json'),('ecos_mortgage_definition','https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/121Y006/M/200601/200610/BECBLA0302','ecos_mortgage_definition.json'),('mois_migration_page','https://jumin.mois.go.kr/etcStatMove.do','mois_migration_page.html')]
    for e in map(fetch,jobs):save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')),flush=True)

def fetch_mortgage():
    definition=json.loads((OUT/'ecos_mortgage_definition.json').read_text(encoding='utf-8'))['StatisticSearch']['row'][0]
    assert definition['ITEM_NAME1']=='주택담보대출'
    months=[f'{y}{m:02}' for y in range(2006,2027) for m in range(1,13) if f'{y}{m:02}'<='202608']
    jobs=[]
    for i in range(0,len(months),10):
        a,b=months[i],months[min(i+9,len(months)-1)]
        jobs.append((f'ecos_mortgage_{a}_{b}',f'https://ecos.bok.or.kr/api/StatisticSearch/sample/json/kr/1/10/121Y006/M/{a}/{b}/BECBLA0302',f'ecos_mortgage_{a}_{b}.json'))
    jobs += [('ecos_mortgage_items_21_30','https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/21/30/121Y006','ecos_mortgage_items_21_30.json')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for e in pool.map(fetch,jobs):save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')),flush=True)

def fetch_migration_release():
    s=(OUT/'migration_202608_page.html').read_text(encoding='utf-8')
    links=re.findall(r'<a class="bvf_name" href="([^"]+)">([^<]+)</a>',s)
    path,name=next((path,name) for path,name in links if name.endswith('.hwpx'))
    e=fetch(('migration_202608_hwpx',urllib.parse.urljoin('https://mods.go.kr/',html.unescape(path)),'migration_202608.hwpx'));save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')))

def migration_tables():
    import sys;sys.stdout.reconfigure(encoding='utf-8')
    p=OUT/'migration_202608.hwpx';z=zipfile.ZipFile(p);tables=[]
    for name in z.namelist():
        if not re.fullmatch(r'Contents/section\d+.xml',name):continue
        root=ET.fromstring(z.read(name))
        for table in root.iter():
            if table.tag.rsplit('}',1)[-1]!='tbl':continue
            rows=[]
            for tr in table:
                if tr.tag.rsplit('}',1)[-1]!='tr':continue
                row=[]
                for tc in tr:
                    if tc.tag.rsplit('}',1)[-1]!='tc':continue
                    row.append(' '.join(t.text or '' for t in tc.iter() if t.tag.rsplit('}',1)[-1]=='t'))
                rows.append(row)
            tables.append({'section':name,'table_index':len(tables),'rows':rows})
    write_json(OUT/'migration_202608_tables.json',tables)
    for t in tables:
        s=str(t['rows'])
        if '전입' in s and '전출' in s and ('서울' in s or '서 울' in s):print(t['table_index'],s[:6500])

def base_row(code,month,var,value,unit,sid,locator,scope,lag=45,actual=None,flag=''):
    return dict(region_code=code,month=month,variable=var,value=value,available_date=actual or assumed(month,lag),availability_basis='verified_official_release_page_date' if actual else f'assumed_month_end_plus_{lag}_calendar_days_not_verified_release',region_name={v:k for k,v in REGIONS.items()}.get(code,'전국' if code=='00' else '전남광주통합특별시'),unit=unit,scope=scope,source_id=sid,source_locator=locator,vintage_date=ASOF,vintage_basis='retrieval_date_latest_revised_not_historical_vintage',quality_flag=flag)

def normalize_mortgage():
    rows=[]
    for p in sorted(OUT.glob('ecos_mortgage_20*.json')):
        if not re.fullmatch(r'ecos_mortgage_\d{6}_\d{6}.json',p.name):continue
        j=json.loads(p.read_text(encoding='utf-8'));data=j.get('StatisticSearch',{}).get('row',[])
        assert data and len(data)<=10,(p.name,j)
        for r in data:
            assert r['ITEM_NAME1']=='주택담보대출' and r['ITEM_CODE1']=='BECBLA0302'
            month=r['TIME'][:4]+'-'+r['TIME'][4:]
            rows.append(base_row('00',month,'mortgage_rate_new_business_pct',r['DATA_VALUE'],'percent_per_annum',p.stem,f'121Y006/BECBLA0302/M/{r["TIME"]}','national_deposit_banks_new_business_mortgage'))
    assert len({r['month'] for r in rows})==len(rows)==248
    write_csv('bok_mortgage_rate_monthly.csv',rows);return rows

def normalize_households():
    rows=[];skipped=[]
    for p in sorted(OUT.glob('mois_population_20*.csv')):
        data=list(csv.reader(p.open(encoding='cp949')));header=data[0]
        assert len(data)>15 and '총인구수' in header[1]
        for raw in data[1:]:
            match=re.search(r'\((\d{10})\)',raw[0]);assert match,raw[0]
            src_code=match[1];code={'10':'00','51':'42','52':'45'}.get(src_code[:2],src_code[:2])
            assert code in set(REGIONS.values())|{'00','12'},code
            for i,h in enumerate(header):
                match=re.fullmatch(r'(\d{4})년(\d{2})월_(총인구수|세대수)',h)
                if not match:continue
                month=f'{match[1]}-{match[2]}'
                val=raw[i].replace(',','').strip()
                if not val or val=='-':continue
                value=int(val)
                if value==0:
                    skipped.append({'source':p.name,'source_region':raw[0],'month':month,'field':match[3],'reason':'zero_in_absent_geography_not_treated_as_observed_zero'});continue
                variable='resident_registered_population' if match[3]=='총인구수' else 'resident_registered_households'
                flag='definition_break_2010_10_and_2015_01;historical_boundaries_not_harmonized'
                if code=='12':flag+=';combined_jeonnam_gwangju_do_not_map_to_29_or_46'
                # Day 10 is a conservative proxy for next business day, including holidays.
                rows.append(base_row(code,month,variable,value,'persons' if match[3]=='총인구수' else 'registered_households',p.stem,raw[0]+';'+h,'registered_korean_nationals_foreigners_excluded',lag=10,flag=flag))
    write_csv('mois_population_households_monthly.csv',rows);write_json(OUT/'mois_geography_missing.json',skipped);return rows

def col_num(s):
    v=0
    for ch in s:v=v*26+ord(ch)-64
    return v
def col_name(n):
    s=''
    while n:n,r=divmod(n-1,26);s=chr(65+r)+s
    return s

def normalize_unsold():
    p=OLD/'raw/unsold_00.xlsx'
    original=next(r for r in json.loads((OLD/'collection_manifest.json').read_text(encoding='utf-8')) if r['name']==p.name)
    save_entry(dict(original,id='molit_unsold_existing_202608',status='reused_existing',local_original=str(p),sha256=digest(p.read_bytes())))
    rows=[];checks=[]
    for sn,c in book(p):
        if sn.startswith('총괄'):header_row=12;firstrow=15;lastrow=32;var='unsold_housing_total'
        else:continue
        # The source has numeric October labels rounded to .1; require all 116 ordered
        # monthly positions 2017-01..2026-08 to match their expected raw numeric label.
        start=next(col_num(re.match('[A-Z]+',k)[0]) for k,v in c.items() if re.fullmatch('[A-Z]+'+str(header_row),k) and v and re.fullmatch(r'[\d.]+',v.strip()) and abs(float(v.strip().strip('.'))-17.1)<1e-7)
        months=[f'{y}-{m:02}' for y in range(2017,2027) for m in range(1,13) if f'{y}-{m:02}'<='2026-08']
        for i,month in enumerate(months):
            col=col_name(start+i);label=c.get(f'{col}{header_row}','').strip().strip('.')
            # Text and numeric representations both occur; equality is numeric here,
            # anchored by all adjacent labels and independently known terminal month.
            expected=f'{int(month[:4])%100}.{int(month[5:])}'
            assert abs(float(label)-float(expected))<1e-7,(sn,col,label,expected)
        checks.append(dict(sheet=sn,header_row=header_row,first_month='2017-01',last_month='2026-08',positions_validated=len(months),mapping='anchored_contiguous_month_sequence_with_every_numeric_label_checked'))
        for row in range(firstrow,lastrow+1):
            region=re.sub(r'\s+','',c.get(f'A{row}',''))
            if region not in REGIONS:continue
            for i,month in enumerate(months):
                col=col_name(start+i);value=c.get(f'{col}{row}','').replace(',','').strip()
                try:value=float(value)
                except ValueError:continue
                rows.append(base_row(REGIONS[region],month,var,value,'housing_units','molit_unsold_existing_202608',f'{sn}!{col}{row};month_header={col}{header_row}','all_reported_unsold_housing_not_apartment_only',flag='date_mapping_validated_contiguous_sequence;latest_revised_vintage'))
    # Completed-unsold is a single-month district table, not the long monthly grid.
    # Read the explicitly dated existing workbook vintages separately.
    for source in json.loads((OLD/'collection_manifest.json').read_text(encoding='utf-8')):
        if not source['name'].startswith('unsold_') or not source['name'].endswith('.xlsx'):continue
        ma=re.search(r'\((\d{4})년(\d{1,2})월말\)',source.get('original_name',''))
        if not ma:continue
        month=f'{ma[1]}-{int(ma[2]):02}';path=OLD/'raw'/source['name'];sid=path.stem
        save_entry(dict(source,id=sid,status='reused_existing',local_original=str(path),sha256=digest(path.read_bytes())))
        for sn,c in book(path):
            if not sn.startswith('공사완료후'):continue
            for row in range(5,max(int(re.search(r'\d+',k)[0]) for k in c)+1):
                region=re.sub(r'\s+','',c.get(f'A{row}',''))
                if region not in REGIONS or c.get(f'B{row}','').strip()!='계':continue
                val=c.get(f'C{row}','').replace(',','').strip()
                try:value=float(val)
                except ValueError:continue
                rows.append(base_row(REGIONS[region],month,'unsold_housing_completed',value,'housing_units',sid,f'{sn}!C{row}','all_reported_completed_unsold_housing_not_apartment_only',flag='workbook_reference_month_verified_from_original_filename'))
    assert rows
    write_csv('molit_unsold_monthly.csv',rows);write_json(OUT/'unsold_header_validation.json',checks);return rows

def normalize_employment():
    rows=[]
    for sn,c in book(OUT/'employment_202609.xlsx'):
        if not sn.startswith('13.'):continue
        for row in range(18,38):
            region=re.sub('[‧\\s]+','',c.get(f'A{row}','') or c.get(f'B{row}',''))
            if region not in REGIONS:continue
            for col,var,unit in [('E','employed_residents_thousand','thousand_persons'),('I','employment_rate_15plus_pct','percent'),('J','unemployment_rate_pct','percent')]:
                value=c.get(f'{col}{row}','')
                if not value:continue
                rows.append(base_row(REGIONS[region],'2026-09',var,round(float(value),1),unit,'employment_202609_xlsx',f'{sn}!{col}{row}','resident_based_economically_active_population_survey_not_workplace_jobs',actual='2026-10-16'))
    assert len(rows)==51,len(rows)
    write_csv('employment_regional_202609.csv',rows);return rows

def normalize_migration():
    tables=json.loads((OUT/'migration_202608_tables.json').read_text(encoding='utf-8'));rows=[]
    codes=['00','11','12','29','46','26','27','28','30','31','36','41','42','43','44','45','47','48','50']
    for ti,var in [(18,'net_migration_thousand'),(19,'migration_inflow_thousand'),(20,'migration_outflow_thousand')]:
        year=None;n=0
        for rn,raw in enumerate(tables[ti]['rows']):
            if len(raw) not in (20,21):continue
            offset=1 if len(raw)==21 else 0
            label=raw[offset].strip();ma=re.fullmatch(r'(?:(\d{4})\.\s*)?(\d{1,2})월',label)
            if not ma:continue
            if ma[1]:year=int(ma[1])
            assert year is not None
            month=f'{year}-{int(ma[2]):02}';values=raw[offset+1:];assert len(values)==19
            for code,val in zip(codes,values):
                try:value=float(val.replace(',',''))
                except ValueError:continue
                rows.append(base_row(code,month,var,value,'thousand_persons','migration_202608_hwpx',f'table={ti};row={rn};region_code={code}','domestic_migration_registration_report_rounded_thousand',actual='2026-09-23' if month=='2026-08' else None,flag='rounded_source_not_exact_person_counts;latest_revised_vintage;combined_code12_not_additive_with_29_and_46'))
            n+=1
        assert n==25,(ti,n)
    # Exact current-month regional persons table; keep distinct variable/unit names.
    for rn,raw in enumerate(tables[16]['rows']):
        name=re.sub(r'\s+','',raw[0]) if raw else ''
        code=REGIONS.get(name,{'전국':'00','전남광주':'12'}.get(name))
        if not code or len(raw)<4:continue
        values=[int(x.replace(',','').strip()) for x in raw[1:4]]
        assert values[0]-values[1]==values[2],raw
        for variable,value in zip(['migration_inflow_persons','migration_outflow_persons','net_migration_persons'],values):
            rows.append(base_row(code,'2026-08',variable,value,'persons','migration_202608_hwpx',f'table=16;row={rn}','domestic_migration_registration_report',actual='2026-09-23',flag='combined_code12_not_additive_with_29_and_46'))
    assert len(rows)==1482,len(rows)
    write_csv('migration_regional_monthly.csv',rows);return rows

def normalize_all():
    import sys;sys.stdout.reconfigure(encoding='utf-8')
    groups=[supply(),rates(),normalize_mortgage(),normalize_households(),normalize_unsold(),normalize_employment(),normalize_migration()]
    allrows=sorted(sum(groups,[]),key=lambda r:(r['region_code'],r['month'],r['variable']))
    assert len({(r['region_code'],r['month'],r['variable']) for r in allrows})==len(allrows)
    write_csv('monthly_exogenous.csv',allrows)
    write_json(OUT/'coverage_summary.json',[dict(variable=v,rows=len(rs),regions=sorted({r['region_code'] for r in rs}),first_month=min(r['month'] for r in rs),last_month=max(r['month'] for r in rs)) for v in sorted({r['variable'] for r in allrows}) for rs in [[r for r in allrows if r['variable']==v]]])
    print('group_rows',[len(g) for g in groups],'total',len(allrows))

def inspect_targeted():
    import sys;sys.stdout.reconfigure(encoding='utf-8')
    p=OUT/'ecos_lending_items.json'
    if p.exists():print(p.read_text(encoding='utf-8')[:13000])
    for sn,c in book(OUT/'employment_202609.xlsx'):
        if not sn.startswith('13.'):continue
        for row in range(1,40):print('EMP',row,' | '.join(f'{col}={c.get(f"{col}{row}","")}' for col in 'ABCDEFGHIJKL'))
    for y in [2008,2026]:
        rows=list(csv.reader((OUT/f'mois_population_{y}.csv').open(encoding='cp949')))
        print('MOIS',y,'rows',len(rows),'cols',len(rows[0]),'regions',[(r[0],r[1:3]) for r in rows[1:]])

if __name__=='__main__':
    import sys
    if sys.argv[1]=='fetch':download_extras()
    elif sys.argv[1]=='inspect':inspect()
    elif sys.argv[1]=='history':fetch_history()
    elif sys.argv[1]=='targeted':inspect_targeted()
    elif sys.argv[1]=='definitions':fetch_definitions()
    elif sys.argv[1]=='mortgage':fetch_mortgage()
    elif sys.argv[1]=='normalize':normalize_all()
    elif sys.argv[1]=='migration_fetch':fetch_migration_release()
    elif sys.argv[1]=='migration_tables':migration_tables()
