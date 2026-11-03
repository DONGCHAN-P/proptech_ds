"""Measure decoded mix/reference correspondence without claiming to listen."""
from pathlib import Path
import json,math,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[1]
Q=E/'qa/top20-explain-v3/production/encoded-v1'
def main():
    segments=[]; totals=np.zeros(5,dtype=np.float64)
    with wave.open(str(Q/'final_mix.wav'),'rb') as mix,wave.open(str(Q/'reference_voice_48k.wav'),'rb') as ref:
        assert mix.getframerate()==ref.getframerate()==48000
        assert mix.getsampwidth()==ref.getsampwidth()==2
        offset=0; rate=48000; peak=0; clipped=0
        while True:
            ab=mix.readframes(rate*2);bb=ref.readframes(rate*2)
            if not ab or not bb:break
            a=np.frombuffer(ab,dtype='<i2').reshape(-1,mix.getnchannels())
            b=np.frombuffer(bb,dtype='<i2').reshape(-1,ref.getnchannels())
            n=min(len(a),len(b));a=a[:n];b=b[:n]
            peak=max(peak,int(np.abs(a.astype(np.int32)).max()));clipped+=int((np.abs(a.astype(np.int32))>=32767).sum())
            x=b.mean(axis=1,dtype=np.float64)/32768;y=a.mean(axis=1,dtype=np.float64)/32768
            xx=float(x@x);yy=float(y@y);xy=float(x@y);rr=float((y-x)@(y-x))
            totals+=np.array([xx,yy,xy,rr,n])
            segments.append({'start_s':offset/rate,'duration_s':n/rate,'mix_rms':math.sqrt(yy/n),'reference_rms':math.sqrt(xx/n),'residual_rms':math.sqrt(rr/n),'gain_to_reference':xy/xx if xx else None})
            offset+=n
    xx,yy,xy,rr,n=totals
    result={'scope':'decoded final AAC mix versus 48k reference narration, signal comparison only','video_sha256':'80b7cd14b0fa15de21a696796b2a996f0fa47e29ad02ab067ab8ca20448220d1','compared_seconds':n/48000,'max_sample_dbfs':20*math.log10(peak/32768),'clipped_samples':clipped,'reference_gain':xy/xx,'uncentred_correlation':xy/math.sqrt(xx*yy),'residual_rms':math.sqrt(rr/n),'segments':segments,'actual_listening_performed':False}
    (D/'evidence/final_mix_signal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='segments'},ensure_ascii=False))
if __name__=='__main__':main()
