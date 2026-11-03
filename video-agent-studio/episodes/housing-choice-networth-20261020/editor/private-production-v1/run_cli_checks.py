"""Runs the installed pinned CLI against local projects; saves bounded JSON evidence."""
import json
import shutil
import subprocess
import sys
import hashlib
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'outputs/private-production-v1'
CLI=shutil.which('hyperframes.cmd')


def main():
    if not CLI:raise RuntimeError('Installed hyperframes.cmd missing; no install/network fallback')
    version=subprocess.check_output([CLI,'--version'],text=True).strip()
    if version!='0.8.181':raise RuntimeError('CLI pin differs: '+version)
    folder=HERE/'checks';folder.mkdir(exist_ok=True)
    times=json.loads((OUT/'snapshot_times.json').read_text(encoding='utf8'))['samples']
    results=[]
    selected=set(map(int,sys.argv[1:])) if sys.argv[1:] else set(range(1,11))
    previous=json.loads((folder/'summary.json').read_text(encoding='utf8')) if selected!=set(range(1,11)) else None
    old_receipt=json.loads((folder/'v4_pre_v5_receipt.json').read_text(encoding='utf8')) if previous else None
    for n in range(1,11):
        html_sha=hashlib.sha256((OUT/f'ch{n:02d}/index.html').read_bytes()).hexdigest()
        if n not in selected:
            prior=next(c for c in previous['chapters'] if c['chapter']==n)
            expected=prior.get('html_sha256') or old_receipt['output_manifest.json'][f'ch{n:02d}/index.html']
            if expected!=html_sha:raise ValueError('Cannot reuse changed CLI source ch'+str(n))
            results.append({**prior,'html_sha256':html_sha,'evidence_reused_from':'checks/v4_pre_v5_receipt.json'});continue
        samples=[s['representative_s'] for s in times if s['chapter']==n]
        command=[CLI,'check','.', '--json','--at',','.join(str(t) for t in samples),'--timeout','10000']
        p=subprocess.run(command,cwd=OUT/f'ch{n:02d}',capture_output=True,text=True,encoding='utf8',errors='replace',timeout=60)
        (folder/f'ch{n:02d}_check.json').write_text(p.stdout,encoding='utf8')
        (folder/f'ch{n:02d}_check_stderr.log').write_text(p.stderr,encoding='utf8')
        try:r=json.loads(p.stdout)
        except json.JSONDecodeError:r={'ok':False,'error':'CLI stdout not JSON'}
        summary={'chapter':n,'html_sha256':html_sha,'returncode':p.returncode,'ok':r.get('ok',False),
                 'passes':{k:{q:v for q,v in r.get(k,{}).items() if q in ['ok','errorCount','warningCount','samples','totalIssueCount']} for k in ['lint','runtime','layout','contrast','motion']},
                 'findings':{k:r[k].get('findings',[]) for k in ['runtime','layout','contrast'] if isinstance(r.get(k),dict)},
                 'history_record_warning':'Check report was not recorded' in p.stderr}
        results.append(summary)
    result={'version':version,'status':'pass' if all(r['ok'] for r in results) else 'findings_require_review','chapters':results,'scope':'CLI representative scene checks; no encoded video/audio quality claim'}
    (folder/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'chapters':len(results),'failed':[r['chapter'] for r in results if not r['ok']]}));return int(result['status']!='pass')


if __name__=='__main__':sys.exit(main())
