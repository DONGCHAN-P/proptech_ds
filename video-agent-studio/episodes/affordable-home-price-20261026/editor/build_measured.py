"""Build 45 authored scenes in 10 measured chapters. No video rendering."""
import hashlib,html,json,re,shutil,sys
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import EP,ROOT,OUT,BASE,HERE,read,sha,dump,e,caption_markup,load_script_lock,resolve_input
from graphics import make,text,rect,house
from voice_input import TIMING,EXPECTED,FORMAL,TECHNICAL,load_voice,spoken_overrides

def compact(s):return re.sub(r'[\s,·]','',s)

def chapter_art(number,title):
    if number in [1,8]:
        name='hero-budget-v1.png' if number==1 else 'newborn-home-v1.png'
        bg=f'<image href="assets/{name}" width="1920" height="1080" preserveAspectRatio="xMidYMid slice"/>'
    else:
        bg=rect(0,0,1920,1080,'var(--canvas)',0)
        if number in [2,9]:
            for i in range(3):
                x=750+i*280;bg+=rect(x,300+i*45,420,290,'#e6e4da',16)+f'<path d="M{x} {300+i*45} L{x+210} {470+i*45} L{x+420} {300+i*45}" stroke="#b4b8b4" stroke-width="4" fill="none"/>'
        elif number in [3,6,10]:
            for i in range(3):bg+=house(830+i*290,280+i*40,1.5)+rect(830+i*290,660-i*40,180,220+i*40,['#286cda55','#c29a4455','#3f8f7f55'][i],8)
        else:
            for i in range(3):
                x=800+i*270;bg+=rect(x,240+i*50,410,490,'#e5e4dc',12)
                for j in range(5):bg+=f'<path d="M{x+45} {330+i*50+j*65} H{x+350}" stroke="#aeb7b4" stroke-width="8"/>'
    return '<svg viewBox="0 0 1920 1080" width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">'+bg+rect(70,350,970,220,'#f6f4eff0',16)+text(110,480,title,76,'var(--ink)',700)+'</svg>'

def source_line(scene):
    ch=scene['chapter']
    by_ch={1:'금융위원회·은행업감독규정',2:'검증 자금계획 사례',3:'금융위원회·은행업감독세칙·주택금융공사',4:'금융위원회·은행업감독규정·검증 상환계산',5:'지방세법·서울시 중개보수 기준·검증 비용 사례',6:'금융위원회·검증 LTV·DSR·비용 사례',7:'주택도시기금·주택금융공사 상품·업무기준',8:'주택도시기금·KB 공시표·검증 상환계산',9:'검증 자금계획 사례',10:'검증 자금계획·상품 요건'}
    note=' · KB 2026.10.19 표·우대 전·추가 출산/중도상환 0' if scene['scene_id'] in ['S034','S034R'] else ''
    if ch==5:note=' · 무주택 한 채·84㎡·중과·감면 전·기타 비용은 계획예산'
    if ch in [3,4,6,9]:note=' · A 서울·전용84㎡·연소득1억원·기존부채0·조건부 계획값'
    if scene['scene_id']=='S028':note=' · 서울 생애최초 LTV70%·임대차 없는 아파트 자체 방수공제0'
    return by_ch[ch]+' / 2026.10.26 기준'+note

class NativeText(HTMLParser):
    def __init__(self):super().__init__();self.active=None;self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=='text':self.active={'attrs':dict(attrs),'text':''}
    def handle_data(self,s):
        if self.active:self.active['text']+=s
    def handle_endtag(self,tag):
        if tag=='text' and self.active:self.rows.append(self.active);self.active=None

def annotate_text(sid,graphic):
    parser=NativeText();parser.feed(graphic);rows=parser.rows;i=0
    def inject(m):
        nonlocal i
        ident=f'{sid}_text{i:03}';rows[i]['id']=ident;i+=1
        return m.group()[:-1]+' id="'+ident+'">'
    graphic=re.sub(r'<text\b[^>]*>',inject,graphic)
    return graphic,rows

