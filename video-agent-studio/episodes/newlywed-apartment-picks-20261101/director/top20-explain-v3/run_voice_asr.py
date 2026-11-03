"""Independent cached offline ASR; produces evidence, never a listening verdict."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,difflib,hashlib,json,os,re,socket,sys,time
D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return re.sub('[^가-힣0-9]','',s)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--timing',required=True);ap.add_argument('--model',choices=['small','medium'],default='small');ap.add_argument('--scenes',nargs='*');a=ap.parse_args()
    tp=Path(a.timing).resolve();tp.relative_to(E);timing=read(tp)
    assert timing['script_sha256']=='4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38'
    base=R/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
    modeldir=base/'models'/('medium'if a.model=='medium'else'systran-faster-whisper-small');assert(modeldir/'model.bin').exists()
    os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4')
    def denied(*args,**kwargs):raise RuntimeError('Offline ASR network denied')
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,str(base/'deps'));import faster_whisper
    model=None;reports=[];out=D/'evidence/audio-asr'/a.model
    for row in timing['scenes']:
        if not row.get('sentences')or(a.scenes and row['scene_id']not in a.scenes):continue
        audio=Path(row['audio_path']);audio=audio if audio.is_absolute()else R/audio;digest=sha(audio);dest=out/(row['scene_id']+'_'+digest[:12]+'.json')
        if dest.exists():reports.append(read(dest));continue
        if model is None:model=faster_whisper.WhisperModel(str(modeldir),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
        start=time.monotonic();segments,info=model.transcribe(str(audio),language='ko',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
        rows=[{'start_s':s.start,'end_s':s.end,'text':s.text,'words':[{'word':w.word,'start_s':w.start,'end_s':w.end,'probability':w.probability}for w in s.words or[]]}for s in segments]
        recognized=' '.join(s['text']for s in rows);expected=row.get('reading_text')or' '.join(s.get('reading_text',s['text'])for s in row['sentences'])
        report={'scene_id':row['scene_id'],'audio_sha256':digest,'audio_file':str(audio),'timing_sha256':sha(tp),'expected_reading':expected,
                'recognized':recognized,'segments':rows,'input_seconds':info.duration,'model':'cached faster-whisper '+a.model+' CPU int8',
                'literal_similarity_not_numeric_normalized':difflib.SequenceMatcher(a=norm(expected),b=norm(recognized),autojunk=False).ratio(),
                'elapsed_s':time.monotonic()-start,'external_audio_transfer':False,'actual_listening_performed':False,
                'interpretation':'ASR spelling/digit differences require interpretation; ASR does not certify speech naturalness'}
        save(dest,report);reports.append(report);print(json.dumps({'scene':row['scene_id'],'seconds':round(info.duration,2),'elapsed_s':round(report['elapsed_s'],2)},ensure_ascii=False),flush=True)
    save(out/'summary.json',{'status':'offline_ASR_evidence_requires_interpretation','checked_at':datetime.now(timezone.utc).isoformat(),
          'timing_sha256':sha(tp),'scene_count':len(reports),'scenes':[r['scene_id']for r in reports],
          'reports':[{'scene_id':r['scene_id'],'audio_sha256':r['audio_sha256'],'recognized':r['recognized']}for r in reports],
          'actual_listening_performed':False,'continuous_playback_performed':False,'external_audio_transfer':False})
if __name__=='__main__':main()
