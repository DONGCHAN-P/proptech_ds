from pathlib import Path
import json,shutil,subprocess,os,hashlib,sys
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/guide-v3';P=O/'project';R=O/'correction-L005';Q=R/'project';C=O/'checks';D=EP/'director/guide-v3'
def read(p):return json.loads(p.read_text('utf-8'))
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=read(P/'timing.json');s=next(s for s in t['scenes'] if s['id']=='L005');off=s['start'];dur=s['duration']
reuse=read(EP/'outputs/literature-visual-v1/reused_assets.json');FF=reuse['ffmpeg'];env=os.environ.copy();env['PATH']=str(Path(FF).parent)+os.pathsep+env.get('PATH','')
def run(args,log,cwd=None):
    with log.open('w',encoding='utf-8') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,cwd=cwd,env=env)
    if r.returncode:raise RuntimeError(log.read_text('utf-8',errors='replace')[-2000:])
def prepare():
    R.mkdir(exist_ok=True);Q.mkdir(exist_ok=True);(Q/'compositions').mkdir(exist_ok=True)
    src=P/'compositions/L005.html';raw=src.read_text('utf-8');assert '순증 200가구' in raw and '순증 1,000가구' in raw
    shutil.copy2(src,R/'L005_before_unit_fix.html');raw=raw.replace('순증 200가구','순증 200채').replace('순증 1,000가구','순증 1,000채');src.write_text(raw,'utf-8')
    shutil.copytree(P/'assets',Q/'assets',dirs_exist_ok=True);shutil.copy2(src,Q/'compositions/L005.html');shutil.copy2(P/'hyperframes.json',Q/'hyperframes.json')
    original=(P/'index.html').read_text('utf-8');head=original[:original.index('<body>')]
    body=f'<body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{dur}" data-fps="30"><div class="clip" id="host-L005" data-composition-id="L005" data-composition-src="compositions/L005.html" data-start="0" data-duration="{dur}" data-track-index="1"></div><div class="clip" id="caption-host" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{dur}" data-track-index="2" data-track-kind="captions"></div></div><script>window.__timelines["main"]=gsap.timeline({{paused:true}});</script></body></html>'
    (Q/'index.html').write_text(head+body,'utf-8')
    cap=(P/'compositions/captions.html').read_text('utf-8');cap=cap.replace(f'data-duration="{t["duration"]}"',f'data-duration="{dur}"').replace('const clock={t:0}',f'const clock={{t:{off}}}').replace(f't:{t["duration"]},duration:{t["duration"]}',f't:{off+dur},duration:{dur}')
    assert f'const clock={{t:{off}}}' in cap and f'duration:{dur},ease' in cap
    (Q/'compositions/captions.html').write_text(cap,'utf-8')
    old=read(D/'render_input_manifest.json');shutil.copy2(D/'render_input_manifest.json',R/'render_input_manifest_before_fix.json')
    changed=[p for p,h in old.items() if sha(ROOT/p)!=h];assert changed==[(P/'compositions/L005.html').relative_to(ROOT).as_posix()],changed
    old[changed[0]]=sha(src);dump(D/'render_input_manifest.json',old)
    dump(R/'correction.json',{'issue':'주택 재고 수량의 가구/채 단위 불일치','old':['순증 200가구','순증 1,000가구'],'new':['순증 200채','순증 1,000채'],'chapter':'L005','body_start_frame':round(off*30),'frames':round(dur*30),'narration_or_timing_changed':False,'changed_composition_files':changed,'source_builder_updated':True})
    run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes','check','--at','20,26.333333,50','--json'],R/'check.log',Q)
    print(json.dumps({'prepared':True,'duration':dur,'start':off}))
def render():
    run(['cmd.exe','/d','/c','npx.cmd','--no-install','hyperframes','render','--fps','30','--quality','looks','--workers','3','--output',str(R/'L005_fixed.mp4')],R/'render.log',Q)
    print('Corrected L005 render complete.')
def splice():
    oldbody=O/'body_before_unit_fix.mp4';assert not oldbody.exists();shutil.copy2(O/'body.mp4',oldbody)
    shutil.copy2(O/'regional_guide_v3.mp4',O/'regional_guide_v3_before_unit_fix.mp4')
    begin=round(off*30);end=round((off+dur)*30);n=end-begin
    graph=f'[0:v]trim=end_frame={begin},setpts=PTS-STARTPTS[a];[1:v]trim=end_frame={n},setpts=PTS-STARTPTS[b];[0:v]trim=start_frame={end},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]'
    run([FF,'-hide_banner','-y','-i',str(oldbody),'-i',str(R/'L005_fixed.mp4'),'-filter_complex',graph,'-map','[v]','-an','-c:v','libx264','-preset','veryfast','-crf','16','-movflags','+faststart',str(O/'body.mp4')],R/'splice.log')
    prior=C/'before_unit_fix';prior.mkdir(exist_ok=True)
    for name in ['encoded','encoded_frames.json','encoded_qa_packet.json','verification.json','ffprobe.json','extract.log','decode.log','assembly.log','assembly.fffilter']:
        f=C/name
        if f.exists():shutil.move(str(f),str(prior/name))
    for f in C.glob('contact-*.jpg'):shutil.move(str(f),str(prior/f.name))
    for f in [EP/'qa/guide-v3/video_review.json',EP/'qa/guide-v3/video_review.md',D/'main_encoded_review.json']:
        shutil.copy2(f,prior/f.name)
    print(json.dumps({'spliced_frames':n,'unchanged_body_frames':t['frames']-n,'total_body_frames':t['frames']}))
if __name__=='__main__':globals()[sys.argv[1]]()
