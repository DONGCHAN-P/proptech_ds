"""Bounded MOLIT 2026 supplement. Writes only beside this helper.

Requires requests and xlrd; supports a folder-local _vendor installation.
No credentials, transactions, model changes, or historical-source rewrites.
"""
from pathlib import Path
import csv, hashlib, json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '_vendor'))
import requests

ASOF = '2026-10-27'
BASE = 'https://stat.molit.go.kr'
KINDS = {'completions': (468, 'housing_completions_all'),
         'starts': (471, 'housing_starts_all'),
         'permits': (31, 'housing_permits_all')}
REGIONS = {'서울':'11','부산':'26','대구':'27','인천':'28','광주':'29',
           '대전':'30','울산':'31','세종':'36','경기':'41','강원':'42',
           '충북':'43','충남':'44','전북':'45','전남':'46','경북':'47',
           '경남':'48','제주':'50','전국':'00','전남광주':'12'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(name, obj):
    (ROOT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def fetch(url, path):
    """Reuse saved raw input; never silently replace its bytes."""
    if not path.exists():
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=25)
        r.raise_for_status()
        path.write_bytes(r.content)
    return {'path':path.relative_to(ROOT).as_posix(),'source_url':url,
            'bytes':path.stat().st_size,'sha256':sha(path),'retrieved_asof':ASOF}

def download():
    raw = ROOT/'raw'; raw.mkdir(exist_ok=True)
    manifest=[]; jobs=[]
    for kind, (rid, _) in KINDS.items():
        url=f'{BASE}/portal/cate/statMetaView.do?hRsId={rid}'
        p=raw/f'metadata_{kind}.html'
        item=fetch(url,p);item.update(kind='official_metadata',source_id=kind);manifest.append(item)
        html=p.read_text(encoding='utf8')
        links=re.findall(r"downFile\('([^']*)','([^']*)','([^']*)','[^']*'\)",html)
        selected=[]
        for orig, remote, mid in links:
            m=re.match(r'26년\s+(\d{2})월', orig)
            if m and orig.lower().endswith('.xls'):
                month=int(m[1])
                if 1 <= month <= 8:
                    selected.append((month,orig,remote,mid))
        assert len(selected)==8,(kind,selected)
        for month,orig,remote,mid in selected:
            url=BASE+'/portal/common/downLoadFile.do?'+urlencode(dict(oFileName=orig,rFileName=remote,midpath=mid))
            jobs.append((kind,month,orig,url,raw/f'{kind}_2026{month:02}.xls'))
    def one(job):
        kind,month,orig,url,path=job
        item=fetch(url,path)
        assert path.read_bytes().startswith(bytes.fromhex('d0cf11e0a1b11ae1')),f'Not XLS: {path}'
        item.update(kind='official_monthly_workbook',source_id=kind,month=f'2026-{month:02}',original_name=orig)
        return item
    errors=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(one,j):j for j in jobs}
        for f in as_completed(tasks):
            try:
                item=f.result();manifest.append(item)
                print('saved',item['path'],item['bytes'],flush=True)
            except Exception as e:
                errors.append({'job':str(tasks[f][0:3]),'error':str(e)})
            write_json('raw_manifest.json',sorted(manifest,key=lambda r:r['path']))
            write_json('status.json',{'status':'collecting_raw','asof':ASOF,'workbooks_saved':sum(x['kind']=='official_monthly_workbook' for x in manifest),'errors':errors})
    return manifest,errors

def inspect():
    import xlrd
    output={}
    for kind in KINDS:
        b=xlrd.open_workbook(ROOT/'raw'/f'{kind}_202608.xls')
        output[kind]={'sheets':b.sheet_names(),'samples':[
            {'sheet':s.name,'rows':[s.row_values(i) for i in range(min(s.nrows,12))]}
            for s in b.sheets()[:3]]}
    write_json('workbook_structure.json',output)
    print('Saved workbook_structure.json')
    p=ROOT/'raw'/'official_release_index_p1.html'
    fetch(BASE+'/portal/notice/colmnList.do?hNum=1394',p)
    html=p.read_text(encoding='utf8')
    print('Saved official_release_index_p1.html')

