"""Retiming adapter for the frozen caption-v7 picture. Local files only; no generation.

--prepare records reusable inputs only. --timing/--handoff require formal Jun delivery.
"""
import argparse, copy, hashlib, html, json, math, re, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
OLD = EP/'outputs/private-production-v3'
OUT = EP/'outputs/jun-production-v1'
AUTH = EP/'director/launch-and-jun-v1/authorization.json'
SCRIPT_SHA = '0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
CUES = re.compile(r'<p\b(?=[^>]*\bclass="clip cue")[^>]*>.*?</p>', re.S)
AUDIO = re.compile(r'<audio\b[^>]*>.*?</audio>', re.S)
TIMED = re.compile(r'<\w+\b[^>]*\bdata-start="[^>]*>')

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def resolve(p):
    p=Path(p)
    return p if p.is_absolute() else ROOT/p if (ROOT/p).exists() else EP/p
def norm(s): return ''.join(c.lower() for c in s if c.isalnum())
def rel(p): return Path(p).resolve().relative_to(ROOT).as_posix()
def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def table(s,name):
    m=re.search(r'\bconst '+name+r'\s*=\s*([\[{].*?[\]}])\s*;',s,re.S)
    if not m: raise ValueError('Missing timing table '+name)
    return m,json.loads(m[1])
def put_table(s,name,value):
    m,_=table(s,name)
    return s[:m.start(1)]+json.dumps(value,ensure_ascii=False)+s[m.end(1):]
def skeleton(s):
    s=AUDIO.sub('',s);s=CUES.sub('__CAPTION__',s)
    s=TIMED.sub(lambda m: re.sub(r'data-(start|duration)="[^"]*"',r'data-\1="__TIME__"',m[0]),s)
    for key in ['C','S','ANCHORS','SPANS']:
        try: s=put_table(s,key,{})
        except ValueError: pass
    return s
def caption_nodes(cues,total,last,number,hook_cut=None):
    nodes=[]
    for i,c in enumerate(cues):
        lines=c.get('display_lines') or [c['text']]
        if not 1<=len(lines)<=2 or norm(''.join(lines))!=norm(c['text']): raise ValueError('Caption lines differ')
        content=html.escape(lines[0]) if len(lines)==1 else '<span class="caption-lines" style="display:block;white-space:pre">'+html.escape('\n'.join(lines))+'</span>'
        end=min(c['end_s']+.08,cues[i+1]['start_s'] if i+1<len(cues) else total,last if number==10 else total)
        if number==1 and c['paragraph']==0 and hook_cut is not None:end=min(end,hook_cut)
        nodes.append(f'<p id="cue{i:03d}" class="clip cue" data-start="{c["start_s"]}" data-duration="{end-c["start_s"]:.6f}" data-track-index="9">{content}</p>')
    return '\n'.join(nodes)

