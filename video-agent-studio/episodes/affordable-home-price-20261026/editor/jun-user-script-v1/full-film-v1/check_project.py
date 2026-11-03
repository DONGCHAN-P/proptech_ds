from pathlib import Path
import subprocess,json,re,os
HERE=Path(__file__).resolve().parent
hf='C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs'
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1'}
r=subprocess.run(['node',hf,'check',str(HERE/'project'),'--json'],capture_output=True,env=env)
(HERE/'check.stderr.log').write_bytes(r.stderr)
(HERE/'check.stdout.log').write_bytes(r.stdout)
raw=r.stdout.decode('utf-8','replace')
m=re.search(r'(?m)^\{',raw)
if not m:
    print('Check failed before JSON:',r.returncode,r.stderr.decode('utf-8','replace')[-1800:]);raise SystemExit(r.returncode or 1)
d,_=json.JSONDecoder().raw_decode(raw[m.start():])
(HERE/'check_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CHECK exit',r.returncode,'topkeys',list(d))
for group in ['lint','runtime','layout','contrast']:
    x=d.get(group,{})
    print(group,{k:x.get(k) for k in ['ok','errorCount','warningCount','checked','duration']})
    for f in x.get('findings',[])[:8]:print(f.get('code'),f.get('message'))
raise SystemExit(r.returncode)
