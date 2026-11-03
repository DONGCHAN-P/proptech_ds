import pathlib,json,subprocess,hashlib,wave,math,shutil
import numpy as np
import io
from PIL import Image,ImageDraw
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/hanam-gyosan-20261019';ed=ep/'editor/shorts-leader-v1';out=ep/'outputs/shorts-leader-v1';v=out/'gyosan_leader_short_v1.mp4';ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';fp=ff.with_name('ffprobe.exe')
def run(argv):return subprocess.run([str(x) for x in argv],capture_output=True,check=True)
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
tagged=out/'tagged.tmp.mp4'
run([ff,'-y','-v','error','-i',v,'-map','0','-c','copy','-metadata','title=3기 신도시 하남 교산의 대장단지는 어디가 될까?',tagged]);tagged.replace(v)
info=json.loads(run([fp,'-v','error','-show_format','-show_streams','-of','json',v]).stdout);save(out/'technical.json',info)
run([ff,'-v','error','-i',v,'-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-']);(out/'decode.txt').write_text('Complete video/audio decode exit 0; stderr empty',encoding='utf8')
for sec in [1,7,11,17,22,28,33,38,44,49]:run([ff,'-y','-v','error','-ss',sec,'-i',v,'-frames:v','1',out/f'encoded-{sec:02}.png'])
w=wave.open(str(ed/'public/voice.wav'),'rb');orig=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float64);sr=w.getframerate()
decoded=run([ff,'-v','error','-i',v,'-vn','-ac','1','-ar',sr,'-c:a','pcm_s16le','-f','wav','pipe:1']).stdout
with wave.open(io.BytesIO(decoded),'rb') as ew: enc=np.frombuffer(ew.readframes(ew.getnframes()),dtype=np.int16).astype(np.float64)
n=min(len(enc),len(orig));cor=float(np.corrcoef(orig[:n],enc[:n])[0,1]);peak=float(np.max(np.abs(enc))/32768)
plan=json.loads((ed/'clip_plan.json').read_text(encoding='utf8'));sw=wave.open(str(ep/'outputs/production-v5-jun/audio/M008.wav'),'rb');raw=sw.readframes(sw.getnframes());stride=sw.getsampwidth()*sw.getnchannels();assembled=(ed/'public/voice.wav');rw=wave.open(str(assembled),'rb');made=rw.readframes(rw.getnframes());cursor=0;comparisons=[]
for c in plan['clips']:
 a=c['source_sample_start'];b=c['source_sample_end'];piece=raw[a*stride:b*stride];exact=made[cursor*stride:(cursor+b-a)*stride]==piece;comparisons.append({'unit_id':c['unit_id'],'exact_source_pcm_with_handles':exact,'samples':b-a});cursor+=b-a+round(.12*sr)
save(out/'audio_comparison.json',{'source_pcm_comparisons':comparisons,'encoded_correlation_zero_lag':cor,'decoded_peak_linear':peak,'decoded_peak_dbfs':20*math.log10(peak),'actual_listening':False,'speech_speed_changed':False,'bgm':None})
sha=hashlib.sha256(v.read_bytes()).hexdigest();save(out/'render_receipt.json',{'path':str(v),'sha256':sha,'status':'local_review_draft','title':plan['title'],'duration':info['format']['duration'],'new_paid_calls':0,'upload':False,'actual_listening':False,'continuous_playback':False})
print(json.dumps({'mp4_sha256':sha,'duration':info['format']['duration'],'correlation':cor,'peak_dbfs':20*math.log10(peak),'source_pcm_exact':all(x['exact_source_pcm_with_handles'] for x in comparisons),'samples':9}))