def release_dates():
    from bs4 import BeautifulSoup
    releases={};sources=[]
    # The site's goPage(page_no) explicitly uses this parameter; two pages only.
    for page in (1,2):
        url=BASE+f'/portal/notice/colmnList.do?hNum=1394&page_no={page}'
        p=ROOT/'raw'/f'official_release_index_p{page}.html'
        item=fetch(url,p); item['kind']='official_release_date_index';sources.append(item)
        soup=BeautifulSoup(p.read_text(encoding='utf8'),'html.parser')
        for tr in soup.select('tr'):
            a=tr.find('a',href=True)
            if not a:continue
            title=a.get_text(' ',strip=True)
            m=re.search(r'26[년.]\s*(\d{1,2})월\s*주택통계',title)
            if not m:continue
            dates=re.findall(r'2026-\d{2}-\d{2}',tr.get_text(' ',strip=True))
            if not dates:continue
            month=f'2026-{int(m[1]):02}'
            releases[month]={'release_date':dates[-1],'title':title,
                             'release_url':a['href'],'evidence_url':url,
                             'evidence_file':item['path']}
    write_json('release_dates.json',releases)
    return releases,sources

def clean(value):
    return re.sub(r'[\s*·ㆍ]','',str(value))

def normalize():
    import xlrd
    target=ROOT/'supplement.csv'
    if (ROOT/'FROZEN.json').exists():
        raise SystemExit('Frozen supplement exists; use a separate version folder for another collection.')
    manifest=json.loads((ROOT/'raw_manifest.json').read_text(encoding='utf8'))
    releases,release_sources=release_dates()
    rows=[];checks=[];cell_audit=[]
    for source in manifest:
        if source['kind']!='official_monthly_workbook':continue
        p=ROOT/source['path'];assert sha(p)==source['sha256']
        kind=source['source_id'];month=source['month'];mo=int(month[-2:])
        b=xlrd.open_workbook(p)
        sheets=[s for s in b.sheets() if '월별' in s.name]
        assert len(sheets)==1,(p,b.sheet_names())
        s=sheets[0]
        headers=[(r,c) for r in range(min(s.nrows,15)) for c in range(s.ncols)
                 if clean(s.cell_value(r,c))==f'{mo}월']
        assert len(headers)==1,(p,headers)
        header,col=headers[0]
        assert all(clean(s.cell_value(header,mm+1))==f'{mm}월' for mm in range(1,13))
        assert any(f'2026년{mo:02}월' in clean(s.cell_value(r,c))
                   for r in range(header) for c in range(s.ncols)),p
        actual=releases.get(month)
        end=date(2026,mo+1,1)-timedelta(days=1)
        available=actual['release_date'] if actual else (end+timedelta(days=45)).isoformat()
        basis='verified_official_release_index_date_not_archived_workbook_vintage' if actual else 'assumed_month_end_plus_45_calendar_days_not_verified_release'
        extracted=[]
        for r in range(header+1,s.nrows):
            name=clean(s.cell_value(r,0));sector=clean(s.cell_value(r,1))
            if sector!='계':continue
            if name in ('계','총계'):name='전국'
            if name not in REGIONS:continue
            code=REGIONS[name];value=s.cell_value(r,col)
            assert isinstance(value,(int,float)) and value>=0 and float(value).is_integer(),(p,r,value)
            assert mo<=6 or code not in ('29','46'),(p,code)
            assert mo>=7 or code!='12',(p,code)
            # Check the monthly row against its own reported YTD, including all prior months.
            ytd=s.cell_value(r,14)
            monthly_sum=sum(s.cell_value(r,mm+1) for mm in range(1,mo+1))
            assert abs(monthly_sum-ytd)<1e-6,(p,r,monthly_sum,ytd)
            row={'region_code':code,'month':month,'variable':KINDS[kind][1],
                 'value':int(value),'available_date':available,'availability_basis':basis,
                 'source_url':source['source_url'],'region_name':name,'unit':'housing_units',
                 'scope':'all_housing_not_apartments_only_multi_family_building_count_basis',
                 'source_id':f'molit_{kind}_{month.replace("-", "")}',
                 'source_page_url':BASE+f'/portal/cate/statMetaView.do?hRsId={KINDS[kind][0]}',
                 'source_file':source['path'],'source_sha256':source['sha256'],
                 'source_locator':f'{s.name}!{xlrd.formula.colname(col)}{r+1}',
                 'release_evidence_url':actual['evidence_url'] if actual else '',
                 'vintage_date':ASOF,'vintage_basis':'retrieval_asof_latest_file_not_original_archived_release',
                 'quality_flag':'provisional_current_year;own_month_workbook;combined_code12_not_additive_with_29_46' if code=='12' else 'provisional_current_year;own_month_workbook'}
            rows.append(row);extracted.append(row)
            cell_audit.append({'file':source['path'],'region_code':code,'month':month,
                'value':int(value),'ytd_reported':ytd,'ytd_sum_months':monthly_sum,
                'month_header_cell':f'{xlrd.formula.colname(col)}{header+1}',
                'value_cell':row['source_locator']})
        national=[r['value'] for r in extracted if r['region_code']=='00']
        regional=sum(r['value'] for r in extracted if r['region_code']!='00')
        assert len(national)==1 and national[0]==regional,(p,national,regional)
        assert len(extracted)==(18 if mo<=6 else 17),(p,len(extracted))
        # Independent sheet: current-month block in housing-type table.
        types=[t for t in b.sheets() if '다가구구분' in t.name]
        assert len(types)==1,p
        t=types[0]
        blocks=[(r,c) for r in range(min(t.nrows,8)) for c in range(t.ncols)
                if clean(t.cell_value(r,c))=='<월계>']
        assert len(blocks)==1,(p,blocks)
        br,bc=blocks[0]
        totals=[(r,t.cell_value(r,bc+1)) for r in range(br+1,min(br+12,t.nrows))
                if clean(t.cell_value(r,bc)) in ('계','총계','합계','전국')]
        assert len(totals)==1 and totals[0][1]==national[0],(p,totals,national)
        checks.append({'file':source['path'],'month':month,'variable':KINDS[kind][1],
                       'national':national[0],'sum_regions':regional,
                       'independent_housing_type_month_total':totals[0][1],
                       'rows':len(extracted),'ytd_checks_passed':True})
    rows.sort(key=lambda x:(x['region_code'],x['month'],x['variable']))
    keys={(r['region_code'],r['month'],r['variable']) for r in rows}
    assert len(rows)==len(keys)==426,len(rows)
    assert all(r['available_date']<=ASOF for r in rows)
    six={'11','26','27','28','30','41'}
    assert sum(r['region_code'] in six for r in rows)==144
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    coverage=[]
    for var in sorted({r['variable'] for r in rows}):
        for code in sorted({r['region_code'] for r in rows if r['variable']==var}):
            rr=[r for r in rows if r['variable']==var and r['region_code']==code]
            coverage.append({'variable':var,'region_code':code,'rows':len(rr),
                             'first_month':min(r['month'] for r in rr),'last_month':max(r['month'] for r in rr)})
    write_json('coverage.json',{'asof':ASOF,'rows':len(rows),'existing_six_region_rows':144,
        'first_month':'2026-01','last_month':'2026-08','by_region_variable':coverage,
        'gaps':[{'series':'housing_supply','months':['2026-09','2026-10'],
                 'reason':'Not listed in the three official metadata pages as of collection; no estimates inserted.'}],
        'release_date_rows':sum('verified_official' in r['availability_basis'] for r in rows),
        'assumed_45_day_rows':sum('assumed_' in r['availability_basis'] for r in rows)})
    write_json('validation.json',{'status':'passed','rows':len(rows),'unique_keys':len(keys),
        'national_equals_regions_all_workbooks':True,'ytd_all_rows':True,
        'independent_month_total_all_workbooks':True,'checks':checks,'cell_audit':cell_audit})
    write_json('raw_manifest.json',sorted(manifest+release_sources,key=lambda r:r['path']))
    write_json('status.json',{'status':'normalized_ready_for_parent','asof':ASOF,'rows':len(rows),
        'existing_six_region_rows':144,'last_month':'2026-08','sha256':sha(target),
        'pending':'final provenance and freeze marker; CSV is ready'})
    print(json.dumps({'rows':len(rows),'six_region_rows':144,'sha256':sha(target),'releases':releases},ensure_ascii=True))

