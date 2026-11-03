"""Keep local HyperFrames logs on disk and print compact verification summaries."""
from pathlib import Path
import subprocess,json,sys,os,re
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project';S=OUT/'checks/smoke'
job=sys.argv[1];log=OUT/'checks'/f'{job}.log';extra=sys.argv[2:]
timing=json.loads((P/'timing.json').read_text(encoding='utf8'));all_times=','.join(str(round(s['start']+b['start']+.85*b['duration'],3)) for s in timing['scenes'] for b in s['beats'])
jobs={
 'smoke-check':(S,['check','--at','8,30,45','--json']),
 'smoke-snapshot':(S,['snapshot','--at','12,30,45','--no-end','--describe','false','--output',str(OUT/'checks/smoke_frames')]),
 'check':(P,['check','--json','--max-issues','100']),
 'check-all':(P,['check','--at',all_times,'--json','--max-issues','100']),
 'snapshot-all':(P,['snapshot','--at',all_times,'--no-end','--describe','false','--output',str(OUT/'checks/all_beat_frames')]),
 'snapshot':(P,['snapshot','--at',extra[0] if extra else '12','--no-end','--describe','false','--output',str(OUT/'checks/representative_frames')]),
 'render-smoke':(S,['render','--quality','draft','--fps','30','--workers','2','--output',str(OUT/'checks/smoke.mp4')]),
 'render':(P,['render','--quality','looks','--fps','30','--workers','3','--output',str(OUT/'previews/literature_visual_body_v1.mp4')]),
 'preview':(P,['preview','--background','--no-open','--port','3027']),
 'history-begin':(P,['history','begin','--who','codex','--label','literature-visual-v1']),
 'history-end':(P,['history','end']),
 'usage':(P,['usage','--json']),
}
cwd,args=jobs[job]
if job=='render-smoke':
    source=(S/'index.html').read_text(encoding='utf8');source=re.sub(r'(data-composition-id="main"[^>]*data-duration=")[^"]+',r'\g<1>8',source,count=1);(S/'render-test.html').write_text(source,encoding='utf8');args+=['--composition','render-test.html']
reuse=json.loads((OUT/'reused_assets.json').read_text(encoding='utf8'));env=os.environ.copy();env['PATH']=str(Path(reuse['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
with log.open('w',encoding='utf8') as stream:
    proc=subprocess.run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes',*args],cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,encoding='utf8')
text=log.read_text(encoding='utf8');summary={'job':job,'exit_code':proc.returncode,'log':str(log)}
if job in ('check','check-all','smoke-check'):
    decoder=json.JSONDecoder();obj=None
    for i,c in enumerate(text):
        if c=='{':
            try:
                candidate,_=decoder.raw_decode(text[i:])
                if isinstance(candidate,dict) and 'lint' in candidate:obj=candidate;break
            except json.JSONDecodeError:pass
    if obj:
        (OUT/'checks'/f'{job}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
        summary['ok']=obj['ok'];summary['passes']={k:{'ok':v.get('ok'),'errors':v.get('errorCount'),'warnings':v.get('warningCount')} for k,v in obj.items() if isinstance(v,dict) and 'ok' in v}
        summary['issues']=[{k:f.get(k) for k in ('code','selector','message','text','sourceFile','time')} for v in obj.values() if isinstance(v,dict) for f in v.get('findings',[]) if f.get('severity')=='error'][:18]
else:summary['tail']=text[-2400:]
(OUT/'checks'/f'{job}_receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False));sys.exit(proc.returncode)
