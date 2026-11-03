"""A second ASR family for ambiguous Whisper numeric formatting, fully offline."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
prior=EP/'qa/audio-v1/vosk-v1';sys.path.insert(0,str(prior/'deps'))
def deny(*a,**k):raise RuntimeError('Offline ASR only')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=deny
import vosk
vosk.SetLogLevel(-1)
model=vosk.Model(str(prior/'model-cache/vosk-model-small-ko-0.22'))
timing=EP/'narration/rebuild-v2/audio-r2-recovered/final_timing.json'
data=json.loads(timing.read_text(encoding='utf-8'));out=HERE/'asr-vosk';out.mkdir(exist_ok=True)
ff=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
for s in data['scenes']:
 if s['id'] not in ['R005','R008','R013']:continue
 wp=ROOT/s['audio_path'];sha=hashlib.sha256(wp.read_bytes()).hexdigest();dest=out/(s['id']+'_'+sha[:12]+'.json')
 assert not dest.exists()
 raw=subprocess.check_output([str(ff),'-v','error','-i',str(wp),'-ac','1','-ar','16000','-f','s16le','-'])
 rec=vosk.KaldiRecognizer(model,16000);rec.SetWords(True);rows=[]
 for i in range(0,len(raw),8000):
  if rec.AcceptWaveform(raw[i:i+8000]):rows.append(json.loads(rec.Result()))
 rows.append(json.loads(rec.FinalResult()));text=' '.join(r.get('text','') for r in rows)
 report={'scene_id':s['id'],'audio_sha256':sha,'recognized':text,'expected':s['spoken_text'],'results':rows,'model':'vosk-model-small-ko-0.22','prompted':False,'grammar_supplied':False,'network':False,'actual_listening':False}
 dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'id':s['id'],'recognized':text},ensure_ascii=False),flush=True)
