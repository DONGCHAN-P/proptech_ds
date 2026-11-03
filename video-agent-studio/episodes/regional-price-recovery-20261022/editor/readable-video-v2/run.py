from pathlib import Path
import subprocess,os,json,sys
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/readable-video-v2';P=OUT/'project';mode=sys.argv[1]
t=json.loads((P/'timing.json').read_text('utf-8'))
times=[]
for s in t['scenes']:
    for b in s['beats']:times.append(round(s['start']+b['start']+min(b['duration']*.5,7),3))
correction_times=[7,59.9,83.5,86,251.8,460.2]
for c in t['captions']:
    if any(g in c['text'] for g in ['2021년 4분기','Elliot Kang 님','2013년 5월']):correction_times.append(round((c['start']+c['end'])/2,3))
jobs={
 'snapshot':['snapshot','--at',','.join(map(str,times)),'--no-end','--describe','false','--output',str(OUT/'checks/storyboard')],
 'check':['check','--at',','.join(map(str,[0,*times,t['duration']-.2])),'--json','--max-issues','70'],
 'render':['render','--quality','looks','--fps','30','--workers','3','--output',str(OUT/'body.mp4')],
 'render-corrected':['render','--quality','looks','--fps','30','--workers','3','--output',str(OUT/'body_corrected.mp4')],
 'correction-preview':['snapshot','--at',','.join(map(str,sorted(correction_times))),'--no-end','--describe','false','--output',str(OUT/'checks/correction-preview')],
}
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));env=os.environ.copy();env['PATH']=str(Path(reuse['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
log=OUT/'checks'/f'{mode}.log'
with log.open('w',encoding='utf-8') as stream:
    proc=subprocess.run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes',*jobs[mode]],cwd=P,env=env,stdout=stream,stderr=subprocess.STDOUT)
raw=log.read_text('utf-8',errors='replace');result={'mode':mode,'exit_code':proc.returncode,'log':str(log)}
if mode=='check':
    for i,ch in enumerate(raw):
        if ch=='{':
            try:
                obj,_=json.JSONDecoder().raw_decode(raw[i:])
                if 'lint' not in obj:continue
                (OUT/'checks/check.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
                result.update(ok=obj['ok'],findings=[f for v in obj.values() if isinstance(v,dict) for f in v.get('findings',[])]);break
            except (json.JSONDecodeError,TypeError):pass
else:result['tail']=raw[-1200:]
(OUT/'checks'/f'{mode}_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(result,ensure_ascii=False));sys.exit(proc.returncode)