def native_focus(cue,rendered,ordinal):
    value=compact(cue['text']);matched=[t['id'] for t in rendered['targets'] if any(compact(p) in value for p in t['phrases'])]
    method='authored_phrase_match'
    if not matched:
        # Explicit audited ordering, never a missing literal -> time-zero fallback.
        matched=[rendered['targets'][min(ordinal,len(rendered['targets'])-1)]['id']];method='authored_semantic_order_audited'
    scored=[]
    for row in rendered['text_nodes']:
        label=compact(row['text']);blocks=SequenceMatcher(None,value,label,autojunk=False).get_matching_blocks()
        longest=max((b.size for b in blocks),default=0)
        score=sum(b.size for b in blocks if b.size>=2)+longest*2
        if longest>=2:scored.append((score,row['id'],row['text']))
    scored.sort(reverse=True)
    row={'cue_id':cue['id'],'scene_id':cue['scene_id'],'text':cue['text'],'start_s':cue['start_s'],'end_s':cue['end_s'],'native_start_s':cue['native_start_s'],'native_end_s':cue['native_end_s'],'target_ids':matched,'text_target_ids':[r[1] for r in scored[:3]],'matched_screen_labels':[r[2] for r in scored[:3]],'mapping_method':method,'clock':'actual native cue, not estimated'}
    explicit={
        'C07_S031Q001':(['S031_didim','S031_bogeum'],[0,4]),
        'C07_S031Q002':(['S031_didim'],[2,3]),
        'C07_S031Q003':(['S031_bogeum'],[4,6]),
        'C07_S031Q004':(['S031_plan'],[7]),
        'C09_S040Q003':([],[3,4,8,9]),
        'C09_S040Q004':([],[5,10]),
    }
    if cue['id'] in explicit:
        groups,indices=explicit[cue['id']];ids=[f'{cue["scene_id"]}_text{i:03}' for i in indices]
        by_id={r['id']:r['text'] for r in rendered['text_nodes']};assert all(i in by_id for i in ids)
        row.update(target_ids=groups,text_target_ids=ids,matched_screen_labels=[by_id[i] for i in ids],mapping_method='explicit_native_cue_target',reason='SOURCE-FOCUS-003: separate product deadlines and monthly amounts/savings')
    return row

RUNTIME=r'''
document.fonts.ready.then(()=>{
 const root=document.getElementById('root'),tl=gsap.timeline({paused:true});
 for(const scene of SCENES){
  tl.fromTo('#'+scene.scene_id+' .panel-inner',{opacity:.35,y:8},{opacity:1,y:0,duration:.35,ease:'power2.out',immediateRender:false},scene.clip_start_s);
 }
 for(const cue of CUES){
  const el=document.getElementById(cue.dom_id);tl.set(el,{opacity:0},0);tl.set(el,{opacity:1},cue.start_s);tl.set(el,{opacity:0},cue.end_s);
 }
 for(const beat of BEATS){
  for(const id of beat.target_ids){
   const ring=document.querySelector('#'+id+' > .focus-ring');
   tl.fromTo(ring,{opacity:0},{opacity:.9,duration:.15,immediateRender:false},beat.start_s);
   tl.to(ring,{opacity:0,duration:Math.min(.12,(beat.end_s-beat.start_s)/4)},Math.max(beat.start_s,beat.end_s-.12));
  }
  for(const id of beat.text_target_ids){
   const el=document.getElementById(id);if(!el)throw Error('Missing native focus label '+id);
   const box=el.getBBox(),ring=document.createElementNS('http://www.w3.org/2000/svg','rect');
   for(const [key,val] of Object.entries({x:box.x-6,y:box.y-4,width:box.width+12,height:box.height+8,rx:5,fill:'none',stroke:'#286cda','stroke-width':2,opacity:0}))ring.setAttribute(key,val);
   ring.classList.add('native-word-focus');el.parentNode.insertBefore(ring,el);
   tl.fromTo(ring,{opacity:0},{opacity:.75,duration:.12,immediateRender:false},beat.start_s);
   tl.to(ring,{opacity:0,duration:.1},Math.max(beat.start_s,beat.end_s-.1));
  }
 }
 window.__timelines=window.__timelines||{};window.__timelines.main=tl;
 window.__sourceSeek=t=>{tl.pause().time(t,false);for(const el of document.querySelectorAll('.clip'))el.style.visibility=t>=Number(el.dataset.start)&&t<Number(el.dataset.start)+Number(el.dataset.duration)?'visible':'hidden'};
 window.__sourceSeek(0);
});
'''

