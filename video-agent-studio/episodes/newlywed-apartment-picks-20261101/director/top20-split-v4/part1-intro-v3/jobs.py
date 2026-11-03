"""Local HyperFrames prefix render, lossless body video splice and actual media evidence."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ENV={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),'HYPERFRAMES_EXTRACT_CACHE_DIR':str(D/'.extract-cache'),'XDG_STATE_HOME':str(D/'.preview-state'),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    with log.open('wb')as o,Path(str(log)+'.stderr.log').open('wb')as e:
        r=subprocess.Popen(list(map(str,cmd)),cwd=R,env=ENV,stdout=o,stderr=e,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(D/'active_job.json',{'pid':r.pid,'command':list(map(str,cmd)),'log':str(log)});r.wait()
    assert r.returncode==0,log
    return time.monotonic()-started
def fingerprint(p):
    fs={x.relative_to(p).as_posix():sha(x)for x in p.rglob('*')if x.is_file()and not any(a in x.parts for a in ['.hyperframes','.thumbnails'])and x.suffix in ['.html','.css','.js','.json','.woff2','.wav','.png','.mp4']}
    return hashlib.sha256(json.dumps(fs,sort_keys=True).encode()).hexdigest(),fs
def check(p,v):
    t=read(D/'locked_timing.json');points={.1,.8,1.6,2.8,4.5,7,9.8,11.2,13.5,17,18.5,20.9,23,26.3,27.5,29,31,34.2,36.3,38.5,40.4,42.2,44.5,45.4,47.7,48.49,48.7,50,t['prefix_end_s']-.06}
    for s in t['intro_sentences']:points.update([s['start_s']+.12,(s['start_s']+s['end_s'])/2])
    before,files=fingerprint(p);path=D/'evidence'/v/'check.json'
    run(['npx.cmd','--no-install','hyperframes','check',p,'--at',','.join(map(str,sorted(points))),'--json','--snapshots','--timeout','20000'],path)
    r=read(path);assert r['ok']and not r.get('browserSkipped');assert fingerprint(p)[0]==before
    save(D/f'check_{v}.json',{'status':'passed','project':str(p),'project_sha256':before,'files':files,'points':sorted(points),'source_timing_sha256':sha(D/'locked_timing.json'),'actual_listening':False})
    print(json.dumps({'status':'source_check_passed','points':len(points)}),flush=True)
def render(p,v):
    t=read(D/'locked_timing.json');c=read(D/f'check_{v}.json');assert c['project_sha256']==fingerprint(p)[0]
    folder=E/'outputs/top20-split-v4/intro-rationale-v3';folder.mkdir(parents=True,exist_ok=True);out=folder/f'intro_prefix_{v}.mp4';assert not out.exists()
    print(json.dumps({'status':'prefix_render_started','duration_s':t['prefix_end_s']}),flush=True)
    elapsed=run(['npx.cmd','--no-install','hyperframes','render',p,'--output',out,'--fps','30','--quality','delivery','--workers','2'],D/'evidence'/v/'render.log')
    assert fingerprint(p)[0]==c['project_sha256']
    save(D/f'prefix_render_{v}.json',{'status':'rendered','project':str(p),'project_sha256':c['project_sha256'],'output':str(out),'sha256':sha(out),'elapsed_s':elapsed,'new_paid_calls':0})
    print(json.dumps({'status':'prefix_rendered','output':str(out)}),flush=True)
def probe(p):
    r=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels,start_time','-of','json',str(p)],capture_output=True);assert r.returncode==0;return json.loads(r.stdout)
def assemble(p,v):
    t=read(D/'locked_timing.json');prefix=Path(read(D/f'prefix_render_{v}.json')['output']);old=Path(t['original_video']);assert sha(old)==t['original_video_sha256']
    out=prefix.parent/f'part1_intro_revised_{v}.mp4';assert not out.exists();work=D/'media'/v;work.mkdir(parents=True,exist_ok=True)
    tail=work/'tail_video.mp4';joined=work/'joined_video.mp4'
    run([FF,'-v','error','-y','-ss',str(t['stream_copy_keyframe_s']),'-i',old,'-map','0:v:0','-an','-c:v','copy',tail],D/'evidence'/v/'tail_copy.log')
    pt=probe(tail);sv=next(x for x in pt['streams']if x['codec_type']=='video');assert int(sv['nb_frames'])==18006-t['stream_copy_keyframe']
    pp=probe(prefix);pv=next(x for x in pp['streams']if x['codec_type']=='video');assert int(pv['nb_frames'])==t['prefix_frames']
    listing=work/'join.ffconcat';listing.write_text("ffconcat version 1.0\nfile '"+prefix.as_posix()+"'\nduration "+f"{t['prefix_end_s']:.9f}"+"\nfile '"+tail.as_posix()+"'\n",encoding='utf-8')
    run([FF,'-v','error','-y','-f','concat','-safe','0','-i',listing,'-map','0:v:0','-c:v','copy','-an',joined],D/'evidence'/v/'concat.log')
    run([FF,'-v','error','-y','-i',joined,'-i',t['master_audio'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',f"{t['total_s']:.9f}",'-movflags','+faststart',out],D/'evidence'/v/'mux.log')
    q=probe(out);vv=next(x for x in q['streams']if x['codec_type']=='video');assert int(vv['nb_frames'])==t['total_frames']
    assert abs(float(q['format']['duration'])-t['total_s'])<.04
    run([FF,'-v','error','-xerror','-i',out,'-f','null','-'],D/'evidence'/v/'full_decode.log')
    receipt={'status':'assembled_strict_decode_passed','video':str(out),'video_sha256':sha(out),'prefix':str(prefix),'prefix_sha256':sha(prefix),'old_video_sha256':sha(old),'duration_s':float(q['format']['duration']),'probe':q,'tail_stream_copy':True,'prefix_frames':t['prefix_frames'],'body_copy_frames':18006-t['stream_copy_keyframe'],'actual_listening':False,'cash_cost_krw':0}
    save(D/f'assembly_{v}.json',receipt);print(json.dumps({'status':receipt['status'],'video':str(out),'sha256':receipt['video_sha256'],'duration_s':receipt['duration_s']}),flush=True)
def evidence(p,v):
    from PIL import Image,ImageDraw,ImageFont
    t=read(D/'locked_timing.json');r=read(D/f'assembly_{v}.json');video=Path(r['video']);assert sha(video)==r['video_sha256']
    samples=[{'purpose':'motion','time_s':z}for z in [.15,.6,1.2,2,2.8,3.6,4.5,7,10.5,11.5,13,14.7,16.8,18.5,21.5,23.5,25.6,26.4,27.2,28,29.3,31.8,34.3,35.8,37.8,40.5,41.5,43.8,45.3,46.4,47.8,48.47,48.6,t['prefix_end_s']-.04,t['prefix_end_s']+.04]]
    for s in t['body_scenes']:samples.append({'purpose':s['scene_id'],'time_s':s['start_s']+3})
    samples.extend([{'purpose':'last_speech_hold','time_s':t['last_spoken_end_s']+2},{'purpose':'outro','time_s':t['brand_outro']['start_s']+5},{'purpose':'last_frame','time_s':t['total_s']-.05}])
    folder=E/'qa/top20-split-v4/intro-rationale-v3'/v/'encoded_frames';folder.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(samples):
        dest=folder/f"{i:02d}_{s['purpose']}.jpg";result=subprocess.run([str(FF),'-v','error','-y','-ss',str(s['time_s']),'-i',str(video),'-frames:v','1','-q:v','2',str(dest)],capture_output=True);assert result.returncode==0;s.update(file=str(dest),sha256=sha(dest))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);contacts=[]
    for k in range(0,len(samples),12):
        im=Image.new('RGB',(1440,1188),'#e7e9ea');draw=ImageDraw.Draw(im)
        for i,s in enumerate(samples[k:k+12]):
            x=i%3*480;y=i//3*297;pic=Image.open(s['file']);pic.thumbnail((480,270));im.paste(pic,(x,y));draw.text((x+5,y+273),f"{i+k:02d} {s['time_s']:.3f}s {s['purpose']}",font=font,fill='#173348')
        dest=folder.parent/f'contact_{k//12+1:02d}.jpg';im.save(dest,quality=94);contacts.append(str(dest))
    save(folder.parent/'encoded_manifest.json',{'video':str(video),'video_sha256':sha(video),'frames':samples,'contacts':contacts,'actual_listening':False,'continuous_playback':False})
    print(json.dumps({'status':'encoded_evidence_ready','frames':len(samples),'folder':str(folder.parent)}),flush=True)
def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['check','render','assemble','evidence']);a.add_argument('--project',type=Path,required=True);a.add_argument('--version',default='v1');o=a.parse_args();p=o.project.resolve();p.relative_to(E/'editor/top20-split-v4/intro-rationale-v3');{'check':check,'render':render,'assemble':assemble,'evidence':evidence}[o.action](p,o.version)
if __name__=='__main__':main()
