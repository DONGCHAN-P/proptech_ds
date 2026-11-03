"""Assemble the exact Jun scene clocks, native graphics, captions and channel media."""
from pathlib import Path
import json,math,hashlib,html,os,wave,subprocess,sys
import numpy as np
from scipy.signal import resample_poly

HERE=Path(__file__).resolve().parent; EP=HERE.parents[2]; ROOT=EP.parents[2]
PROJECT=HERE/'project';OUT=EP/'outputs/jun-quality-v2/main'
N=EP/'narration/jun-user-script-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
HF=Path('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs')
FPS=30;SR=48000
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v,encoding='utf-8')
def stage(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(dst)==sha(src);return
    os.link(src,dst)
def run(args):
    r=subprocess.run([str(x) for x in args],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace')[-4000:])
    return r
def e(t):return html.escape(str(t),quote=True)
def srt(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def schedule():
    a=load(N/'scene_alignment.json');media=load(EP/'visual/jun-user-script-v1/editor_asset_packet.json')
    placements=[];frame=0
    def add(kind,id,duration,**kw):
        nonlocal frame
        count=math.ceil(duration*FPS-1e-8)
        p={'kind':kind,'id':id,'frame':frame,'frames':count,'start':frame/FPS,'duration':count/FPS,**kw}
        placements.append(p);frame+=count
        return p
    assets={x['before_scene_id']:x for x in media['chapter_assets']}
    for scene in a['scenes']:
        sid=scene['scene_id']
        if sid in assets:add('chapter','CH'+str(assets[sid]['asset_id'])[-2:],2.5,asset=assets[sid])
        p=add('scene',sid,scene['duration_s'],scene=scene)
        if sid=='S02':add('brand','brand_intro',5.0)
        if sid=='S31':
            existing_tail=p['duration']-scene['last_spoken_end_s']
            gap=max(0,math.ceil((3-existing_tail)*FPS-1e-8))/FPS
            p['frames']+=round(gap*FPS);p['duration']+=gap;frame+=round(gap*FPS)
    add('brand','brand_outro',10)
    result={'fps':FPS,'frames':frame,'duration':frame/FPS,'source_alignment_sha256':sha(N/'scene_alignment.json'),'placements':placements,'last_speech_end':next(p for p in placements if p['id']=='S31')['start']+a['scenes'][-1]['last_spoken_end_s'],'actual_listening':False}
    save(HERE/'schedule.json',result)
    return a,media,result

def audio(a,sch):
    audiofile=PROJECT/'assets/mix.m4a'
    audiofile.parent.mkdir(parents=True,exist_ok=True)
    if audiofile.exists():return
    brand=load(EP/'visual/jun-user-script-v1/brand_audio_refs.json')['assets']
    refs={x['asset_id']:ROOT/x['path'] for x in brand}
    units={x['audio_unit_id']:x for x in a['audio_units']}
    pcm=np.zeros((round(sch['duration']*SR),2),dtype=np.float32)
    for p in sch['placements']:
        start=round(p['start']*SR)
        if p['kind']=='scene':
            s=p['scene'];src=ROOT/units[s['audio_unit_id']]['path']
            with wave.open(str(src),'rb') as w:
                rate=w.getframerate();i=round(s['audio_start_s']*rate);j=round(s['audio_end_s']*rate);w.setpos(i);x=np.frombuffer(w.readframes(j-i),dtype='<i2').astype(np.float32)/32768
            y=resample_poly(x,160,147);y=np.repeat(y[:,None],2,axis=1)
        elif p['kind']=='brand':
            key='channel_brand_intro_clean_v7' if p['id']=='brand_intro' else 'channel_brand_outro_clean_v7'
            raw=run([FF,'-v','error','-i',refs[key],'-t',p['duration'],'-f','f32le','-ar',SR,'-ac',2,'-']).stdout
            y=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
        else:continue
        maxn=min(len(y),round(p['duration']*SR));pcm[start:start+maxn]+=y[:maxn]
    temp=HERE/'dry_voice_brand.wav'
    with wave.open(str(temp),'wb') as w:
        w.setparams((2,2,SR,0,'NONE','not compressed'));w.writeframes((np.clip(pcm,-1,1)*32767).astype('<i2').tobytes())
    del pcm
    intervals=[p for p in sch['placements'] if p['kind']=='brand']
    mute='+'.join(f'between(t,{p["start"]:.9f},{p["start"]+p["duration"]:.9f})' for p in intervals)
    filters=f"[1:a]highpass=f=80,lowpass=f=12000,equalizer=f=2200:t=o:w=2:g=-5,volume='if({mute},0,0.045)':eval=frame,afade=t=in:st=0:d=1.5[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[mix]"
    run([FF,'-v','error','-n','-i',temp,'-stream_loop','-1','-i',refs['existing_channel_bgm'],'-filter_complex',filters,'-map','[mix]','-t',sch['duration'],'-c:a','aac','-b:a','192k',audiofile])
    save(HERE/'audio_mix_receipt.json',{'output':str(audiofile),'sha256':sha(audiofile),'duration_s':sch['duration'],'sample_rate':SR,'filters':filters,'brand_music_duplicated':False,'raw_chapter_audio_preserved':True,'actual_listening':False,'intermediate_dry_wav':str(temp)})

STYLE='''*{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden;background:#f6f4ef} .scene{position:relative;width:100%;height:100%;overflow:hidden;color:var(--ink);background:var(--canvas)}.txt{position:absolute;line-height:1.32;white-space:nowrap;letter-spacing:-.015em;font-variant-numeric:tabular-nums}.shape{position:absolute;transform-origin:left center;border-radius:4px}.group{position:absolute;inset:0}img{object-fit:contain}.brand{position:absolute;left:88px;top:28px;font-size:22px;color:#173348}'''

def make_project(a,media,sch):
    sys.path.insert(0,str(HERE));from build_visuals import build_scene
    assets=PROJECT/'assets';assets.mkdir(parents=True,exist_ok=True)
    old=EP/'editor/jun-user-script-v1/project/S13/assets'
    stage(old/'gsap.min.js',assets/'gsap.min.js')
    for p in (old/'fonts').glob('*.woff2'):stage(p,assets/'fonts'/p.name)
    for i,x in enumerate(media['optional_cutouts']):stage(Path(x['file']),assets/('house.png' if i==0 else 'budget.png'))
    fonts=''.join(f'@font-face{{font-family:Pretendard;font-weight:{weight};src:url(assets/fonts/{file})}}' for weight,file in [(400,'Pretendard-Regular.woff2'),(600,'Pretendard-SemiBold.woff2'),(700,'Pretendard-Bold.woff2')])
    hosts=[];all_cues=[];visual_receipts=[]
    for p in sch['placements']:
        id=p['id'];dur=p['duration'];start=p['start']
        if p['kind']=='brand':
            name='brand_intro_clean_v7.mp4' if id=='brand_intro' else 'brand_outro_clean_v7.mp4'
            src=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/production-v1-jun/reusable_assets'/name
            stage(src,assets/name)
            hosts.append(f'<video id="{id}" class="clip" muted src="assets/{name}" data-start="{start}" data-duration="{dur}" data-track-index="2" style="position:absolute;inset:0;width:100%;height:100%"></video>')
            continue
        hosts.append(f'<div id="{id}" class="clip" data-composition-id="{id}" data-composition-src="scenes/{id}.html" data-start="{start}" data-duration="{dur}" data-track-index="1"></div>')
        if p['kind']=='chapter':
            x=p['asset'];name=id+'.png';stage(Path(x['file']),assets/name)
            color=x['title_color'];body=f'<img src="../assets/{name}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"><div style="position:absolute;left:96px;top:270px;width:820px;color:{color};font-size:26px">{id.replace("CH","CH ")}</div><div id="{id}_title" style="position:absolute;left:96px;top:338px;width:820px;color:{color};font-size:64px;line-height:1.35;font-weight:700">{e(x["title"])}</div>'
            script=f'tl.fromTo("#{id}_title",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.45,ease:"power2.out"}},.15);'
        else:
            s=p['scene'];v=build_scene(id,s,{'house_cutout_src':'../assets/house.png','budget_cutout_src':'../assets/budget.png'})
            readable_html=v['html'].replace('color:var(--gold)','color:#88631b').replace('color:#c29a44','color:#88631b')
            body='<div class="brand">부동산 데이터 | 내 집 예산</div>'+readable_html;script=''
            first_beat=min((x['beat'] for x in v.get('animations',[])),default=1)
            for motion in v.get('animations',[]):
                bi=motion['beat']-1;assert 0<=bi<len(s['beats']),(id,motion)
                targets=motion['targets'];assert all(t.startswith(id+'_') and f'id="{t}"' in body for t in targets),(id,targets)
                selector=','.join('#'+t for t in targets);at=motion.get('at_s',s['beats'][bi]['start_s']);duration=motion.get('duration',.4)
                # The first subject is resident from entry; narration later focuses it.
                # No heading-only wait for a keyword that may occur 10+ seconds later.
                if motion['beat']==first_beat and 'at_s' not in motion:at=min(.12,at)
                if motion['kind']=='hide':script+=f'tl.set({json.dumps(selector)},{{opacity:0}},{at});'
                elif motion['kind']=='fill':script+=f'tl.set({json.dumps(selector)},{{scaleX:0}},0);tl.fromTo({json.dumps(selector)},{{scaleX:0}},{{scaleX:1,duration:{duration},ease:"power2.out",immediateRender:false}},{at});'
                else:script+=f'tl.set({json.dumps(selector)},{{opacity:0}},0);tl.fromTo({json.dumps(selector)},{{opacity:0}},{{opacity:1,duration:{duration},ease:"power2.out",immediateRender:false}},{at});'
            if id=='S14':
                body+='<div id="S14_subscribe" style="position:absolute;right:96px;top:66px;display:flex;align-items:center;gap:20px;background:#173348;color:white;border-radius:30px;padding:14px 24px;font-size:26px;font-weight:600;opacity:0"><span style="color:#bdd9ff">내 집 예산을 함께 계산해요</span><span>구독 · 좋아요</span></div>'
                script+='tl.fromTo("#S14_subscribe",{opacity:0},{opacity:1,duration:.35},1);tl.to("#S14_subscribe",{opacity:0,duration:.35},7);'
            if id=='S31':
                body+='<div id="S31_subscribe" style="position:absolute;left:1220px;top:760px;width:600px;height:72px;background:#286cda;border-radius:36px;color:white;font-size:32px;font-weight:700;display:flex;align-items:center;justify-content:center">구독 · 좋아요로 다음 편도 함께</div>'
                script+='tl.fromTo("#S31_subscribe",{opacity:0},{opacity:1,duration:.4},.2);'
            if id in ['S13','S15','S16','S18']:
                # A concrete destination remains visible while cash is introduced.
                xy={'S13':(1260,350),'S15':(1350,370),'S16':(1210,405),'S18':(1260,355)}[id]
                body+=f'<div id="{id}_resident_placeholder" style="position:absolute;inset:0"><img src="../assets/house.png" style="position:absolute;left:{xy[0]}px;top:{xy[1]}px;width:310px;height:268px;object-fit:contain"><div style="position:absolute;left:{xy[0]-60}px;top:{xy[1]+290}px;width:500px;font-size:30px;color:#607680;text-align:center">자기자금과 대출로 집값 연결</div></div>'
                result_beat={'S13':4,'S15':2,'S16':2,'S18':2}[id]
                end=max(.6,s['beats'][result_beat-1]['start_s']-(.25 if id=='S18' else .1))
                script+=f'tl.to("#{id}_resident_placeholder",{{opacity:0,duration:.25}},{end});'
            visual_receipts.append({'scene_id':id,'motions':len(v.get('animations',[])),'duration_s':dur})
            for c in s['captions']:
                end=start+c['end_s']
                if id=='S31':end=min(end,start+s['last_spoken_end_s'])
                all_cues.append({**c,'global_start':start+c['start_s'],'global_end':end,'scene_id':id})
        doc=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{STYLE}</style></head><body><div class="scene" id="{id}" data-composition-id="{id}" data-width="1920" data-height="1080" data-duration="{dur}">{body}</div><script>document.fonts.ready.then(()=>{{const tl=gsap.timeline({{paused:true}});{script}window.__timelines["{id}"]=tl;}});</script></body></html>'
        write(PROJECT/'scenes'/f'{id}.html',doc)
    # One full-film caption composition, separate from scene graphics and unvoiced cards.
    capbody='<div id="caption_rail" style="position:absolute;left:96px;top:876px;width:1728px;height:124px;border-radius:16px;background:white;opacity:0"></div>'
    capscript=''
    for i,c in enumerate(all_cues):
        id=f'global_cue_{i}';lines='<br>'.join(e(x) for x in c['display_lines'])
        capbody+=f'<div id="{id}" style="position:absolute;left:140px;top:876px;width:1640px;height:124px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:40px;line-height:50px;color:#173348;opacity:0"><span>{lines}</span></div>'
        capscript+=f'tl.set("#{id}",{{opacity:1}},{c["global_start"]});tl.set("#{id}",{{opacity:0}},{c["global_end"]});'
    for p in sch['placements']:
        if p['kind']=='scene':
            end=p['start']+p['duration'] if p['id']!='S31' else p['start']+p['scene']['last_spoken_end_s']
            capscript+=f'tl.set("#caption_rail",{{opacity:1}},{p["start"]});tl.set("#caption_rail",{{opacity:0}},{end});'
    obsolete_caption=PROJECT/'captions.html'
    if obsolete_caption.exists():obsolete_caption.rename(PROJECT/'captions_invalid_root.txt')
    write(PROJECT/'scenes/captions.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><div id="captions" data-composition-id="captions" data-width="1920" data-height="1080" data-duration="{sch["duration"]}" style="width:100%;height:100%;position:relative">{capbody}</div><script>const tl=gsap.timeline({{paused:true}});{capscript}window.__timelines["captions"]=tl;</script></body></html>')
    hosts.append(f'<div id="captions" class="clip" data-composition-id="captions" data-composition-src="scenes/captions.html" data-track-kind="captions" data-track-index="4" data-start="0" data-duration="{sch["duration"]}"></div>')
    hosts.append(f'<audio id="final_mix" class="clip" src="assets/mix.m4a" data-start="0" data-duration="{sch["duration"]}" data-track-index="3"></audio>')
    css=fonts+':root{--ink:#173348;--blue:#286cda;--gold:#c29a44;--green:#3f8f7f;--muted:#607680;--canvas:#f6f4ef}*{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden}#film{width:100%;height:100%;position:relative;font-family:Pretendard,sans-serif;background:var(--canvas)}'
    write(PROJECT/'index.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>{css}</style></head><body><div id="film" data-composition-id="film" data-width="1920" data-height="1080" data-duration="{sch["duration"]}">{"".join(hosts)}</div><script>window.__timelines["film"]=gsap.timeline({{paused:true}});</script></body></html>')
    save(PROJECT/'hyperframes.json',{'name':'affordable-price-Jun-quality-v2','width':1920,'height':1080,'fps':30,'entry':'index.html'})
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/'subtitles.srt','\n\n'.join(f'{i+1}\n{srt(c["global_start"])} --> {srt(c["global_end"])}\n'+ '\n'.join(c['display_lines']) for i,c in enumerate(all_cues))+'\n')
    save(HERE/'full_caption_timing.json',{'duration_s':sch['duration'],'cues':all_cues,'audio_alignment_sha256':sha(N/'scene_alignment.json')})
    save(HERE/'assembly_receipt.json',{'status':'project_authored_real_timing','duration_s':sch['duration'],'scenes':31,'chapter_cards':7,'captions':len(all_cues),'visuals':visual_receipts,'audio_mix_sha256':sha(PROJECT/'assets/mix.m4a'),'last_speech_end_s':sch['last_speech_end'],'outro_start_s':next(p['start'] for p in sch['placements'] if p['id']=='brand_outro'),'actual_listening':False,'continuous_playback':False})

if __name__=='__main__':
    PROJECT.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    a,m,s=schedule()
    audio(a,s)
    if '--audio-only' not in sys.argv:make_project(a,m,s)
    print(json.dumps({'project':str(PROJECT),'duration_s':s['duration'],'frames':s['frames'],'audio_only':'--audio-only' in sys.argv}))
