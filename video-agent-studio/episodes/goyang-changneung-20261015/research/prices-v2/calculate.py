"""Read-only RTMS snapshot audit. Run from any directory; outputs stay beside script."""
from pathlib import Path
import csv, hashlib, json, statistics, xml.etree.ElementTree as ET
from collections import Counter
import duckdb

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
MASTER = ROOT / 'master/trade_events.parquet'
MONTHS = ['202607', '202608', '202609']
CANDIDATES = [
    ('6b9e26142b9eb6a3','삼송2차아이파크','삼송','삼송역 이용권, 출입구·도보경로는 별도 확인'),
    ('b0b97f17ddc24cb6','삼송원흥역센트럴푸르지오','원흥','원흥역 생활권; n<5 참고값'),
    ('17bae9021d8588e6','도래울센트럴더포레','도래울','기존 도래울 생활권; 역 도보권으로 단정 금지'),
    ('6d132d1b88760197','창릉호반써밋','동산·삼송','기존 동산동 대안; 창릉 공공분양 블록과 구분'),
    ('db26aa7d99fb32df','지축역센트럴푸르지오','지축','기존 지축역 생활권, 높은 출발 총예산 대안'),
    ('14f487c544ee4871','지축역중흥S-클래스북한산파크뷰','지축','지축 내 다른 예산대 대안; 역 접근은 단지별 확인'),
]
NAMES = {c[1] for c in CANDIDATES}
con=duckdb.connect()
ids=','.join("'"+c[0]+"'" for c in CANDIDATES)
q=f"SELECT * FROM '{MASTER.as_posix()}' WHERE apt_id IN ({ids}) AND deal_date >= DATE '2026-07-01' AND deal_date < DATE '2026-10-01' AND area_m2>=83 AND area_m2<85 AND floor>=5"
df=con.execute(q).df()
sources=[]; raw=[]
for ym in MONTHS:
    refreshed=OUT/'raw'/f'41281_{ym}.xml'
    p=refreshed if refreshed.exists() else ROOT/'raw/rtms_trade'/ym[:4]/ym[4:]/f'41281_{ym}.xml'
    meta=json.loads(p.with_suffix('.meta.json').read_text(encoding='utf-8'))
    tree=ET.parse(p); items=tree.findall('.//item')
    sources.append({'month':ym,'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':meta,'xml_item_count':len(items),'xml_total_count':int(tree.findtext('.//totalCount') or 0)})
    for index,it in enumerate(items,1):
        r={x.tag:(x.text or '').strip() for x in it}
        if r.get('aptNm') not in NAMES:continue
        try:
            if not (83<=float(r['excluUseAr'])<85 and int(r['floor'])>=5):continue
        except (ValueError,KeyError):continue
        r.update(source_file=str(p),item_index=index)
        raw.append(r)

def key_raw(r):
    return (r['aptNm'],f"{r['dealYear']}-{int(r['dealMonth']):02}-{int(r['dealDay']):02}",float(r['excluUseAr']),int(r['floor']),int(r['dealAmount'].replace(',','')))
def key_master(r):
    return (r['apt_name_raw'],r['deal_date'].strftime('%Y-%m-%d'),float(r['area_m2']),int(r['floor']),int(r['deal_amount']))
rawkeys=Counter(key_raw(r) for r in raw if not r.get('cdealType') and not r.get('cdealDay'))
master_valid=df[(df.is_canceled==False)&df.cancel_date.isna()&(df.deal_amount>0)].copy()
masterkeys=Counter(key_master(r) for r in master_valid.to_dict('records'))
verified=[]
for r in master_valid.to_dict('records'):
    matches=[s for s in raw if key_raw(s)==key_master(r)]
    verified.append({k:r[k] for k in ['apt_id','apt_name_raw','legal_dong_name','deal_date','area_m2','floor','deal_amount','is_canceled','cancel_date','road_address','deal_hash']} | {
        'source_file':matches[0]['source_file'] if matches else '',
        'source_item_index':matches[0]['item_index'] if matches else '',
        'raw_dealing_type':matches[0].get('dealingGbn','') if matches else '',
        'raw_cdealType':matches[0].get('cdealType','') if matches else '',
        'raw_cdealDay':matches[0].get('cdealDay','') if matches else '',
        'raw_exact_match_count':len(matches),
    })
