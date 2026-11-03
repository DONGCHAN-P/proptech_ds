"""Read-only provisioned Kaldi/Vosk; only v3 S019/S024, no grammar bias.

Main exclusively provisions deps/ and model-cache/. This runner never installs,
downloads or writes there. `prepare` needs no Vosk import; `run` requires an
explicit completed provision receipt and the pinned local model directory.
"""
import argparse,hashlib,json,os,re,socket,subprocess,sys,wave
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;QA=OUT.parent
sys.path.insert(0,str(QA));sys.path.insert(0,str(QA/'v3_delta'))
from prepare import EP,read,sha,pin,dump
from semantic_checks import compare

TARGETS=['S019','S024']

def header(p):
    with wave.open(str(p),'rb') as w:
        assert w.getcomptype()=='NONE'
        return {'sample_rate':w.getframerate(),'channels':w.getnchannels(),'sample_bytes':w.getsampwidth(),'frames':w.getnframes(),'seconds':w.getnframes()/w.getframerate()}

def prepare():
    packetp=EP/'narration/production-injoon-v3/qa_packet.json';packet=read(packetp)
    cfg=read(QA/'config.json');assert packet['script_sha256']==cfg['script_sha256']
    fft=Path(read(EP/'narration/prepare-v3/prepared.json')['dependencies']['ffmpeg'])
    assert fft.is_file()
    version=subprocess.run([str(fft),'-version'],check=True,capture_output=True,text=True).stdout
    (OUT/'ffmpeg_version.txt').write_text(version,encoding='utf-8')
    jobs=[]
    for sid in TARGETS:
        t=next(t for t in packet['targets'] if t['scene_id']==sid)
        source=Path(t['audio']['path']).resolve()
        assert source.is_relative_to(EP/'narration/production-injoon-v3/paragraphs'/sid)
        assert sha(source)==t['audio']['sha256']
        dest=OUT/'pcm16k'/f'{sid}-{t["audio"]["sha256"][:12]}.wav';dest.parent.mkdir(exist_ok=True)
        command=[str(fft),'-nostdin','-hide_banner','-loglevel','error','-n','-i',str(source),'-map','0:a:0','-vn','-sn','-dn','-ar','16000','-ac','1','-c:a','pcm_s16le',str(dest)]
        if dest.exists():
            previous=read(OUT/'prepared.json')
            prev=next(p for p in previous['jobs'] if p['scene_id']==sid)
            assert sha(dest)==prev['resampled_audio']['sha256']
        else:subprocess.run(command,check=True,capture_output=True)
        h=header(dest);original=header(source)
        assert (h['sample_rate'],h['channels'],h['sample_bytes'])==(16000,1,2)
        assert abs(h['seconds']-original['seconds'])<=1/16000
        assert sha(source)==t['audio']['sha256']
        jobs.append({'scene_id':sid,'input_audio':t['audio'],'resampled_audio':pin(dest),'source_header':original,'resampled_header':h,'ffmpeg_command':command,'approved_display':t['display_expected'],'approved_spoken':t['spoken_expected'],'critical_cues':t['target_cues'],'whole_raw_paragraph':True})
    prepared={'status':'audio_preparation_only_no_Vosk_inference','script_sha256':packet['script_sha256'],'final_timing':packet['final_timing'],'source_packet':pin(packetp),'standard_Whisper_review':pin(QA/'v3_delta/review.json'),'failed_no_digit_diagnostic':pin(QA/'v3_delta/phonetic_decode/review.json'),'jobs':jobs,'ffmpeg':pin(fft),'ffmpeg_version_first_line':version.splitlines()[0],'ffmpeg_version_output':pin(OUT/'ffmpeg_version.txt'),'deps_main_owned_readonly_for_QA':str(OUT/'deps'),'model_cache_main_owned_readonly_for_QA':str(OUT/'model-cache'),'expected_package':'vosk==0.3.45','expected_model':'vosk-model-small-ko-0.22','expected_model_license':'Apache-2.0','expected_model_license_basis':'Main reports primary official model-row verification; actual provision receipt required before inference.','ASR_runs':0,'actual_listening':False,'continuous_playback':False}
    dump(OUT/'prepared.json',prepared)
    print({'status':prepared['status'],'scenes':TARGETS,'input_seconds':sum(p['source_header']['seconds'] for p in jobs),'actual_ASR_runs':0},flush=True)

