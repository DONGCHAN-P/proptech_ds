"""Offline, unprompted ASR of four numeric-dense scene excerpts; no TTS calls."""
from pathlib import Path
import os,sys,socket,json,hashlib,wave,time
OWN=Path(__file__).resolve().parent;EP=OWN.parents[1];ROOT=EP.parents[2]
SOURCE=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
MEDIUM='--medium' in sys.argv
ALL='--all' in sys.argv
DEST=OWN/('asr-full-medium' if ALL else ('asr-medium' if MEDIUM else 'asr-samples'));DEST.mkdir(exist_ok=True)
sys.path[:0]=[str(SOURCE/'deps'),str(SOURCE)]
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',HF_HOME=str(DEST/'cache'),XDG_CACHE_HOME=str(DEST/'cache'))
def refuse(*a,**kw):raise RuntimeError('offline ASR: network forbidden')
socket.socket.connect=refuse;socket.socket.connect_ex=refuse;socket.create_connection=refuse
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
from comparison import analyze_text
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
alignment=load(OWN/'scene_alignment.json');manifest=load(OWN/'narration_manifest.json')
paras={p['paragraph_id']:p for p in manifest['paragraphs']};units={u['audio_unit_id']:u for u in alignment['audio_units']}
model_path=SOURCE/('models/medium' if MEDIUM else 'models/systran-faster-whisper-small')
model=WhisperModel(str(model_path),device='cpu',compute_type='int8',cpu_threads=3,num_workers=1,local_files_only=True)
rows=[]
items=alignment['scenes']
if ALL:
    items=[{'scene_id':c['chapter_id'],'audio_unit_id':c['chapter_id'],'audio_start_s':0,'audio_end_s':units[c['chapter_id']]['duration_s'],'paragraph_ids':c['paragraph_ids']} for c in manifest['chapters']]
selected=[s['scene_id'] for s in items] if ALL else (['S13','S15','S21'] if MEDIUM else ['S13','S15','S21','S26'])
for sid in selected:
    s=next(s for s in items if s['scene_id']==sid)
    u=units[s['audio_unit_id']];source=ROOT/u['path'];out=DEST/(sid+'.wav')
    if ALL:out=source
    else:
        with wave.open(str(source),'rb') as w:
            rate=w.getframerate();w.setpos(round(s['audio_start_s']*rate));pcm=w.readframes(round(s['audio_end_s']*rate)-round(s['audio_start_s']*rate))
        with wave.open(str(out),'wb') as w:
            w.setparams((1,2,rate,0,'NONE','not compressed'));w.writeframes(pcm)
    t=time.monotonic()
    it,info=model.transcribe(str(out),language='ko',task='transcribe',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None)
    segments=list(it);transcript=' '.join(s.text.strip() for s in segments)
    reference=' '.join(paras[pid]['text'] for pid in s['paragraph_ids'])
    comparison=analyze_text(reference,transcript)
    row={'scene_id':sid,'audio_sha256':sha(out),'reference':reference,'transcript':transcript,'comparison':comparison,'seconds':info.duration,'elapsed_s':time.monotonic()-t,'segments':[{'start':v.start,'end':v.end,'text':v.text,'avg_logprob':v.avg_logprob} for v in segments],'actual_listening':False,'naturalness_verified':False,'external_upload':False}
    (DEST/(sid+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');rows.append(row)
    print(json.dumps({'scene':sid,'seconds':row['seconds'],'numeric_differences':comparison.get('numeric_differences'),'elapsed_s':row['elapsed_s']},ensure_ascii=False),flush=True)
summary={'status':'full_chapter_audio_locally_transcribed' if ALL else 'numeric_dense_scenes_locally_transcribed','scene_ids':[r['scene_id'] for r in rows],'seconds':sum(r['seconds'] for r in rows),'rows':rows,'model_sha256':sha(model_path/'model.bin'),'alignment_sha256':sha(OWN/'scene_alignment.json'),'actual_listening':False,'full_episode_ASR':ALL,'external_upload':False}
(DEST/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
