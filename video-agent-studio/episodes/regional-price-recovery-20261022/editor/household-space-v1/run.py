from pathlib import Path
import subprocess,os,json,sys
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/household-space-v1'; P=OUT/'project'
mode=sys.argv[1]
jobs={
 'snapshot':['snapshot','--at','2,4.5,5.7,6.5,7.5,8.7,12,19.9','--no-end','--describe','false','--output',str(OUT/'checks/storyboard')],
 'check':['check','--at','0,2,4.5,5.7,6.5,7.5,8.7,12,19.9','--json','--max-issues','50'],
 'render':['render','--quality','looks','--fps','30','--workers','2','--output',str(OUT/'household_space_sample_v1.mp4')],
 'usage':['usage','--json'],
 'history-begin':['history','begin','--who','codex','--label','household-space-v1'],
 'history-end':['history','end'],
}
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'))
env=os.environ.copy();env['PATH']=str(Path(reuse['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
log=OUT/'checks'/f'{mode}.log'
with log.open('w',encoding='utf-8') as s:
    proc=subprocess.run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes',*jobs[mode]],cwd=P,env=env,stdout=s,stderr=subprocess.STDOUT)
raw=log.read_text('utf-8',errors='replace');result={'mode':mode,'exit_code':proc.returncode,'log':str(log)}
if mode=='check':
    for n,char in enumerate(raw):
        if char=='{':
            try:
                obj,_=json.JSONDecoder().raw_decode(raw[n:])
                if 'lint' not in obj:continue
                (OUT/'checks/check.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
                result.update(ok=obj['ok'],errors=[f for p in obj.values() if isinstance(p,dict) for f in p.get('findings',[]) if f['severity']=='error'],warnings=[{'code':f['code'],'message':f['message'],'selector':f.get('selector')} for p in obj.values() if isinstance(p,dict) for f in p.get('findings',[]) if f['severity']=='warning'])
                break
            except (json.JSONDecodeError,TypeError):pass
else:result['tail']=raw[-1300:]
(OUT/'checks'/f'{mode}_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False));sys.exit(proc.returncode)