def verify():
    frozen=json.loads((ROOT/'FROZEN.json').read_text(encoding='utf8'))
    assert sha(ROOT/'supplement.csv')==frozen['supplement_sha256']
    assert sha(Path(__file__))==frozen['collector_sha256']
    manifest=json.loads((ROOT/'raw_manifest.json').read_text(encoding='utf8'))
    for source in manifest:
        assert sha(ROOT/source['path'])==source['sha256'],source['path']
    with (ROOT/'supplement.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==426
    assert len({(r['region_code'],r['month'],r['variable']) for r in rows})==426
    assert all(r['available_date']<=ASOF for r in rows)
    expected=frozen['previous_frozen_input']
    assert sha(ROOT/expected['path_from_data'])==expected['sha256']
    print(json.dumps({'status':'verified_frozen','rows':426,'raw_inputs_checked':len(manifest),
                      'sha256':frozen['supplement_sha256'],'previous_frozen_input_unchanged':True}))

def finalize():
    from datetime import datetime, timezone
    manifest=json.loads((ROOT/'raw_manifest.json').read_text(encoding='utf8'))
    coverage=json.loads((ROOT/'coverage.json').read_text(encoding='utf8'))
    previous=ROOT.parent.parent/'지역별 집값 6개월 예측 연구'/'collected'/'monthly_exogenous.csv'
    expected='cbccdf22841a4d93c0233696e182c693fd05801929ba94522dc941e96646b576'
    assert sha(previous)==expected,'Previous frozen input hash differs.'
    frozen={'status':'FINAL_FROZEN','asof':ASOF,'created_utc':datetime.now(timezone.utc).isoformat(),
        'supplement_file':'supplement.csv','supplement_sha256':sha(ROOT/'supplement.csv'),
        'supplement_bytes':(ROOT/'supplement.csv').stat().st_size,'rows':426,
        'collector_sha256':sha(Path(__file__)),
        'raw_manifest_sha256':sha(ROOT/'raw_manifest.json'),
        'previous_frozen_input':{'path_from_data':'../../지역별 집값 6개월 예측 연구/collected/monthly_exogenous.csv','sha256':expected}}
    write_json('FROZEN.json',frozen)
    write_json('status.json',dict(frozen,status='FINAL_FROZEN_VALIDATED',existing_six_region_rows=144,
        last_month='2026-08',errors=[],optional_employment_young_migration='deferred_bounded_scope'))
    provenance={'asof':ASOF,'scope':'MOLIT public actual housing supply supplement, no forecasts',
        'frozen':frozen,'coverage':coverage,'sources':manifest,
        'release_dates':json.loads((ROOT/'release_dates.json').read_text(encoding='utf8')),
        'method':{'extract':'Each workbook reference month only, sector total row, labeled monthly column; excludes future zero placeholders and YTD columns.',
                  'definition':'All housing, public plus private; standard total counts multi-family houses by building, not by household.',
                  'geography':'Legacy model codes 42 (Gangwon), 45 (Jeonbuk) retained; 29 and 46 through June, combined 12 from July, no backfill or disaggregation.',
                  'availability':'All 426 rows use verified official release-index dates; no 45-day fallback was needed. Current downloaded workbook vintage was not authenticated against an archived first-release file.',
                  'tests':'All 24 national totals equal sums of regional rows and independently match the housing-type monthly total; all 426 YTD sums agree with workbook YTD; uniqueness and as-of date checks passed.'},
        'limitations':['2026-09 and 2026-10 not provided in the three observed official attachment lists as of this collection.',
                       'Long historical employment and younger-age migration were not collected; optional expansion deferred to keep scope bounded.',
                       'Supplement adds current-year actual observations; it does not establish historical real-time vintages.'],
        'runtime':{'python':'existing project .venv (requires normal host execution because sandbox cannot access underlying Windows Python installation)',
                   'new_dependency':'xlrd==2.0.2, installed only into assigned data/_vendor; no global or existing-venv package changes',
                   'network':'public MOLIT metadata and attachments only, plus bounded public xlrd dependency retrieval'},
        'authorization_observed':{'paid_calls':False,'credentials_read':False,'transaction_parsing':False,'raw_transactions_uploaded':False,'prior_research_modified':False},
        'diagnostic_duplicate':{'path':'data/completions_202608.xls','sha256':sha(ROOT/'completions_202608.xls'),
                                'reason':'Initial connectivity probe, identical to raw/completions_202608.xls; not another observation.'}}
    (ROOT.parent/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    verify()

if __name__=='__main__':
    if '--verify' in sys.argv:
        verify()
    elif (ROOT/'FROZEN.json').exists():
        raise SystemExit('FINAL/FROZEN: writes refused. Use --verify or copy helper into a new version folder.')
    elif '--inspect' in sys.argv:
        inspect()
    elif '--normalize' in sys.argv:
        normalize()
    elif '--finalize' in sys.argv:
        finalize()
    elif '--download-only' in sys.argv:
        download()
    else:
        _,errors=download()
        if errors:raise SystemExit('Some downloads failed; see status.json')
        normalize()
        finalize()
