from pathlib import Path
import json,html,os,subprocess,hashlib,time
HERE=Path(__file__).resolve().parent;EP=HERE.parents[2];ROOT=EP.parents[2]
BASE=HERE/'project';P=HERE/'patch-S18/project';P.mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sch=load(HERE/'schedule.json');part=next(x for x in sch['placements'] if x['id']=='S18');dur=part['duration']
for name in ['gsap.min.js','house.png','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2']:
    dst=P/'assets'/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():os.link(BASE/'assets'/name,dst)
(P/'scenes').mkdir(exist_ok=True)
(P/'scenes/S18.html').write_bytes((BASE/'scenes/S18.html').read_bytes())
caps=[c for c in load(HERE/'full_caption_timing.json')['cues'] if c['scene_id']=='S18']
body='<div style="position:absolute;left:96px;top:876px;width:1728px;height:124px;background:white;border-radius:16px"></div>';script=''
for i,c in enumerate(caps):
    text='<br>'.join(html.escape(x) for x in c['display_lines'])
    body+=f'<div id="patch_cue_{i}" style="position:absolute;left:140px;top:876px;width:1640px;height:124px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:40px;line-height:50px;color:#173348;opacity:0"><span>{text}</span></div>'
    script+=f'tl.set("#patch_cue_{i}",{{opacity:1}},{c["global_start"]-part["start"]});tl.set("#patch_cue_{i}",{{opacity:0}},{c["global_end"]-part["start"]});'
fonts=''.join(f'@font-face{{font-family:Pretendard;font-weight:{w};src:url(assets/fonts/Pretendard-{name}.woff2)}}' for w,name in [(400,'Regular'),(600,'SemiBold'),(700,'Bold')])
css=fonts+':root{--ink:#173348;--blue:#286cda;--gold:#c29a44;--green:#3f8f7f;--muted:#607680;--canvas:#f6f4ef}*{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden}#patch_s18{width:100%;height:100%;position:relative;font-family:Pretendard,sans-serif;background:var(--canvas)}'
doc=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>{css}</style></head><body><div id="patch_s18" data-composition-id="patch_s18" data-width="1920" data-height="1080" data-duration="{dur}"><div id="S18" class="clip" data-composition-id="S18" data-composition-src="scenes/S18.html" data-start="0" data-duration="{dur}" data-track-index="1"></div>{body}</div><script>document.fonts.ready.then(()=>{{const tl=gsap.timeline({{paused:true}});{script}window.__timelines["patch_s18"]=tl;}});</script></body></html>'
(P/'index.html').write_text(doc,encoding='utf-8');(P/'hyperframes.json').write_text(json.dumps({'name':'S18-required-correction','width':1920,'height':1080,'fps':30,'entry':'index.html'}),encoding='utf-8')
HF='C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs'
env={**os.environ,'PATH':str(ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin')+';'+str(ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc')+';'+os.environ['PATH'],'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1'}
target=HERE/'patch-S18/S18_corrected_v1.mp4'
assert not target.exists()
cmd=['node',HF,'render',str(P),'--output',str(target),'--fps','30','--quality','delivery','--workers','2']
with (HERE/'patch-S18/render.log').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
record={'command':cmd,'exit_code':r.returncode,'issue':'JQV2-N01','scene_id':'S18','frame_start':part['frame'],'frame_count':part['frames'],'duration_s':dur,'corrected_source_sha256':hashlib.sha256((BASE/'scenes/S18.html').read_bytes()).hexdigest(),'voice_changed':False}
if target.exists():record['patch_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(HERE/'patch-S18/receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record));raise SystemExit(r.returncode)
