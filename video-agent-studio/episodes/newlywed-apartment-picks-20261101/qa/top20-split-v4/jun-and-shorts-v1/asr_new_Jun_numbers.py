"""Offline cached-small ASR for selected new Jun numeric sentences; never hearing."""
import pathlib,json,os,sys,socket,time,re,argparse
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];R=E.parents[2];CACHE=R/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
sys.dont_write_bytecode=True;sys.path.insert(0,str(CACHE/'deps'))
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',HF_HOME=str(Q/'asr_cache'),XDG_CACHE_HOME=str(Q/'asr_cache'))
def deny(*a,**kw):raise RuntimeError('QA offline ASR: network disabled')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
ap=argparse.ArgumentParser();ap.add_argument('--medium-targets',action='store_true');args=ap.parse_args()
rows=json.loads((Q/'ASR_selection.json').read_text(encoding='utf-8'))['sentences']
if args.medium_targets:rows=[x for x in rows if x['sentence_id'] in ['P01-INTRO-V3-05','P01-R15-V2-01']]
model_name='medium' if args.medium_targets else 'systran-faster-whisper-small'
start=time.monotonic();model=WhisperModel(str(CACHE/'models'/model_name),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True);cache={};out=[]
def numbers(s):return re.findall(r'\d+(?:\.\d+)?',s.replace(',',''))
for x in rows:
    p=str(R/x['wav_path'])
    if p not in cache:cache[p]=decode_audio(p,sampling_rate=16000)
    pcm=cache[p];a=max(0,x['chunk_local_start_s']-.16);b=min(len(pcm)/16000,x['chunk_local_end_s']+.24)
    iterator,_=model.transcribe(pcm[int(a*16000):int(b*16000)],language='ko',task='transcribe',beam_size=5,temperature=0,condition_on_previous_text=False,vad_filter=False,initial_prompt=None,hotwords=None)
    segments=list(iterator);text=' '.join(s.text.strip() for s in segments)
    out.append(dict(**x,clip_start_s=a,clip_end_s=b,recognized=text,expected_Arabic_numeric_sequence=numbers(x['text']),recognized_Arabic_numeric_sequence=numbers(text),numeric_surface_equal=numbers(x['text'])==numbers(text),scope='ASR supporting evidence only; Arabic/Korean normalization and recognition may differ'))
report=dict(status='supporting_ASR_evidence_only',model='cached '+model_name+' cpu/int8',local_only=True,network_blocked=True,reference_prompted=False,old_free_voice_processed=False,sentences=out,elapsed_s=time.monotonic()-start,selected_seconds=sum(x['clip_end_s']-x['clip_start_s'] for x in out),numeric_surface_difference_candidates=[x['sentence_id'] for x in out if not x['numeric_surface_equal']],actual_hearing=False,actual_listening=False,continuous_playback=False,actual_numeric_pronunciation='unchecked')
dest=Q/('ASR_new_Jun_numeric_recheck.json' if args.medium_targets else 'ASR_new_Jun_numbers.json')
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(sentences=len(out),elapsed_s=report['elapsed_s'],selected_seconds=report['selected_seconds'],numeric_surface_difference_candidates=report['numeric_surface_difference_candidates'],output=str(dest)),ensure_ascii=False))
