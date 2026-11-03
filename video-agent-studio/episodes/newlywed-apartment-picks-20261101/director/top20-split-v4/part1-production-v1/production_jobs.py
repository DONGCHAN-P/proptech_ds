"""Local-only part1 source check, render and decoded evidence; no paid calls."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,subprocess,time

D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ENV={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1',
     'HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),
     'HYPERFRAMES_EXTRACT_CACHE_DIR':str(D/'.render-cache'),
     'XDG_CACHE_HOME':str(D/'.cache'),'XDG_STATE_HOME':str(D/'.preview-state'),
     'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stamp(): return datetime.now(timezone.utc).isoformat()
def fingerprint(p):
    files={x.relative_to(p).as_posix():sha(x)for x in sorted(p.rglob('*'))if x.is_file()
           and not any(a in x.parts for a in ['.hyperframes','.thumbnails','node_modules'])
           and x.suffix in ['.html','.css','.js','.json','.woff2','.wav','.mp3','.mp4','.jpg','.png','.svg']}
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),files
def run(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    with log.open('wb')as out,Path(str(log)+'.stderr.log').open('wb')as err:
        p=subprocess.Popen(list(map(str,cmd)),cwd=R,env=ENV,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(D/'active_job.json',{'pid':p.pid,'command':list(map(str,cmd)),'log':str(log),'status':'running','started_at':stamp()})
        p.wait()
    save(D/'active_job.json',{'pid':p.pid,'exit_code':p.returncode,'elapsed_s':time.monotonic()-start,'log':str(log),'status':'finished'})
    return p.returncode,time.monotonic()-start
def sample_plan(t):
    points={.04,t['total_s']-.04};samples=[]
    for s in t['scenes']:
        phases={}
        for v in s['sentences']:phases.setdefault(v['map_phase'],[]).append(v)
        for phase,vs in phases.items():
            v=vs[0];at=(v['start_s']+v['end_s'])/2
            points.add(at);samples.append({'scene_id':s['scene_id'],'phase':phase,'time_s':at})
        points.add(s['start_s']+.1)
    for b in t['brand_inserts']:
        for edge in [b['start_s'],b['start_s']+b['duration_s']]:
            points.update([max(0,edge-.04),min(t['total_s']-.001,edge+.04)])
    for c in sorted(t['captions'],key=lambda v:-len(v['text']))[:8]:points.add((c['start_s']+c['end_s'])/2)
    points.add(t['last_spoken_end_s']+.04)
    return sorted({round(p,6)for p in points}),samples

def check(p,v):
    lock=D/'locked_timing.json';t=read(lock);assert t['timing_locked'] and t['part']==1
    points,samples=sample_plan(t);before,files=fingerprint(p)
    log=D/'evidence'/v/'check.json'
    code,elapsed=run(['npx.cmd','--no-install','hyperframes','check',p,'--at',','.join(map(str,points)),'--json','--snapshots','--timeout','20000'],log)
    report=read(log)
    save(D/'evidence'/v/'check_summary.json',{'exit_code':code,'ok':report.get('ok'),'elapsed_s':elapsed,'samples':len(points),
         'lint':report.get('lint'),'runtime':report.get('runtime'),'layout':report.get('layout'),'contrast':report.get('contrast')})
    assert code==0 and report['ok'] and not report.get('browserSkipped'),log
    after,_=fingerprint(p);assert after==before,'Source changed during check'
    save(D/('check_receipt_'+v+'.json'),{'status':'passed','project':str(p),'source_sha256':before,'files':files,
         'timing_sha256':sha(lock),'sample_count':len(points),'points':points,'phase_samples':samples,
         'elapsed_s':elapsed,'actual_listening_performed':False,'continuous_playback_performed':False})
    print(json.dumps({'status':'check_passed','samples':len(points),'elapsed_s':elapsed}),flush=True)

def render(p,v):
    t=read(D/'locked_timing.json');auth=read(D/'production_authorization.json')
    assert auth['scope']['part']==1 and auth['scope']['cash_cap_krw']==0
    c=read(D/('check_receipt_'+v+'.json'));assert c['source_sha256']==fingerprint(p)[0]
    assert c['timing_sha256']==sha(D/'locked_timing.json')
    out=E/'outputs/top20-split-v4/part1'/('part1_free_'+v+'.mp4');out.parent.mkdir(parents=True,exist_ok=True)
    assert not out.exists(),'Preserve previous version'
    receipt={'status':'render_started','part':1,'output':str(out),'project':str(p),'source_sha256':c['source_sha256'],
             'timing_sha256':c['timing_sha256'],'started_at':stamp(),'expected_duration_s':t['total_s'],'paid_calls':0,'cash_cost_krw':0}
    rp=D/('render_receipt_'+v+'.json');save(rp,receipt)
    print(json.dumps({'status':'render_started','output':str(out)}),flush=True)
    code,elapsed=run(['npx.cmd','--no-install','hyperframes','render',p,'--output',out,'--fps','30','--quality','delivery','--workers','4'],D/'evidence'/v/'render.log')
    receipt.update(exit_code=code,elapsed_s=elapsed);save(rp,receipt);assert code==0 and out.stat().st_size>0
    assert c['source_sha256']==fingerprint(p)[0],'Source changed during render'
    result=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels,duration','-of','json',str(out)],capture_output=True)
    assert result.returncode==0;probe=json.loads(result.stdout)
    video=next(s for s in probe['streams']if s['codec_type']=='video')
    assert(video['width'],video['height'],video['r_frame_rate'])==(1920,1080,'30/1')
    assert any(s['codec_type']=='audio'for s in probe['streams'])
    assert abs(float(probe['format']['duration'])-t['total_s'])<1/30+.005
    code,decode_s=run([FF,'-v','error','-xerror','-i',out,'-f','null','-'],D/'evidence'/v/'decode.log');assert code==0
    receipt.update(status='rendered_full_decode_passed',finished_at=stamp(),output_sha256=sha(out),bytes=out.stat().st_size,probe=probe,
                   full_decode_exit_code=0,decode_elapsed_s=decode_s,actual_listening_performed=False,continuous_playback_performed=False)
    save(rp,receipt);print(json.dumps({'status':receipt['status'],'sha256':receipt['output_sha256'],'duration_s':probe['format']['duration']},ensure_ascii=False),flush=True)

def evidence(p,v):
    from PIL import Image,ImageDraw,ImageFont
    t=read(D/'locked_timing.json');receipt=read(D/('render_receipt_'+v+'.json'));video=Path(receipt['output'])
    assert sha(video)==receipt['output_sha256'];_,samples=sample_plan(t)
    for s in t['scenes']:
        if s['scene_kind']in ['intro','outro']:
            for j,sen in enumerate(s['sentences']):
                samples.append({'scene_id':s['scene_id'],'phase':f'sentence_{j+1:02d}','time_s':(sen['start_s']+sen['end_s'])/2})
    for s in t['scenes'][1:]:
        for delta,label in [(-.04,'before'),(.04,'after')]:
            samples.append({'scene_id':s['scene_id'],'phase':'cut_'+label,'time_s':s['start_s']+delta})
    for j,c in enumerate(sorted(t['captions'],key=lambda c:-len(c['text']))[:8]):
        samples.append({'scene_id':'CAPTION','phase':f'long_{j+1:02d}','time_s':(c['start_s']+c['end_s'])/2})
    # Every content scene/phase plus exact brand/last-speech/final boundaries from the encoded MP4.
    for b in t['brand_inserts']:samples.append({'scene_id':'BRAND','phase':b['kind'],'time_s':b['start_s']+.5})
    samples.extend([{'scene_id':'END','phase':'last_speech_plus_2','time_s':t['last_spoken_end_s']+2},
                    {'scene_id':'END','phase':'last_frame','time_s':t['total_s']-.08}])
    folder=E/'qa/top20-split-v4/part1-production-v1'/v/'encoded_frames';folder.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(samples):
        name=f"{i:02d}_{s['scene_id']}_{s['phase']}.jpg";dest=folder/name
        command=[str(FF),'-v','error','-ss',str(s['time_s']),'-i',str(video),'-frames:v','1','-q:v','2','-y',str(dest)]
        r=subprocess.run(command,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert r.returncode==0 and dest.exists()
        s.update(file=str(dest),sha256=sha(dest))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    sheets=[]
    for start in range(0,len(samples),12):
        group=samples[start:start+12];im=Image.new('RGB',(1440,4*297),'#e7e9ea');draw=ImageDraw.Draw(im)
        for j,s in enumerate(group):
            x=(j%3)*480;y=(j//3)*297
            photo=Image.open(s['file']).convert('RGB');photo.thumbnail((480,270));im.paste(photo,(x,y))
            draw.text((x+5,y+273),f"{start+j:02d} {s['time_s']:.2f}s {s['scene_id']} {s['phase']}",font=font,fill='#173348')
        dest=folder.parent/f'contact_{start//12+1:02d}.jpg';im.save(dest,quality=92);sheets.append(str(dest))
    save(folder.parent/'encoded_frame_manifest.json',{'video':str(video),'video_sha256':sha(video),'frames':samples,'contact_sheets':sheets,
            'scope':'decoded MP4 samples, not continuous playback or listening','actual_listening_performed':False})
    print(json.dumps({'encoded_frames':len(samples),'contact_sheets':sheets},ensure_ascii=False),flush=True)

def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['check','render','evidence']);a.add_argument('--project',type=Path,required=True);a.add_argument('--version',default='v1');v=a.parse_args()
    p=v.project.resolve();p.relative_to(E/'editor/top20-split-v4/part1-production-v1')
    assert re.fullmatch(r'v\d+',v.version)
    {'check':check,'render':render,'evidence':evidence}[v.action](p,v.version)
if __name__=='__main__': main()
