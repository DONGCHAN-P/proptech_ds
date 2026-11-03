"""Pinned source CLI checks only; never renders the film."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parent;OUT=EP/'outputs/private-production-v1'
cli=shutil.which('hyperframes.cmd');assert cli
assert subprocess.check_output([cli,'--version'],text=True).strip()=='0.8.181'
samples=json.loads((OUT/'snapshot_times.json').read_text(encoding='utf8'))['samples']
rows=[];folder=HERE/'checks/native-v4';folder.mkdir(parents=True,exist_ok=True)
selected=set(map(int,sys.argv[1:])) if len(sys.argv)>1 else set(range(1,11))
previous=json.loads((folder/'summary.json').read_text(encoding='utf8')) if selected!=set(range(1,11)) else None
for chapter in range(1,11):
    project=OUT/f'ch{chapter:02}';times=[s['representative_s'] for s in samples if s['chapter']==chapter]
    if chapter not in selected:
        prior=next(r for r in previous['chapters'] if r['chapter']==chapter)
        assert prior['html_sha256']==hashlib.sha256((project/'index.html').read_bytes()).hexdigest()
        rows.append(prior);continue
    argv=[cli,'check','.','--json','--at',','.join(str(t) for t in times),'--timeout','10000']
    p=subprocess.run(argv,cwd=project,env=dict(os.environ,DO_NOT_TRACK='1'),capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90)
    (folder/f'ch{chapter:02}.json').write_text(p.stdout,encoding='utf8');(folder/f'ch{chapter:02}.log').write_text(p.stderr,encoding='utf8')
    try:d=json.loads(p.stdout)
    except ValueError:d={'ok':False}
    rows.append({'chapter':chapter,'ok':d.get('ok',False),'returncode':p.returncode,'html_sha256':hashlib.sha256((project/'index.html').read_bytes()).hexdigest(),'sections':{k:{q:v for q,v in d.get(k,{}).items() if q in ['ok','errorCount','warningCount','samples','totalIssueCount','findings']} for k in ['lint','runtime','layout','contrast','motion']}})
    print(json.dumps({'chapter':chapter,'ok':rows[-1]['ok']}),flush=True)
r={'status':'pass' if all(r['ok'] for r in rows) else 'findings','version':'0.8.181','timing_revision':'production-injoon-v3','chapters':rows,'full_render':False}
(folder/'summary.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');raise SystemExit(0 if r['status']=='pass' else 1)
