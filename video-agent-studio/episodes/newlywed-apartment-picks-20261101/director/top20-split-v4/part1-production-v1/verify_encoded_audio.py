"""Check that the actual encoded film carries the approved voice at scene times."""
from pathlib import Path
import argparse,hashlib,json,subprocess,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    a=argparse.ArgumentParser();a.add_argument('--version',required=True);v=a.parse_args().version
    rr=read(D/f'render_receipt_{v}.json');video=Path(rr['output']);assert sha(video)==rr['output_sha256']
    t=read(D/'locked_timing.json');ff=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
    result=subprocess.run([str(ff),'-v','error','-i',str(video),'-vn','-ar','44100','-ac','1','-f','s16le','-'],capture_output=True)
    assert result.returncode==0;encoded=np.frombuffer(result.stdout,dtype='<i2')
    with wave.open(str(R/t['audio_path']),'rb')as w:assert w.getframerate()==44100;source=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
    checks=[]
    for s in t['scenes']:
        start=s['sentences'][0]['start_s']+.7;end=min(start+2.5,s['sentences'][0]['end_s'])
        lo=round(start*44100);hi=round(end*44100)
        x=source[lo:hi].astype(float);y=encoded[lo:hi].astype(float)
        assert len(x)==len(y)and len(x)>1000
        correlation=float(np.corrcoef(x,y)[0,1]);assert correlation>.85,(s['scene_id'],correlation)
        checks.append({'scene_id':s['scene_id'],'start_s':start,'end_s':end,'sample_count':len(x),'pearson_source_voice_to_encoded_mix':correlation})
    peak=int(np.abs(encoded.astype(np.int32)).max());rms=float(np.sqrt(np.mean(encoded.astype(np.float64)**2)))
    assert peak<32767 and rms>200
    report={'status':'passed_signal_alignment','video_sha256':sha(video),'source_voice_sha256':t['audio_sha256'],
            'decoded_samples':len(encoded),'decoded_duration_s':len(encoded)/44100,'peak_pcm':peak,'rms_pcm':rms,
            'peak_dbfs':float(20*np.log10(max(1,peak)/32768)),'checked_scene_windows':checks,
            'actual_listening_performed':False,'continuous_playback_performed':False,
            'scope':'signal correlation proves source voice survives encoding at these twelve windows; no pronunciation/naturalness verdict'}
    out=D/'evidence'/v/'encoded_audio_signal.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'windows':len(checks),'min_correlation':min(x['pearson_source_voice_to_encoded_mix']for x in checks),'peak_dbfs':report['peak_dbfs']}))
if __name__=='__main__':main()
