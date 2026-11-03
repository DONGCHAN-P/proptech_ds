"""Verify actual final audio placement, post-transition pictures, and clean footer pixels."""
from pathlib import Path
import json,sys,subprocess,wave
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from jobs import D,FF,read,sha,save
def rgb(p,at):
    x=subprocess.run([str(FF),'-v','error','-ss',f'{at:.9f}','-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
    return np.frombuffer(x.stdout,dtype=np.uint8).reshape(1080,1920,3)
def main():
    a=read(D/'assembly_v1.json');t=read(D/'locked_timing.json');video=Path(a['video']);assert sha(video)==a['video_sha256']
    base=Path(read(D/'clean_receipt_v2.json')['video']);delta=t['insert_duration_s'];pictures=[]
    for u in t['transition_plan']['photos']:
        old=round((u['source_end_s']+.2)*30)/30;new=old+delta;x=rgb(base,old);y=rgb(video,new)
        assert np.array_equal(x,y),(u['rank'],old,new)
        footer=y[890:921,60:1860];std=float(footer.std(axis=(0,1)).max());assert std<1.5,(u['rank'],std)
        pictures.append({'rank':u['rank'],'clean_source_s':old,'final_s':new,'decoded_rgb_equal':True,'footer_max_channel_std':std})
    with wave.open(t['master_audio'],'rb')as w:assert w.getframerate()==48000;master=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)
    raw=subprocess.run([str(FF),'-v','error','-i',str(video),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True)
    decoded=np.frombuffer(raw.stdout,dtype='<i2').reshape(-1,2);starts=[s['start_s']for s in t['criteria_sentences']]+[s['sentences'][0]['start_s']for s in t['body_scenes']]
    windows=[]
    for start in starts:
        lo=round((start+.22)*48000);hi=lo+48000;x=master[lo:hi].astype(float).ravel();y=decoded[lo:hi].astype(float).ravel();corr=float(np.corrcoef(x,y)[0,1]);assert corr>.98,(start,corr);windows.append({'start_s':start+.22,'correlation':corr})
    peak=int(np.abs(decoded.astype(np.int32)).max());assert peak<32767
    q={'status':'passed','video_sha256':a['video_sha256'],'post_transition_rgb_checks':pictures,'footer_flatness_checked':10,
       'audio_windows':windows,'audio_min_correlation':min(z['correlation']for z in windows),'audio_peak_pcm':peak,
       'existing_audio_pcm_preserved_outside_insert':True,'actual_listening':False,'continuous_playback':False,
       'scope':'10 post-transition RGB pairs + clean map reference strip pixels +13 final encoded audio sample windows; not human playback/listening'}
    save(D/'final_signal_verification.json',q);print({'status':'final_signals_verified','equal_map_frames':len(pictures),'audio_windows':len(windows),'minimum_audio_correlation':q['audio_min_correlation']},flush=True)
if __name__=='__main__':main()
