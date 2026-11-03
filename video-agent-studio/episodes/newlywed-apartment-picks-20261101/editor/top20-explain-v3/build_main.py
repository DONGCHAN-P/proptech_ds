"""전체26장면 전용. prepare는 시간 없는 템플릿만, production은 실제 lock만 사용합니다."""
from pathlib import Path
import argparse,copy,json,re,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from main_contract import H,E,R,JSON_SHA,MD_SHA,load_inputs,validate_lock,normalize_director_lock,sha,save,write,resolve
import main_primitives
from main_layouts import install as install_main_layouts
from v3_visuals import install_v3,FIT_SCRIPT
from caption_tools import make_cues,set_protected_phrases
from caption_backgrounds import body_windows,markup

def stage(asset,directory):
    source=Path(asset['source']);dest=directory/asset['dest']
    if sha(source)!=asset['sha256']:raise ValueError('staging 직전 입력SHA 변경: '+str(source))
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        if sha(dest)!=asset['sha256']:raise ValueError('기존 고정 에셋과 다릅니다: '+str(dest))
    else:shutil.copy2(source,dest)
    return {'path':str(dest),'sha256':sha(dest),'kind':asset['kind']}

def source_manifest(data,extra=None):
    paths=list(dict.fromkeys([str(p)for p in data['inputs']]+[a['source']for a in data['assets']]+list(extra or [])))
    return [{'path':str(Path(p).resolve()).replace('\\','/'),'sha256':sha(p)}for p in paths]

