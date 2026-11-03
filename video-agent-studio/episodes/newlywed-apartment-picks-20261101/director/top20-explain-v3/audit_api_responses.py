"""Independent protocol/coverage audit of bounded official API responses; no network."""
from pathlib import Path
from collections import Counter
import hashlib,json,xml.etree.ElementTree as ET

D=Path(__file__).resolve().parent; E=D.parents[1]
P=E/'research/top20-explain-v3/prices'; Q=E/'qa/top20-explain-v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    ledger=read(P/'api_request_log.json'); receipt=read(P/'api_collection_receipt.json')
    assert receipt['complete'] and len(ledger['requests'])<=200
    checks=[]; returned=Counter(); completed=[]
    for row in ledger['requests']:
        if row['status']!='ok':
            checks.append({'sequence':row['sequence'],'status':row['status'],'excluded':True})
            continue
        path=P/row['response_file']; body=path.read_bytes()
        assert hashlib.sha256(body).hexdigest()==row['response_sha256']
        root=ET.fromstring(body); items=root.findall('.//item')
        assert len(items)==row['rows']
        assert root.findtext('.//resultCode') in ['000','00','0']
        expected=row['contract_month']
        for item in items:
            assert item.findtext('dealYear')+item.findtext('dealMonth').zfill(2)==expected
        returned[(row['lawd_cd'],expected)]+=len(items)
        if row.get('total_count',0): completed.append((row['lawd_cd'],expected))
        checks.append({'sequence':row['sequence'],'status':'verified','rows':len(items),'source_sha256':row['response_sha256']})
    cross=read(E/'research/top20-8min-v2/price_context.json')['geography_crosswalk']
    expected={(code,ym) for r in cross for code in r['current_cache_codes'] for ym in ['202605','202606','202607','202608','202609','202610']}
    successful={(r['lawd_cd'],r['contract_month']) for r in ledger['requests'] if r['status']=='ok' and r.get('total_count',0)>0}
    assert expected<=successful, sorted(expected-successful)
    for r in ledger['requests']:
        if r['status']=='ok' and r.get('total_count',0)>0:
            assert returned[(r['lawd_cd'],r['contract_month'])]==r['total_count']
    out={'status':'passed','scope':'protocol/hash/month/coverage only; no listening, frame or price-statistic review',
         'request_count':len(ledger['requests']),'successful_required_code_months':len(expected),
         'returned_rows_required':sum(v for k,v in returned.items() if k in expected),
         'missing_required_code_months':[],'checks':checks}
    Q.mkdir(parents=True,exist_ok=True)
    (Q/'api_response_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='checks'},ensure_ascii=False))

if __name__=='__main__':main()
