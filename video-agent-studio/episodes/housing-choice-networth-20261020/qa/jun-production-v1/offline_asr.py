"""Existing local models only. References never enter recognizers; QA outputs only."""
import os,sys,json,hashlib,socket,wave,subprocess,time,argparse
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent;R=E.parents[2]
A=E/'qa/private-production-v1/asr'
V=R/'video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/vosk-v1'
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',HF_HOME=str(Q/'asr-cache'),XDG_CACHE_HOME=str(Q/'asr-cache'),NUMBA_CACHE_DIR=str(Q/'asr-cache'))
def denied(*a,**k):raise RuntimeError('QA offline: network forbidden')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(p,d):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='+',required=True);ap.add_argument('--engines',nargs='+',choices=['small','medium','vosk'],default=['small']);args=ap.parse_args()
    sys.path.insert(0,str(A/'deps'));sys.path.insert(0,str(V/'deps'))
    import av,numpy as np
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio
    import onnxruntime;onnxruntime.disable_telemetry_events()
    import vosk;vosk.SetLogLevel(-1)
    records=[];jobs=[];pho=read(E/'narration/jun-replacement-v1/pronunciation_proposal.json')
    for pid in args.ids:
        src=E/'narration/jun-production-v1/paragraphs'/pid/'audio.wav';recp=E/'narration/jun-production-v1/receipts'/f'{pid}.json'
        assert src.is_file() and recp.is_file(),f'not ready: {pid}'
        receipt=read(recp);assert receipt['status']=='complete'
        assert receipt['artifact_sha256'][f'paragraphs/{pid}/audio.wav']==sha(src)
        target=next(p for p in pho['paragraphs'] if p['paragraph_id']==pid)
        assert receipt['request']['text']==target['proposed_spoken_text']
        jobs.append(dict(pid=pid,source=src,sourcepin=pin(src),receipt=pin(recp),expected=target['proposed_spoken_text']))
    for engine in args.engines:
        start=time.monotonic()
        if engine=='vosk':
            runtime=read(V/'runtime_manifest.json');modelp=Path(runtime['model_path'])
            for item in runtime['model_files']:assert sha(modelp/item['relative_path'])==item['sha256']
            model=vosk.Model(model_path=str(modelp));modelpin=pin(V/'runtime_manifest.json')
        else:
            modelp=A/'models'/('systran-faster-whisper-small' if engine=='small' else 'medium')
            manifestp=A/'model_manifest.json' if engine=='small' else modelp/'model_manifest.json'
            if manifestp.exists():
                manifest=read(manifestp)
                entries=manifest.get('files',[])
                weights=next((x for x in entries if x.get('path')=='model.bin'),None)
                if weights:assert sha(modelp/'model.bin')==weights['sha256']
            modelpin=pin(modelp/'model.bin')
            model=WhisperModel(str(modelp),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
        for job in jobs:
            pid=job['pid'];dest=Q/'asr'/pid/(engine+'.json')
            if dest.exists():
                old=read(dest);assert old['audio']==job['sourcepin'];records.append(pin(dest));continue
            t=time.monotonic();decoded=decode_audio(str(job['source']),sampling_rate=16000)
            if engine=='vosk':
                pcm=(np.clip(decoded,-1,1)*32767).astype('<i2').tobytes();rec=vosk.KaldiRecognizer(model,16000);rec.SetWords(True);pieces=[]
                for n in range(0,len(pcm),8000):
                    if rec.AcceptWaveform(pcm[n:n+8000]):pieces.append(json.loads(rec.Result()))
                pieces.append(json.loads(rec.FinalResult()));transcript=' '.join(x.get('text','') for x in pieces).strip();segments=pieces
                opts=dict(constructor='KaldiRecognizer(model,16000)',grammar=None,hotwords=None,reference_supplied=False)
            else:
                itr,info=model.transcribe(decoded,language='ko',task='transcribe',beam_size=5,temperature=0.0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
                s=list(itr);transcript=' '.join(x.text.strip() for x in s);segments=[dict(start=x.start,end=x.end,text=x.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in (x.words or [])]) for x in s]
                opts=dict(language='ko',beam_size=5,temperature=0,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None,reference_supplied=False)
            d=dict(paragraph_id=pid,audio=job['sourcepin'],receipt=job['receipt'],engine=engine,model=modelpin,options=opts,raw_transcript=transcript,segments=segments,expected_after_inference=job['expected'],decoded_seconds=len(decoded)/16000,all_decoded_samples_submitted=True,elapsed_seconds=round(time.monotonic()-t,3),actual_listening=False,continuous_playback=False,naturalness='unchecked',network_connections=0,downloads=0,paid_API_calls=0,interpretation='ASR 보조 근거. 발음/자연스러움의 청취 검증이나 자동 승인을 뜻하지 않음',checked_at=datetime.now(timezone.utc).isoformat())
            assert sha(job['source'])==job['sourcepin']['sha256'];dump(dest,d);records.append(pin(dest));print(json.dumps(dict(id=pid,engine=engine,transcript=transcript,seconds=d['elapsed_seconds']),ensure_ascii=False),flush=True)
        del model
    dump(Q/'asr'/('batch-'+hashlib.sha256((' '.join(args.ids)+' '.join(args.engines)).encode()).hexdigest()[:12]+'.json'),dict(results=records,run_ids=args.ids,engines=args.engines,actual_listening=False,continuous_playback=False,script_sha256=pho['script_sha256']))
if __name__=='__main__':main()
