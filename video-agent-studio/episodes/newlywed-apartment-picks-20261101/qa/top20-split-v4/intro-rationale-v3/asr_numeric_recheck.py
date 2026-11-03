"""Independent second-model evidence for ambiguous numeric ASR, two clips only."""
import os,pathlib,sys,socket,json,time,hashlib
Q=pathlib.Path(__file__).resolve().parent; E=Q.parents[2];ROOT=E.parents[2]
CACHE=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
sys.dont_write_bytecode=True;sys.path.insert(0,str(CACHE/'deps'))
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',XDG_CACHE_HOME=str(Q/'asr_cache'),HF_HOME=str(Q/'asr_cache'))
def deny(*a,**kw):raise RuntimeError('QA offline mode')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
audio=E/'narration/top20-split-v4/intro-rationale-v3/intro_with_brand.wav'
timing=json.loads((audio.parent/'timing_proposals.json').read_text(encoding='utf-8-sig'))
model=CACHE/'models/medium'
start=time.monotonic()
m=WhisperModel(str(model),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
pcm=decode_audio(str(audio),sampling_rate=16000)
rows=[]
for s in timing['sentences']:
    if s['sentence_id'] not in ['P01-INTRO-V3-05','P01-INTRO-V3-08']:continue
    a=max(0,s['start_s']-.4);b=min(len(pcm)/16000,s['end_s']+.6)
    iterator,info=m.transcribe(pcm[int(a*16000):int(b*16000)],language='ko',task='transcribe',beam_size=5,temperature=0,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
    segments=list(iterator)
    rows.append(dict(sentence_id=s['sentence_id'],start_s=a,end_s=b,expected=s['reading_text'],recognized=' '.join(x.text.strip() for x in segments)))
out=dict(status='supporting_ASR_evidence_only',reason='small model numeric ambiguity; not a confirmed pronunciation defect',model='cached medium',model_sha256=hashlib.sha256((model/'model.bin').read_bytes()).hexdigest(),elapsed_s=time.monotonic()-start,clips=rows,reference_prompted=False,network_blocked=True,actual_listening=False,actual_numeric_pronunciation='unchecked')
(Q/'asr_numeric_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