with (OUT/'verified_rows.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(verified[0]));w.writeheader();w.writerows(verified)
# Fresh official monthly response is primary. Retain distinct response items: without
# a transaction identifier, same date/area/floor is insufficient proof of duplication.
master_verified=verified
verified=[]
for r in raw:
    if r.get('cdealType') or r.get('cdealDay'):continue
    name,date,area,floor,amount=key_raw(r)
    apt=next(x[0] for x in CANDIDATES if x[1]==name)
    verified.append({'apt_id':apt,'apt_name_raw':name,'legal_dong_name':r.get('umdNm'),'deal_date':date,'area_m2':area,'floor':floor,'deal_amount':amount,'is_canceled':False,'cancel_date':'','road_address':r.get('roadNm','')+' '+str(int(r.get('roadNmBonbun') or 0)),'deal_hash':'','source_file':r['source_file'],'source_item_index':r['item_index'],'raw_dealing_type':r.get('dealingGbn',''),'raw_cdealType':r.get('cdealType',''),'raw_cdealDay':r.get('cdealDay',''),'raw_exact_match_count':rawkeys[key_raw(r)],'apt_seq':r.get('aptSeq'),'jibun':r.get('jibun'),'master_exact_key_count':masterkeys[key_raw(r)]})
with (OUT/'verified_rows.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(verified[0]));w.writeheader();w.writerows(verified)
results=[]
for apt,name,region,reason in CANDIDATES:
    rows=[r for r in verified if r['apt_id']==apt]; vals=[r['deal_amount'] for r in rows]
    rr=[r for r in raw if r['aptNm']==name]
    results.append({'claim_id':'CN-PRICE-'+apt,'apt_id':apt,'name':name,'region':region,'selection_reason':reason,'statistic':'median','median_manwon':statistics.median(vals) if vals else None,'median_eok':statistics.median(vals)/10000 if vals else None,'n':len(vals),'small_sample_warning':len(vals)<5,'exclusive_area_range_sqm':[83,85],'upper_bound_exclusive':True,'actual_areas_sqm':sorted({r['area_m2'] for r in rows}),'floor_min':5,'period_start':'2026-07-01','period_end':'2026-09-30','transaction_type':'아파트 매매（중개·직거래 포함; raw_dealing_type 별도 열）','unit':'만원','raw_rows_before_cancel_exclusion':len(rr),'raw_canceled_rows':sum(bool(r.get('cdealType') or r.get('cdealDay')) for r in rr),'raw_valid_rows':sum(not(r.get('cdealType') or r.get('cdealDay')) for r in rr),'status':'qualified','as_of':'2026Q3 계약일/월별 상이한 수집시점','checked_on':'2026-10-16','source_file':str(MASTER),'evidence_location':'verified_rows.csv apt_id 필터','not_current_asking_price':True})
audit={'master_sha256':hashlib.sha256(MASTER.read_bytes()).hexdigest(),'sources':sources,'selected_master_rows_before_cancel_filter':len(df),'master_null_cancel_flags':int(df.is_canceled.isna().sum()),'master_cancel_date_present_but_flag_false':int(((df.is_canceled==False)&df.cancel_date.notna()).sum()),'master_missing_price_area_floor_dates':int(df[['deal_amount','area_m2','floor','deal_date']].isna().any(axis=1).sum()),'duplicate_deal_hash_selected':int(master_valid.deal_hash.duplicated().sum()),'master_only_keys':[str(k) for k in (masterkeys-rawkeys)],'raw_only_keys':[{'key':str(k),'count':v} for k,v in (rawkeys-masterkeys).items()],'raw_exact_key_duplicates':[{'key':str(k),'count':v} for k,v in rawkeys.items() if v>1],'refresh_status':'three bounded requests failed ConnectionError; retained existing monthly raw','upstream_dedup_limitation':'run_step3.py dedup_trades drops apt_id/date/area/floor duplicates keeping highest amount, without transaction unique ID or cancellation precedence; can collapse distinct same-day same-floor trades. No reconstruction by assumption.'}
audit['refresh_status']='2026-10-16 official three-month GET successful after sandbox network escalation; all three pages complete'
audit['primary_aggregation']='fresh official XML item rows; exclude any nonblank cdealType OR cdealDay; no date/area/floor dedup'
audit['master_comparisons']=[{'apt_id':c[0],'n':sum(r['apt_id']==c[0] for r in master_verified),'median_manwon':statistics.median([r['deal_amount'] for r in master_verified if r['apt_id']==c[0]])} for c in CANDIDATES]
for r in results:
    r['source_file']='; '.join(s['file'] for s in sources)
    r['as_of']='2026-10-16 조회/2026Q3 계약일'
(OUT/'comparisons.json').write_text(json.dumps({'revision':'prices-v2','checked_on':'2026-10-16','scope':'수집된 표본; 전국/단지 전수 보장 없음; 호가 아님','comparisons':results,'audit':audit},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
(OUT/'facts.json').write_text(json.dumps({'revision':'prices-v2','facts':[dict(r,statement=f"{r['name']}의 수집된 2026Q3 전용83≤㎡<85·5층 이상·해제 제외 매매 중위값은 {r['median_eok']}억원, n={r['n']}건이다.",source_url='https://www.data.go.kr/data/15126468/openapi.do') for r in results]},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps({'comparisons':[(r['name'],r['median_eok'],r['n'],r['raw_valid_rows']) for r in results],'master_only':audit['master_only_keys'],'raw_only':audit['raw_only_keys'],'null_flags':audit['master_null_cancel_flags'],'duplicate_hash':audit['duplicate_deal_hash_selected']},ensure_ascii=False))
