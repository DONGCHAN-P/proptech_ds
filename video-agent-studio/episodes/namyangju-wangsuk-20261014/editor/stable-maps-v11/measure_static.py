from pathlib import Path
import subprocess,numpy as np,json,sys
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/stable-maps-v11';stage=sys.argv[1] if len(sys.argv)>1 else 'rail'
FF='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
p=subprocess.Popen([FF,'-v','error','-i',str(OUT/f'stable-maps_v11_{stage}.mp4'),'-vf','crop=1920:912:0:0,scale=480:228,format=gray','-f','rawvideo','-'],stdout=subprocess.PIPE)
previous=None;d=[];held=[];i=0;cuts=[]
while True:
 raw=p.stdout.read(480*228)
 if len(raw)!=480*228:break
 a=np.frombuffer(raw,dtype=np.uint8).astype(np.int16)
 if previous is not None:
  diff=np.abs(a-previous);mean=float(diff.mean());d.append(mean)
  if mean>1 and (stage=='rail' or i>=1068):cuts.append({'frame':i,'mean_abs_pixel_difference':mean})
 if previous is not None and (stage=='rail' or i>=1068) and i not in [1750,2305,4942,8190,10290]:held.append(mean)
 previous=a;i+=1
assert p.wait()==0
result={'file':f'stable-maps_v11_{stage}.mp4','decoded_frames':i,'roi':'top 1920x912 excludes subtitle bar','comparison':'every consecutive decoded frame, grayscale 480x228','max_mean_abs_difference':max(d),'mean_difference':float(np.mean(d)),'max_hold_mean_difference':max(held),'map_analysis_start_frame':1068 if stage=='front' else 0,'over_1_candidates':cuts,'codec_noise_not_motion':True,'actual_listening':False,'expected_static_boundaries_frames':([1750,2305,4942,8190,10290] if stage=='front' else []),'minimum_static_hold_s':18.5}
(OUT/f'dense_static_{stage}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
