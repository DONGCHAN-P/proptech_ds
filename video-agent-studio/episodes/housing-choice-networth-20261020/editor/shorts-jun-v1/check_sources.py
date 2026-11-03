"""Pinned local HyperFrames checks of the two actual portrait sources."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
CLI=shutil.which('hyperframes.cmd')
assert CLI and subprocess.check_output([CLI,'--version'],text=True).strip()=='0.8.181'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
checks=HERE/'checks';checks.mkdir(exist_ok=True)
env=os.environ.copy();env['DO_NOT_TRACK']='1'
rows=[]
for ident in ['funnel','analysis']:
    folder=EP/'outputs/shorts-jun-v1'/ident
    samples=[(s['start_s']+s['end_s'])/2 for s in read(folder/'scenes.json')['scenes']]
    argv=[CLI,'check','.', '--json','--at',','.join(map(str,samples)),'--timeout','10000']
    p=subprocess.run(argv,cwd=folder,capture_output=True,text=True,encoding='utf8',errors='replace',env=env,timeout=150)
    (checks/f'{ident}.json').write_text(p.stdout,encoding='utf8');(checks/f'{ident}.stderr.log').write_text(p.stderr,encoding='utf8')
    try:r=json.loads(p.stdout)
    except json.JSONDecodeError:r={'ok':False,'error':'stdout not JSON'}
    row={'id':ident,'returncode':p.returncode,'ok':r.get('ok',False),'html_sha256':hashlib.sha256((folder/'index.html').read_bytes()).hexdigest(),'argv':argv}
    rows.append(row);print(json.dumps(row),flush=True)
(checks/'summary.json').write_text(json.dumps({'version':'0.8.181','status':'pass' if all(r['ok'] for r in rows) else 'requires_review','shorts':rows},indent=2)+'\n',encoding='utf8')
raise SystemExit(0 if all(r['ok'] for r in rows) else 1)
