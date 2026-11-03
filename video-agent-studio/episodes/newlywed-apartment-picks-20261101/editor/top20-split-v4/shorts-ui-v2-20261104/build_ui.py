"""Owned, local-only native portrait revision. No voice generation or uploads."""
import json, re, sys, shutil, hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
E=H.parents[2]
ROOT=E.parents[2]
D=E/'director/top20-split-v4/shorts-ui-v2-20261104'
OLD=E/'editor/top20-split-v4/jun-and-shorts-v1/shorts'
sys.path.insert(0,str(OLD))
import build_native_v4 as b
b.HERE=H
b.OUT=E/'outputs/top20-split-v4/shorts-ui-v2-20261104'
b.D=D
IDS=b.IDS
def save(p,x): b.save(p,x)
def write(p,x): b.write(p,x)
def el(cid,key,text,cls,kind='label',style=''): return b.text_el(cid,key,text,cls,kind,style)
CSS=r'''
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2');font-weight:400}
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef}body{font-family:Pretendard,sans-serif;color:#142e42}#short{position:relative;width:100%;height:100%;overflow:hidden}
.scene-host{position:absolute;inset:0}.photo-clip{position:absolute;inset:0;overflow:hidden}.hero{width:100%;height:100%;object-fit:cover}.photo-top{position:absolute;inset:0;background:linear-gradient(180deg,rgba(246,244,239,.96) 0%,rgba(246,244,239,.92) 34%,rgba(246,244,239,0) 51%,rgba(246,244,239,0) 62%,rgba(246,244,239,.97) 78%)}
.scope{position:absolute;left:150px;top:268px;width:680px;font-size:56px;line-height:1.12;font-weight:700;letter-spacing:-1.6px;white-space:pre-wrap}
.eyebrow{position:absolute;left:154px;top:350px;width:674px;font-size:32px;line-height:1.15;font-weight:700;color:#286cda}
.rank{position:absolute;left:150px;top:397px;width:680px;font-size:96px;line-height:1.05;font-weight:700;color:#ad762e;letter-spacing:-3px}
.region{position:absolute;left:146px;top:497px;width:690px;font-size:144px;line-height:1.06;font-weight:700;letter-spacing:-5px}
.couples{position:absolute;left:154px;top:665px;width:674px;font-size:52px;line-height:1.14;font-weight:700;letter-spacing:-1.3px}
.price-board{position:absolute;inset:0}.chart-title{position:absolute;left:154px;top:737px;width:674px;font-size:30px;font-weight:700;line-height:1.2}
.price-row{position:absolute;left:0;width:1080px;height:158px;background:#f6f4ef;color:#142e42}.row-0{top:782px}.row-1{top:950px}
.price-label{position:absolute;left:154px;top:6px;width:674px;font-size:34px;line-height:1.12;font-weight:700}.value{position:absolute;left:150px;top:43px;width:680px;font-size:88px;line-height:1.06;font-weight:700;letter-spacing:-3.6px;font-variant-numeric:tabular-nums}.sample{position:absolute;left:154px;top:136px;width:674px;font-size:26px;line-height:1.05}
.value.blue{color:#286cda}.value.gold{color:#946019}.caption-group{position:absolute;inset:0}.caption-rail{position:absolute;left:122px;top:1118px;width:744px;height:142px;background:#fff;border-radius:12px;box-shadow:0 3px 14px #142e4218}.caption{position:absolute;left:152px;top:1125px;width:676px;height:128px;font-size:54px;line-height:1.14;font-weight:400;display:flex;align-items:center;justify-content:center;text-align:center;white-space:pre-wrap;word-break:keep-all;letter-spacing:-1px;color:#142e42}
.credits{position:absolute;left:0;top:1266px;width:1080px;height:102px;background:#f6f4ef}.credit-line{position:absolute;left:152px;width:680px;height:29px;white-space:nowrap;font-size:26px;line-height:1.1;letter-spacing:-.35px}
.intro-panel{position:absolute;left:0;top:375px;width:1080px;height:372px;background:#f6f4ef}.intro-question{position:absolute;left:150px;top:410px;width:680px;font-size:102px;line-height:1.12;letter-spacing:-3px;font-weight:700;white-space:pre-wrap}.intro-range{position:absolute;left:150px;top:786px;width:680px;font-size:144px;line-height:1.08;font-weight:700;letter-spacing:-5px;color:#f6f4ef;text-shadow:0 3px 16px #142e42}.intro-sub{position:absolute;left:154px;top:974px;width:674px;font-size:44px;line-height:1.2;color:#142e42;background:#f6f4ef;padding:10px 0;font-weight:700}
.outro-panel{position:absolute;left:0;top:372px;width:1080px;height:719px;background:#f6f4ef}.outro-title{position:absolute;left:150px;top:405px;width:680px;font-size:82px;line-height:1.12;letter-spacing:-2px;font-weight:700;white-space:pre-wrap}.outro-range{position:absolute;left:150px;top:666px;width:680px;font-size:124px;line-height:1.12;font-weight:700;letter-spacing:-4px;color:#286cda}.outro-detail{position:absolute;left:154px;top:824px;width:674px;font-size:44px;line-height:1.3;white-space:pre-wrap;font-weight:700}.outro-main{position:absolute;left:154px;top:972px;width:674px;font-size:36px;line-height:1.2;white-space:pre-wrap}
'''
def photo(cid,rid):
    return f'<div class="photo-clip"><img id="{cid}-photo" class="hero" src="assets/{rid}.jpg" alt="" data-layout-allow-overflow></div><div class="photo-top" data-layout-ignore></div>'
