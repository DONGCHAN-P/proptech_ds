from pathlib import Path
import json,os,subprocess,sys
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/guide-v3';P=O/'project';mode=sys.argv[1]
t=json.loads((P/'timing.json').read_text('utf-8'));times=[];seen=set()
for s in t['scenes']:
    times.append(s['start']+1.5)
    for u in s['units']:
        key=(u['paragraph_id'],u['mode'])
        if key not in seen:times.append(round((u['start']+u['end'])/2,3));seen.add(key)
    for u in [max(s['units'],key=lambda x:len(x['display_text'])),s['units'][-1]]:times.append(round((u['start']+u['end'])/2,3))
times=sorted(set(times));checktimes=times+[t['duration']-.1]
jobs={'check':['check','--at',','.join(map(str,checktimes)),'--json','--max-issues','70'],
 'snapshot':['snapshot','--at',','.join(map(str,times)),'--no-end','--describe','false','--output',str(O/'checks/storyboard')],
 'render':['render','--quality','looks','--fps','30','--workers','3','--output',str(O/'body.mp4')]}
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));env=os.environ.copy();env['PATH']=str(Path(reuse['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
log=O/'checks'/f'{mode}.log'
with log.open('w',encoding='utf-8') as stream:p=subprocess.run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes',*jobs[mode]],cwd=P,env=env,stdout=stream,stderr=subprocess.STDOUT)
raw=log.read_text('utf-8',errors='replace');res={'mode':mode,'exit_code':p.returncode,'log':str(log),'proof_times':times}
if mode=='check':
    for i,ch in enumerate(raw):
        if ch=='{':
            try:
                ob,_=json.JSONDecoder().raw_decode(raw[i:])
                if 'lint' not in ob:continue
                (O/'checks/check.json').write_text(json.dumps(ob,ensure_ascii=False,indent=2),'utf-8')
                fs=[f for v in ob.values() if isinstance(v,dict) for f in v.get('findings',[])];res.update(ok=ob['ok'],errors=[f for f in fs if f['severity']=='error'],warning_codes=sorted(set(f['code'] for f in fs if f['severity']=='warning')));break
            except (json.JSONDecodeError,TypeError):pass
else:res['tail']=raw[-650:]
(O/'checks'/f'{mode}_receipt.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({k:v for k,v in res.items() if k!='proof_times'},ensure_ascii=False));sys.exit(p.returncode)
