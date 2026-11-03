"""대표시안 검사를 일괄 실행합니다. 네트워크·유료·TTS·MP4·업로드 명령이 없습니다."""
from pathlib import Path
import json,os,subprocess
H=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1'}
t=read(H/'timeline_resolved.json');ph={v['scene_id']:v for v in read(H/'phase_audit.json')};times=[]
for s in t['scenes']:
 p=ph.get(s['scene_id']);times.append(s['start_s']+12 if not p else s['start_s']+p['switch_s']-.04)
 if p:times.append(s['start_s']+p['switch_s']+.04)
times=','.join(f'{v:.5f}' for v in times)
out=H/'evidence';out.mkdir(exist_ok=True)
argv=['npx.cmd','--no-install','hyperframes','check',str(H/'spec'),'--at',times,'--json','--snapshots','--timeout','20000']
with (out/'check-spec.json').open('wb') as stdout,(out/'check-spec.stderr.log').open('wb') as stderr:
 p=subprocess.run(argv,env=env,stdout=stdout,stderr=stderr)
result=read(out/'check-spec.json')
summary={'status':'passed' if p.returncode==0 and result.get('ok') and not result.get('browserSkipped') else 'failed','command':argv,'timing_locked':False,'lint_errors':result['lint']['errorCount'],'runtime_errors':result['runtime']['errorCount'],'layout_findings':result['layout']['totalIssueCount'],'sample_count':len(result['layout']['samples']),'contrast_checked':result['contrast']['checked'],'contrast_passed':result['contrast']['passed'],'full_render':False}
(out/'check_receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
assert summary['status']=='passed'
subprocess.run(['node',str(H/'inspect_specs.cjs')],env=env,check=True)