def preparation():
    auth=read(AUTH);assert auth['script_sha256']==SCRIPT_SHA and auth['paid_voice_generation_authorized']
    prior=read(OLD/'render_plan.json');assert prior['script_sha256']==SCRIPT_SHA
    script=resolve(prior['script_path']);assert sha(script)==SCRIPT_SHA
    files=[AUTH,script,OLD/'render_plan.json',EP/'editor/private-production-v3/visual_audio_reuse_manifest.json',
           EP/'editor/private-production-v2/prepare_mix.py',EP/'editor/private-production-v2/render_pipeline.py',
           EP/'editor/private-production-v3/run_cli_checks.py',
           EP/'outputs/private-production-v1/media-bin/ffmpeg.exe',
           ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe',
           EP/'outputs/private-production-v1/audio-deps/package-lock.json']
    files += list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))
    requirements=[]
    for ch in prior['chapters']:
        folder=OLD/ch['project'];files += [folder/'index.html',folder/'timing.json',folder/'anchor_audit.json']
        for a in read(folder/'anchor_audit.json')['anchors']:
            requirements.append({'chapter':ch['chapter'],'literal':a['literal'],'chapter_normalized_character_offset':a['new_character_offset']})
        files += [p for p in (folder/'assets').rglob('*') if p.is_file() and p.name not in ['narration.wav','music-bed.wav']]
    for key in ['clean_intro','clean_outro','existing_music']:
        asset=prior['brand_assembly'][key];p=resolve(asset['path']);assert sha(p)==asset['sha256'];files.append(p)
    inputs={rel(p):sha(p) for p in files}
    dump(HERE/'reuse_preparation.json',{'status':'prepared_only_no_Jun_timing_no_final_edit','script_sha256':SCRIPT_SHA,'input_sha256':inputs,'source_projects':10,'semantic_cues':206,'picture_policy':'frozen caption-v7 HTML/CSS/assets and chart numbers; timing tables/clip intervals/audio only change','new_paid_calls':0,'render_started':False,'CLI_pin':'0.8.181'})
    dump(HERE/'anchor_requirements.json',{'anchors':requirements,'basis':'same frozen chapter text; map exact alphanumeric offset through prepared display_mapping and actual Jun alignment'})
    return prior,inputs

def actual_hook(ch):
    first=ch['paragraphs'][0];pid=first['paragraph']
    end=max(max(c['end_s'] for c in ch['cues'] if c['paragraph']==pid),first['last_native_word_end_s'],first['last_pcm_signal_end_s'])
    hook=math.ceil(end*30-1e-8)/30
    if any(c['start_s']<hook<c['end_s'] for c in ch['cues']):raise ValueError('Brand split would intersect actual Jun speech')
    return hook

def anchor_clock(ch,prepared):
    """Map frozen original-text positions to provider character times, without interpolation."""
    points=[];evidence=[];paragraph_meta={p['paragraph']:p for p in ch['paragraphs']}
    for para in prepared['paragraphs']:
        p=paragraph_meta[para['paragraph']]
        pid=p.get('paragraph_id') or para['paragraph_id']
        align_path=EP/'narration/jun-production-v1/paragraphs'/pid/'alignment.json'
        align=read(align_path)
        if ''.join(align['characters'])!=para['spoken_text']: raise ValueError('Aligned voice input differs '+pid)
        starts=align['character_start_times_seconds'];ends=align['character_end_times_seconds']
        for raw,c in enumerate(para['text']):
            if not c.isalnum(): continue
            m=next(x for x in para['display_mapping'] if x['source_start']<=raw<x['source_end'])
            si=m['spoken_start']+(raw-m['source_start'] if m['kind']=='literal' else 0)
            points.append((p['offset_s']+starts[si],pid,raw,si,m['kind']))
        evidence.append({'paragraph_id':pid,'alignment_file':rel(align_path),'alignment_sha256':sha(align_path),'PCM_sha256':sha(resolve(p['wave_file'])),'offset_s':p['offset_s'],'first_provider_character_s':min(starts),'last_provider_character_s':max(ends)})
    def clock(a):
        idx=a['new_character_offset'];t,pid,raw,si,kind=points[idx]
        return t,{**a,'time_s':t,'paragraph_id':pid,'source_character_index':raw,'spoken_character_index':si,'mapping_kind':kind,'timing_basis':'actual Jun provider character alignment + measured chapter paragraph offset; pronunciation token starts atomically'}
    return clock,evidence

