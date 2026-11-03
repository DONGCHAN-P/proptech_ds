from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
D=Path(__file__).resolve().parent
def main():
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    ledger=read(D/'osm/ledger.json');rows=[]
    for i in range(1,21):
        rid=f'R{i:02d}';p=D/'osm'/f'{rid}.json';assert p.is_file()
        data=read(p);sha=hashlib.sha256(p.read_bytes()).hexdigest();entry=next((x for x in reversed(ledger) if x['region_id']==rid and x['status']=='ok' and x['response_sha256']==sha),None)
        if entry is None:
            entry=read(D/'osm'/f'{rid}_provenance_recovery.json')
            assert entry['status']=='ok' and entry['response_sha256']==sha
        rows.append({'region_id':rid,'file':p.relative_to(D).as_posix(),'sha256':sha,'elements':len(data['elements']),'source':entry['endpoint'],'queried_bbox':entry['bbox'],'query_sha256':entry['query_sha256'],'retrieved_at':entry.get('requested_at') or entry['retrieved_at'],'retrieval_time_basis':entry.get('retrieval_time_basis','request_start'),'osm_base':entry['osm_base'],'license':'ODbL 1.0','attribution':'© OpenStreetMap contributors','license_url':'https://www.openstreetmap.org/copyright','method':entry.get('method','POST')})
    coverage=read(D/'coverage.json');coverage.update(missing_layers=[],osm_context_regions=len(rows),osm_context_source_records=rows,query_limit_scope='20 named study districts; cached raw vectors, no raster tiles or continuous service',actual_store_operating_status_checked=False,updated_at=datetime.now(timezone.utc).isoformat())
    (D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'regions':len(rows),'raw_context_bytes':sum((D/x['file']).stat().st_size for x in rows),'missing_context_regions':0,'paid_api_calls':0}))
if __name__=='__main__':main()
