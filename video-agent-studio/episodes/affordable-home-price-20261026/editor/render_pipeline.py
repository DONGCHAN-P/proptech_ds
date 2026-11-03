"""Prepare pinned local commands by default. Execution requires exact Main authorization.

No TTS, remote calls, upgrade, upload, old AAC reuse or timing adjustment.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from html.parser import HTMLParser
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parent;ROOT=EP.parents[2];OUT=EP/'outputs/private-production-v1'
DEFAULT_RUN='measured-v3-visual-v4-r1'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf8')).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def path_of(value):
    p=Path(value)
    if p.is_absolute():return p.resolve()
    return (ROOT/p).resolve() if (ROOT/p).exists() else (EP/p).resolve()
def dest_of(run):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',run):raise ValueError('Unsafe run id')
    return OUT/'renders'/run
def tools():
    receipt=read(ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/director/two-episode-production-v1/ffmpeg_receipt.json')
    ffmpeg=path_of(receipt['binary']);assert sha(ffmpeg)==receipt['binary_sha256']
    ffprobe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    cli=Path(shutil.which('hyperframes.cmd') or 'missing-cli');node=Path(shutil.which('node.exe') or shutil.which('node') or 'missing-node')
    env=dict(os.environ,DO_NOT_TRACK='1',HYPERFRAMES_NO_UPDATE_CHECK='1',HYPERFRAMES_NO_AUTO_INSTALL='1')
    assert subprocess.check_output([str(cli),'--version'],text=True,env=env).strip()=='0.8.181'
    return cli,node,ffmpeg,ffprobe

class Resources(HTMLParser):
    def __init__(self):super().__init__();self.files=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        for key in ['src','href','data-composition-src']:
            if a.get(key):self.files.append(a[key])

def collect_inputs():
    cli,node,ffmpeg,ffprobe=tools();plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json');mix=read(HERE/'mix_receipt.json')
    assert plan['status']=='measured_audio_units' and plan['audio_revision']=='production-injoon-v3'
    assert len(plan['chapters'])==10 and plan['source_scene_count']==45 and plan['native_cues']==150
    assert abs(edl['total_seconds']-1186.0333333333335)<1e-7
    assert mix['status']=='canonical_carve_pass' and mix['timing_sha256']==plan['caption_timing_sha256']
    assert sha(HERE/'mix_receipt.json')==plan['prepared_mix_receipt_sha256']
    files={}
    def pin(p,category):
        p=Path(p).resolve();assert p.is_file(),str(p)
        files[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'category':category}
        return files[str(p)]
    common=['render_plan.json','assembly_edl.json','captions_measured.srt','global_captions.json','scene_source_manifest.json','snapshot_times.json','encoded_frame_plan.prepared.json']
    for name in common:pin(OUT/name,'measured source')
    for name in ['render_pipeline.py','encoded_evidence.py','build_measured.py','graphics.py','build.py','voice_input.py','mix_receipt.json','checks/native-v4/summary.json','bbox_measured_v4.json','source_build_v4_handoff.json','visual_v4_delta.json','visual_v4_targeted_handoff.json']:pin(HERE/name,'editor code or source evidence')
    lock=read(EP/'director/production-v1/locked_script.json');assert lock['approved'] is True and lock['script_sha256']==plan['script_sha256']
    pin(EP/'director/production-v1/locked_script.json','script lock');assert pin(path_of(lock['script_path']),'display script')['sha256']==lock['script_sha256']
    for name in ['handoff.production-v3.json','production-injoon-v3/final_timing.json','production-injoon-v3/technical_validation.json']:pin(EP/'narration'/name,'formal actual voice')
    assert sha(EP/'narration/production-injoon-v3/final_timing.json')==edl['timing_sha256']==plan['caption_timing_sha256']
    media=read(EP/'director/production-v1/media_assets.json');pin(EP/'director/production-v1/media_assets.json','media lock')
    for a in media['assets']:assert pin(path_of(a['path']),'approved original media')['sha256']==a['sha256']
    pkg=cli.parent/'node_modules/hyperframes';assert read(pkg/'package.json')['version']=='0.8.181'
    runtimes=[cli,node,ffmpeg,ffprobe,Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),pkg/'package.json',pkg/'bin/hyperframes.mjs']
    # Only the installed distribution's direct JS bundles; never dependency/cache trees.
    runtimes+=sorted((pkg/'dist').glob('*.js'))
    for p in runtimes:pin(p,'pinned local runtime')
    runtime_digest=digest([files[str(p.resolve())] for p in runtimes])
    chapters=[]
    cli_check=read(HERE/'checks/native-v4/summary.json');bbox=read(HERE/'bbox_measured_v4.json');assert cli_check['status']==bbox['status']=='pass'
    for ch in plan['chapters']:
        folder=OUT/ch['project'];html=folder/'index.html';html_sha=sha(html)
        for proof in [plan['chapters'],mix['chapters'],cli_check['chapters'],bbox['chapters']]:assert next(c['html_sha256'] for c in proof if c['chapter']==ch['chapter'])==html_sha
        local=[]
        for name in ['index.html','timing.json','anchor_audit.json']:local.append(pin(folder/name,'chapter source'))
        content=html.read_text(encoding='utf8');parser=Resources();parser.feed(content)
        names=parser.files+re.findall(r'url\([\'\"]?([^\)\'\"]+)',content)
        for name in sorted(set(names)):
            assert not re.match(r'^[a-zA-Z]+:|^//',name),'Remote resource is prohibited: '+name
            target=(folder/name.split('#')[0].split('?')[0]).resolve();assert target.is_relative_to(folder.resolve())
            local.append(pin(target,'chapter local asset'))
        timing=read(folder/'timing.json');assert pin(path_of(timing['audio_file']),'original chapter voice')['sha256']==ch['audio_sha256']==sha(folder/'assets/narration.wav')
        chapters.append({'chapter':ch['chapter'],'html_sha256':html_sha,'files':local,'input_sha256':digest({'files':local,'runtime':runtime_digest,'render_settings':{'fps':30,'quality':'delivery','crf':18,'workers':4,'format':'mp4','resolution':'landscape'}})})
    result={'schema_version':1,'episode':EP.name,'script_sha256':plan['script_sha256'],'timing_sha256':edl['timing_sha256'],'EDL_sha256':sha(OUT/'assembly_edl.json'),'SRT_sha256':sha(OUT/'captions_measured.srt'),'runtime_sha256':runtime_digest,'chapters':chapters,'files':sorted(files.values(),key=lambda x:x['path']),'excluded_trees':['audio-deps','ffmpeg-deps','media-bin dependency trees','frames-cache','tmp','source-archive'],'old_episode_AAC_copy':False}
    result['input_sha256']=digest(result);return result

def assembly_command(plan,edl,ffmpeg,dest):
    inputs=[dest/'ch01.mp4',path_of(plan['brand_assembly']['intro']['path'])];indices={1:0}
    for c in plan['chapters'][1:]:indices[c['chapter']]=len(inputs);inputs.append(dest/f'ch{c["chapter"]:02}.mp4')
    outro=len(inputs);inputs.append(path_of(plan['brand_assembly']['outro']['path']))
    filters=['[0:v]split=2[c1vpre][c1vpost]','[0:a]asplit=2[c1apre][c1apost]'];labels=[]
    assert len(edl['segments'])==13
    for i,seg in enumerate(edl['segments']):
        if seg['id']=='opening_hook':vi,ai='c1vpre','c1apre'
        elif seg['id']=='chapter_1_after_hook':vi,ai='c1vpost','c1apost'
        else:
            index=1 if seg['id']=='clean_brand_intro' else outro if seg['id']=='clean_brand_outro' else indices[seg['chapter']];vi,ai=f'{index}:v',f'{index}:a'
        start,end=seg['source_start_s'],seg['source_end_s'];length=end-start
        a,b=round(start*30),round(end*30);samples=round(length*48000)
        assert abs((b-a)/30-length)<1e-7 and samples==1600*(b-a)
        filters.append(f'[{vi}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,fps=30,setsar=1,format=yuv420p[v{i}]')
        filters.append(f'[{ai}]atrim=start={start:.12f}:end={end:.12f},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=whole_len={samples},atrim=end_sample={samples},afade=t=in:st=0:d=0.008,afade=t=out:st={length-.008:.12f}:d=0.008[a{i}]')
        labels.append(f'[v{i}][a{i}]')
    filters.append(''.join(labels)+f'concat=n={len(labels)}:v=1:a=1[vout][aout]')
    script=dest/'assembly.ffscript';script.parent.mkdir(parents=True,exist_ok=True);script.write_text(';\n'.join(filters),encoding='utf8')
    final=dest/'affordable_home_price_private_voice_v3_visual_v4.mp4';argv=[str(ffmpeg),'-v','warning','-nostdin']
    for p in inputs:argv+=['-i',str(p)]
    argv+=['-filter_complex_script',str(script),'-map','[vout]','-map','[aout]','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-frames:v',str(round(edl['total_seconds']*30)),'-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart','-n',str(final)]
    return argv,final

def prepare(run):
    dest=dest_of(run);inputs=collect_inputs();plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json');cli,node,ffmpeg,ffprobe=tools()
    dump(HERE/'render_input_manifest.json',inputs)
    commands=[{'chapter':c['chapter'],'cwd':str(OUT/c['project']),'input_sha256':next(r['input_sha256'] for r in inputs['chapters'] if r['chapter']==c['chapter']),'argv':[str(cli),'render','.','--fps','30','--resolution','landscape','--format','mp4','--quality','delivery','--crf','18','--workers','4','--browser-gpu','--output',str(dest/f'ch{c["chapter"]:02}.mp4'),'--frames-cache-dir',str(dest/'frames-cache'/f'ch{c["chapter"]:02}')]} for c in plan['chapters']]
    assembly,final=assembly_command(plan,edl,ffmpeg,dest)
    spec={'status':'commands_prepared_not_authorized','run_id':run,'pipeline_sha256':sha(Path(__file__)),'input_manifest_sha256':sha(HERE/'render_input_manifest.json'),'input_sha256':inputs['input_sha256'],'script_sha256':inputs['script_sha256'],'timing_sha256':inputs['timing_sha256'],'EDL_sha256':inputs['EDL_sha256'],'SRT_sha256':inputs['SRT_sha256'],'film_seconds':edl['total_seconds'],'total_video_frames':round(edl['total_seconds']*30),'chapter_commands':commands,'assembly_command':assembly,'assembly_filter_sha256':sha(dest/'assembly.ffscript'),'final_file':str(final),'captions_file':str(OUT/'captions_measured.srt'),'full_render_executed':False,'authorization_owner':'main','old_AAC_stream_copy':False,'audio_join_fade_s':.008}
    dump(HERE/'render_commands.json',spec)
    template={'schema_version':1,'approved':False,'status':'awaiting_main_exact_authorization','scope':'full_local_render_voice_v3_visual_v4','episode':EP.name,'run_id':run,'pipeline_sha256':spec['pipeline_sha256'],'render_commands_sha256':sha(HERE/'render_commands.json'),'input_manifest_sha256':spec['input_manifest_sha256'],'script_sha256':inputs['script_sha256'],'timing_sha256':inputs['timing_sha256'],'edl_sha256':inputs['EDL_sha256'],'captions_sha256':inputs['SRT_sha256'],'evidence':{key:{'path':None,'sha256':None} for key in ['source_qa','audio_qa','edl_review']},'note':'Template only. Main owns the actual authorized file under director/production-v1. No authority is inferred from this template.'}
    dump(HERE/'main_render_authorization_template.json',template)
    dump(HERE/'render_receipt_schema.json',{'required':['status','final_file','final_sha256','captions_file','captions_sha256','decode_returncode','decode_log_sha256','ffprobe','duration_s','expected_duration_s','input_manifest_sha256','input_sha256','gate_receipts','chapters'],'film_specs':{'width':1920,'height':1080,'fps':'30/1','video_codec':'h264','audio_codec':'aac','sample_rate':48000,'channels':2},'approval_scope':'technical receipt does not approve release/upload'})
    return spec

def approved_evidence(row,kind,script_sha):
    p=path_of(row['path']);assert p.is_relative_to(EP) and p.is_file() and sha(p)==row['sha256'],'Stale/missing independent evidence'
    d=read(p)
    for key in ['open_required','open_issue_ids','required_issues','required_audio_QA_remaining','required_open_issues']:
        if d.get(key):raise ValueError('Independent '+kind+' issues remain: '+key)
    positive=d.get('approved') is True or (kind=='source_qa' and d.get('source_approved') is True) or (kind=='audio_qa' and d.get('audio_approved') is True)
    if kind=='edl_review':positive=str(d.get('status','')).startswith('passed') or d.get('status')=='pass'
    if not positive:raise ValueError('Independent '+kind+' approval required')
    for value in [d.get('script_sha256'),d.get('checked_sha256'),d.get('checked_revision',{}).get('script_sha256')]:
        if value:assert value==script_sha,'Independent script mismatch'
    return d

def preflight(spec,authorization):
    p=path_of(authorization);assert p.is_relative_to((EP/'director/production-v1').resolve()),'Main must own the actual authorization'
    auth=read(p);assert auth['approved'] is True and auth['scope']=='full_local_render_voice_v3_visual_v4' and auth['episode']==EP.name and auth['run_id']==spec['run_id'],'Exact Main full-render authorization required'
    for key,value in {'pipeline_sha256':sha(Path(__file__)),'render_commands_sha256':sha(HERE/'render_commands.json'),'input_manifest_sha256':sha(HERE/'render_input_manifest.json'),'script_sha256':spec['script_sha256'],'timing_sha256':spec['timing_sha256'],'edl_sha256':spec['EDL_sha256'],'captions_sha256':spec['SRT_sha256']}.items():assert auth.get(key)==value,'Authorization is stale: '+key
    assert collect_inputs()['input_sha256']==spec['input_sha256'],'Actual render inputs changed'
    assert sha(dest_of(spec['run_id'])/'assembly.ffscript')==spec['assembly_filter_sha256']
    evidence={k:approved_evidence(auth['evidence'][k],k,spec['script_sha256']) for k in ['source_qa','audio_qa','edl_review']}
    edl=evidence['edl_review'];assert edl['edl_sha256']==spec['EDL_sha256'] and edl['subtitles_sha256']==spec['SRT_sha256'] and edl['timing_sha256']==spec['timing_sha256']
    return {'authorization':str(p),'authorization_sha256':sha(p),'independent_evidence':auth['evidence']}

def probe(file,ffprobe,expected):
    info=json.loads(subprocess.check_output([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(file)]))
    video=[s for s in info['streams'] if s['codec_type']=='video'];audio=[s for s in info['streams'] if s['codec_type']=='audio'];assert len(video)==len(audio)==1
    v,a=video[0],audio[0];assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],v['pix_fmt'])==(1920,1080,'30/1','h264','yuv420p')
    assert a['codec_name']=='aac' and int(a['sample_rate'])==48000 and a['channels']==2
    assert abs(float(info['format']['duration'])-expected)<.06
    if v.get('nb_frames'):assert int(v['nb_frames'])==round(expected*30)
    return info

def execute(spec,authorization):
    gates=preflight(spec,authorization);dest=dest_of(spec['run_id']);_,_,ffmpeg,ffprobe=tools();plan=read(OUT/'render_plan.json')
    env=dict(os.environ,PATH=str(ffmpeg.parent)+os.pathsep+str(ffprobe.parent)+os.pathsep+os.environ['PATH'],DO_NOT_TRACK='1',HYPERFRAMES_NO_UPDATE_CHECK='1',HYPERFRAMES_NO_AUTO_INSTALL='1',TEMP=str(dest/'tmp'),TMP=str(dest/'tmp'));(dest/'tmp').mkdir(exist_ok=True)
    receipt=HERE/'render_receipt.json'
    if Path(spec['final_file']).exists() and receipt.exists():
        old=read(receipt)
        assert old['status']=='rendered_technical_pass_independent_media_review_pending' and old['input_sha256']==spec['input_sha256'] and old['final_sha256']==sha(Path(spec['final_file'])) and old['captions_sha256']==spec['SRT_sha256'] and old['decode_returncode']==0,'Existing final is not an exact completed render; preserve it and use a new run id'
        return old
    result={'status':'rendering','gate_receipts':gates,'input_manifest_file':str(HERE/'render_input_manifest.json'),'input_manifest_sha256':spec['input_manifest_sha256'],'input_sha256':spec['input_sha256'],'pipeline_sha256':spec['pipeline_sha256'],'render_commands_sha256':sha(HERE/'render_commands.json'),'chapters':[],'actual_listening':False,'continuous_playback':False,'old_AAC_stream_copy':False}
    for command,ch in zip(spec['chapter_commands'],plan['chapters']):
        target=dest/f'ch{ch["chapter"]:02}.mp4';record=dest/f'ch{ch["chapter"]:02}.receipt.json'
        if target.exists() and record.exists():
            old=read(record);assert old['input_sha256']==command['input_sha256'] and old['output_sha256']==sha(target),'Existing chapter has different inputs; preserve and use a new run id'
            probe(target,ffprobe,ch['total_seconds']);result['chapters'].append(old);print('reuse exact completed chapter '+str(ch['chapter']),flush=True);continue
        assert not target.exists(),'Unverified existing chapter output; preserve it and use a new run id'
        # Recheck chapter assets/runtime at each boundary; never silently mix changed inputs.
        assert collect_inputs()['input_sha256']==spec['input_sha256']
        print('render chapter '+str(ch['chapter'])+' / 10',flush=True)
        with (dest/f'ch{ch["chapter"]:02}.render.log').open('w',encoding='utf8') as log:p=subprocess.run(command['argv'],cwd=command['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT)
        if p.returncode:
            result.update(status='render_failed',failed_chapter=ch['chapter'],returncode=p.returncode);dump(receipt,result);raise RuntimeError('Render failed; log preserved')
        info=probe(target,ffprobe,ch['total_seconds']);row={'chapter':ch['chapter'],'input_sha256':command['input_sha256'],'html_sha256':sha(OUT/ch['project']/'index.html'),'output_sha256':sha(target),'file':str(target),'ffprobe':info,'argv':command['argv']};dump(record,row);result['chapters'].append(row);dump(receipt,result)
    final=Path(spec['final_file']);assert not final.exists(),'Preserve existing final; use a new run id'
    with (dest/'assembly.log').open('w',encoding='utf8') as log:p=subprocess.run(spec['assembly_command'],env=env,stdout=log,stderr=subprocess.STDOUT)
    if p.returncode:result['status']='assembly_failed';dump(receipt,result);raise RuntimeError('Assembly failed')
    info=probe(final,ffprobe,spec['film_seconds']);decode=[str(ffmpeg),'-v','error','-xerror','-nostdin','-i',str(final),'-map','0:v:0','-map','0:a:0','-f','null','-']
    with (dest/'decode.log').open('w',encoding='utf8') as log:p=subprocess.run(decode,env=env,stdout=subprocess.DEVNULL,stderr=log)
    decoded_ok=p.returncode==0 and not (dest/'decode.log').read_text(encoding='utf8').strip()
    result.update(status='rendered_technical_pass_independent_media_review_pending' if decoded_ok else 'decode_failed',final_file=str(final),final_sha256=sha(final),captions_file=spec['captions_file'],captions_sha256=sha(Path(spec['captions_file'])),decode_returncode=p.returncode,decode_argv=decode,decode_log_sha256=sha(dest/'decode.log'),ffprobe=info,duration_s=float(info['format']['duration']),expected_duration_s=spec['film_seconds'],final_video_frames=round(spec['film_seconds']*30),full_AV_decode=decoded_ok)
    dump(receipt,result);dump(dest/'render_receipt.json',result)
    if result['status']=='decode_failed':raise RuntimeError('Complete final AV decode failed')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',default=DEFAULT_RUN);parser.add_argument('--execute',action='store_true');parser.add_argument('--check-gates',action='store_true');parser.add_argument('--authorization');args=parser.parse_args()
    if args.execute or args.check_gates:
        if not args.authorization:parser.error('--authorization from Main is mandatory; no rendering started')
        spec=read(HERE/'render_commands.json');assert spec['run_id']==args.run_id
        result=execute(spec,args.authorization) if args.execute else {'status':'gates_pass_no_render','gates':preflight(spec,args.authorization)}
        if args.execute:
            command=[sys.executable,'-X','utf8',str(HERE/'encoded_evidence.py'),'--run-id',spec['run_id'],'--extract']
            log=dest_of(spec['run_id'])/'encoded-evidence.log'
            with log.open('w',encoding='utf8') as stream:completed=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            if completed.returncode:raise RuntimeError('Film technical receipt preserved; encoded evidence failed, see '+str(log))
    else:result=prepare(args.run_id)
    print(json.dumps({k:v for k,v in result.items() if k not in ['chapter_commands','assembly_command','chapters','ffprobe']},ensure_ascii=False))
if __name__=='__main__':main()
