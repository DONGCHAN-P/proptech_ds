"""Offline check/snapshot/render/encoded QA runner. Never uploads.
python local_jobs.py check main
python local_jobs.py render main --version v1
"""
from pathlib import Path
import argparse,hashlib,json,math,os,subprocess,time,urllib.request
H=Path(__file__).resolve().parent;E=H.parents[1];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),'HYPERFRAMES_EXTRACT_CACHE_DIR':str(H/'.render-cache'),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def project(k):
 assert k=='main','This runner handles main only'
 return H/'main'
def fingerprint(p):
 records={str(q.relative_to(p)).replace('\\','/'):sha(q) for q in sorted(p.rglob('*')) if q.is_file() and not any(part in q.parts for part in ['.hyperframes','.thumbnails','node_modules']) and q.suffix in ['.html','.css','.js','.woff2','.wav','.mp3','.m4a','.mp4','.jpg','.svg']}
 return hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),records
def run(argv,log,timeout=None):
 begin=time.time();Path(log).parent.mkdir(parents=True,exist_ok=True)
 with Path(log).open('wb') as stdout,Path(str(log)+'.stderr.log').open('wb') as stderr:
  p=subprocess.Popen([str(v) for v in argv],cwd=R,env=env,stdout=stdout,stderr=stderr)
  save(H/'active_local_job.json',{'pid':p.pid,'command':list(map(str,argv)),'log':str(log),'started_at_epoch':begin,'owner':'director_after_editor_handoff'})
  p.wait(timeout=timeout)
 save(H/'active_local_job.json',{'pid':p.pid,'log':str(log),'exit_code':p.returncode,'elapsed_s':time.time()-begin,'owner':'director_after_editor_handoff'})
 return p,round(time.time()-begin,3)
def schedule(k):
 if k=='main':
  t=read(H/'timeline_resolved.json');ss=t['scenes'];return t['duration_s'],ss
 c=read(project(k)/'clip_contract.json');return c['duration_s'],c['placements']
def check(k):
 p=project(k);duration,ss=schedule(k);times=[(s['start_s']+s['end_s'])/2 for s in ss]
 if k=='main':
  t=read(H/'timeline_resolved.json');lock=read(t['source_timing'])
  for b in lock.get('brand_visuals',[]):times.extend([b['start_s']+.04,b['start_s']+b['duration_s']-.04])
  times.extend([.04,duration-.04])
 else:times.extend([duration-3+.04,duration-.04])
 times=sorted(set(round(t,5) for t in times));stamp,files=fingerprint(p)
 report=H/'evidence'/f'check-{k}-locked.json'
 cp,secs=run(['npx.cmd','--no-install','hyperframes','check',p,'--at',','.join(map(str,times)),'--json','--snapshots','--timeout','20000'],report)
 j=read(report);assert j['ok'],f'{k}: check failed ({report})'
 assert not j.get('browserSkipped'),f'{k}: browser checks did not run'
 save(H/'evidence'/f'check-{k}-receipt.json',{'project_sha256':stamp,'files':files,'exit_code':cp.returncode,'report':str(report),'elapsed_s':secs,'samples':times,'lint_errors':j['lint']['errorCount'],'lint_warnings':j['lint']['warningCount'],'runtime_errors':j['runtime']['errorCount'],'layout_findings':j['layout']['totalIssueCount'],'contrast_checks':j['contrast']['checked'],'motion_enabled':j.get('motion',{}).get('enabled',False),'timing_locked':True,'actual_listening':False,'continuous_playback':False})
 # check keeps at most five automatic snapshots; explicit snapshot captures every scene slot.
 out=H/'evidence'/f'snapshots-{k}-locked'
 sp,secs=run(['npx.cmd','--no-install','hyperframes','snapshot',p,'--at',','.join(map(str,times)),'--no-end','--describe','false','--output',out],H/'evidence'/f'snapshot-{k}-locked.log')
 assert sp.returncode==0 and len(list(out.glob('frame*.png')))>=len(times),f'{k}: missing snapshots'
 print(json.dumps({'target':k,'check':True,'samples':len(times),'snapshots':len(list(out.glob('frame*.png'))),'lint_warnings':j['lint']['warningCount'],'project_sha256':stamp}),flush=True)
def preview():
 p=H/'main';cp,secs=run(['npx.cmd','--no-install','hyperframes','preview',p,'--background','--port','3049'],H/'evidence/preview.log')
 ok=False
 try:ok=urllib.request.urlopen('http://127.0.0.1:3049/',timeout=8).status==200
 except Exception:pass
 save(H/'evidence/preview_receipt.json',{'url':'http://localhost:3049/#project/main','http_200':ok,'exit_code':cp.returncode})
 assert ok,'preview server did not respond'