def build(timing_path,handoff_path):
    prior,inputs=preparation();delivery=read(handoff_path);timing=read(timing_path)
    status=str(delivery.get('status','')).lower()
    if any(x in status for x in ['pending','failed','in_progress']) or not any(x in status for x in ['complete','pass','완료','통과']): raise ValueError('Formal narrator handoff incomplete: '+status)
    if delivery.get('required_open_count',0) or delivery.get('required_issues') or delivery.get('required_narration_errors'): raise ValueError('Narrator required issue remains')
    if timing['script_sha256']!=SCRIPT_SHA or timing['audio_revision']!='jun-production-v1': raise ValueError('Jun script/version lock differs')
    if sha(resolve(timing['script_path']))!=SCRIPT_SHA: raise ValueError('Script bytes changed')
    if len(timing['chapters'])!=10 or sum(len(c['cues']) for c in timing['chapters'])!=206: raise ValueError('206 semantic captions required')
    if (OUT/'render_plan.json').exists(): raise ValueError('Preserve existing built project; choose a new version before rebuild')
    prepared=read(EP/'narration/free-tts-v1/prepare-v6/prepared.json')
    phonetics=read(EP/'narration/jun-replacement-v1/pronunciation_proposal.json')
    phon={p['paragraph_id']:p for p in phonetics['paragraphs']}
    for ch in prepared['chapters']:
        for p in ch['paragraphs']:
            if p['spoken_text']!=phon[p['paragraph_id']]['proposed_spoken_text']: raise ValueError('Frozen display/spoken mapping differs')
    ffprobe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    chapters=[];proof=[];snapshots=[];speech=[]
    for ch in timing['chapters']:
        n=int(ch['chapter']);folder=OLD/f'ch{n:02d}';dest=OUT/f'ch{n:02d}'
        old=read(folder/'timing.json');source=(folder/'index.html').read_text(encoding='utf8');old_cues=old['cues']
        if [(c['id'],c['text'],c.get('display_lines')) for c in ch['cues']] != [(c['id'],c['text'],c.get('display_lines')) for c in old_cues]: raise ValueError('Frozen semantic segmentation changed')
        order=[p['paragraph'] for p in ch['paragraphs']];pm={p:i for i,p in enumerate(order)}
        cues=[{**c,'paragraph_source':c['paragraph'],'paragraph':pm[c['paragraph']]} for c in ch['cues']]
        total=ch['total_seconds'];last=ch['last_speech_end_s'];audio=resolve(ch['audio_file'])
        assert sha(audio)==ch['audio_sha256'] and abs(total*30-round(total*30))<1e-5
        if n==10 and not 3-1e-6<=total-last<3+1/30+1e-5: raise ValueError('Final speech + 3s frame-aligned hold required')
        previous=0
        for c in cues:
            if not previous<=c['start_s']<c['end_s']<=total: raise ValueError('Overlapping or invalid cue')
            previous=c['end_s']
        actual=read_probe(audio,ffprobe);assert abs(float(actual['format']['duration'])-total)<1/30
        clock,pe=anchor_clock(ch,next(x for x in prepared['chapters'] if x['chapter']==n))
        audit=read(folder/'anchor_audit.json');anchors=[]
        for a in audit['anchors']:
            t,b=clock(a);anchors.append(b)
        by_literal={a['literal']:a['time_s'] for a in anchors}
        starts=[0 if n==1 else 3]+[max(0 if n==1 else 3,by_literal[s['narration_anchor']]-.15) for s in old['scenes'][1:]]
        if any(b<=a for a,b in zip(starts,starts[1:])): raise ValueError('Nonmonotonic actual scene anchors')
        scenes=[{**s,'start_s':starts[i],'end_s':starts[i+1] if i+1<len(starts) else total} for i,s in enumerate(old['scenes'])]
        spans={s['scene_id']:[s['start_s'],s['end_s']-s['start_s']] for s in scenes}
        text=AUDIO.sub('',source)
        matches=list(CUES.finditer(text));block=caption_nodes(cues,total,last,n,actual_hook(ch) if n==1 else None)
        text=text[:matches[0].start()]+block+text[matches[-1].end():]
        if n==1:
            _,old_times=table(text,'C');assert len(old_times)==len(anchors)
            text=put_table(text,'C',[a['time_s'] for a in anchors]);text=put_table(text,'S',spans)
        else:
            text=put_table(text,'ANCHORS',by_literal);text=put_table(text,'SPANS',spans)
        intervals={'root':(0,total),'brand':(0 if n==1 else 3,total),'tag':(0 if n==1 else 3,total),'capbox':(0 if n==1 else 3,last if n==10 else total),'card':(0,3)}
        for s in scenes:
            for key in [s['scene_id'],'title-'+s['scene_id'],'src-'+s['scene_id']]: intervals[key]=(s['start_s'],s['end_s'])
        def timed(m):
            tag=m[0];idmatch=re.search(r'\bid="([^"]+)"',tag);ident=idmatch[1]
            if ident.startswith('cue'): return tag
            if ident not in intervals: raise ValueError('Unmapped timed node '+ident)
            a,b=intervals[ident]
            return re.sub(r'data-duration="[^"]*"',f'data-duration="{b-a}"',re.sub(r'data-start="[^"]*"',f'data-start="{a}"',tag))
        text=TIMED.sub(timed,text)
        if skeleton(text)!=skeleton(source): raise ValueError('Non-timing picture bytes changed')
        dest.mkdir(parents=True,exist_ok=True)
        assets={}
        for p in (folder/'assets').rglob('*'):
            if not p.is_file() or p.name in ['narration.wav','music-bed.wav']:continue
            target=dest/'assets'/p.relative_to(folder/'assets');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
            assert sha(target)==sha(p);assets[p.relative_to(folder/'assets').as_posix()]=sha(p)
        for name in ['hyperframes.json','package.json','meta.json']:
            shutil.copy2(folder/name,dest/name)
        shutil.copy2(audio,dest/'assets/narration.wav')
        # Preserve the existing location of the narration element (ch01 is inside root in frozen v7).
        original_audio=AUDIO.search(source)
        tail=source[original_audio.end():];tail=AUDIO.sub('',tail)
        # Existing audio was contiguous at root close; insert at the same unchanged suffix.
        marker=tail[:min(80,len(tail))]
        pos=text.rfind(marker)
        if pos<0:raise ValueError('Cannot preserve audio insertion point')
        voice=f'<audio id="narration" class="clip" src="assets/narration.wav" data-start="0" data-duration="{total}" data-track-index="10"></audio>'
        text=text[:pos]+voice+text[pos:]
        (dest/'index.html').write_text(text,encoding='utf8')
        dump(dest/'timing.json',{'chapter':n,'timing_basis':'actual_Jun_provider_character_alignment_and_PCM','total_seconds':total,'last_speech_end_s':last,'audio_revision':'jun-production-v1','cues':cues,'scenes':scenes})
        dump(dest/'anchor_audit.json',{'chapter':n,'anchors':anchors,'paragraph_alignment':audit.get('paragraph_alignment',[]),'paragraph_audio_alignment':pe,'zero_second_fallback':False})
        row={'chapter':n,'title':ch['title'],'total_seconds':total,'last_speech_end_s':last,'timing_basis':'measured_audio_units','project':f'ch{n:02d}','scenes':scenes}
        chapters.append(row)
        proof.append({'chapter':n,'prior_HTML_sha256':sha(folder/'index.html'),'new_HTML_sha256':sha(dest/'index.html'),'normalized_non_timing_picture_sha256':hashlib.sha256(skeleton(text).encode()).hexdigest(),'non_timing_picture_bytes_preserved':skeleton(text)==skeleton(source),'assets_sha256':assets,'voice_sha256':sha(audio)})
        speech.append({**{k:v for k,v in ch.items() if k not in ['cues','paragraphs']},'paragraphs':ch['paragraphs']})
        for s in scenes:
            d=s['end_s']-s['start_s'];snapshots.append({'chapter':n,'scene_id':s['scene_id'],'project':f'ch{n:02d}','representative_s':s['start_s']+d*.7,'before_end_s':s['end_s']-1/30,'after_start_s':s['start_s']+1/30,'timing_basis':'measured_audio_units'})
    edl=assembly(chapters,prior,timing)
    for ch in speech:
        for p in ch['paragraphs']:
            start=p['first_provider_character_start_s']
            off=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==ch['chapter'] and o['local_start_s']<=start<o['local_end_s'])
            p['film_global_offset_s']=off
            for key in ['first_provider_character_start_s','first_pcm_signal_start_s','last_native_word_end_s','last_pcm_signal_end_s']:
                p['film_'+key]=p[key]+off
    plan={**prior,'revision':'jun-production-v1','chapters':chapters,'status':'measured_audio_units','audio_revision':'jun-production-v1','voice':timing['voice'],'caption_revision':'frozen-206-with-Jun-times','caption_candidate':False,'caption_timing_path':timing_path.relative_to(EP).as_posix(),'caption_timing_sha256':sha(timing_path),'full_rendered':False,'full_render_allowed':False,'total_seconds_with_brand':edl['total_seconds'],'offset_map':edl['offset_map'],'pending':['current Jun source/bounds/carve checks','new actual render and decode','independent exact-final Codex/Claude reviews by main']}
    for key in ['final_mp4','final_sha256','render_gate_receipts','render_receipt','prepared_mix_receipt','prepared_mix_receipt_sha256']:plan.pop(key,None)
    dump(OUT/'render_plan.json',plan);dump(OUT/'snapshot_times.json',{'samples':snapshots});dump(OUT/'cue_change_groups.json',{'groups':[],'scope':'all206 timing changed; every cue checked by preview validator'})
    dump(HERE/'visual_reuse_manifest.json',{'status':'frozen_picture_retimed_only','chapters':proof,'financial_data_QA':'unchanged data/geometry retained; old timing QA is not inherited'})
    dump(OUT/'speech_boundaries.json',{'audio_revision':timing['audio_revision'],'caption_timing_sha256':sha(timing_path),'chapters':speech,'actual_listening':False,'timing_note':'provider character and thresholded PCM estimates; no human listening claim'})
    for p in [timing_path,handoff_path,EP/'narration/free-tts-v1/prepare-v6/prepared.json',EP/'narration/jun-replacement-v1/pronunciation_proposal.json']:
        inputs[rel(p)]=sha(p)
    for d in (OUT.glob('ch??')):
        a=read(d/'anchor_audit.json')
        for p in a['paragraph_audio_alignment']:
            inputs[p['alignment_file']]=p['alignment_sha256']
    dump(OUT/'input_manifest.json',{'script_sha256':SCRIPT_SHA,'caption_timing_sha256':sha(timing_path),'inputs_sha256':inputs,'CLI_pin':'0.8.181','new_paid_calls':0})
    dump(HERE/'build_receipt.json',{'status':'Jun_measured_source_built_checks_pending','script_sha256':SCRIPT_SHA,'caption_timing_sha256':sha(timing_path),'narrator_handoff':rel(handoff_path),'narrator_handoff_sha256':sha(handoff_path),'cue_count':206,'scene_count':len(snapshots),'actual_listening':False,'continuous_playback':False})
    print(json.dumps({'status':'source_built','chapters':10,'cues':206,'scenes':len(snapshots),'film_seconds':edl['total_seconds']}))

