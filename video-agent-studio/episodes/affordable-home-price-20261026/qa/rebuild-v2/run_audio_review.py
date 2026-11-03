"""Offline ASR and signal evidence for the revised scene audio; no listening claim."""
import argparse,hashlib,json,os,socket,sys,time,wave
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(p):return Path(p) if Path(p).is_absolute() else ROOT/p
ap=argparse.ArgumentParser();ap.add_argument('--timing',required=True);ap.add_argument('--model',choices=['small','medium'],default='small');ap.add_argument('--scenes',nargs='+',default=['R005','R006','R008','R013','R015','R026','R030','R032']);a=ap.parse_args()
tp=resolve(a.timing);assert tp.resolve().is_relative_to(EP)
timing=read(tp)
deps=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/deps'
modelroot=deps.parent/'models'/('systran-faster-whisper-small' if a.model=='small' else 'medium')
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false')
def denied(*args,**kwargs):raise RuntimeError('Network disabled for offline audio QA')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
sys.path.insert(0,str(deps));sys.path.insert(0,str(EP/'qa/audio-v1'))
import numpy as np
import faster_whisper
from checks import compare
out=HERE/f'asr-{a.model}';out.mkdir(exist_ok=True)
all_dsp=[]
for row in timing['scenes']:
 wp=resolve(row['audio_path']);assert wp.resolve().is_relative_to(EP/'narration/rebuild-v2')
 with wave.open(str(wp),'rb') as w:
  rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth();raw=w.readframes(w.getnframes())
 assert width==2
 x=np.frombuffer(raw,dtype='<i2').astype(np.int32)
 all_dsp.append({'id':row['id'],'audio_path':str(wp),'sha256':sha(wp),'sample_rate':rate,'channels':channels,'duration_s':len(x)/channels/rate,'peak':int(np.abs(x).max()),'clipped_samples':int(np.count_nonzero(np.abs(x)>=32767)),'RMS_dbfs':float(20*np.log10(max(float(np.sqrt(np.mean(x.astype(float)**2))),1e-10)/32768))})
save(out/'all_scene_signal.json',{'timing_sha256':sha(tp),'scenes':all_dsp,'actual_listening':False})
model=None;reports=[]
for row in timing['scenes']:
 if row['id'] not in a.scenes:continue
 wp=resolve(row['audio_path']);digest=sha(wp);dest=out/(row['id']+'_'+digest[:12]+'.json')
 if dest.exists():reports.append(read(dest));continue
 if model is None:model=faster_whisper.WhisperModel(str(modelroot),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
 started=time.monotonic()
 segments,info=model.transcribe(str(wp),language='ko',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
 rows=[]
 for s in segments:rows.append({'start_s':s.start,'end_s':s.end,'text':s.text,'words':[{'word':w.word,'start_s':w.start,'end_s':w.end,'probability':w.probability} for w in (s.words or [])]})
 text=' '.join(x['text'] for x in rows)
 report={'id':row['id'],'audio_sha256':digest,'expected':row['spoken_text'],'recognized':text,'comparison':compare(row['spoken_text'],text),'segments':rows,'input_seconds':info.duration,'elapsed_s':round(time.monotonic()-started,2),'model':str(modelroot),'prompted':False,'actual_listening':False}
 save(dest,report);reports.append(report)
 print(json.dumps({'id':row['id'],'similarity':report['comparison']['text_similarity'],'numeric_differences':len(report['comparison']['numeric_differences']),'elapsed_s':report['elapsed_s']}),flush=True)
save(out/'summary.json',{'timing_sha256':sha(tp),'scene_count':len(reports),'scene_ids':[r['id'] for r in reports],'model':a.model,'reports':[{'id':r['id'],'audio_sha256':r['audio_sha256'],'comparison':r['comparison']} for r in reports],'classification':'unprompted_ASR_supporting_evidence_requires_review_of_differences','actual_listening':False,'continuous_playback':False})
