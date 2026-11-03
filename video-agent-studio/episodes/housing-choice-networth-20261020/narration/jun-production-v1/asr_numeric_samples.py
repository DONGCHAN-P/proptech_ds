"""기존 로컬 small ASR로 숫자 밀집3문단만 보조 점검. 원문 prompt/외부 전송/음성 재생성 없음."""
import os
import sys
import json
import time
import socket
import re
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone

sys.dont_write_bytecode=True
OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
SOURCE=EP/'qa/private-production-v1/asr'
sys.path[:0]=[str(SOURCE/'deps'),str(SOURCE)]
DEST=OWN/'asr-numeric-samples'
DEST.mkdir(exist_ok=True)
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',
                  HF_HOME=str(DEST/'cache'),XDG_CACHE_HOME=str(DEST/'cache'))

def refuse(*args,**kwargs):raise RuntimeError('offline ASR: network forbidden')
socket.socket.connect=refuse
socket.socket.connect_ex=refuse
socket.create_connection=refuse
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
from comparison import analyze_text,normalize

sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
prepared=json.loads((EP/'narration/free-tts-v1/prepare-v6/prepared.json').read_text(encoding='utf-8'))
paras={p['paragraph_id']:p for c in prepared['chapters'] for p in c['paragraphs']}
ids=['C02P02','C06P02','C07P02']
model_path=SOURCE/'models/systran-faster-whisper-small'
model=WhisperModel(str(model_path),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
rows=[]
for pid in ids:
    dest=DEST/(pid+'.json')
    if dest.exists():
        rows.append(json.loads(dest.read_text(encoding='utf8')))
        continue
    audio=OWN/'paragraphs'/pid/'audio.wav'
    start=time.monotonic()
    iterator,info=model.transcribe(str(audio),language='ko',task='transcribe',beam_size=5,temperature=0,
                                  word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
    segments=list(iterator)
    transcript=' '.join(s.text.strip() for s in segments)
    reference=paras[pid]['text']
    comparison=analyze_text(reference,transcript)
    row={'paragraph_id':pid,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'audio_sha256':sha(audio),
         'reference':reference,'reference_sha256':sha256(reference.encode()).hexdigest(),'transcript':transcript,
         'segments':[{'start_s':s.start,'end_s':s.end,'text':s.text,'avg_logprob':s.avg_logprob,
                      'words':[{'word':w.word,'start_s':w.start,'end_s':w.end,'probability':w.probability} for w in (s.words or [])]} for s in segments],
         'comparison':comparison,'elapsed_seconds':time.monotonic()-start,'input_duration_s':info.duration,
         'actual_listening':False,'pronunciation_verified':False,'naturalness_verified':False,'new_audio_generation_calls':0,
         'network':'offline local files only; Python socket connections blocked','engine':'existing faster-whisper small CPU int8',
         'options':{'beam_size':5,'temperature':0,'initial_prompt':None,'hotwords':None,'condition_on_previous_text':False},
         'limits':'ASR 숫자/누락 후보는 독립 검토 대상. 음향적 발음 정답이나 실제 청취 증거가 아님.'}
    dest.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    rows.append(row)
    print(json.dumps({'paragraph_id':pid,'seconds':round(row['elapsed_seconds'],2),'numeric_difference_groups':len(comparison['numeric_differences']),
                      'normalized_equal':comparison['normalized_text_equal'],'actual_listening':False}),flush=True)
summary={'status':'three_numeric_dense_paragraphs_locally_transcribed','sampled_paragraph_ids':ids,'total_paragraphs':54,
         'sampled_seconds':sum(r['input_duration_s'] for r in rows),'full_episode_ASR':False,'actual_listening':False,'external_upload':False,
         'rows':[{'paragraph_id':r['paragraph_id'],'audio_sha256':r['audio_sha256'],'numeric_difference_groups':len(r['comparison']['numeric_differences']),
                  'normalized_equal':r['comparison']['normalized_text_equal'],'result_path':str((DEST/(r['paragraph_id']+'.json')).relative_to(EP)).replace('\\','/')} for r in rows],
         'model_path':str(model_path),'model_weight_sha256':sha(model_path/'model.bin'),'model_config_sha256':sha(model_path/'config.json'),
         'comparison_code_sha256':sha(SOURCE/'comparison.py'),'runner_sha256':sha(Path(__file__))}
(DEST/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
