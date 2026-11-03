"""Offline independent transcription evidence; never claims human listening."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,difflib,hashlib,json,os,re,socket,subprocess,sys,time
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return re.sub('[^가-힣0-9]','',s)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['small','medium'],default='small');ap.add_argument('--scenes',nargs='*');a=ap.parse_args()
    lp=D/'locked_timing.json';t=read(lp);assert t['timing_locked'] and t['part']==1
    base=R/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr'
    modeldir=base/'models'/('medium'if a.model=='medium'else'systran-faster-whisper-small');assert(modeldir/'model.bin').exists()
    os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4')
    def denied(*args,**kwargs):raise RuntimeError('Offline ASR network denied')
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,str(base/'deps'));import faster_whisper
    model=None;reports=[];folder=D/'evidence/asr'/a.model;folder.mkdir(parents=True,exist_ok=True)
    ff=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
    for s in t['scenes']:
        if a.scenes and s['scene_id']not in a.scenes:continue
        start=max(0,s['sentences'][0]['start_s']-.08);end=min(s['end_s'],s['sentences'][-1]['end_s']+.3)
        wav=folder/(s['scene_id']+'.wav');dest=folder/(s['scene_id']+'.json')
        if dest.exists():
            old=read(dest)
            if old['timing_sha256']==sha(lp) and sha(wav)==old['audio_sha256']:reports.append(old);continue
        cmd=[str(ff),'-v','error','-y','-ss',str(start),'-i',str(R/t['audio_path']),'-t',str(end-start),'-ar','16000','-ac','1','-c:a','pcm_s16le',str(wav)]
        result=subprocess.run(cmd,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert result.returncode==0
        if model is None:model=faster_whisper.WhisperModel(str(modeldir),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
        started=time.monotonic();segments,info=model.transcribe(str(wav),language='ko',beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
        rows=[{'start_s':seg.start,'end_s':seg.end,'global_start_s':start+seg.start,'global_end_s':start+seg.end,'text':seg.text,
               'words':[{'text':w.word,'start_s':start+w.start,'end_s':start+w.end,'probability':w.probability}for w in seg.words or[]]}for seg in segments]
        expected=' '.join(v['reading_text']for v in s['sentences']);recognized=' '.join(v['text']for v in rows)
        report={'scene_id':s['scene_id'],'timing_sha256':sha(lp),'audio_file':str(wav),'audio_sha256':sha(wav),
                'expected_reading':expected,'recognized':recognized,'segments':rows,'clip_global_start_s':start,'clip_global_end_s':end,
                'input_duration_s':info.duration,'elapsed_s':time.monotonic()-started,'model':a.model,
                'literal_similarity_not_numeric_normalized':difflib.SequenceMatcher(a=norm(expected),b=norm(recognized),autojunk=False).ratio(),
                'external_audio_transfer':False,'actual_listening_performed':False,'continuous_playback_performed':False,
                'scope':'ASR supports content checks; numbers and proper-name spellings require interpretation; no naturalness score'}
        save(dest,report);reports.append(report)
        print(json.dumps({'scene_id':s['scene_id'],'input_s':round(info.duration,2),'elapsed_s':round(report['elapsed_s'],2)},ensure_ascii=False),flush=True)
    save(folder/'summary.json',{'status':'offline_ASR_evidence_requires_interpretation','checked_at':datetime.now(timezone.utc).isoformat(),
         'timing_sha256':sha(lp),'scenes':[{k:v[k]for k in ['scene_id','recognized','literal_similarity_not_numeric_normalized']}for v in reports],
         'actual_listening_performed':False,'external_audio_transfer':False})
if __name__=='__main__':main()
