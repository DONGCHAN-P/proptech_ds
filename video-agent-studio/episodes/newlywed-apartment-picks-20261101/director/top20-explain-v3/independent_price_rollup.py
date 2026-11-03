"""Recompute regional/apartment medians directly from frozen public XML responses."""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
from statistics import median
import hashlib,json,xml.etree.ElementTree as ET

D=Path(__file__).resolve().parent; E=D.parents[1]
P=E/'research/top20-explain-v3/prices'; Q=E/'qa/top20-explain-v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    codes={c:r['region_id'] for r in read(E/'research/top20-8min-v2/price_context.json')['geography_crosswalk'] for c in r['current_cache_codes']}
    regions=defaultdict(list); apartments=defaultdict(list); names={}; cancelled=0; rows=0; observed=set()
    for request in read(P/'api_request_log.json')['requests']:
        code=request['lawd_cd']; ym=request['contract_month']; key=(code,ym,request['page'])
        if request['status']!='ok' or code not in codes or not ('202605'<=ym<='202610'):continue
        assert key not in observed,'Duplicate page must not be aggregated twice'
        observed.add(key); body=(P/request['response_file']).read_bytes()
        assert hashlib.sha256(body).hexdigest()==request['response_sha256']
        for node in ET.fromstring(body).findall('.//item'):
            v={c.tag:(c.text or '').strip() for c in node}; rows+=1
            area=Decimal(v['excluUseAr']); amount=Decimal(v['dealAmount'].replace(',',''))
            if not(83<=area<=85 and amount>0):continue
            if v.get('cdealType') or v.get('cdealDay'):
                cancelled+=1;continue
            rid=codes[code]; aptkey=(rid,v['aptSeq'])
            regions[rid].append(amount);apartments[aptkey].append(amount)
            names[aptkey]={'apt_name':v['aptNm'],'legal_dong':v['umdNm']}
    assert len(regions)==20
    stats=lambda values:{'n':len(values),'median_manwon':float(median(values))}
    output={'status':'computed_for_independent_comparison','basis':'raw official XML; all floors;83<=area<=85;positive amount;cdealType/cdealDay empty; no active-row deduplication',
            'contract_window':['2026-05-01','2026-10-31'],'retrieval_date':'2026-11-03',
            'raw_rows':rows,'eligible_cancelled_rows_excluded':cancelled,
            'regions':[{'region_id':k,**stats(v)} for k,v in sorted(regions.items())],
            'complexes':[{'region_id':k[0],'apt_seq':k[1],**names[k],**stats(v)} for k,v in sorted(apartments.items())]}
    Q.mkdir(parents=True,exist_ok=True)
    path=Q/'independent_price_rollup.json';path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'regions':20,'complexes':len(apartments),'raw_rows':rows,'eligible_active_n':sum(len(v) for v in regions.values()),'eligible_cancelled':cancelled},ensure_ascii=False))

if __name__=='__main__':main()
