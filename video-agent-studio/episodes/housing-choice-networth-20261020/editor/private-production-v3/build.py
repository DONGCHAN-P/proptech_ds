"""Caption-only v7 integration into frozen v2 picture/audio. Never generates voice or renders."""
import argparse,copy,hashlib,html,json,re,shutil,sys
from difflib import SequenceMatcher
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
OLD=EP/'outputs/private-production-v2';OUT=EP/'outputs/private-production-v3'
AUTH=EP/'director/two-episode-production-v1/render_authorization_caption_v7.json'
CUES=re.compile(r'<p\b(?=[^>]*\bclass="clip cue")[^>]*>.*?</p>',re.S)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(s):return re.sub(r'\s+','',s)
def dump(p,r):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def resolve(p):
    p=Path(p)
    return p if p.is_absolute() else ROOT/p if (ROOT/p).exists() else EP/p
def cue_signature(c):return (c['text'],round(c['start_s'],8),round(c['end_s'],8))
def paragraph_text(cues,p):return compact(''.join(c['text'] for c in cues if int(c['paragraph'])==p))
def captions(cues,total,body_end):
    rows=[]
    for i,c in enumerate(cues):
        lines=c.get('display_lines') or [c['text']]
        if not isinstance(lines,list) or not all(isinstance(line,str) for line in lines) or not 1<=len(lines)<=2 or compact(''.join(lines))!=compact(c['text']):raise ValueError('Invalid explicit lines '+c['id'])
        if any('\n' in line or '\r' in line for line in lines):raise ValueError('display_lines must contain individual lines')
        content=html.escape(lines[0]) if len(lines)==1 else '<span class="caption-lines" style="display:block;white-space:pre">'+html.escape('\n'.join(lines))+'</span>'
        end=min(c['end_s']+.08,cues[i+1]['start_s'] if i+1<len(cues) else total,body_end)
        rows.append(f'<p id="cue{i:03d}" class="clip cue" data-start="{c["start_s"]}" data-duration="{end-c["start_s"]:.6f}" data-track-index="9">{content}</p>')
    return '\n'.join(rows)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--timing',default='narration/free-tts-v1/caption-v7/final_timing.json');parser.add_argument('--narration-receipt',required=True);parser.add_argument('--candidate',action='store_true');parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    timing_path=resolve(args.timing);narration_path=resolve(args.narration_receipt)
    delivery=read(narration_path);timing_bytes=timing_path.read_bytes();timing=json.loads(timing_bytes.decode('utf-8-sig'));timing_sha=hashlib.sha256(timing_bytes).hexdigest();auth=read(AUTH);lock=read(EP/'director/two-episode-production-v1/locked_script.json');prior=read(OLD/'render_plan.json')
    script=resolve(lock['script_path'])
    if sha(script)!=lock['script_sha256'] or timing['script_sha256']!=lock['script_sha256'] or auth['script_sha256']!=lock['script_sha256']:raise ValueError('Immutable approved script lock differs')
    if auth.get('full_affected_render_authorized') is not True or auth['output_revision']!='private-production-v3':raise ValueError('Current caption-only authorization required')
    if timing['audio_revision']!='production-injoon-v6' or delivery.get('required_open_count',0):raise ValueError('Narrator completion/audio revision contract failed')
    if not args.candidate:
        checks_path=narration_path.parent/delivery.get('checks','checks.json');checks=read(checks_path)
        if checks.get('passed') is not True or delivery.get('required_narration_errors') or delivery.get('cues_after')!=sum(len(c['cues']) for c in timing['chapters']):raise ValueError('Formal narrator cue validation is incomplete or differs from timing')
    if args.freeze:
        built=read(HERE/'build_receipt.json');plan=read(OUT/'render_plan.json')
        if built['caption_timing_sha256']!=sha(timing_path) or plan['caption_timing_sha256']!=sha(timing_path):raise ValueError('Candidate timing changed; regenerate affected source before freeze')
        status=str(delivery.get('status','')).lower()
        if not any(t in status for t in ['pass','통과','완료','complete']) or delivery.get('required_open_count',0) or delivery.get('required_issues'):raise ValueError('Formal narrator validation/handoff required')
        built.update(status='caption_only_source_built',candidate=False,narrator_receipt=str(narration_path.relative_to(EP)).replace('\\','/'),narrator_receipt_sha256=sha(narration_path))
        plan['caption_candidate']=False;dump(HERE/'build_receipt.json',built);dump(OUT/'render_plan.json',plan)
        manifest=read(OUT/'input_manifest.json');manifest['inputs_sha256'][narration_path.relative_to(ROOT).as_posix()]=sha(narration_path);dump(OUT/'input_manifest.json',manifest)
        print(json.dumps({'status':'formal_caption_source_frozen','caption_timing_sha256':sha(timing_path),'source_HTML_regenerated':False}));return
    if OUT.exists() and (OUT/'render_plan.json').exists() and not read(OUT/'render_plan.json').get('caption_candidate'):raise ValueError('Frozen caption project already exists; preserve before rebuilding')
    OUT.mkdir(exist_ok=True)
    all_groups=[];proof=[];chapters=[];mix=read(EP/'editor/private-production-v2/mix_receipt.json');counts=[]
    for current in timing['chapters']:
        n=int(current['chapter']);project=f'ch{n:02d}';source=OLD/project;target=OUT/project;old_timing=read(source/'timing.json');old_cues=old_timing['cues']
        if abs(current['total_seconds']-old_timing['total_seconds'])>1e-7 or abs(current['last_speech_end_s']-old_timing['last_speech_end_s'])>1e-7:raise ValueError('Audio duration/scene clock changed')
        if sha(resolve(current['audio_file']))!=sha(source/'assets/narration.wav'):raise ValueError('Audio bytes changed')
        source_order=[int(p['paragraph']) for p in current['paragraphs']];pmap={p:i for i,p in enumerate(source_order)}
        cues=[{**c,'paragraph_source':c['paragraph'],'paragraph':pmap[int(c['paragraph'])]} for c in current['cues']]
        for key in ['text','spoken_text']:
            if compact(''.join(c[key] for c in cues))!=compact(''.join(c[key] for c in old_cues)):raise ValueError('Caption/spoken text conservation failed')
        for p in range(len(source_order)):
            if paragraph_text(cues,p)!=paragraph_text(old_cues,p):raise ValueError('Caption paragraph mapping changed')
        previous=0
        for c in cues:
            if not previous<=c['start_s']<c['end_s']<=current['total_seconds']:raise ValueError('Caption overlap or invalid native time')
            if c['text'].strip() in ['바뀝니다.','있습니다.']:raise ValueError('Known orphan predicate remains')
            previous=c['end_s']
        shutil.copytree(source,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.hyperframes','node_modules','renders'))
        original=(source/'index.html').read_text(encoding='utf8');old_nodes=CUES.findall(original)
        if len(old_nodes)!=len(old_cues):raise ValueError('Cannot identify every existing caption node')
        cap_end=current['last_speech_end_s'] if n==10 else current['total_seconds']
        generated=captions(cues,current['total_seconds'],cap_end)
        # Keep every byte outside caption nodes, including newlines, GSAP, IDs and exact carve attrs.
        first=CUES.search(original);end=list(CUES.finditer(original))[-1].end()
        between=CUES.sub('',original[first.start():end])
        if between.strip():raise ValueError('Caption nodes are not a contiguous isolated block')
        result=original[:first.start()]+generated+original[end:]
        def strip(s):
            nodes=list(CUES.finditer(s))
            return s[:nodes[0].start()]+'__FROZEN_CAPTION_BLOCK__'+s[nodes[-1].end():]
        if strip(result)!=strip(original):raise ValueError('Non-caption picture/audio HTML changed')
        (target/'index.html').write_text(result,encoding='utf8')
        new_timing={**old_timing,'cues':cues,'caption_revision':'caption-v7','visual_timing_basis':'frozen v2 scenes and T anchors; identical v6 audio'}
        dump(target/'timing.json',new_timing)
        asset_sha={p.relative_to(source/'assets').as_posix():sha(p) for p in (source/'assets').rglob('*') if p.is_file()}
        if any(sha(target/'assets'/k)!=v for k,v in asset_sha.items()):raise ValueError('Asset bytes changed during copy')
        matcher=SequenceMatcher(None,[cue_signature(c) for c in old_cues],[cue_signature(c) for c in cues],autojunk=False)
        for op,a,b,c,d in matcher.get_opcodes():
            if op=='equal':continue
            all_groups.append({'group_id':f'{project}-G{len(all_groups)+1:03d}','chapter':n,'operation':op,'old_cues':old_cues[a:b],'new_cues':cues[c:d],
                               'source_HTML_sha256':sha(target/'index.html'),'source_scene_ids':[s['scene_id'] for s in new_timing['scenes'] if any(s['start_s']<=q['start_s']<s['end_s'] for q in cues[c:d])]})
        row=next(c for c in prior['chapters'] if c['chapter']==n);chapters.append(copy.deepcopy(row));counts.append({'chapter':n,'previous':len(old_cues),'current':len(cues),'HTML_identical':result==original})
        proof.append({'chapter':n,'prior_HTML_sha256':sha(source/'index.html'),'html_sha256':sha(target/'index.html'),'non_caption_HTML_normalized_sha256':hashlib.sha256(strip(result).encode()).hexdigest(),
                      'picture_GSAP_scenes_T_anchors_unchanged':True,'audio_tags_exact':re.findall(r'<audio\b[^>]*>.*?</audio>',original,re.S)==re.findall(r'<audio\b[^>]*>.*?</audio>',result,re.S),
                      'anchor_audit_sha256':sha(source/'anchor_audit.json'),'all_asset_sha256':asset_sha})
        m=next(c for c in mix['chapters'] if c['chapter']==n);m['prior_HTML_sha256']=m['html_sha256'];m['html_sha256']=sha(target/'index.html');m['canonical_carve_reused_exact_audio_tags_and_assets']=True
    plan=copy.deepcopy(prior);plan.update(revision='private-production-v3',full_rendered=False,full_render_allowed=False,caption_revision='caption-v7',caption_candidate=args.candidate,caption_timing_path=str(timing_path.relative_to(EP)).replace('\\','/'),caption_timing_sha256=sha(timing_path),chapters=chapters,
        pending=['independent caption-v7 source QA and current CLI/BBox','affected renders, unchanged final audio stream reuse and final encoded QA'])
    for key in ['final_mp4','final_sha256','render_gate_receipts','render_execution_scope','render_receipt']:plan.pop(key,None)
    dump(OUT/'render_plan.json',plan)
    shutil.copy2(OLD/'assembly_edl.json',OUT/'assembly_edl.json');shutil.copy2(OLD/'snapshot_times.json',OUT/'snapshot_times.json')
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    offsets=read(OUT/'assembly_edl.json')['offset_map'];srt=[]
    for ch in chapters:
        for c in read(OUT/ch['project']/'timing.json')['cues']:
            off=next(o['global_offset_s'] for o in offsets if o['chapter']==ch['chapter'] and o['local_start_s']<=c['start_s']<o['local_end_s'])
            lines=c.get('display_lines') or [c['text']]
            srt.append(f'{len(srt)+1}\n{stamp(c["start_s"]+off)} --> {stamp(c["end_s"]+off)}\n'+ '\n'.join(lines)+'\n')
    (OUT/'captions_measured.srt').write_text('\n'.join(srt),encoding='utf8')
    dump(OUT/'cue_change_groups.json',{'script_sha256':timing['script_sha256'],'caption_timing_sha256':sha(timing_path),'groups':all_groups,'chapter_counts':counts})
    dump(HERE/'visual_audio_reuse_manifest.json',{'status':'caption_only_invariance_pass','chapters':proof,'prior_mix_receipt_sha256':sha(EP/'editor/private-production-v2/mix_receipt.json'),'prior_final_MP4_sha256':sha(OLD/'renders/measured-v6/housing_choice_private_v2_injoon_v6.mp4')})
    mix['reuse_basis']='exact v2 audio tags, all audio bytes and original canonical carve; no carve recomputation';dump(HERE/'mix_receipt.json',mix)
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in [timing_path,narration_path,AUTH,script,EP/'director/two-episode-production-v1/locked_script.json',EP/'director/two-episode-production-v1/caption_revision_v7.json']}
    if not args.candidate:inputs[checks_path.relative_to(ROOT).as_posix()]=sha(checks_path)
    dump(OUT/'input_manifest.json',{'inputs_sha256':inputs,'script_sha256':timing['script_sha256'],'caption_timing_sha256':sha(timing_path),'new_paid_calls':0})
    dump(HERE/'build_receipt.json',{'status':'caption_candidate_built' if args.candidate else 'caption_only_source_built','candidate':args.candidate,'script_sha256':timing['script_sha256'],'caption_timing_sha256':sha(timing_path),'narrator_receipt':str(narration_path.relative_to(EP)).replace('\\','/'),'narrator_receipt_sha256':sha(narration_path),'authorization_sha256':sha(AUTH),
        'cue_count':sum(r['current'] for r in counts),'changed_groups':len(all_groups),'chapter_counts':counts,'source_QA_pending':True,'actual_listening':False,'continuous_playback':False})
    if sha(timing_path)!=timing_sha:raise ValueError('Narrator candidate changed while building; generated candidate must not be frozen until rebuilt from delivered bytes')
    print(json.dumps({'status':'caption_candidate_built' if args.candidate else 'caption_only_source_built','cue_count':sum(r['current'] for r in counts),'changed_groups':len(all_groups),'changed_chapters':[r['chapter'] for r in counts if not r['HTML_identical']]}))
if __name__=='__main__':
    try:main()
    except Exception as e:
        dump(HERE/'issue_BUILD_CONTRACT.json',{'problem':str(e),'impact':'caption integration stopped; no render','next_owner':'main/narrator/editor'});raise
