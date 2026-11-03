from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/locator-timeline-v14'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
v=O/'landuse_locator_timeline_v14.mp4';base=EP/'outputs/caption-station-v13/caption-station_v13_full.mp4'
subprocess.run([F,'-v','error','-y','-i',str(O/'landuse_locator_timeline_v14_video.mp4'),'-ss','273','-i',str(base),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(7568/30),'-movflags','+faststart',str(v)],check=True)
probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(v)]));vs=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(vs['nb_frames'])==7568
subprocess.run([F,'-v','error','-i',str(v),'-f','null','-'],check=True)
boundaries=[8190,8703,8794,9202,9704,10290,10678,11026,11170,11672,12003,12289,12694,13485,14104,14214,14533,14793,15126,15758]
frames=sorted({0,1,7566,7567,2180,3000,*[n-8190+d for n in boundaries for d in [-1,0,1] if 0<=n-8190+d<7568]})
for f in frames:subprocess.run([F,'-v','error','-y','-i',str(v),'-vf',f'select=eq(n\,{f})','-frames:v','1',str(O/f'actual_detail_{f+8190}.png')],check=True)
r={'file':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'video_frames':7568,'duration_s':7568/30,'original_frame_range':[8190,15758],'whole_decode_passed':True,'probe':probe,'known_state_boundaries_global':boundaries,'actual_frames_inspected_pending':frames,'audio':'original AAC stream copied','actual_listening':False,'continuous_playback':False}
(O/'technical_detail.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:r[k] for k in ['file','sha256','video_frames']}))
