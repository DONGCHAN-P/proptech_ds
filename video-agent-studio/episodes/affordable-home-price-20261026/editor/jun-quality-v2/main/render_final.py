from pathlib import Path
import json,hashlib,subprocess,os,time
HERE=Path(__file__).resolve().parent;EP=HERE.parents[2];ROOT=EP.parents[2]
out=EP/'outputs/jun-quality-v2/main';out.mkdir(parents=True,exist_ok=True)
hf='C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs'
ff=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin'
probe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
env={**os.environ,'PATH':str(ff)+';'+str(probe)+';'+os.environ['PATH'],'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1'}
target=out/'affordable_home_price_jun_quality_v2.mp4'
assert not target.exists(),'Versioned output already exists; do not overwrite'
command=['node',hf,'render',str(HERE/'project'),'--output',str(target),'--fps','30','--quality','delivery','--workers','4']
source={str(p.relative_to(HERE/'project')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'project').rglob('*.html'))}
record={'command':command,'source_html_sha256':source,'audio_mix_sha256':hashlib.sha256((HERE/'project/assets/mix.m4a').read_bytes()).hexdigest(),'start_epoch':time.time(),'new_paid_calls':0}
(HERE/'render_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
with (HERE/'render.log').open('wb') as stream:r=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env)
record.update(exit_code=r.returncode,elapsed_s=time.time()-record['start_epoch'])
if target.exists():record.update(output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),output_size=target.stat().st_size,output=str(target))
(HERE/'render_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ['source_html_sha256','command']}))
raise SystemExit(r.returncode)
