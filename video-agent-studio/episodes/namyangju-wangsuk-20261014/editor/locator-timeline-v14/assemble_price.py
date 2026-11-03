from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2]
O=EP/'outputs/locator-timeline-v14'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
F=str(B/'ffmpeg.exe'); P=str(B/'ffprobe.exe')
base=EP/'outputs/caption-station-v13/caption-station_v13_full.mp4'
target=O/'region_prices_v14_M007.mp4'
args=[F,'-v','error','-y','-ss',str(15758/30),'-i',str(base),'-loop','1','-framerate','30','-i',str(O/'price_plate.png'),'-filter_complex','[1:v]crop=1920:920:0:0[plate];[0:v][plate]overlay=0:0:shortest=1[v]','-map','[v]','-map','0:a:0','-frames:v','2890','-t',str(2890/30),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(target)]
subprocess.run(args,check=True)
probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(target)]))
v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==2890
subprocess.run([F,'-v','error','-i',str(target),'-f','null','-'],check=True)
for frame in [0,1,300,1500,2888,2889]:
 subprocess.run([F,'-v','error','-y','-i',str(target),'-vf',f'select=eq(n\,{frame})','-frames:v','1',str(O/f'actual_price_{frame}.png')],check=True)
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':2890,'original_frame_range':[15758,18648],'duration_s':2890/30,'whole_decode_passed':True,'probe':probe,'audio':'original v13 AAC stream copied at chapter cut; no new TTS','captions':'original burned captions preserved below y=920','actual_listening':False,'continuous_playback':False}
(O/'technical_price.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:r[k] for k in ['file','sha256','video_frames']}))