def credits(cid,f,kind):
    lines=['국가데이터처 · 2024.11.01 거주 수', '국토부 83~85㎡ · 26.05~10 계약 · 11.03 조회',b.photo_credit(f['photo'])]
    if kind=='region': lines[0]='단지별 중위값 분포 · 77개 단지' if f['region_id']=='R16' else '실거래 중위값 · 취소 제외 · 10월 조회일까지'
    return '<div class="credits">'+''.join(el(cid,f'credit{i}',x,'credit-line','condition_source',f'top:{i*29+2}px')for i,x in enumerate(lines))+'</div>'
def build(sid):
    lockfile=D/'shorts'/sid/'locked_timing.json';lock=b.read(lockfile)
    assert lock['status']=='actual_Jun_reuse_locked'
    assert b.sha(lock['master_audio'])==lock['master_audio_sha256']
    assert b.sha(b.FACTS)==lock['source_visual_facts_sha256']
    facts={f['region_id']:f for f in b.read(b.FACTS)}
    regions={r['region_id']:r for name in b.PLANFILES.values()for r in b.read(b.WRITER/name)['regions']}
    project=H/sid;project.mkdir(parents=True,exist_ok=True)
    if (project/'render_receipt.json').exists(): raise RuntimeError('Rendered project is frozen')
    for name in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2','Pretendard-Regular.ttf']: b.cp(OLD/'native-v4/SHORT03-R15-R11/assets'/name,project/'assets'/name)
    used=set([s.get('region_id')for s in lock['scenes']if s.get('region_id')]+['R17'])
    for rid in used:
        f=facts[rid]; assert b.sha(f['photo']['file'])==f['photo']['sha256'];b.cp(f['photo']['file'],project/f'assets/{rid}.jpg')
    b.cp(lock['master_audio'],project/'assets/master_audio.wav')
    # Parent owns SRT creation; exact bytes are mirrored only as an editable-project input.
    b.cp(lockfile.parent/'captions.srt',project/'captions.srt')
    write(project/'style.css',CSS+'\n.price-row{height:166px}.price-label{width:350px}.value{top:36px}.sample{left:510px;top:10px;width:318px;text-align:right;white-space:nowrap}.bar-track{position:absolute;left:154px;top:142px;width:674px;height:10px;background:#dedfd9}.bar{height:10px;background:#286cda;transform-origin:left center}.row-1 .bar{background:#ad762e}.intro-range{background:#142e42;text-shadow:none;padding:8px 0 12px}\n')
    hosts=[];scenes=[];anchors=[]
    rr=lock['rankrange'];scope='20~11위 · 본편 미리보기' if sid==IDS[0] else f'{rr["from"]}~{rr["to"]}위 · 거주 수 순위'
    for i,sc in enumerate(lock['scenes']):
        cid=f'scene-{i:02d}';start=sc['start_s'];end=sc['end_s'];dur=end-start
        rid=sc.get('region_id') or next((x['region_id']for x in lock['scenes']if x.get('region_id')),'R17');f=facts[rid]
        body=photo(cid,rid)+f'<div id="{cid}-info">';cmd=''
        body+=el(cid,'scope',scope,'scope','title')
        if sc['kind']=='region':
            r=regions[rid]
            body+=el(cid,'province',r['province']+(' 수원시' if '수원시' in r['region'] else ' 부천시' if '부천시' in r['region'] else ' 용인시' if '용인시' in r['region'] else ''),'eyebrow')
            body+=el(cid,'rank',f'{r["rank"]}위','rank','key_value')+el(cid,'region',r['region'].split()[-1],'region','title')+el(cid,'couples',f'신혼부부 {r["couples"]:,}쌍','couples','key_value')
            sentence=next(x for x in sc['sentences']if x['sentence_id']==r['price_sentence_id'])
            a0,_=b.price_anchor(sentence,'61곳' if rid=='R16' else f['rows'][0]['value'])
            body+=el(cid,'charttitle',f['title'],'chart-title','label','opacity:0')
            cmd+=f'tl.set("#{cid}-charttitle",{{opacity:1}},{a0-start:.9f});'
            for j,row in enumerate(f['rows']):
                at,a=b.price_anchor(sentence,['61곳','16곳'][j]if rid=='R16' else row['value']);local=at-start
                a.update(scene_id=sc['scene_id'],row=j,rendered_value=row['value'],reveal_local_s=local,bar_fraction=row['bar_fraction'],bar_duration_s=.35);anchors.append(a)
                body+=f'<div id="{cid}-row{j}" class="price-row row-{j}" style="opacity:0">'+el(cid,f'label{j}',row['label'],'price-label')+el(cid,f'value{j}',row['value'],'value '+('blue'if j==0 else 'gold'),'key_value')+el(cid,f'sample{j}',row['sample'],'sample','condition_source')+f'<div class="bar-track"><div id="{cid}-bar{j}" class="bar" style="width:{row["bar_fraction"]*100:.9f}%"></div></div></div>'
                cmd+=f'tl.set("#{cid}-row{j}",{{opacity:1}},{local:.9f});'
                cmd+=f'tl.fromTo("#{cid}-bar{j}",{{scaleX:0}},{{scaleX:1,duration:.35,ease:"power2.out"}},{local:.9f});'
            cmd+=f'tl.fromTo("#{cid}-photo",{{opacity:0}},{{opacity:1,duration:.35,ease:"power2.inOut"}},0);'
        elif sc['kind']=='hook':
            body+='<div class="intro-panel"></div>'+el(cid,'question','신혼부부\n어디에 살까?','intro-question','title')
            body+=el(cid,'range','20~11위' if sid==IDS[0]else f'{rr["from"]}~{rr["to"]}위','intro-range','key_value')+el(cid,'subtitle','수도권 53개 구 · 아파트 가격','intro-sub')
        else:
            other='15~11위' if sid==IDS[1]else '20~16위'if sid==IDS[2]else '20~11위'
            body+='<div class="outro-panel"></div>'+el(cid,'title','가격과 생활권\n본편에서 이어집니다'if sid==IDS[0]else '다른 순위도\n확인해 보세요','outro-title','title','font-size:68px'if sid==IDS[0]else '')
            body+=el(cid,'range',other,'outro-range','key_value')+el(cid,'detail','전체 비교는 본편에서'if sid==IDS[0]else '다른 순위 영상에서 이어보기','outro-detail')+el(cid,'main','20~11위 전체 가격·생활권은 본편','outro-main')
        body+=credits(cid,f,sc['kind'])+'</div>'
        if i<len(lock['scenes'])-1:cmd+=f'tl.set("#{cid}-info",{{opacity:0}},{dur:.9f});'
        write(project/'compositions'/f'{cid}.html',b.scene_file(cid,body,cmd,dur))
        # Previous picture remains underneath during the next scene's 0.35s dissolve.
        hd=dur+(.35 if i<len(lock['scenes'])-1 else 0)
        hosts.append(f'<div id="host-{cid}" class="clip scene-host" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{start:.9f}" data-duration="{hd:.9f}" data-track-index="0" data-width="1080" data-height="1920"></div>')
        scenes.append(dict(scene_id=sc['scene_id'],composition_id=cid,kind=sc['kind'],start_s=start,end_s=end,region_id=sc.get('region_id')))
    from PIL import ImageFont
    font=ImageFont.truetype(str(project/'assets/Pretendard-Regular.ttf'),54);capbody='';cues=[]
    for i,c in enumerate(lock['captions']):
        wrapped=b.wrap_caption(c['text'],font);cues.append({**c,'wrapped_text':wrapped})
        capbody+=f'<div id="cap-{i:03d}" class="clip caption-group" data-start="{c["start_s"]:.9f}" data-duration="{c["end_s"]-c["start_s"]:.9f}" data-track-index="0"><div class="caption-rail"></div>'+el(f'cap-{i:03d}','text',wrapped,'caption','caption')+'</div>'
    write(project/'compositions/captions.html',b.scene_file('captions',capbody,'',lock['total_s']))
    hosts.append(f'<div id="captions-host" class="clip scene-host" style="z-index:10" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{lock["total_s"]:.9f}" data-track-index="1" data-track-kind="captions" data-width="1080" data-height="1920"></div>')
    hosts.append(f'<audio id="master-audio" src="assets/master_audio.wav" data-start="0" data-duration="{lock["total_s"]:.9f}" data-track-index="2" data-volume="1"></audio>')
    write(project/'index.html','<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><link rel="stylesheet" href="style.css"></head><body>'+f'<div id="short" data-composition-id="short" data-duration="{lock["total_s"]:.9f}" data-width="1080" data-height="1920" data-fps="30">'+''.join(hosts)+'</div><script>window.__timelines["short"]=gsap.timeline({paused:true});</script></body></html>')
    save(project/'hyperframes.json',dict(name=sid.lower()+'-ui-v2',width=1080,height=1920,fps=30))
    save(project/'storyboard.json',dict(short_id=sid,scenes=scenes,single_caption_track=True))
    save(project/'price_anchor_audit.json',anchors)
    save(project/'caption_integrity.json',dict(source_srt_sha256=b.sha(lockfile.parent/'captions.srt'),font_px=54,cues=cues,lexical_change=False,timing_changed=False))
    inputs=[lockfile,b.FACTS,D/'design.md',D/'plan.md',Path(__file__),Path(lock['master_audio']),lockfile.parent/'captions.srt']
    files=[project/n for n in ['index.html','style.css','captions.srt','hyperframes.json']]
    files += [p for folder in ['compositions','assets']for p in (project/folder).rglob('*')if p.is_file()]
    save(project/'input_manifest.json',dict(short_id=sid,lock_path=str(lockfile),lock_sha256=b.sha(lockfile),master_audio_sha256=lock['master_audio_sha256'],total_s=lock['total_s'],total_frames=lock['total_frames'],safe_rect=[140,260,840,1360],inputs=[dict(path=str(p),sha256=b.sha(p))for p in inputs],project_files=[dict(path=str(p.relative_to(project)),sha256=b.sha(p))for p in files]))
    return project
if __name__=='__main__':
    for sid in IDS: print(build(sid),flush=True)
