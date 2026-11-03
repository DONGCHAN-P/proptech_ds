"""Local rebuild-v2 entrypoint. No synthesis, upgrades, network or shared writes.

preflight: inspect installed dependencies and existing immutable inputs.
build: require parent script lock + actual measured voice; emit one scene/project.
render: render ONLY the three representatives, then verify encoded media.
Full film assembly follows representative independent QA in the next phase.
"""
import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
STUDIO = EP.parents[1]
ROOT = STUDIO.parent
OUT = EP / 'outputs/rebuild-v2'
sys.path.insert(0, str(HERE))
from graphics import make

KINDS = ['funding_waterfall', 'ltv_dsr', 'monthly_budget']
ENV = dict(os.environ, DO_NOT_TRACK='1', HYPERFRAMES_NO_UPDATE_CHECK='1', HYPERFRAMES_NO_AUTO_INSTALL='1')
FFMPEG = STUDIO / 'episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FFPROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ASSETS = EP / 'outputs/private-production-v1/ch01/assets'
ENV['PATH']=str(FFMPEG.parent)+os.pathsep+str(FFPROBE.parent)+os.pathsep+os.environ['PATH']


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(p, value):
    p = owned(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def owned(p):
    p = Path(p).resolve()
    if not any(p.is_relative_to(root.resolve()) for root in [HERE, OUT]):
        raise ValueError('Write outside assigned rebuild-v2 folders: '+str(p))
    return p


def source(raw):
    p = Path(raw)
    options = [p] if p.is_absolute() else [EP/p, ROOT/p]
    p = next((v.resolve() for v in options if v.is_file()), None)
    if not p or not p.is_relative_to(ROOT.resolve()) or p.name=='.env':
        raise ValueError('Missing or out-of-workspace input: '+str(raw))
    return p


def pin(raw):
    p = source(raw)
    return {'path':str(p), 'sha256':sha(p), 'bytes':p.stat().st_size}


def checked_ref(ref):
    p = source(ref['path'])
    if sha(p) != ref['sha256']:
        raise ValueError('Changed input: '+str(p))
    return p


def cli_path():
    cli = shutil.which('hyperframes.cmd')
    if not cli or subprocess.check_output([cli,'--version'], text=True, env=ENV).strip()!='0.8.181':
        raise ValueError('Installed HyperFrames 0.8.181 required; no auto-install')
    return cli


def probe(audio):
    return json.loads(subprocess.check_output([str(FFPROBE),'-v','error','-show_format','-show_streams','-of','json',str(audio)],text=True,encoding='utf8',env=ENV))


def preflight():
    cli=cli_path()
    paths=[FFMPEG, FFPROBE, ASSETS/'gsap.min.js', STUDIO/'assets/chapter-backgrounds/v1/manifest.json', EP/'research/verified_case_packet.json', EP/'research/newborn_policy_addendum_v2.json']
    media=read(EP/'director/production-v1/media_assets.json')
    for a in media['assets']:
        checked_ref(a)
    deps=[pin(p) for p in paths]
    expected=read(STUDIO/'episodes/housing-choice-networth-20261020/director/two-episode-production-v1/ffmpeg_receipt.json')['binary_sha256']
    if sha(FFMPEG)!=expected:
        raise ValueError('FFmpeg differs from existing receipt')
    for name in ['Pretendard-Regular.woff2','Pretendard-SemiBold.woff2','Pretendard-Bold.woff2','Pretendard-ExtraBold.woff2']:
        deps.append(pin(ASSETS/'fonts'/name))
    receipt={'status':'local_dependencies_ready_inputs_pending','cli':cli,'version':'0.8.181','dependencies':deps,'brand_and_BGM':media['assets'],'usage':{'status':'unknown','reason':'usage_request_failed','basis':'parent handoff; no repeat credential/network call'},'render_executed':False,'audio_listened':False}
    dump(HERE/'preflight_receipt.json',receipt)
    return receipt


def compact(text):
    return re.sub(r'\s+','',text)


def resolve_beats(scene, voice, graphic, mapping):
    """Literal, span, cue and time must ALL agree. No fuzzy/order/time-zero fallback."""
    actual={b['beat_index']:b for b in voice['beatanchors']}
    if len(actual)!=len(voice['beatanchors']) or set(actual)!=set(range(len(scene['beats']))):
        raise ValueError(scene['id']+': each writer beat needs one actual anchor')
    cues={c['id']:c for c in voice['cues']}
    resolved=[]
    if len(graphic['stages'])!=len(scene['beats']) or len(set(mapping.values()))!=len(scene['beats']):
        raise ValueError(scene['id']+': use a bespoke graphic with one authored stage per scene beat; do not compress generic templates')
    if set(mapping)!=set(s['key'] for s in graphic['stages']):
        raise ValueError(scene['id']+': explicit stage-to-writer-beat map required')
    for index, b in actual.items():
        expected=scene['beats'][index]['anchor']
        if not 0<=b['char_start']<b['char_end']<=len(scene['narration']) or b['anchor']!=expected or scene['narration'][b['char_start']:b['char_end']]!=expected:
            raise ValueError(scene['id']+': anchor text/span differs from locked narration')
        if not b['cue_ids'] or any(k not in cues for k in b['cue_ids']):
            raise ValueError(scene['id']+': anchor has no actual cue evidence')
        selected=[cues[k] for k in b['cue_ids']]
        if not 0<=b['start_s']<b['end_s']<=voice['last_speech_end_s']+.001:
            raise ValueError(scene['id']+': anchor outside actual speech')
        if b['start_s']<min(c.get('native_start_s',c['start_s']) for c in selected)-.001 or b['end_s']>max(c.get('native_end_s',c['end_s']) for c in selected)+.001:
            raise ValueError(scene['id']+': anchor outside evidence cues')
        if b['timing_basis'] not in ['native_word_boundary','forced_alignment','manual_audio_verified']:
            raise ValueError(scene['id']+': estimated anchor timing forbidden')
    for stage in graphic['stages']:
        b=actual[mapping[stage['key']]]
        resolved.append({**stage,**b,'action':scene['beats'][b['beat_index']]['action']})
    times=[b['start_s'] for b in resolved]
    if times!=sorted(times) or len(set(times))<min(3,len(times)):
        raise ValueError(scene['id']+': representative stages need at least three ordered actual anchors')
    return resolved


def validate_voice(scene, voice):
    if not scene['narration'].strip() or not scene['beats']:
        raise ValueError('Empty narration/beats forbidden')
    if not re.search('[\uac00-\ud7a3]',scene['narration']) or re.search(r'\?{2,}|\ufffd',scene['narration']+scene['title']):
        raise ValueError('Corrupted Korean text; wait for writer restoration')
    if voice['scene_id']!=scene['id'] or voice['duration_s']<=0 or not 0<voice['last_speech_end_s']<=voice['duration_s']:
        raise ValueError('Invalid scene audio timing')
    if not voice['cues'] or len({c['id'] for c in voice['cues']})!=len(voice['cues']):
        raise ValueError('Unique measured cues required')
    previous=0
    for c in voice['cues']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',c['id']):
            raise ValueError('Unsafe cue id')
        if not 1<=len(c['display_lines'])<=2 or compact(''.join(c['display_lines']))!=compact(c['text']):
            raise ValueError('Cue needs exact one/two display lines')
        if not previous<=c['start_s']<c['end_s']<=voice['last_speech_end_s']+.001:
            raise ValueError('Overlapping, unsorted or out-of-speech cues')
        previous=c['end_s']
    if compact(''.join(c['text'] for c in voice['cues']))!=compact(scene['narration']):
        raise ValueError('Caption display text differs from approved narration; explicit display map adapter needed')


def emit_project(folder, scene, voice, graphic, beats, source_text, template=False):
    # Production-only context: actual writer beat times/count remain untouched.
    from opening_context import attach_opening_context, source_footer
    if not template and not graphic.get('opening_context'):
        attach_opening_context(graphic,scene['id'],beats[0]['start_s'])
    source_text=source_footer(scene['id'])
    folder=owned(folder);folder.mkdir(parents=True,exist_ok=False)
    assets=folder/'assets';(assets/'fonts').mkdir(parents=True)
    shutil.copy2(ASSETS/'gsap.min.js',assets/'gsap.min.js')
    for p in (ASSETS/'fonts').glob('Pretendard-*.woff2'):
        shutil.copy2(p,assets/'fonts'/p.name)
    settled=max(b['start_s']+min(.45,max(.06,b['end_s']-b['start_s'])) for b in beats)
    duration=math.ceil(max(voice['duration_s'],settled+1.2)*30-1e-8)/30
    model={'scene_id':scene['id'],'duration_s':duration,'beats':beats,'cues':voice['cues'],'opening_context':graphic.get('opening_context')}
    cues=''.join(f'<div id="cue-{html.escape(c["id"])}" class="clip cue" data-start="{c["start_s"]}" data-duration="{c["end_s"]-c["start_s"]}" data-track-index="3"><span class="caption-lines">{html.escape(chr(10).join(c["display_lines"]))}</span></div>' for c in voice['cues'])
    doc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>'+html.escape(scene['title'])+'</title><script src="assets/gsap.min.js"></script><style>'+(HERE/'shell.css').read_text(encoding='utf8')+'</style></head><body>'
    doc+=f'<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-fps="30" data-duration="{duration:.12f}"><div id="brand">Ⅰ &nbsp; 데이터로 보는 부동산</div><div id="tag">감당 가능한 집값</div>'
    doc+='<h1 id="message">'+html.escape(scene['title'])+'</h1><section id="graphic" class="clip" data-start="0" data-duration="'+str(duration)+'" data-track-index="1">'+graphic['html']+'</section><div id="capbox"></div>'+cues+'<div id="source">'+html.escape(source_text)+'</div></div>'
    doc+='<script>const MODEL='+json.dumps(model,ensure_ascii=False).replace('</','<\/')+';</script><script>'+(HERE/'runtime.js').read_text(encoding='utf8')+'</script></body></html>'
    (folder/'index.html').write_text(doc,encoding='utf8')
    dump(folder/'scene.json',{'scene_id':scene['id'],'duration_s':duration,'audio':voice,'cues':voice['cues'],'beats':beats,'objects':graphic['objects'],'graphic_bbox':graphic['graphic_bbox'],'source_recipe':graphic['source_recipe'],'opening_context':graphic.get('opening_context'),'source_ids':scene.get('source_ids',[]),'source_footer':source_text,'last_information_settled_s':settled,'read_hold_s':duration-settled,'tail_added_s':duration-voice['duration_s'],'template_only':template,'actual_encoded_frames':False,'scene_start_frame':None,'scene_end_frame':None})
    return duration


def build(packet_path, run):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',run):
        raise ValueError('Unsafe run id')
    packet_path=source(packet_path);p=read(packet_path)
    lock_path=checked_ref(p['script_lock']);lock=read(lock_path)
    if lock.get('approved') is not True:
        raise ValueError('Parent script lock approval required')
    script_path=source(lock['script_path'])
    if sha(script_path)!=lock['script_sha256']:
        raise ValueError('Approved script changed')
    script=read(script_path)
    if not script['scenes'] or not script['revision'] or not script['policy_as_of']:
        raise ValueError('Nonempty locked scenes_v3.json required')
    timing_path=checked_ref(p['timing']);timing=read(timing_path)
    if timing['status']!='timing_locked' or timing['script_sha256']!=sha(script_path) or timing['clock']!='scene_local_seconds' or timing.get('rate')!='0%':
        raise ValueError('New actual timing lock for exact script required')
    research_path=checked_ref(p['research']);research=read(research_path)
    if research['policy_as_of']!=script['policy_as_of']:
        raise ValueError('Policy date mismatch')
    if len(p['representatives'])!=3 or set(b['kind'] for b in p['representatives'])!=set(KINDS):
        raise ValueError('Build exactly the three representatives before expansion')
    scenes={s['id']:s for s in script['scenes']};voices={s['scene_id']:s for s in timing['scenes']}
    if len(scenes)!=len(script['scenes']) or len(voices)!=len(timing['scenes']):
        raise ValueError('Duplicate scene IDs')
    plans=[];audio_pins=[]
    binding_by_id={b['scene_id']:b for b in p['representatives']}
    if len(binding_by_id)!=len(p['representatives']):raise ValueError('Duplicate representative IDs')
    # The approved array order is authoritative (R029 may precede R012).
    for b in [binding_by_id[s['id']] for s in script['scenes'] if s['id'] in binding_by_id]:
        sid=b['scene_id']
        if not re.fullmatch(r'R[0-9]{3,}',sid):
            raise ValueError('Use locked writer scene ID')
        s,v=scenes[sid],voices[sid];validate_voice(s,v)
        if not set(b['source_ids'])<=set(s['source_ids']) or not b['source_text'].strip():
            raise ValueError('Scene source binding differs from writer')
        audio=source(v['audio_path'])
        if sha(audio)!=v['audio_sha256']:
            raise ValueError('Actual audio changed')
        info=probe(audio);streams=[x for x in info['streams'] if x['codec_type']=='audio']
        if len(streams)!=1 or abs(float(info['format']['duration'])-v['duration_s'])>.05:
            raise ValueError('Audio duration/stream mismatch')
        g=make(b['kind'],research);beats=resolve_beats(s,v,g,b['stage_beats'])
        plans.append((b,s,v,g,beats));audio_pins.append(pin(audio))
    # Validate all inputs before creating an output run. No placeholder body render.
    run_dir=owned(OUT/run)
    if run_dir.exists():
        raise ValueError('Use a new version/run id; existing outputs are preserved')
    rows=[]
    for b,s,v,g,beats in plans:
        folder=run_dir/'scenes'/s['id']
        duration=emit_project(folder,s,v,g,beats,b['source_text'])
        rows.append({'scene_id':s['id'],'kind':g['kind'],'project':str(folder),'html_sha256':sha(folder/'index.html'),'duration_s':duration,'source_ids':b['source_ids']})
    code=[pin(HERE/n) for n in ['pipeline.py','graphics.py','runtime.js','shell.css','verify_templates.cjs']]
    dependencies=[pin(f) for row in rows for f in sorted(Path(row['project']).rglob('*')) if f.is_file()]
    receipt={'status':'representatives_built_for_measured_QA','approved_scene_order':[s['id'] for s in script['scenes']],'packet':pin(packet_path),'script_lock':pin(lock_path),'script':pin(script_path),'timing':pin(timing_path),'research':pin(research_path),'audio_inputs':audio_pins,'code_inputs':code,'project_inputs':dependencies,'scenes':rows,'render_executed':False,'full_film_allowed':False,'actual_listening':False,'continuous_playback':False}
    dump(run_dir/'build_receipt.json',receipt)
    return receipt


def render(run):
    # Only representative execution is exposed at this phase; no full-film mode.
    run_dir=owned(OUT/run);receipt=read(run_dir/'build_receipt.json');cli=cli_path()
    for ref in [receipt['packet'],receipt['script_lock'],receipt['script'],receipt['timing'],receipt['research'],*receipt['audio_inputs'],*receipt['code_inputs'],*receipt['project_inputs']]:
        checked_ref(ref)
    args=[shutil.which('node'),str(HERE/'verify_templates.cjs'),str(run_dir)]
    subprocess.run(args,check=True,env=ENV)
    results=[]
    for row in receipt['scenes']:
        folder=Path(row['project']);sid=row['scene_id'];v=read(folder/'scene.json')['audio']
        if (folder/'silent.mp4').exists() or (folder/(sid+'.mp4')).exists():
            raise ValueError('Preserve existing renders; build a new run id')
        if sha(folder/'index.html')!=row['html_sha256']:
            raise ValueError('Source changed after build')
        times=sorted({max(0,b['start_s']-.0333333333) for b in read(folder/'scene.json')['beats']}|{min(row['duration_s']-.0333333333,b['start_s']+.6) for b in read(folder/'scene.json')['beats']})
        commands=[([cli,'check','.','--json','--at',','.join(map(str,times)),'--timeout','10000'],folder,'check'),([cli,'render','.','--quality','looks','--fps','30','--output',str(folder/'silent.mp4')],folder,'render')]
        for argv,cwd,label in commands:
            log=folder/(label+'.log')
            with log.open('w',encoding='utf8') as f:
                r=subprocess.run(argv,cwd=cwd,env=ENV,stdout=f,stderr=subprocess.STDOUT)
            if r.returncode:
                raise ValueError(f'{sid} {label} failed: {log}')
        final=folder/(sid+'.mp4');frames=round(row['duration_s']*30)
        argv=[str(FFMPEG),'-n','-i',str(folder/'silent.mp4'),'-i',str(source(v['audio_path'])),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','apad','-t',str(frames/30),'-c:a','aac','-ar','48000','-ac','2',str(final)]
        subprocess.run(argv,check=True,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        info=probe(final);video=next(x for x in info['streams'] if x['codec_type']=='video');audio=next(x for x in info['streams'] if x['codec_type']=='audio')
        if (video['width'],video['height'],video['r_frame_rate'],audio['sample_rate'])!=(1920,1080,'30/1','48000') or abs(float(info['format']['duration'])-frames/30)>.06:
            raise ValueError('Encoded stream/duration mismatch: '+sid)
        subprocess.run([str(FFMPEG),'-v','error','-xerror','-i',str(final),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        rows=[]
        for i,t in enumerate(times):
            target=folder/f'encoded-{i:03}.png'
            subprocess.run([str(FFMPEG),'-n','-v','error','-ss',str(t),'-i',str(final),'-frames:v','1',str(target)],check=True,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            rows.append({'requested_time_s':t,'path':str(target),'sha256':sha(target),'manual_viewed':False})
        results.append({'scene_id':sid,'mp4':pin(final),'probe':info,'decode':'pass','frames':rows,'commands':[x[0] for x in commands]+[argv]})
    result={'status':'representatives_encoded_independent_visual_QA_pending','scenes':results,'BGM':'not mixed in representative isolates; reuse at final assembly','actual_listening':False,'continuous_playback':False,'full_film_rendered':False}
    dump(run_dir/'render_receipt.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['preflight','build','render'])
    parser.add_argument('--packet');parser.add_argument('--run')
    args=parser.parse_args()
    if args.action=='preflight':
        result=preflight()
    else:
        if not args.run or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',args.run):
            parser.error('--run requires a versioned safe identifier')
        if args.action=='build' and not args.packet:
            parser.error('build requires --packet with locked script + actual audio/timing')
        result=build(args.packet,args.run) if args.action=='build' else render(args.run)
    print(json.dumps({'status':result['status'],'full_film_rendered':False},ensure_ascii=False))


if __name__=='__main__':
    main()
