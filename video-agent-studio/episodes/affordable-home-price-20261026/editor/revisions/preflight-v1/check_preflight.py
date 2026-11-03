"""Pinned installed CLI. No updates, installation, external provider, TTS or render."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'outputs/private-production-v1'
cli=shutil.which('hyperframes.cmd')
if not cli:raise RuntimeError('Pinned installed CLI unavailable')
env=dict(os.environ,DO_NOT_TRACK='1')
def run(args,cwd=OUT):return subprocess.run([cli,*args],cwd=cwd,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90,env=env)
version=run(['--version']).stdout.strip()
assert version=='0.8.181',version
records=json.loads((HERE/'cli_preflight.json').read_text(encoding='utf8'))['records'] if (HERE/'cli_preflight.json').exists() else {}
if not records:
    for label,args in [('usage',['usage','--json']),('registry',['catalog','--query','waterfall bar line chart','--json'])]:
        p=run(args);(HERE/(label+'_preflight.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf8')
        try:d=json.loads(p.stdout)
        except ValueError:d={'status':'unknown','message':p.stdout.strip() or p.stderr.strip()}
        records[label]={'returncode':p.returncode,'result':d}
rows=[]
for scene in ['cash','fees_cases','reset_budget']:
    p=run(['check','.','--json','--at','2,6,11','--timeout','10000'],OUT/scene)
    (HERE/(scene+'_cli.json')).write_text(p.stdout,encoding='utf8')
    (HERE/(scene+'_cli_stderr.log')).write_text(p.stderr,encoding='utf8')
    try:d=json.loads(p.stdout)
    except ValueError:d={'ok':False,'parse_error':True}
    rows.append({'scene':scene,'returncode':p.returncode,'ok':d.get('ok',False),'html_sha256':hashlib.sha256((OUT/scene/'index.html').read_bytes()).hexdigest(),'sections':{k:{a:b for a,b in d.get(k,{}).items() if a in ['ok','errorCount','warningCount','samples','totalIssueCount','findings']} for k in ['lint','runtime','layout','contrast','motion']}})
receipt={'status':'pass' if all(r['ok'] for r in rows) else 'findings','version':version,'records':records,'scenes':rows,'scope':'provisional source only; no film render'}
(HERE/'cli_preflight.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':receipt['status'],'version':version,'usage_status':records['usage']['result'].get('status'),'failed':[r['scene'] for r in rows if not r['ok']]}))
raise SystemExit(0 if receipt['status']=='pass' else 1)
