from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/locator-timeline-v14'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe');base=EP/'outputs/caption-station-v13/caption-station_v13_full.mp4'
reports=[]
for name,start,end in [('OutsideDatesV14',18648,21636)]:
 target=O/(name+'.mp4');src=O/(name+'_video.mp4');assert src.exists()
 subprocess.run([F,'-v','error','-y','-i',str(src),'-ss',str(start/30),'-i',str(base),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str((end-start)/30),'-movflags','+faststart',str(target)],check=True)
 probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(target)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==end-start
 subprocess.run([F,'-v','error','-i',str(target),'-f','null','-'],check=True)
 for frame in sorted({0,1,end-start-2,end-start-1,300,(end-start)//2}):subprocess.run([F,'-v','error','-y','-i',str(target),'-vf',f'select=eq(n\,{frame})','-frames:v','1',str(O/f'actual_{name}_{frame+start}.png')],check=True)
 reports.append({'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'original_frame_range':[start,end],'video_frames':end-start,'whole_decode_passed':True,'probe':probe})
(O/'technical_outside_corrected.json').write_text(json.dumps({'clips':reports,'new_tts':False,'actual_listening':False,'continuous_playback':False},indent=2),encoding='utf-8');print(json.dumps([{k:x[k] for k in ['file','sha256','video_frames']} for x in reports]))