def prepare(data):
    assets=H/'main/prepared/assets';staged=[stage(a,assets)for a in data['assets']]
    templates=[];anchor_plan=[]
    for s in data['scenes']:
        rid=s.get('region_id');kind='region_two_phase' if rid else {'O001':'opening','O002':'source_and_scope','I001':'same7797_change','I002':'total59_first_marriage','C001':'price_range_criteria_cta','E001':'hold_C001_end_state'}[s['scene_id']]
        price_ids=[st['sentence_id']for st in s['sentences']if st.get('price_role')]
        if rid:
            p=data['panels'][rid]
            scalar_ids=[b['sentence_ids'][0]for b in s['screen_beats']if b.get('purpose')in ['regional_price','separate_complex_price_example']]
            by_sid={st['sentence_id']:st for st in s['sentences']}
            if len(scalar_ids)!=2:raise ValueError('지역/단지 가격 문장 연결 누락')
            if p['display_price'] not in by_sid[scalar_ids[0]]['display_text'] or p['representative']['display_price'] not in by_sid[scalar_ids[1]]['display_text']:raise ValueError('승인 가격 표시문 연결 불일치')
        templates.append({'scene_id':s['scene_id'],'region_id':rid,'renderer':kind,'sentence_ids':[st['sentence_id']for st in s['sentences']],'start_s':None,'end_s':None,'duration_s':None,'timing_locked':False,'photo_binding':data['bindings'].get(s['scene_id']),'price_panel':data['panels'].get(rid),'price_sentence_ids':price_ids})
        anchor_plan.extend({'scene_id':s['scene_id'],'sentence_id':st['sentence_id'],'anchor_string':st.get('anchor_string'),'timing_basis':'실제 단어 입력 대기; sentence인덱스/추정초 fallback 없음'}for st in s['sentences'])
    save(H/'production/all_photo_bindings.json',{'status':'승인된 기존 사진20개 명시연결','source_manifest':'visual/top20-8min-v2/photo_assets_v2.json','bindings':data['bindings'],'new_images_generated':False})
    save(H/'main/prepared/scene_templates.json',{'scene_count':26,'sentence_count':133,'timing_locked':False,'templates':templates})
    save(H/'main/prepared/anchor_plan.json',anchor_plan)
    save(H/'production/preparation_input_manifest.json',{'inputs':source_manifest(data),'staged_assets':staged})
    receipt={'status':'전체인프라준비완료_실측대기','approval_decision_id':data['authorization']['decision_id'],'scene_json_sha256':JSON_SHA,'script_md_sha256':MD_SHA,'canonical_narration_ready':data['script'].get('narration_ready'),'approval_basis':'canonical 메타를 수정하지 않고 matching script/production receipt로 허용','scene_count':26,'sentence_count':133,'photo_bindings':20,'price_panels':20,'verified_price_maps':20,'staged_assets':len(staged),'renderer_types':sorted(set(t['renderer']for t in templates)),'main_timeline_created':False,'production_duration_s':None,'timing_locked':False,'full_render_started':False,'next_input':'총괄의실제 locked_timing.json; render_contract.json 참조'}
    save(H/'production/preparation.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

def production(data,timing_path,version):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,40}',version):raise ValueError('안전한 새 버전명이 필요합니다.')
    tp=Path(timing_path).resolve()
    if sha(tp)!='62c379c0b4d3d73e4ee3f9b17a0ecf6cab18edc2e38151df7b98369a23f206e6':raise ValueError('현재 최종 총괄lock SHA와 다릅니다.')
    T=normalize_director_lock(json.loads(tp.read_text(encoding='utf-8-sig')));lock=validate_lock(T,data)
    project=H/'main'/version
    if project.exists():raise FileExistsError('기존 본편 입력 보존: 새 --version을 사용하십시오.')
    assets=project/'assets';staged=[stage(a,assets)for a in data['assets']]
    audio=lock['audio_path'];audio_dest='narration'+audio.suffix
    staged.append(stage({'source':str(audio),'dest':audio_dest,'sha256':sha(audio),'kind':'actual_audio'},assets))
    scenes=lock['scenes'];panels={k:dict(v,status='verified')for k,v in data['panels'].items()}
    maps=copy.deepcopy(data['map_assets'])
    for rid,m in maps.items():m['_staged_file']='../assets/'+rid+'_price_map.svg'
    g=dict(T=T,scenes=scenes,regions=data['regions'],photos=data['photos'],panels=panels,word_groups=lock['word_groups'],readings=lock['readings'])
    g.update(main_primitives.install(g));ctx={'anchor_audit':[],'layout_families':{}}
    install_main_layouts(g,ctx);g['opening']=g['main_opening'];install_v3(g,ctx,panels,maps,data['bindings'])
    set_protected_phrases([p['representative']['apt_name']for p in panels.values()])
    write(project/'style.css',main_primitives.CSS)
    hosts=[];caps=[];story=[]
    for s in scenes:
        sid=s['scene_id'];dur=s['duration_s']
        if s.get('region_id'):body,anim=g['region_scene'](s)
        elif sid in ['O001','O002']:body,anim=g['opening'](s)
        elif sid=='I001':body,anim=g['insight1'](s)
        elif sid=='I002':body,anim=g['insight2'](s)
        else:body,anim=g['conclusion'](s,hold=sid=='E001')
        content=g['shell'](s)+body
        if 'provisional' in content or '확정 대기' in content or 'spec-flag' in content:raise ValueError('본편에 임시시안 문구가 남았습니다: '+sid)
        sub=f'<template><style>#{sid}{{position:absolute;inset:0;width:100%;height:100%;background:#f6f4ef;overflow:hidden}}</style><div id="{sid}" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur:.9f}">{content}</div><script>document.fonts.ready.then(()=>{{{FIT_SCRIPT}const tl=gsap.timeline({{paused:true}});{anim}window.__timelines["{sid}"]=tl;}});</script></template>'
        write(project/f'scenes/{sid}.html',sub)
        hosts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="scenes/{sid}.html" data-start="{s["start_s"]:.9f}" data-duration="{dur:.9f}" data-track-index="1" data-width="1920" data-height="1080"></div>')
        for st in s['sentence_times']:
            for c in make_cues(st,lock['word_groups'][st['sentence_id']],lock['readings'][st['sentence_id']]):caps.append(dict(c,scene_id=sid,start_s=s['start_s']+c['start_s'],end_s=s['start_s']+c['end_s']))
        story.append({'scene_id':sid,'start_s':s['start_s'],'end_s':s['end_s'],'timing_locked':True,'photo':data['bindings'].get(sid),'price_phase':s.get('_phase')})
    expected={st['sentence_id']:st['display_text']for s in data['scenes']for st in s['sentences']};grouped={}
    for c in caps:
        grouped.setdefault(c['sentence_id'],[]).append(c)
        for b in lock['inserts']:
            if c['start_s']<b['start_s']+b['duration_s'] and c['end_s']>b['start_s']:raise ValueError('브랜드 위 자막 침범')
    if set(grouped)!=set(expected) or any(' '.join(c['text']for c in grouped[sid])!=text for sid,text in expected.items()):raise ValueError('전체133문장 display_text와 실제큐 결합이 다릅니다.')
    total=lock['total_s'];windows=body_windows(scenes,lock['last_word'])
    for a,b in windows:
        if any(a<v['start_s']+v['duration_s'] and b>v['start_s']for v in lock['inserts']):raise ValueError('브랜드 위 흰 자막배경 침범')
    caption_body=markup(windows,'main-'+version)+''.join(f'<div id="main-cue-{i}" class="clip caption fit" data-min-font="24" data-start="{c["start_s"]:.9f}" data-duration="{c["end_s"]-c["start_s"]:.9f}" data-track-index="4" data-track-kind="captions">{g["esc"](c["text"])}</div>'for i,c in enumerate(caps))
    write(project/'scenes/CAPTIONS.html',f'<template><style>#CAPTIONS{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}</style><div id="CAPTIONS" data-composition-id="CAPTIONS" data-width="1920" data-height="1080" data-duration="{total:.9f}">{caption_body}</div><script>document.fonts.ready.then(()=>{{{FIT_SCRIPT}window.__timelines["CAPTIONS"]=gsap.timeline({{paused:true}});}});</script></template>')
    hosts.append(f'<div id="CAPTIONS" class="clip" data-composition-id="CAPTIONS" data-composition-src="scenes/CAPTIONS.html" data-start="0" data-duration="{total:.9f}" data-track-index="4" data-track-kind="captions" data-width="1920" data-height="1080"></div>')
    for b in lock['inserts']:
        kind=b['kind'];sound='muted' if T.get('audio_includes_brand') else 'data-has-audio="true"'
        hosts.append(f'<video id="brand-{kind}" class="clip" src="assets/brand_{kind}.mp4" {sound} data-start="{b["start_s"]:.9f}" data-duration="{b["duration_s"]:.9f}" data-track-index="2" style="position:absolute;inset:0;width:100%;height:100%"></video>')
    hosts.append(f'<audio id="main-narration" class="clip" src="assets/{audio_dest}" data-start="0" data-duration="{total:.9f}" data-track-index="3"></audio>')
    write(project/'index.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><link rel="stylesheet" href="style.css"></head><body><div id="film" data-composition-id="film" data-width="1920" data-height="1080" data-duration="{total:.9f}">{"".join(hosts)}</div><script>window.__timelines["film"]=gsap.timeline({{paused:true}});</script></body></html>')
    save(project/'caption_mapping.json',{'timing_locked':True,'source_script_sha256':JSON_SHA,'source_markdown_sha256':MD_SHA,'basis':'actual_original_word_boundaries_display_reading_map','scene_count':26,'sentence_count':133,'cues':caps,'caption_background_windows':windows,'brand_intersections':0,'E001_captions':0})
    save(project/'timeline_resolved.json',{'timing_locked':True,'duration_s':total,'scenes':scenes,'inserts':lock['inserts'],'last_speech_end_s':lock['last_word'],'source_timing':str(tp),'source_timing_sha256':sha(tp)})
    save(project/'anchor_audit.json',ctx['anchor_audit']);save(project/'phase_audit.json',ctx['phase_audit']);save(project/'photo_audit.json',ctx['photo_audit']);save(project/'price_audit.json',ctx['price_audit'])
    save(project/'placement.json',story)
    credits=[{'region_id':rid,'actual_place':p['actual_place'],'capture_year':p['photo_capture_year'],'license':p['license'],'full_attribution':p['license']['attribution_ko'],'price_map_attribution':maps[rid]['attribution'],'photo_use':'지역자료사진; 대표가격단지의전경이아님','changes':'원본바이트·비율 유지; 새 생성·크롭·색보정없음'}for rid,p in data['photos'].items()]
    save(project/'credits.json',credits)
    manifest=source_manifest(data,[str(tp),str(lock['words_path']),str(audio),T['_normalization_source']])
    save(project/'input_freeze.json',{'inputs':manifest,'staged_assets':staged,'approval_decision_id':data['authorization']['decision_id'],'source_script_sha256':JSON_SHA,'source_markdown_sha256':MD_SHA})
    freeze=[{'path':str(p.relative_to(project)).replace('\\','/'),'sha256':sha(p)}for p in sorted(project.rglob('*'))if p.is_file()]
    save(project/'source_freeze.json',{'files':freeze,'timing_locked':True})
    receipt={'status':'전체실측HTML빌드완료_자동품질검사대기','project':str(project),'version':version,'scene_count':26,'sentence_count':133,'photo_count':20,'price_panel_count':20,'caption_cue_count':len(caps),'timing_locked':True,'duration_s':total,'canvas':[1920,1080],'fps':30,'approval_decision_id':data['authorization']['decision_id'],'audio_connected':True,'full_render_started':False,'actual_listening_performed':False,'continuous_playback_performed':False}
    save(project/'build_receipt.json',receipt);save(H/'production/active_project.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(description='승인된26장면 main 인프라·실측 전용 빌드');ap.add_argument('--mode',choices=['prepare','production'],required=True);ap.add_argument('--timing');ap.add_argument('--version',default='v1');args=ap.parse_args()
    if args.mode=='production' and not args.timing:ap.error('production은 부모의 실제 --timing 입력이 필요합니다. preview fallback 없음')
    data=load_inputs()
    if args.mode=='prepare':prepare(data)
    else:production(data,args.timing,args.version)
if __name__=='__main__':main()
