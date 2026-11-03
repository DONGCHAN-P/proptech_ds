"""Final local check/render/decode after editor handoff. Never uploads or generates media."""
from pathlib import Path
import argparse,hashlib,json,math,os,subprocess,time
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2];P=None
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ENV={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1',
     'HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),
     'HYPERFRAMES_EXTRACT_CACHE_DIR':str(D/'.render-cache'),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fingerprint():
    files={p.relative_to(P).as_posix():sha(p)for p in sorted(P.rglob('*'))if p.is_file()and not any(v in p.parts for v in ['.hyperframes','.thumbnails','node_modules'])and p.suffix in ['.html','.css','.js','.json','.woff2','.wav','.mp3','.mp4','.jpg','.png','.svg']}
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),files
def run(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    with log.open('wb')as out,Path(str(log)+'.stderr.log').open('wb')as err:
        p=subprocess.Popen([str(a)for a in cmd],cwd=R,env=ENV,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(D/'active_job.json',{'pid':p.pid,'command':list(map(str,cmd)),'log':str(log),'started_at_epoch':time.time(),'owner':'director_after_editor_handoff'})
        p.wait()
    save(D/'active_job.json',{'pid':p.pid,'exit_code':p.returncode,'elapsed_s':time.monotonic()-start,'log':str(log)})
    return p.returncode,time.monotonic()-start
def check():
    t=read(P/'timeline_resolved.json');assert t['timing_locked'];duration=t['duration_s'];starts={s['scene_id']:s['start_s']for s in t['scenes']}
    points={.04,duration-.04}
    for s in t['scenes']:points.add((s['start_s']+s['end_s'])/2)
    for b in t['inserts']:
        for edge in [b['start_s'],b['start_s']+b['duration_s']]:points.update([max(0,edge-.04),min(duration-.001,edge+.04)])
    for a in read(P/'phase_audit.json'):
        at=starts[a['scene_id']]+a['switch_s'];points.update([at-.05,at+.05])
    for a in read(P/'anchor_audit.json'):
        if a.get('local_s')is not None and a['scene_id']in starts:points.add(starts[a['scene_id']]+a['local_s']+.25)
    points=sorted(set(round(p,5)for p in points if 0<=p<duration));stamp,files=fingerprint();log=D/'evidence/final_check.json'
    code,elapsed=run(['npx.cmd','--no-install','hyperframes','check',P,'--at',','.join(map(str,points)),'--json','--snapshots','--timeout','20000'],log)
    report=read(log);assert code==0 and report['ok'] and not report.get('browserSkipped'),log
    stamp_after,files_after=fingerprint();assert stamp_after==stamp,'Check mutated render inputs; inspect before accepting'
    receipt={'status':'passed','project_sha256':stamp,'files':files,'samples':points,'sample_count':len(points),
       'elapsed_s':elapsed,'lint_errors':report['lint']['errorCount'],'runtime_errors':report['runtime']['errorCount'],
       'layout_findings':report['layout']['totalIssueCount'],'contrast_checked':report['contrast']['checked'],
       'timing_lock_sha256':sha(D/'locked_timing.json'),'actual_listening_performed':False,'continuous_playback_performed':False}
    save(D/'final_check_receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in ['files','samples']},ensure_ascii=False))
def render(version):
    lock=read(D/'locked_timing.json');assert read(D/'script_decision.json')['status']=='approved'
    assert read(D/'final_check_receipt.json')['project_sha256']==fingerprint()[0]
    assert read(D/'final_check_receipt.json')['timing_lock_sha256']==sha(D/'locked_timing.json')
    out=E/'outputs/top20-explain-v3/main'/f'top20_v6_free_{version}.mp4';out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists(),'Preserve prior output; use a new version'
    command=['npx.cmd','--no-install','hyperframes','render',P,'--output',out,'--fps','30','--quality','delivery','--workers','4'];log=D/'evidence'/f'render_{version}.log'
    receipt={'status':'started','command':list(map(str,command)),'source_project_sha256':fingerprint()[0],'timing_sha256':sha(D/'locked_timing.json'),
       'expected_duration_s':lock['duration_s'],'output':str(out),'new_paid_calls':0,'cloud_render':False,'actual_listening_performed':False,'continuous_playback_performed':False}
    save(D/f'render_receipt_{version}.json',receipt);print(json.dumps({'status':'render_started','output':str(out)},ensure_ascii=False),flush=True)
    code,elapsed=run(command,log);receipt.update(exit_code=code,elapsed_s=elapsed);save(D/f'render_receipt_{version}.json',receipt)
    assert code==0 and out.exists()and out.stat().st_size>0,log
    result=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels,duration','-of','json',str(out)],capture_output=True)
    assert result.returncode==0;probe=json.loads(result.stdout);v=next(s for s in probe['streams']if s['codec_type']=='video')
    assert(v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')and any(s['codec_type']=='audio'for s in probe['streams'])
    assert abs(float(probe['format']['duration'])-lock['duration_s'])<=1/30+.003
    code,decode_s=run([FF,'-v','error','-xerror','-i',out,'-f','null','-'],D/'evidence'/f'decode_{version}.log');assert code==0
    receipt.update(status='encoded_decode_passed_for_independent_QA',output_sha256=sha(out),bytes=out.stat().st_size,probe=probe,full_decode_passed=True,decode_s=decode_s)
    save(D/f'render_receipt_{version}.json',receipt);print(json.dumps({'status':receipt['status'],'output':str(out),'sha256':receipt['output_sha256'],'duration_s':probe['format']['duration']},ensure_ascii=False),flush=True)
def main():
    global P
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','render']);ap.add_argument('--project',required=True);ap.add_argument('--version',default='v1');a=ap.parse_args()
    P=Path(a.project).resolve();assert P.is_relative_to(E/'editor/top20-explain-v3/main')
    check()if a.action=='check'else render(a.version)
if __name__=='__main__':main()
