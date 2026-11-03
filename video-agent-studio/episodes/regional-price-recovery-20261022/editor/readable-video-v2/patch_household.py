from pathlib import Path
import json,shutil,subprocess,os,sys
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/readable-video-v2';P=O/'project';PATCH=O/'household-patch-project'
t=json.loads((P/'timing.json').read_text('utf-8'));s=next(s for s in t['scenes'] if s['id']=='L002');D=s['duration'];START=s['start']
shutil.copytree(P/'assets',PATCH/'assets',dirs_exist_ok=True);(PATCH/'compositions').mkdir(parents=True,exist_ok=True)
shutil.copy2(P/'compositions/L002.html',PATCH/'compositions/L002.html')
cap=(P/'compositions/captions.html').read_text('utf-8').replace('const clock={t:0};',f'const clock={{t:{START}}};').replace(f't:{t["duration"]},duration:{t["duration"]}',f't:{START+D},duration:{D}').replace(f'data-duration="{t["duration"]}"',f'data-duration="{D}"')
(PATCH/'compositions/captions.html').write_text(cap,'utf-8')
original=(P/'index.html').read_text('utf-8');head=original[:original.index('<body>')+6]
index=head+f'''<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{D}" data-fps="30"><div id="host-L002" class="clip" data-composition-id="L002" data-composition-src="compositions/L002.html" data-start="0" data-duration="{D}" data-track-index="1"></div><div id="caption-host" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{D}" data-track-kind="captions" data-track-index="2"></div></div><script>window.__timelines['main']=gsap.timeline({{paused:true}});</script></body></html>'''
(PATCH/'index.html').write_text(index,'utf-8');shutil.copy2(P/'hyperframes.json',PATCH/'hyperframes.json')
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));env=os.environ.copy();env['PATH']=str(Path(reuse['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
jobs={'check':['check','--at','7,11,14,25,49,75','--json','--max-issues','15'],'snapshot':['snapshot','--at','6,11,14,25','--no-end','--describe','false','--output',str(O/'checks/household-patch-preview')],'render':['render','--quality','looks','--fps','30','--workers','2','--output',str(O/'household_patch.mp4')]}
mode=sys.argv[1];log=O/'checks'/f'household-patch-{mode}.log'
with log.open('w',encoding='utf-8') as stream:p=subprocess.run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes',*jobs[mode]],cwd=PATCH,env=env,stdout=stream,stderr=subprocess.STDOUT)
record={'mode':mode,'exit_code':p.returncode,'source_start_frame':round(START*30),'patch_frames':round(D*30),'source_end_frame':round((START+D)*30),'duration':D,'log':str(log),'reason':'Keep accepted three-cup to two-plus-one household continuity; no narration or timing change'}
(O/'checks'/f'household-patch-{mode}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(record));sys.exit(p.returncode)
