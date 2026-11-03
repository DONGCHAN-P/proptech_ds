"""Run installed HyperFrames with the project's existing local media tools."""
from pathlib import Path
import json, os, shutil, subprocess, sys
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1];ROOT=EP.parents[2];QA=EP/'qa/monthly-v2'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin'
FP=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
env=os.environ.copy();env['PATH']=str(FF)+os.pathsep+str(FP)+os.pathsep+env.get('PATH','')
args=sys.argv[1:];assert args and args[0] in ['render','check','timeline','preview']
log=QA/('hyperframes_'+args[0]+'.log')
with log.open('w',encoding='utf-8') as out:
    p=subprocess.run([shutil.which('npx.cmd'),'--no-install','hyperframes',*args],cwd=HERE/'project',env=env,stdout=out,stderr=subprocess.STDOUT,encoding='utf-8')
print(json.dumps({'command':args[0],'exit_code':p.returncode,'log':str(log)}));sys.exit(p.returncode)
