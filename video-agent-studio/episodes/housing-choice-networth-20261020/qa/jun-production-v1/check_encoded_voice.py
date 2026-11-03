"""Per-chapter sampled encoded waveform/Jun-source correspondence. No listening claim."""
import sys,json,hashlib,wave,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent;R=E.parents[2];sys.path.insert(0,str(E/'qa/private-production-v1/asr/deps'))
import numpy as np
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 t=read(Q/'final_technical_checks.json');video=Path(t['video']['path']);assert sha(video)==t['video']['sha256'];timing=read(E/'narration/jun-production-v1/final_timing.json');edl=read(E/'outputs/jun-production-v1/assembly_edl.json');ff=E/'outputs/private-production-v1/media-bin/ffmpeg.exe';out=Q/('encoded-'+sha(video)[:12])/'voice-correspondence';out.mkdir(exist_ok=True);rows=[]
 def wav(p):
  with wave.open(str(p),'rb') as w:assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(22050,1,2);return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)
 for ch in timing['chapters']:
  p=ch['paragraphs'][1];raw=R/p['wave_file'];srcstart=.5;duration=min(8,p['measured_seconds']-1);local=p['offset_s']+srcstart;off=next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter']==ch['chapter'] and x['local_start_s']<=local<x['local_end_s']);globalstart=local+off;files=[]
  for key,source,start in [('raw',raw,srcstart),('final',video,globalstart)]:
   dest=out/f'{p["paragraph_id"]}-{key}.wav'
   if not dest.exists():subprocess.run([str(ff),'-v','error','-nostdin','-ss',f'{start:.9f}','-i',str(source),'-t',f'{duration:.9f}','-map','0:a:0','-vn','-ac','1','-ar','22050','-c:a','pcm_s16le','-n',str(dest)],check=True,capture_output=True)
   files.append(dest)
  a,b=map(wav,files);n=min(len(a),len(b));a=a[:n]-np.mean(a[:n]);b=b[:n]-np.mean(b[:n]);margin=441
  # +/-20ms normalized correlation via FFT, independent of any speech text.
  kernel=a[margin:-margin];size=1<<((n+len(kernel)-2).bit_length())
  dots=np.fft.irfft(np.fft.rfft(b,size)*np.fft.rfft(kernel[::-1],size),size)[len(kernel)-1:n]
  energy=np.r_[0,np.cumsum(b*b)];window=energy[len(kernel):]-energy[:-len(kernel)]
  scores=dots/np.sqrt(np.maximum(np.sum(kernel*kernel)*window,1e-20));idx=int(np.argmax(scores));best=float(scores[idx]);lag=idx-margin;zero=float(scores[margin])
  rows.append(dict(chapter=ch['chapter'],paragraph_id=p['paragraph_id'],raw_audio_sha256=sha(raw),global_start_s=globalstart,raw_start_s=srcstart,duration_s=duration,best_correlation=best,best_lag_samples_at_22050=lag,best_lag_ms=lag/22050*1000,zero_lag_correlation=zero,supports_voice_correspondence=best>.95 and abs(lag)<=220,samples=[dict(path=str(f),sha256=sha(f),bytes=f.stat().st_size) for f in files]))
 d=dict(status='pass' if all(x['supports_voice_correspondence'] for x in rows) else 'required_review',video_sha256=sha(video),timing_sha256=sha(E/'narration/jun-production-v1/final_timing.json'),rows=rows,coverage='각10장 두번째문단의 실제 인코딩 믹스8초와 원본Jun PCM 파형 상관. 전체발화·음질승인 아님.',actual_listening=False,continuous_playback=False)
 (Q/'encoded_voice_correspondence.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(d,ensure_ascii=False))
if __name__=='__main__':main()
