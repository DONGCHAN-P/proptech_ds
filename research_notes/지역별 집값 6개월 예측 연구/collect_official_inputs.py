"""Key-free official input collection. All outputs are contained in this folder."""
from pathlib import Path
import csv, json, hashlib, datetime as dt, calendar, re, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'collected'
OUT.mkdir(exist_ok=True)
ASOF='2026-10-27'
PROJECT=ROOT.parents[1]
OLD=PROJECT/'analysis/housing_growth_2006/research'
MANIFEST=ROOT/'official_provenance.json'

def digest(b):return hashlib.sha256(b).hexdigest()
def write_json(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read_manifest():return json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {'as_of_date':ASOF,'sources':[],'outputs':[],'issues':[]}
def save_entry(e):
    m=read_manifest();m['sources']=[x for x in m['sources'] if x.get('id')!=e['id']]+[e];write_json(MANIFEST,m)
def fetch(job):
    sid,url,name=job
    allowed={'www.bok.or.kr','bok.or.kr','stat.molit.go.kr','jumin.mois.go.kr','mods.go.kr','www.mods.go.kr','kosis.kr','www.index.go.kr','index.go.kr','snapshot.bok.or.kr','ecos.bok.or.kr'}
    assert urllib.parse.urlsplit(url).hostname in allowed
    e={'id':sid,'requested_url':url,'local_file':str((OUT/name).relative_to(ROOT)),'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'key_required':False}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':url})
        with urllib.request.urlopen(req,timeout=40) as r:
            b=r.read();e.update(final_url=r.url,http_status=r.status,content_type=r.headers.get('Content-Type'),bytes=len(b),sha256=digest(b))
        if name.endswith('.xlsx') and not b.startswith(b'PK'):raise ValueError('response_not_xlsx')
        (OUT/name).write_bytes(b);e['status']='downloaded'
    except Exception as ex:e.update(status='failed',error=str(ex))
    return e

REGIONS={'서울':'11','부산':'26','대구':'27','인천':'28','광주':'29','대전':'30','울산':'31','세종':'36','경기':'41','강원':'42','충북':'43','충남':'44','전북':'45','전남':'46','경북':'47','경남':'48','제주':'50'}
FIELDS=['region_code','month','variable','value','available_date','availability_basis','region_name','unit','scope','source_id','source_locator','vintage_date','vintage_basis','quality_flag']
def write_csv(name,rows,fields=FIELDS):
    p=OUT/name
    if name=='monthly_exogenous.csv' and read_manifest().get('frozen_combined_csv',{}).get('frozen'):
        raise RuntimeError('Combined CSV is frozen for parent integration; create a separately named version instead.')
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
    m=read_manifest();m['outputs']=[x for x in m['outputs'] if x.get('file')!=str(p.relative_to(ROOT))]
    m['outputs'].append({'file':str(p.relative_to(ROOT)),'sha256':digest(p.read_bytes()),'rows':len(rows),'bytes':p.stat().st_size});write_json(MANIFEST,m)
    return p
def end_month(s):
    y,mo=map(int,s.split('-'));return dt.date(y,mo,calendar.monthrange(y,mo)[1])
def assumed(s,days=45):return (end_month(s)+dt.timedelta(days=days)).isoformat()

def supply():
    p=OLD/'extracted/supply_monthly_six_regions.csv'
    ms=json.loads((OLD/'collection_manifest.json').read_text(encoding='utf-8'))
    mp={x['name']:x for x in ms}
    save_entry({'id':'existing_supply_normalized','status':'reused_existing','local_original':str(p),'sha256':digest(p.read_bytes()),'original_collection_manifest':str(OLD/'collection_manifest.json'),'scope':'all_housing_not_apartments_only'})
    for name in ['completions_01.xlsx','starts_01.xlsx','permits_00.xlsx']:
        e=mp[name].copy();e.update(id=name.split('_')[0],status='reused_existing',local_original=str(OLD/'raw'/name),sha256=digest((OLD/'raw'/name).read_bytes()));save_entry(e)
    rows=[]
    for r in csv.DictReader(p.open(encoding='utf-8-sig')):
        if not '2006-01'<=r['month']<=ASOF[:7]:continue
        v=float(r['housing_units']);rows.append(dict(region_code=REGIONS[r['region']],month=r['month'],variable='housing_'+r['measure']+'_all',value=r['housing_units'],available_date=assumed(r['month']),availability_basis='assumed_month_end_plus_45_calendar_days_not_verified_release',region_name=r['region'],unit='housing_units',scope='all_housing_not_apartments_only',source_id=r['measure'],source_locator=r['source_grid'],vintage_date='2026-10-22',vintage_basis='prior_collection_asof_context_not_original_publication_date',quality_flag='negative_source_value_review_required' if v<0 else ''))
    write_csv('supply_monthly_six_regions.csv',rows)
    return rows

