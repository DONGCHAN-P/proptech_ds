"""Check/render the HyperFrames insert reel and assemble without re-encoding body again."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ENV={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),'HYPERFRAMES_EXTRACT_CACHE_DIR':str(D/'.extract-cache'),'XDG_STATE_HOME':str(D/'.preview-state'),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    with log.open('wb')as o,Path(str(log)+'.stderr.log').open('wb')as er:
        p=subprocess.Popen(list(map(str,cmd)),cwd=R,env=ENV,stdout=o,stderr=er,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(D/'active_job.json',{'pid':p.pid,'log':str(log)});p.wait()
    assert p.returncode==0,log
    return time.monotonic()-started
def probe(p):
    z=subprocess.run([str(FP),'-v','error','-show_entries','format=duration,size:stream=codec_type,codec_name,nb_frames,r_frame_rate,width,height,sample_rate,channels','-of','json',str(p)],capture_output=True,check=True)
    return json.loads(z.stdout)
def framecount(p):return int(next(s['nb_frames']for s in probe(p)['streams']if s['codec_type']=='video'))
def fingerprint(p):
    rows={x.relative_to(p).as_posix():sha(x)for x in p.rglob('*')if x.is_file()and not any(a in x.parts for a in ['.hyperframes','.thumbnails'])and x.suffix in ['.html','.css','.js','.json','.mp4','.wav','.woff2','.jpg']}
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
def check(p,v):
    plan=read(D/'transition_plan.json');pts={.1,.7,2.5,5.7,7.3,8.8,10.5,12.6}
    for u in plan['photos']:pts.update([u['reel_start_s']+.25,u['reel_start_s']+.8,u['reel_start_s']+u['duration_s']/2,u['reel_end_s']-.12])
    before=fingerprint(p);out=D/'evidence'/v/'check.json'
    run(['npx.cmd','--no-install','hyperframes','check',p,'--at',','.join(f'{z:.6f}'for z in sorted(pts)),'--json','--snapshots','--timeout','20000'],out)
    r=read(out);assert r['ok']and not r.get('browserSkipped');assert fingerprint(p)==before
    save(D/f'check_{v}.json',{'status':'passed','project':str(p),'fingerprint':before,'points':sorted(pts),'actual_listening':False})
    print(json.dumps({'status':'source_check_passed','points':len(pts)}),flush=True)
def render(p,v):
    check=read(D/f'check_{v}.json');assert fingerprint(p)==check['fingerprint']
    out=E/'outputs/top20-split-v4/map-clean-v1';out.mkdir(parents=True,exist_ok=True);mp4=out/f'insert_reel_{v}.mp4';assert not mp4.exists()
    sec=run(['npx.cmd','--no-install','hyperframes','render',p,'--output',mp4,'--fps','30','--quality','delivery','--workers','2'],D/'evidence'/v/'render.log')
    assert fingerprint(p)==check['fingerprint']
    save(D/f'render_{v}.json',{'status':'rendered','video':str(mp4),'sha256':sha(mp4),'project':str(p),'fingerprint':check['fingerprint'],'elapsed_s':sec})
    print(json.dumps({'status':'reel_rendered','video':str(mp4),'elapsed_s':sec}),flush=True)
def assemble(p,v):
    t=read(D/'locked_timing.json');plan=t['transition_plan'];r=read(D/f'render_{v}.json');assert sha(r['video'])==r['sha256']
    base=Path(read(D/'clean_receipt_v2.json')['video']);reel=Path(r['video']);work=D/'media'/v;work.mkdir(parents=True,exist_ok=True)
    keys=[0,t['insert_duration_s']]+[u['reel_end_s']for u in plan['photos']]
    uniform=work/'reel_splice_ready.mp4'
    run([FF,'-v','error','-y','-i',reel,'-an','-vf','setpts=N/(30*TB)','-c:v','libx264','-preset','fast','-crf','17','-threads','6','-pix_fmt','yuv420p','-bf','0','-r','30','-force_key_frames',','.join(f'{z:.9f}'for z in keys),'-video_track_timescale','15360',uniform],D/'evidence'/v/'reel_encode.log')
    assert framecount(uniform)==round(plan['reel_total_s']*30)
    segments=[]
    def add(source,start,end,purpose):
        if end-start<.001:return
        start=round(start*30)/30;end=round(end*30)/30;segments.append({'source':str(source),'start_s':start,'end_s':end,'duration_s':end-start,'purpose':purpose})
    cut=t['insert_at_s'];add(base,0,cut,'opening');add(uniform,0,t['insert_duration_s'],'criteria')
    cursor=cut
    for u in plan['photos']:
        add(base,cursor,u['source_start_s'],'body');add(uniform,u['reel_start_s'],u['reel_end_s'],f"R{u['rank']}_photo");cursor=u['source_end_s']
    add(base,cursor,602.3333333333333,'body_outro')
    for i,s in enumerate(segments):
        dest=work/f'segment_{i:02d}.mp4'
        run([FF,'-v','error','-y','-ss',f"{s['start_s']:.9f}",'-i',s['source'],'-t',f"{s['duration_s']:.9f}",'-map','0:v:0','-an','-c:v','copy',dest],D/'evidence'/v/f'cut_{i:02d}.log')
        assert framecount(dest)==round(s['duration_s']*30),(s,framecount(dest));s['file']=str(dest)
    listing=work/'join.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join("file '"+Path(s['file']).as_posix()+"'\nduration "+f"{s['duration_s']:.9f}"+'\n'for s in segments),encoding='utf-8')
    joined=work/'joined_video.mp4';run([FF,'-v','error','-y','-f','concat','-safe','0','-i',listing,'-map','0:v:0','-an','-c:v','copy',joined],D/'evidence'/v/'concat.log')
    assert framecount(joined)==t['total_frames']
    final=reel.parent/f'part1_map_clean_photo_{v}.mp4';assert not final.exists()
    run([FF,'-v','error','-y','-i',joined,'-i',t['master_audio'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',f"{t['total_s']:.9f}",'-movflags','+faststart',final],D/'evidence'/v/'mux.log')
    assert framecount(final)==t['total_frames'];q=probe(final);assert abs(float(q['format']['duration'])-t['total_s'])<.04
    run([FF,'-v','error','-xerror','-i',final,'-f','null','-'],D/'evidence'/v/'full_decode.log')
    receipt={'status':'assembled_strict_decode_passed','video':str(final),'video_sha256':sha(final),'probe':q,'duration_s':float(q['format']['duration']),'segments':segments,'master_audio_sha256':sha(t['master_audio']),'source_project':str(p),'cash_cost_krw':0,'actual_listening':False,'continuous_playback':False}
    save(D/f'assembly_{v}.json',receipt);print(json.dumps({k:receipt[k]for k in ['status','video','video_sha256','duration_s']}),flush=True)
def evidence(p,v):
    from PIL import Image,ImageDraw,ImageFont
    a=read(D/f'assembly_{v}.json');t=read(D/'locked_timing.json');video=Path(a['video']);assert sha(video)==a['video_sha256']
    samples=[{'purpose':'criteria','time_s':z}for z in [39.65,40.3,42.1,45.3,47.8,49.8,52.45,53.2,56.8]]
    for u in t['transition_plan']['photos']:
        s=u['final_start_s'];e=u['final_end_s'];samples.extend({'purpose':f"R{u['rank']}_{name}",'time_s':z}for name,z in [('before',s-.04),('wipe',s+.3),('hero',s+1.2),('exit',e-.25),('map',e+.12)])
    for s in t['body_scenes'][:10]:samples.append({'purpose':s['scene_id']+'_map','time_s':s['start_s']+8})
    samples.extend([{'purpose':'outro','time_s':t['brand_outro']['start_s']+5},{'purpose':'final','time_s':t['total_s']-.05}])
    folder=E/'qa/top20-split-v4/map-clean-v1'/v/'encoded_frames';folder.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(samples):
        out=folder/f"{i:02d}_{s['purpose']}.jpg";subprocess.run([str(FF),'-v','error','-y','-ss',str(s['time_s']),'-i',str(video),'-frames:v','1','-q:v','2',str(out)],check=True,capture_output=True);s.update(file=str(out),sha256=sha(out))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);contacts=[]
    for k in range(0,len(samples),12):
        im=Image.new('RGB',(1440,1188),'#e7e9ea');dr=ImageDraw.Draw(im)
        for i,s in enumerate(samples[k:k+12]):
            x=i%3*480;y=i//3*297;pic=Image.open(s['file']);pic.thumbnail((480,270));im.paste(pic,(x,y));dr.text((x+5,y+273),f"{k+i:02d} {s['time_s']:.3f}s {s['purpose']}",font=font,fill='#173348')
        f=folder.parent/f'contact_{k//12+1:02d}.jpg';im.save(f,quality=94);contacts.append(str(f))
    save(folder.parent/'encoded_manifest.json',{'video':str(video),'video_sha256':a['video_sha256'],'frames':samples,'contacts':contacts,'actual_listening':False,'continuous_playback':False})
    print(json.dumps({'status':'encoded_evidence_ready','frames':len(samples),'folder':str(folder.parent)}),flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','render','assemble','evidence']);ap.add_argument('--project',type=Path,required=True);ap.add_argument('--version',default='v1');a=ap.parse_args();p=a.project.resolve();p.relative_to(E/'editor/top20-split-v4/map-clean-v1');globals()[a.action](p,a.version)
if __name__=='__main__':main()
