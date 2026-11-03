"""Offline cached ASR of only the new 47.67s intro; no reference prompts."""
import os, pathlib, sys, socket, json, hashlib, time, difflib
Q=pathlib.Path(__file__).resolve().parent
E=Q.parents[2]; ROOT=E.parents[2]
CACHE=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
sys.dont_write_bytecode=True
sys.path.insert(0,str(CACHE/'deps'))
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',XDG_CACHE_HOME=str(Q/'asr_cache'),HF_HOME=str(Q/'asr_cache'))
def deny(*a,**kw):raise RuntimeError('QA offline mode: network disabled')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
audio=E/'narration/top20-split-v4/intro-rationale-v3/intro_with_brand.wav'
model=CACHE/'models/systran-faster-whisper-small'
manifest=json.loads((CACHE/'model_manifest.json').read_text(encoding='utf-8-sig'))
model_sha=hashlib.sha256((model/'model.bin').read_bytes()).hexdigest()
assert model_sha==next(x['sha256'] for x in manifest['files'] if x['path']=='model.bin')
start=time.monotonic()
m=WhisperModel(str(model),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
iterator,info=m.transcribe(str(audio),language='ko',task='transcribe',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
segments=list(iterator)
transcript=' '.join(s.text.strip() for s in segments)
reference=(audio.parent/'reading_text.txt').read_text(encoding='utf-8-sig')
norm=lambda s:''.join(c for c in s if c.isalnum())
a,b=norm(reference),norm(transcript)
diff=[dict(tag=tag,expected=a[i:j],recognized=b[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
rows=[dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words or []]) for s in segments]
out=dict(status='supporting_ASR_evidence_only',audio=str(audio),audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),model='Systran/faster-whisper-small',model_sha256=model_sha,local_only=True,python_network_blocked=True,reference_prompted=False,scope='new_intro_47.672313s_only_no_old_body_ASR',elapsed_s=time.monotonic()-start,transcript=transcript,normalized_similarity=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio(),differences=diff,segments=rows,actual_listening=False,naturalness='unchecked',actual_numeric_pronunciation='unchecked',continuous_playback=False)
(Q/'asr_new_intro.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(Q/'asr_transcript.txt').write_text(transcript+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['status','elapsed_s','transcript','normalized_similarity','differences']},ensure_ascii=False))