def rates():
    from html.parser import HTMLParser
    class Table(HTMLParser):
        def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
        def handle_starttag(self,t,a):
            if t=='tr':self.row=[]
            if t in ('td','th'):self.cell=''
        def handle_data(self,d):
            if self.cell is not None:self.cell+=d
        def handle_endtag(self,t):
            if t in ('td','th') and self.cell is not None:
                if self.row is not None:self.row.append(self.cell.strip())
                self.cell=None
            if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
    p=OUT/'bok_rate_history.html'
    h=Table();h.feed(p.read_text(encoding='utf-8'));changes=[]
    for r in h.rows:
        if len(r)!=3 or not re.fullmatch(r'\d{4}',r[0]):continue
        d=re.search(r'(\d+)월\s*(\d+)일',r[1])
        if not d:continue
        try:date=dt.date(int(r[0]),int(d[1]),int(d[2]));value=float(r[2])
        except ValueError:continue
        if date.isoformat()<=ASOF:changes.append((date,value))
    changes=sorted(set(changes));assert changes and changes[0][0].year<=2005
    write_csv('bok_policy_rate_changes.csv',[dict(effective_date=d.isoformat(),rate_pct=v,available_date=d.isoformat(),availability_basis='official_rate_change_date_same_day_announcement_assumed_from_change_table',source_id='bok_rate_history',definition='call_rate_target_through_2008_02_base_rate_from_2008_03') for d,v in changes],['effective_date','rate_pct','available_date','availability_basis','source_id','definition'])
    rows=[]
    for y in range(2006,2027):
        for mo in range(1,13):
            month=f'{y}-{mo:02}';end=end_month(month)
            if end.isoformat()>ASOF:continue
            d,v=max((d,v) for d,v in changes if d<=end)
            rows.append(dict(region_code='00',month=month,variable='bok_policy_rate_eom_pct',value=v,available_date=end.isoformat(),availability_basis='derived_calendar_month_end_from_official_rate_change_dates_not_monthly_release',region_name='전국',unit='percent_per_annum',scope='national_common_exogenous',source_id='bok_rate_history',source_locator=f'last_effective_date={d.isoformat()}',vintage_date=ASOF,vintage_basis='retrieval_date_current_official_change_history',quality_flag='call_rate_target_before_2008_03' if month<'2008-03' else ''))
    write_csv('bok_policy_rate_monthly.csv',rows);return rows

if __name__=='__main__':
    import sys
    mode=sys.argv[1] if len(sys.argv)>1 else 'fetch'
    if mode=='fetch':
        jobs=[('bok_rate_history','https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643','bok_rate_history.html'),('bok_main','https://www.bok.or.kr/portal/main/main.do','bok_main.html'),('mois_population_page','https://jumin.mois.go.kr/statMonth.do','mois_population.html'),('molit_unsold_metadata','https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32','molit_unsold_metadata.html'),('molit_completions_metadata','https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=468','molit_completions_metadata.html'),('employment_202609_page','https://mods.go.kr/board.es?act=view&bid=210&list_no=447479&mid=a10301030100','employment_202609_page.html'),('migration_202608_page','https://mods.go.kr/board.es?act=view&bid=205&list_no=447113&mid=a10301020400','migration_202608_page.html')]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for e in pool.map(fetch,jobs):save_entry(e);print(e['id'],e['status'],e.get('bytes',e.get('error')),flush=True)
    elif mode=='normalize':
        a=supply();b=rates();write_csv('monthly_exogenous.csv',sorted(a+b,key=lambda r:(r['region_code'],r['month'],r['variable'])));print('normalized',len(a),len(b),flush=True)
    elif mode=='supply':print('supply',len(supply()),flush=True)
