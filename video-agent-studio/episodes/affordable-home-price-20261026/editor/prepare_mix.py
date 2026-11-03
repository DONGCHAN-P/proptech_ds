"""Local canonical carve of the measured v3 voice; no film render or approval."""
import array,html,json,math,os,re,subprocess,sys,wave
from html.parser import HTMLParser
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import EP,ROOT,OUT,HERE,BASE,read,sha,dump,resolve_input,load_script_lock
from voice_input import EXPECTED,load_voice

CARVE=Path('C:/Users/e2ken/.agents/skills/hyperframes-audio/scripts/carve.mjs')
CORE=BASE/'outputs/private-production-v1/audio-deps'
RECEIPT=BASE/'director/two-episode-production-v1/ffmpeg_receipt.json'

class AudioAttrs(HTMLParser):
    def __init__(self):super().__init__();self.rows={}
    def handle_starttag(self,tag,attrs):
        if tag=='audio':
            row=dict(attrs);self.rows[row['id']]=row

def run(argv,env=None):
    p=subprocess.run(argv,env=env,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf8',errors='replace'))
    return p

def smoke(ffmpeg,path):
    raw=run([str(ffmpeg),'-v','error','-i',str(path),'-t','0.25','-ar','48000','-ac','1','-f','f32le','pipe:1']).stdout
    samples=array.array('f');samples.frombytes(raw)
    assert len(samples)==12000 and all(math.isfinite(x) for x in samples)
    return {'file':str(path),'sha256':sha(path),'sample_format':'float32 little-endian pipe','samples':len(samples),'peak':max(map(abs,samples))}

def main():
    timing,formal,technical=load_voice();lock,_,_=load_script_lock();plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json')
    assert plan['caption_timing_sha256']==edl['timing_sha256']==EXPECTED
    assert plan['script_sha256']==lock['script_sha256'] and plan['status']=='measured_audio_units'
    assert read(HERE/'audio_revision_gate.json')['canonical_carve_allowed']
    ffreceipt=read(RECEIPT);ffmpeg=resolve_input(ffreceipt['binary'])
    assert ffreceipt['status']=='f32le_decode_pass' and sha(ffmpeg)==ffreceipt['binary_sha256']
    assert read(CORE/'node_modules/@hyperframes/core/package.json')['version']=='0.8.181'
    media=read(EP/'director/production-v1/media_assets.json');musicrow=media['assets'][2];music=resolve_input(musicrow['path']);assert sha(music)==musicrow['sha256']
    decoded=OUT/'audio-source/thinking_music-48k.wav';decoded.parent.mkdir(parents=True,exist_ok=True)
    run([str(ffmpeg),'-v','error','-y','-i',str(music),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(decoded)])
    with wave.open(str(decoded),'rb') as w:music_seconds=w.getnframes()/w.getframerate()
    env=dict(os.environ,PATH=str(ffmpeg.parent)+os.pathsep+os.environ['PATH'],DO_NOT_TRACK='1')
    logs=HERE/'checks/carve-v3';logs.mkdir(parents=True,exist_ok=True)
    report={'status':'running','audio_revision':timing['audio_revision'],'script_sha256':lock['script_sha256'],'timing_sha256':EXPECTED,'EDL_sha256':sha(OUT/'assembly_edl.json'),'canonical_script_sha256':sha(CARVE),'core_version':'0.8.181','core_directory':str(CORE),'ffmpeg_sha256':sha(ffmpeg),'ffmpeg_receipt_sha256':sha(RECEIPT),'music_sha256':sha(music),'decoded_music_sha256':sha(decoded),'music_seconds':music_seconds,'strength':0.8,'placement_clock':'actual global EDL time including 5s clean intro; ch01 skips those 5s in its local bed','decode_smokes':[smoke(ffmpeg,music),smoke(ffmpeg,resolve_input(timing['chapters'][3]['audio_file']))],'actual_listening':False,'ASR_approval':'pending','full_film_render_executed':False,'full_film_render_authorized':False,'chapters':[]}
    dump(HERE/'mix_receipt.json',report)
    for ch in plan['chapters']:
        number=ch['chapter'];folder=OUT/ch['project'];file=folder/'index.html';before=file.read_text(encoding='utf8');assert 'id="music-bed"' not in before,'Rebuild source before reapplying carve'
        assert sha(folder/'assets/narration.wav')==ch['audio_sha256']
        (logs/f'ch{number:02}.before_carve.html.txt').write_text(before,encoding='utf8')
        duration=ch['last_speech_end_s'] if number==10 else ch['total_seconds']
        offsets=[o for o in edl['offset_map'] if o['chapter']==number];pieces=[]
        for i,o in enumerate(offsets):
            local_start=o['local_start_s'];end=min(duration,o['local_end_s'])
            if end<=local_start:continue
            start=(local_start+o['global_offset_s'])%music_seconds;length=end-local_start
            pieces.append({'local_start_s':local_start,'local_end_s':end,'global_start_s':local_start+o['global_offset_s'],'music_start_s':start})
        args=[str(ffmpeg),'-v','error','-y']
        for piece in pieces:args+=['-stream_loop','-1','-ss',str(piece['music_start_s']),'-i',str(decoded)]
        filters=[]
        for i,p in enumerate(pieces):filters.append(f'[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=end_sample={round((p["local_end_s"]-p["local_start_s"])*48000)},asetpts=PTS-STARTPTS[p{i}]')
        if len(pieces)>1:filters.append(''.join(f'[p{i}]' for i in range(len(pieces)))+f'concat=n={len(pieces)}:v=0:a=1[bed]')
        else:filters.append('[p0]anull[bed]')
        bed=folder/'assets/music-bed.wav';args+=['-filter_complex',';'.join(filters),'-map','[bed]','-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)];run(args)
        with wave.open(str(bed),'rb') as w:assert abs(w.getnframes()/w.getframerate()-duration)<1/48000+1e-8
        narration=re.search(r'<audio\b[^>]*id="narration"[^>]*></audio>',before);assert narration
        voice=narration.group().replace('id="narration"','id="narration" data-audio-group="voiceover"')
        bedtag=f'<audio id="music-bed" class="clip" data-audio-group="music" src="assets/music-bed.wav" data-start="0" data-duration="{duration:.12f}" data-track-index="11" data-volume="1"></audio>'
        file.write_text(before[:narration.start()]+voice+bedtag+before[narration.end():],encoding='utf8')
        argv=['node',str(CARVE),'--comp',str(file),'--bed','music-bed','--voice','narration','--strength','0.8','--core',str(CORE)]
        result=subprocess.run(argv,env=env,capture_output=True,text=True,encoding='utf8',errors='replace');(logs/f'ch{number:02}.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
        if result.returncode:
            report.update(status='failed',failed_chapter=number);dump(HERE/'mix_receipt.json',report);raise RuntimeError('Canonical carve failed: '+str(logs/f'ch{number:02}.log'))
        source=file.read_text(encoding='utf8');parser=AudioAttrs();parser.feed(source);attrs=parser.rows['music-bed'];chain=json.loads(attrs['data-fx-chain']);automation=json.loads(attrs['data-automation']);settings=json.loads(attrs['data-fx-carve'])
        nodes=chain['nodes'];ids={n['id'] for n in nodes}
        assert any(n['type']=='peaking' and n.get('fromCarve') for n in nodes)
        assert any(n['type']=='gain' and n.get('fromCarve') for n in nodes)
        assert settings['enabled'] and settings['sources']==['voiceover']
        for lane in automation['lanes']:
            target=lane['target'].split('.');assert len(target)==3 and target[0]=='fx' and target[1] in ids and len(lane['points'])>=2
            assert all(math.isfinite(p['t']) and math.isfinite(p['v']) for p in lane['points'])
        # A volume envelope only softens chapter boundaries; the spectral carve remains canonical.
        automation['lanes'].append({'target':'volume','points':[{'t':0,'v':0},{'t':.6,'v':1},{'t':max(.6,duration-.8),'v':1},{'t':duration,'v':0}]})
        tag=re.search(r'<audio\b[^>]*id="music-bed"[^>]*></audio>',source);assert tag
        updated=re.sub(r'data-automation="[^"]*"','data-automation="'+html.escape(json.dumps(automation,separators=(',',':')),quote=True)+'"',tag.group())
        source=source[:tag.start()]+updated+source[tag.end():];file.write_text(source,encoding='utf8')
        # The entire picture, caption text, cue times and GSAP runtime stay byte-identical.
        strip=lambda s:re.sub(r'<audio\b[^>]*></audio>','',s)
        assert strip(source)==strip(before)
        report['chapters'].append({'chapter':number,'html_sha256':sha(file),'before_carve_html_sha256':sha(logs/f'ch{number:02}.before_carve.html.txt'),'voice_sha256':sha(folder/'assets/narration.wav'),'bed_sha256':sha(bed),'bed_duration_s':duration,'EDL_music_pieces':pieces,'carve_argv':argv,'settings':settings,'spectral_nodes':sum(n['type']=='peaking' for n in nodes),'automation_lanes':len(automation['lanes']),'non_audio_DOM_GSAP_byte_identical':True})
        ch['html_sha256']=sha(file);dump(HERE/'mix_receipt.json',report);print(json.dumps({'chapter':number,'canonical_carve':'pass','non_audio_source_unchanged':True}),flush=True)
    report['status']='canonical_carve_pass';dump(HERE/'mix_receipt.json',report)
    plan.update(prepared_mix_receipt='editor/mix_receipt.json',prepared_mix_receipt_sha256=sha(HERE/'mix_receipt.json'),source_QA='pending final carved SHA',full_render_allowed_now=False);dump(OUT/'render_plan.json',plan)
    built=read(HERE/'measured_build_receipt.json');built.update(chapters=plan['chapters'],canonical_carve_receipt_sha256=sha(HERE/'mix_receipt.json'),source_QA='pending final carved SHA');dump(HERE/'measured_build_receipt.json',built)
    dump(HERE/'audio_recipe_v3.json',{'status':'canonical_carve_prepared_pending_independent_audio_source_QA','voice':'original v3 PCM, gain1, no speed change/no deletions','canonical_carve':'0.8 strength: measured frequency peaking filters plus level-match, dynamic fx automation','bed':'Thinking Music, SHA-pinned original, EDL-global content clock; native hook uses0..23.0333 then source28.0333 onward after 5s brand','chapter_boundary_volume_fade_s':{'in':.6,'out':.8},'assembly_preventive_audio_join_fade_s':.008,'join_fade_application':'after final atrim; duration and EDL unchanged; future assembly only','actual_click_or_listening_claim':False,'new_paid_calls':0,'mix_receipt_sha256':sha(HERE/'mix_receipt.json'),'full_render_authorized':False})

if __name__=='__main__':main()