def render(k,version):
 p=project(k);duration,ss=schedule(k);build=read(H/'build_receipt.json');assert build['timing_locked'] and build['audio_connected']
 if k!='main':assert read(p/'clip_contract.json')['timing_locked']
 check_receipt=read(H/'evidence'/f'check-{k}-receipt.json');stamp,files=fingerprint(p)
 assert check_receipt['project_sha256']==stamp,'Project changed after checks; rerun affected check'
 assert duration>480,'Enhanced main must exceed 480 seconds'
 assert Path(read(H/'timeline_resolved.json')['source_timing']).resolve()==(E/'director/top20-enhance-v2/locked_timing.json').resolve(),'Use the enhanced timing lock for production'
 out=E/'outputs/top20-enhance-v2/main';out.mkdir(parents=True,exist_ok=True)
 target=out/f'top20_main_enhanced_{version}.mp4';assert not target.exists(),'Preserve existing version; pass a new --version'
 log=H/'evidence'/f'render-{k}-{version}.log';cmd=['npx.cmd','--no-install','hyperframes','render',p,'--output',target,'--fps','30','--quality','delivery','--workers','4']
 rec={'target':k,'command':list(map(str,cmd)),'project_sha256':stamp,'source_files':files,'audio_input_sha256':sha(p/'assets/narration.wav'),'planned_duration_s':duration,'started_at_epoch':time.time(),'new_paid_calls':0,'cloud_render':False}
 save(H/f'render_receipt_{k}_{version}.json',rec);print(json.dumps({'target':k,'status':'render_started','output':str(target)}),flush=True)
 cp,elapsed=run(cmd,log);rec.update(exit_code=cp.returncode,elapsed_s=elapsed,log=str(log));save(H/f'render_receipt_{k}_{version}.json',rec)
 assert cp.returncode==0 and target.exists() and target.stat().st_size>0,f'render failed: {log}'
 pp=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=index,codec_type,width,height,r_frame_rate,sample_rate,channels,duration','-of','json',str(target)],capture_output=True)
 probe=json.loads(pp.stdout);v=next(s for s in probe['streams'] if s['codec_type']=='video');au=[s for s in probe['streams'] if s['codec_type']=='audio']
 assert (v['width'],v['height'])==(1920,1080);assert v['r_frame_rate']=='30/1';assert au;assert abs(float(probe['format']['duration'])-duration)<=1/30+.002
 dp,de=run([FF,'-v','error','-xerror','-i',target,'-f','null','-'],H/'evidence'/f'decode-{k}-{version}.log');assert dp.returncode==0,'Full decode failed'
 rec.update(output=str(target),output_sha256=sha(target),bytes=target.stat().st_size,probe=probe,full_decode_passed=True,actual_listening=False,continuous_playback=False,status='encoded_ready_for_independent_QA_frames_following')
 save(H/f'render_receipt_{k}_{version}.json',rec)
 print(json.dumps({'target':k,'status':'encoded_ready_for_QA','output':str(target),'sha256':rec['output_sha256'],'duration_s':probe['format']['duration']}),flush=True)
 extract(k,version)
def extract(k,version):
 rec=read(H/f'render_receipt_{k}_{version}.json');target=Path(rec['output']);duration,ss=schedule(k)
 assert rec.get('full_decode_passed') and sha(target)==rec['output_sha256']
 probe=rec['probe']
 decoded=H/'evidence'/f'encoded-{k}-{version}';decoded.mkdir(exist_ok=True)
 # All cut boundaries: previous frame / first frame / following frame, plus each scene midpoint.
 times={.04,max(0,duration-.04)}
 for s in ss:
  b=s['start_s'];times.update([max(0,b-1/30),b,min(duration-.001,b+1/30),(s['start_s']+s['end_s'])/2])
 if k=='main':
  lock=read(read(H/'timeline_resolved.json')['source_timing'])
  for b in lock.get('brand_visuals',[]):
   for edge in [b['start_s'],b['start_s']+b['duration_s']]:times.update([max(0,edge-1/30),min(duration-.001,edge),min(duration-.001,edge+1/30)])
 # A seek after the final displayed frame can exit0 without producing an image.
 last_decodable=max(0,(math.ceil(duration*30)-1)/30-.001)
 times=sorted({min(t,last_decodable) for t in times});frame_manifest=[]
 for i,t in enumerate(times):
  name=decoded/f'{i:03d}-{t:.3f}s.jpg';ep=subprocess.run([str(FF),'-v','error','-ss',str(t),'-i',str(target),'-frames:v','1','-q:v','2','-y',str(name)],capture_output=True)
  if ep.returncode!=0 or not name.exists():
   (decoded/'extract-error.log').write_bytes(ep.stderr)
   raise RuntimeError(f'Frame extraction failed at {t}: {name}')
  frame_manifest.append({'time_s':t,'file':str(name),'sha256':sha(name)})
 save(decoded/'frames.json',frame_manifest)
 rec.update(output=str(target),output_sha256=sha(target),bytes=target.stat().st_size,probe=probe,full_decode_passed=True,decoded_frame_count=len(frame_manifest),decoded_frame_manifest=str(decoded/'frames.json'),actual_listening=False,continuous_playback=False)
 save(H/f'render_receipt_{k}_{version}.json',rec)
 print(json.dumps({'target':k,'status':'render_and_decode_complete','duration_s':probe['format']['duration'],'frames':len(frame_manifest),'sha256':rec['output_sha256'],'output':str(target)}),flush=True)
ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','preview','render','extract']);ap.add_argument('target',nargs='?',default='main',choices=['main']);ap.add_argument('--version',default='v1');a=ap.parse_args()
ks=['main']
if a.action=='preview':preview()
else:
 for k in ks:check(k) if a.action=='check' else extract(k,a.version) if a.action=='extract' else render(k,a.version)