def main(selected=None):
    lock,script,_=load_script_lock();timing,formal,technical=load_voice();overrides=spoken_overrides()
    assert sha(TIMING)==EXPECTED==formal['final_timing_sha256']==technical['final_timing_sha256']
    assert timing['script_sha256']==lock['script_sha256'] and not formal['required_technical_errors']
    assert not technical['required_technical_errors']
    edl=read(OUT/'assembly_edl.json');assert edl['timing_sha256']==EXPECTED
    proposal=read(resolve_input(lock['source_proposals']));central=read(EP/'scenes.json');central_map={s['scene_id']:s for s in central['scenes']}
    assert central['script_sha256']==lock['script_sha256'] and len(central_map)==45
    packet=read(EP/'research/verified_case_packet.json');data={'packet':packet,'cases':{c['case_id']:c for c in packet['cases']},'reset':read(EP/'research/newborn_policy_addendum_v2.json')}
    source_assets=BASE/'outputs/private-production-v3/ch01/assets';css=(HERE/'templates/shell.css').read_text(encoding='utf8').replace('url(fonts/','url(assets/fonts/')
    css+='\n.scene-panel{position:absolute;left:80px;top:225px;width:1740px;height:590px;border-radius:16px;background:var(--panel);overflow:hidden}.scene-source{position:absolute;left:96px;top:1020px;width:1728px;white-space:nowrap;font-size:18px;line-height:24px;color:var(--muted)}.chapter-card{position:absolute;inset:0}.panel-inner{width:1740px;height:590px;display:block}.scene-topic{position:absolute;left:80px;top:142px;font-size:43px;font-weight:700;letter-spacing:-.01em}'
    selected=set(selected or range(1,11))
    if selected!=set(range(1,11)):
        previous=read(OUT/'scene_source_manifest.json');previous_plan=read(OUT/'render_plan.json')
        all_scenes=[s for s in previous['scenes'] if s['chapter'] not in selected]
        other_ids={s['scene_id'] for s in all_scenes}
        samples=[s for s in read(OUT/'snapshot_times.json')['samples'] if s['chapter'] not in selected]
        chapters=[c for c in previous_plan['chapters'] if c['chapter'] not in selected]
        warnings=[w for w in previous['anchor_order_mappings_for_independent_review'] if w['scene_id'] in other_ids]
        all_beats=[]
        for ch in chapters:
            file=OUT/ch['project']/'index.html'
            assert sha(file)==ch['html_sha256'],'Cannot reuse changed chapter source'
            all_beats.extend(read(OUT/ch['project']/'anchor_audit.json')['beats'])
    else:all_scenes=[];all_beats=[];samples=[];chapters=[];warnings=[]
    for chapter in timing['chapters']:
        number=chapter['chapter']
        if number not in selected:continue
        folder=OUT/f'ch{number:02}';assets=folder/'assets';(assets/'fonts').mkdir(parents=True,exist_ok=True)
        old_audio_tags=[]
        if (folder/'index.html').exists():
            old_doc=(folder/'index.html').read_text(encoding='utf8')
            if 'id="music-bed"' in old_doc:
                old_mix=read(HERE/'mix_receipt.json');old_ch=next(c for c in old_mix['chapters'] if c['chapter']==number)
                assert sha(folder/'index.html')==old_ch['html_sha256'] and old_ch['voice_sha256']==chapter['audio_sha256']
                assert old_mix['timing_sha256']==EXPECTED and old_mix['EDL_sha256']==sha(OUT/'assembly_edl.json')
                assert sha(assets/'music-bed.wav')==old_ch['bed_sha256']
                old_audio_tags=re.findall(r'<audio\b[^>]*></audio>',old_doc)
                assert len(old_audio_tags)==2
        for name in ['gsap.min.js','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2','fonts/Pretendard-ExtraBold.woff2']:shutil.copy2(source_assets/name,assets/name)
        audio=resolve_input(chapter['audio_file']);assert sha(audio)==chapter['audio_sha256'] and audio.resolve().is_relative_to((EP/'narration').resolve())
        shutil.copy2(audio,assets/'narration.wav');assert sha(assets/'narration.wav')==chapter['audio_sha256']
        if number in [1,8]:
            name='hero-budget-v1.png' if number==1 else 'newborn-home-v1.png';shutil.copy2(EP/'visual'/name,assets/name)
        own_scenes=[s for s in proposal['scenes'] if s['chapter']==number];parts=[];rows=[];beats=[]
        for i,(scene,paragraph) in enumerate(zip(own_scenes,chapter['paragraphs'])):
            sid=scene['scene_id'];adopted=central_map[sid]
            assert adopted['narration_text']==scene['display_text'] and adopted['spoken_text']==scene['spoken_text']
            cues=[c for c in chapter['cues'] if c['scene_id']==sid]
            assert cues and compact(''.join(c['text'] for c in cues))==compact(scene['display_text'])
            assert compact(''.join(c['spoken_text'] for c in cues))==compact(overrides.get(sid,scene['spoken_text']))
            assert paragraph['paragraph']==cues[0]['paragraph'] and all(c['paragraph']==paragraph['paragraph'] for c in cues)
            for cue in cues:
                assert cue['start_s']==cue['native_start_s'] and cue['end_s']<=cue['native_end_s']
                assert 1<=len(cue['display_lines'])<=2 and compact(''.join(cue['display_lines']))==compact(cue['text'])
            start=0 if number==1 and i==0 else paragraph['offset_s']
            end=chapter['paragraphs'][i+1]['offset_s'] if i+1<len(own_scenes) else chapter['total_seconds']
            if sid=='S001':end=edl['hook_cut_s']
            if sid=='S002':start=edl['hook_cut_s']
            rendered=make(sid,data);rendered['svg'],rendered['text_nodes']=annotate_text(sid,rendered['svg'])
            scene_beats=[native_focus(c,rendered,j) for j,c in enumerate(cues)];beats.extend(scene_beats)
            warnings.extend({'scene_id':sid,'cue_id':b['cue_id'],'mapping':b['mapping_method']} for b in scene_beats if b['mapping_method'] not in ['authored_phrase_match','explicit_native_cue_target'])
            for b in scene_beats:
                if not b['text_target_ids']:raise ValueError('No visual label for native meaning cue: '+sid+' '+b['cue_id']+' '+b['text'])
            row={'scene_id':sid,'chapter':number,'paragraph':paragraph['paragraph'],'kind':rendered['kind'],'clip_start_s':start,'clip_end_s':end,'start_s':cues[0]['start_s'],'end_s':cues[-1]['end_s'],'timing_basis':'actual native paragraph placement + exact cue anchors','message':scene['message'],'graphic_id':scene['graphic_id'],'claim_ids':scene['claim_ids'],'asset_ids':scene['asset_ids'],'cue_ids':[c['id'] for c in cues]}
            rows.append(row);all_scenes.append(row)
            parts.append(f'<section id="{sid}" class="clip scene-panel" data-start="{start:.12f}" data-duration="{end-start:.12f}" data-track-index="2"><div class="panel-inner">'+rendered['svg']+'</div></section>')
            parts.append(f'<div class="clip scene-source" data-start="{start:.12f}" data-duration="{end-start:.12f}" data-track-index="5">'+e(source_line(scene))+'</div>')
            samples.append({'chapter':number,'scene_id':sid,'representative_s':(cues[len(cues)//2]['start_s']+cues[len(cues)//2]['end_s'])/2,'after_start_s':max(start,cues[0]['start_s'])+.1,'before_end_s':min(end-.1,cues[-1]['end_s']-.05),'cue_sample_times_s':[(c['start_s']+c['end_s'])/2 for c in cues],'kind':rendered['kind']})
        title=next(c['title'] for c in proposal['chapter_entries'] if c['chapter_entry_id']==f'CH{number:02}')
        lead=chapter['leading_silence_s']
        chapter_card='' if number==1 else f'<div class="clip chapter-card" data-start="0" data-duration="{lead}" data-track-index="1">'+chapter_art(number,title)+'</div>'
        duration=chapter['total_seconds'];box_end=chapter['last_speech_end_s'] if number==10 else duration
        cue_rows=[{**c,'dom_id':f'cue{i:03}'} for i,c in enumerate(chapter['cues'])]
        runtime='const SCENES='+json.dumps(rows,ensure_ascii=False)+';const CUES='+json.dumps(cue_rows,ensure_ascii=False)+';const BEATS='+json.dumps(beats,ensure_ascii=False)+';'+RUNTIME
        doc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1920, height=1080"><title>'+e(title)+'</title><script src="assets/gsap.min.js"></script><style>'+css+'</style></head><body>'
        doc+=f'<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{duration:.12f}"><div id="brand" class="abs"><i>Ⅰ</i> 데이터로 보는 부동산</div><div id="tag" class="abs">감당 가능한 집값</div>'+chapter_card
        doc+=f'<h1 class="clip scene-topic" data-start="{0 if number==1 else lead}" data-duration="{duration-(0 if number==1 else lead)}" data-track-index="4">'+e(title)+'</h1>'+''.join(parts)
        doc+=f'<div id="capbox" class="clip abs" data-start="0" data-duration="{box_end:.12f}" data-track-index="9"></div>'+caption_markup(chapter['cues'])
        doc+=f'<audio id="narration" class="clip" src="assets/narration.wav" data-start="0" data-duration="{duration:.12f}" data-track-index="10" data-volume="1"></audio></div><script>'+runtime+'</script></body></html>'
        if old_audio_tags:
            doc=re.sub(r'<audio\b[^>]*></audio>',''.join(old_audio_tags),doc,count=1)
        (folder/'index.html').write_text(doc,encoding='utf8')
        dump(folder/'timing.json',{**chapter,'script_sha256':lock['script_sha256'],'caption_timing_sha256':EXPECTED,'status':'measured_audio_units','scenes':rows})
        dump(folder/'anchor_audit.json',{'clock':'exact native cue times; no missing literal zero fallback','beats':beats,'audited_order_mappings':[w for w in warnings if w['scene_id'] in {s['scene_id'] for s in rows}]})
        chapters.append({'chapter':number,'project':f'ch{number:02}','total_seconds':duration,'leading_silence_s':lead,'last_speech_end_s':chapter['last_speech_end_s'],'title':chapter['title'],'scene_ids':[s['scene_id'] for s in rows],'html_sha256':sha(folder/'index.html'),'audio_sha256':sha(assets/'narration.wav')})
        all_beats.extend(beats)
    all_scenes.sort(key=lambda s:s['paragraph']);chapters.sort(key=lambda c:c['chapter'])
    order={s['scene_id']:s['paragraph'] for s in all_scenes};samples.sort(key=lambda s:order[s['scene_id']])
    dump(OUT/'snapshot_times.json',{'timing_sha256':EXPECTED,'samples':samples,'scope':'45 scene representatives/boundaries plus 150 exact native cue midpoints'})
    dump(OUT/'scene_source_manifest.json',{'status':'measured_45_scene_source_authored_QA_pending','script_sha256':lock['script_sha256'],'timing_sha256':EXPECTED,'central_scenes_sha256':sha(EP/'scenes.json'),'scene_count':len(all_scenes),'cue_count':len(all_beats),'scenes':all_scenes,'anchor_order_mappings_for_independent_review':warnings,'different_native_graphic_kinds':len({s['kind'] for s in all_scenes}),'raster_scenes':{'S001':'HB01','S032':'NB01'},'full_render_authorized':False})
    plan=read(OUT/'render_plan.json');plan.update(status='measured_audio_units',chapters=chapters,source_scene_count=len(all_scenes),native_cues=len(all_beats),central_scenes_sha256=sha(EP/'scenes.json'),full_render_allowed_now=False,source_QA='pending')
    revision_gate=read(HERE/'audio_revision_gate.json') if (HERE/'audio_revision_gate.json').exists() else {}
    plan.update(status='measured_audio_units',native_revision='production-injoon-v3',canonical_carve_allowed=True,final_timing_freeze_allowed=False,pending_audio_QA_scene_ids=['S014','S019','S024','S030'])
    dump(OUT/'render_plan.json',plan)
    dump(HERE/'measured_build_receipt.json',{'status':'measured_source_built','script_sha256':lock['script_sha256'],'timing_sha256':EXPECTED,'scene_count':len(all_scenes),'native_cues':len(all_beats),'chapters':chapters,'EDL_sha256':sha(OUT/'assembly_edl.json'),'SRT_sha256':sha(OUT/'captions_measured.srt'),'narration_handoff_sha256':sha(FORMAL),'technical_validation_sha256':sha(TECHNICAL),'source_QA':'pending','independent_audio_QA':'pending','full_render_executed':False})
    (OUT/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>실측 소스 45장면</title><body><h1>실측 소스 · 45장면</h1><p>승인 대본 v2 · 실제 InJoon 음성·150 native 의미 큐. 본편 렌더 전 소스 검수 단계입니다.</p><ol>'+''.join(f'<li><a href="ch{i:02}/index.html">CH{i:02}</a></li>' for i in range(1,11))+'</ol><a href="assembly_edl.json">EDL</a> · <a href="captions_measured.srt">SRT</a></body></html>',encoding='utf8')
    print(json.dumps({'status':'measured_source_built','chapters':len(chapters),'scenes':len(all_scenes),'native_cues':len(all_beats),'audited_order_mappings':len(warnings),'full_render':False}))
if __name__=='__main__':main([int(n) for n in sys.argv[1:]] if len(sys.argv)>1 else None)