def run(args):
    prepared=read(OUT/'prepared.json');receiptp=Path(args.receipt).resolve();modelp=Path(args.model).resolve()
    assert receiptp.is_file() and receiptp.is_relative_to(EP)
    receipt=read(receiptp)
    assert modelp.is_relative_to(OUT/'model-cache') and modelp.name=='vosk-model-small-ko-0.22'
    assert (modelp/'am/final.mdl').is_file() and (modelp/'conf/model.conf').is_file()
    # Receipt status/schema is reviewed by QA when supplied; pin the exact
    # already-completed main receipt rather than infer readiness from folders.
    assert args.receipt_sha256 and sha(receiptp)==args.receipt_sha256
    assert not any(bool(receipt.get(k)) for k in ['is_error','failed'])
    assert receipt['status']=='official_model_and_isolated_package_ready'
    assert Path(receipt['model_path']).resolve()==modelp
    assert Path(receipt['deps_path']).resolve()==OUT/'deps'
    assert receipt['packages']['vosk']=='0.3.45' and receipt['model_license']=='Apache-2.0'
    archive=modelp.parent/'vosk-model-small-ko-0.22.zip'
    assert archive.stat().st_size==receipt['archive_bytes'] and sha(archive)==receipt['archive_sha256']
    cfg=read(QA/'config.json')
    assert prepared['script_sha256']==cfg['script_sha256']
    for job in prepared['jobs']:
        assert sha(Path(job['input_audio']['path']))==job['input_audio']['sha256']
        assert sha(Path(job['resampled_audio']['path']))==job['resampled_audio']['sha256']
        assert not (OUT/'results'/f'{job["scene_id"]}.json').exists(),'preserve existing actual inference evidence before any new inference'
    os.environ.update(DO_NOT_TRACK='1',PYTHONDONTWRITEBYTECODE='1')
    def denied(*a,**k):raise RuntimeError('Network forbidden in local Vosk QA')
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,str(OUT/'deps'))
    import vosk,importlib.metadata,inspect
    version=importlib.metadata.version('vosk');assert version=='0.3.45'
    assert Path(vosk.__file__).resolve().is_relative_to(OUT/'deps')
    files=[{'relative_path':str(p.relative_to(modelp)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(modelp.rglob('*')) if p.is_file()]
    modeltree=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    dist=importlib.metadata.distribution('vosk')
    package_versions={}
    for name in ['vosk','cffi','srt','requests','tqdm','websockets']:
        try:
            dep=importlib.metadata.distribution(name)
            package_versions[name]={'version':dep.version,'metadata_license':dep.metadata.get('License')}
        except importlib.metadata.PackageNotFoundError:
            package_versions[name]={'installed_metadata_found':False}
    licenses=[pin(p) for p in modelp.rglob('*') if p.is_file() and any(k in p.name.lower() for k in ['license','readme','copying'])]
    modelmeta={'model_path':str(modelp),'model_name':modelp.name,'model_tree_sha256':modeltree,'model_files':files,'license':'Apache-2.0','license_basis':'Main official primary verification plus supplied exact provision receipt; any shipped license/readme files pinned separately.','license_readme_files':licenses,'package_name':'vosk','package_version':version,'package_metadata_license':dist.metadata.get('License'),'package_module':pin(Path(vosk.__file__)),'package_api':{'Model':str(inspect.signature(vosk.Model)),'KaldiRecognizer':str(inspect.signature(vosk.KaldiRecognizer))},'provision_receipt':pin(receiptp),'model_and_deps_modified_by_QA':False}
    dump(OUT/'runtime_manifest.json',modelmeta)
    dump(OUT/'archive_provenance.json',{'archive':pin(archive),'bytes':archive.stat().st_size,'download_URL':receipt['url'],'final_URL':receipt['final_url'],'model_license':receipt['model_license'],'HTTPS_ZIP_CRC_check_basis':'Main completed provision receipt','publisher_checksum_available':receipt['publisher_checksum_available'],'provision_receipt':pin(receiptp),'no_independent_publisher_checksum_claimed':True})
    dump(OUT/'asr_package_versions.json',package_versions)
    model=vosk.Model(model_path=str(modelp))
    outputs=[]
    for job in prepared['jobs']:
        rec=vosk.KaldiRecognizer(model,16000) # No third grammar argument.
        rec.SetWords(True)
        pieces=[];consumed=0;wp=Path(job['resampled_audio']['path'])
        with wave.open(str(wp),'rb') as w:
            while True:
                chunk=w.readframes(4000)
                if not chunk:break
                consumed+=len(chunk)//2
                if rec.AcceptWaveform(chunk):pieces.append(read_json_string(rec.Result()))
            pieces.append(read_json_string(rec.FinalResult()))
        assert consumed==job['resampled_header']['frames']
        text=' '.join(p.get('text','') for p in pieces if p.get('text')).strip()
        # Reference comparison happens only after native recognizer finishes.
        comparison=compare(job['approved_spoken'],text)
        old=QA/'v3_delta/runs'/job['scene_id']
        d={'scene_id':job['scene_id'],'script_sha256':prepared['script_sha256'],'final_timing':prepared['final_timing'],'input_audio':job['input_audio'],'resampled_audio':job['resampled_audio'],'resampled_header':job['resampled_header'],'PCM_frames_consumed':consumed,'raw_transcript':text,'native_Result_and_FinalResult':pieces,'approved_display':job['approved_display'],'approved_spoken':job['approved_spoken'],'comparison_after_decoding_only':comparison,'standard_Whisper_small':read(old/'small.json')['transcript'],'standard_Whisper_medium':read(old/'medium.json')['transcript'],'model_runtime_manifest':pin(OUT/'runtime_manifest.json'),'recognizer_constructor':'KaldiRecognizer(model,16000); no grammar argument','SetWords':True,'SetGrammar_called':False,'expected_number_list_or_hotwords':False,'network_calls':0,'paid_calls':0,'TTS_calls':0,'actual_listening':False,'continuous_playback':False,'approved':None,'interpretation':'Independent Kaldi/Vosk evidence; no automatic approval or assumed superiority over Whisper. Actual numeral and source differences must be reviewed.'}
        dest=OUT/'results'/f'{job["scene_id"]}.json';dest.parent.mkdir(exist_ok=True);assert not dest.exists(),'preserve existing actual inference evidence'
        dump(dest,d);outputs.append(pin(dest))
        assert sha(Path(job['input_audio']['path']))==job['input_audio']['sha256']
        assert sha(wp)==job['resampled_audio']['sha256']
        print(json.dumps({'scene_id':job['scene_id'],'raw_transcript':text,'numeric_differences':comparison['numeric_differences'],'result':str(dest)},ensure_ascii=False),flush=True)
    assert sha(receiptp)==args.receipt_sha256
    dump(OUT/'run_receipt.json',{'status':'two_actual_unprompted_Vosk_full_paragraph_runs_complete','script_sha256':prepared['script_sha256'],'final_timing':prepared['final_timing'],'results':outputs,'runtime_manifest':pin(OUT/'runtime_manifest.json'),'prepared_audio':pin(OUT/'prepared.json'),'runner':pin(OUT/'run_vosk.py'),'at_utc':datetime.now(timezone.utc).isoformat(),'ASR_runs':2,'source_audio_modified':False,'models_or_deps_installed_by_QA':False,'actual_listening':False,'automatic_issue_closure':False})

def read_json_string(s):return json.loads(s)

if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');p=sub.add_parser('run');p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--model',required=True)
    args=ap.parse_args()
    if args.command=='prepare':prepare()
    else:run(args)
