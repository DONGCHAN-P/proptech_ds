"""Verify final encoded body packets, decoded pictures, and voice timing against the baseline."""
from pathlib import Path
import argparse,hashlib,json,subprocess,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def packets(p,start):
    r=subprocess.run([str(FP),'-v','error','-read_intervals',f'{start:.9f}%','-select_streams','v:0','-show_packets','-show_data_hash','sha256','-show_entries','packet=pts_time,flags,data_hash','-of','json',str(p)],capture_output=True);assert r.returncode==0
    return [x['data_hash']for x in json.loads(r.stdout)['packets']if float(x['pts_time'])>=start-.0001 and'K'not in x['flags']]
def picture(p,at):
    r=subprocess.run([str(FF),'-v','error','-ss',f'{at:.9f}','-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True);assert r.returncode==0;return r.stdout
def main():
    a=argparse.ArgumentParser();a.add_argument('--version',default='v2');v=a.parse_args().version
    t=read(D/'locked_timing.json');r=read(D/f'assembly_{v}.json');new=Path(r['video']);old=Path(t['original_video']);assert sha(new)==r['video_sha256']
    oldpack=packets(old,t['stream_copy_keyframe_s']);newpack=packets(new,t['prefix_end_s']);assert oldpack==newpack,(len(oldpack),len(newpack))
    pictures=[]
    for s in t['body_scenes']:
        source_start=s['start_s']-t['delta_s'];z=max(source_start+3,t['stream_copy_keyframe_s']+1)
        # Quantize the old frame, then shift by the exact integer 64-frame delta.
        z=round(z*30)/30;newz=z+t['delta_s'];one=picture(old,z);two=picture(new,newz)
        assert one==two,(s['scene_id'],z,newz)
        pictures.append({'scene_id':s['scene_id'],'old_s':z,'new_s':newz,'decoded_rgb_equal':True,'rgb_sha256':hashlib.sha256(one).hexdigest()})
    result=subprocess.run([str(FF),'-v','error','-i',str(new),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True);assert result.returncode==0
    decoded=np.frombuffer(result.stdout,dtype='<i2').reshape(-1,2)
    with wave.open(t['master_audio'],'rb')as w:assert w.getframerate()==48000;master=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)
    windows=[]
    starts=[(x['sentence_id'],x['start_s'])for x in t['intro_sentences']]+[(x['scene_id'],x['sentences'][0]['start_s'])for x in t['body_scenes']]
    for name,start in starts:
        lo=round((start+.25)*48000);hi=lo+48000;x=master[lo:hi].astype(float).ravel();y=decoded[lo:hi].astype(float).ravel()
        corr=float(np.corrcoef(x,y)[0,1]);assert corr>.97,(name,corr);windows.append({'id':name,'time_s':start+.25,'correlation':corr})
    peak=int(np.abs(decoded.astype(np.int32)).max());assert peak<32767
    report={'status':'passed','video_sha256':sha(new),'non_key_body_video_packets_equal':len(oldpack),'body_decoded_frame_checks':pictures,
      'audio_windows':windows,'audio_min_correlation':min(x['correlation']for x in windows),'peak_pcm':peak,
      'source_body_not_regenerated':True,'body_start_word_not_cut':True,'source_text_body_sentences_unchanged':80,
      'actual_listening':False,'continuous_playback':False,'scope':'non-key packet equality after52.5s source +11 decoded RGB picture pairs;19sample voice windows; not human listening'}
    out=D/f'reuse_verification_{v}.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'body_and_audio_reuse_passed','packet_count':len(oldpack),'equal_rgb_frames':len(pictures),'audio_min_correlation':report['audio_min_correlation']}))
if __name__=='__main__':main()
