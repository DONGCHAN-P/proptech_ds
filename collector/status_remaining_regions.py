"""Read-only coverage and sample verification for the resumed provincial batch."""
from pathlib import Path
import json,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from collector import collect_remaining_regions as c
def read(p):return json.loads(p.read_text('utf-8-sig'))
plan=read(c.OUT/'plan.json');batch=read(c.OUT/'batch_status.json');status=read(Path(batch['worker_status_file']))
grids={name:c.grid(name,codes) for name,codes in plan['groups'].items()}
ledger=c.LEDGER/f'calls-{c.datetime.now(c.worker.KST):%Y-%m-%d}.json'
latest=[]
for name,g in grids.items():
    files=list(Path(g['source']).glob('*/*.meta.json'))
    if files:
        path=max(files,key=lambda p:p.stat().st_mtime);m=read(path);actual=0
        for i in range(1,m['pages']+1):
            root=ET.fromstring((path.parent/f'{m["code"]}.page{i}.xml').read_bytes())
            assert root.findtext('.//resultCode') in ('000','00','0')
            actual+=len(root.findall('.//items/item'))
        assert actual==m['stored_rows']==m['totalCount']
        latest.append({'region':name,'code':m['code'],'month':m['ym'],'rows':actual,'collected_at':m['collected_at'],'verified':True})
snapshot={'checked_at':c.stamp(),'batch':batch,'worker':status,'groups':grids,'known_daily_calls':read(ledger)['calls'] if ledger.exists() else 0,'daily_known_call_cap':plan['daily_known_call_cap'],'new_complete_code_months_since_launch':sum(v['complete_code_months']-plan['grid'][n]['complete_code_months'] for n,v in grids.items()),'latest_xml_samples':latest,'historical_boundary_and_dedup_review':'before_analysis_integration'}
c.worker.save(c.OUT/'snapshot.json',snapshot)
episode=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/state.json';state=read(episode)
state['collection_status_file']=(c.OUT/'batch_status.json').relative_to(ROOT).as_posix();state['collection_snapshot_file']=(c.OUT/'snapshot.json').relative_to(ROOT).as_posix();state['collection_not_yet_integrated']=True
state['collection_resume_request']={'client_date':'2026-10-26','scope':'Resume missing regions; 2006-01 through 2026-09','priority':plan['priority'],'batch_pid':batch['pid'],'status_at_check':batch['state']}
c.worker.save(episode,state)
print(json.dumps({'state':batch['state'],'pid':batch['pid'],'current_group':batch.get('current_group'),'worker':status,'new_complete_code_months_since_launch':snapshot['new_complete_code_months_since_launch'],'known_daily_calls':snapshot['known_daily_calls'],'latest_xml_samples':latest},ensure_ascii=False,indent=2))
