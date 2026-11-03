"""Read-only metadata audit; snapshot does not imply complete market coverage."""
from pathlib import Path
from datetime import datetime
import json
import xml.etree.ElementTree as ET
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from collector.collect_three_cities import KST,save
OUT=ROOT/'raw/rtms_trade_expansion/additional_20261023'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
snapshot={'checked_at':datetime.now(KST).isoformat(),'groups':{},'metadata_errors':[],'xml_samples_checked':0,'xml_sample_errors':[]}
for city,codes in plan['groups'].items():
    files=sorted((OUT/city).glob('*/*.meta.json'))
    complete=[]
    for path in files:
        meta=json.loads(path.read_text(encoding='utf8'))
        if not meta.get('complete'):
            continue
        if meta['stored_rows']!=meta['totalCount']:
            snapshot['metadata_errors'].append(path.relative_to(ROOT).as_posix())
        complete.append((path,meta))
    snapshot['groups'][city]={'complete_code_months':len(complete),'target_code_months':len(codes)*249,'stored_api_rows':sum(m['stored_rows'] for _,m in complete),'earliest_collected_ym':min((m['ym'] for _,m in complete),default=None),'latest_collected_ym':max((m['ym'] for _,m in complete),default=None),'codes_with_completed_months':sorted({m['code'] for _,m in complete}),'file_grid_complete':len(complete)==len(codes)*249,'historical_boundary_and_dedup_review':'pending_before_analysis_integration'}
    # First/last metadata plus any multipart pages, without repeatedly parsing all raw.
    sample=complete[:1]+complete[-1:]+[(p,m) for p,m in complete if m['pages']>1][:3]
    for path,m in {str(p):(p,m) for p,m in sample}.values():
        count=0
        for page in range(1,m['pages']+1):
            xml=path.parent/f'{m["code"]}.page{page}.xml'
            tree=ET.fromstring(xml.read_bytes())
            assert tree.findtext('.//resultCode') in ('000','00','0')
            count+=len(tree.findall('.//items/item'))
        snapshot['xml_samples_checked']+=1
        if count!=m['totalCount']:
            snapshot['xml_sample_errors'].append(path.relative_to(ROOT).as_posix())
ledger=ROOT/'raw/rtms_trade_expansion/three_cities'/f'calls-{datetime.now(KST):%Y-%m-%d}.json'
snapshot['known_daily_calls']=json.loads(ledger.read_text(encoding='utf8'))['calls'] if ledger.exists() else 0
snapshot['known_daily_cap']=8000
snapshot['other_account_calls']='unknown'
snapshot['worker_status']=json.loads((OUT/'status.json').read_text(encoding='utf8'))
snapshot['batch_status']=json.loads((OUT/'batch_status.json').read_text(encoding='utf8'))
snapshot['all_complete_rows']=sum(g['stored_api_rows'] for g in snapshot['groups'].values())
snapshot['all_complete_code_months']=sum(g['complete_code_months'] for g in snapshot['groups'].values())
assert not snapshot['metadata_errors'] and not snapshot['xml_sample_errors']
save(OUT/'snapshot.json',snapshot)
print(json.dumps(snapshot,ensure_ascii=False,indent=2))