def read_probe(path,ffprobe):
    return json.loads(subprocess.check_output([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(path)]))

def assembly(chapters,prior,timing):
    ch1=read(OUT/'ch01/timing.json');hook=actual_hook(timing['chapters'][0])
    # The split must lie in actual silence; neither caption nor next word crosses the clean brand.
    if any(c['start_s']<hook<c['end_s'] for c in ch1['cues']):raise ValueError('Hook cuts an actual caption/speech interval')
    segments=[];offsets=[]
    def seg(id,kind,ch,a,b,g):
        row={'id':id,'type':kind,'source_start_s':a,'source_end_s':b,'global_start_s':g,'global_end_s':g+b-a}
        if ch:row['chapter']=ch
        else:row['asset']=prior['brand_assembly']['clean_intro' if id=='clean_brand_intro' else 'clean_outro']
        segments.append(row)
    seg('opening_hook','chapter',1,0,hook,0);seg('clean_brand_intro','brand',None,0,5,hook)
    seg('chapter_1_after_hook','chapter',1,hook,chapters[0]['total_seconds'],hook+5)
    offsets=[{'chapter':1,'local_start_s':0,'local_end_s':hook,'global_offset_s':0},{'chapter':1,'local_start_s':hook,'local_end_s':chapters[0]['total_seconds'],'global_offset_s':5}]
    cursor=chapters[0]['total_seconds']+5
    for ch in chapters[1:]:
        seg('chapter_'+str(ch['chapter']),'chapter',ch['chapter'],0,ch['total_seconds'],cursor)
        offsets.append({'chapter':ch['chapter'],'local_start_s':0,'local_end_s':ch['total_seconds'],'global_offset_s':cursor});cursor+=ch['total_seconds']
    seg('clean_brand_outro','brand',None,0,10,cursor)
    srt=[];starts=[]
    for ch in chapters:
        off=next(o['global_offset_s'] for o in offsets if o['chapter']==ch['chapter'])
        starts.append({'chapter':ch['chapter'],'title':ch['title'],'global_start_s':0 if ch['chapter']==1 else off,'duration_s':ch['total_seconds']+(5 if ch['chapter']==1 else 0)})
        for c in read(OUT/ch['project']/'timing.json')['cues']:
            off=next(o['global_offset_s'] for o in offsets if o['chapter']==ch['chapter'] and o['local_start_s']<=c['start_s']<o['local_end_s'])
            srt.append(f'{len(srt)+1}\n{stamp(c["start_s"]+off)} --> {stamp(c["end_s"]+off)}\n'+'\n'.join(c.get('display_lines') or [c['text']])+'\n')
    (OUT/'captions_measured.srt').write_text('\n'.join(srt),encoding='utf8')
    speech_end=offsets[-1]['global_offset_s']+chapters[-1]['last_speech_end_s']
    edl={'status':'measured_audio_units','fps':30,'hook_cut_s':hook,'intro_video_frames':150,'outro_video_frames':300,'segments':segments,'offset_map':offsets,'total_seconds':cursor+10,'actual_last_speech_global_s':speech_end,'outro_delay_from_last_speech_s':cursor-speech_end,'captions':'captions_measured.srt','caption_hidden_intervals':[{'start_s':hook,'end_s':hook+5,'reason':'clean_brand_intro'},{'start_s':speech_end,'end_s':cursor+10,'reason':'silent_hold_then_clean_outro'}],'voice_and_picture_use_identical_splits':True,'execute':False}
    dump(OUT/'assembly_edl.json',edl);dump(OUT/'scene_starts.json',{'chapters':starts,'scenes':[{'chapter':ch['chapter'],**s,'global_start_s':s['start_s']+next(o['global_offset_s'] for o in offsets if o['chapter']==ch['chapter'] and o['local_start_s']<=s['start_s']<o['local_end_s'])} for ch in chapters for s in ch['scenes']]})
    (OUT/'metadata_chapters.txt').write_text('\n'.join(stamp(r['global_start_s']).split(',')[0]+' '+str(r['chapter'])+'. '+r['title'] for r in starts)+'\n',encoding='utf8')
    return edl

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--timing');p.add_argument('--handoff');args=p.parse_args()
    if args.prepare:
        preparation();print(json.dumps({'status':'reuse_prepared_only','render_started':False}))
    else:
        if not args.timing or not args.handoff:p.error('--timing and --handoff required')
        build(resolve(args.timing),resolve(args.handoff))
