from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[2];out=r/'outputs/video-review-v8';v=out/'namyangju-landuse_full_v8.mp4';tools=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');ff=str(tools/'ffmpeg.exe');fp=str(tools/'ffprobe.exe')
p=json.loads(subprocess.check_output([fp,'-v','error','-show_streams','-show_format','-of','json',str(v)]));video=next(s for s in p['streams'] if s['codec_type']=='video');assert int(video['nb_frames'])==26720 and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='30/1'
dec=subprocess.run([ff,'-v','error','-i',str(v),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr.strip(),dec.stderr
stats=subprocess.run([ff,'-hide_banner','-i',str(v),'-vn','-af','astats=metadata=0:reset=0','-f','null','-'],capture_output=True,text=True);assert stats.returncode==0,stats.stderr
(out/'audio_astats.txt').write_text(stats.stderr,encoding='utf-8')
import re
peaks=[float(x) for x in re.findall(r'Peak level dB: ([-0-9.]+)',stats.stderr)]
rms=[float(x) for x in re.findall(r'RMS level dB: ([-0-9.]+)',stats.stderr)]
(out/'audio_measurement.json').write_text(json.dumps({'peak_level_dbfs':max(peaks) if peaks else None,'rms_level_dbfs_channels_and_overall':rms,'astats_exit':stats.returncode,'actual_listening':False,'method':'FFmpeg astats full decoded audio stream; no perceptual claim'},indent=2),encoding='utf-8')
frames=[0,45,179,420,916,917,1066,1067,1898,2048,2497,2498,2588,2678,3398,4942,5198,7558,8190,8798,9398,10290,11170,13000,13485,14248,15758,16398,17998,18648,19248,20198,21636,22148,22998,23498,24298,24898,25868,26419,26420,26520,26719]
expr='+'.join(f'eq(n\\,{n})' for n in frames)
subprocess.run([ff,'-v','error','-i',str(v),'-vf','select='+expr,'-fps_mode','vfr','-y',str(out/'actual_%03d.png')],check=True)
for i,n in enumerate(frames):
 src=out/f'actual_{i+1:03}.png';dst=out/f'encoded_{n}.png';src.replace(dst)
d={'file':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'bytes':v.stat().st_size,'whole_decode_exit':dec.returncode,'whole_decode_errors':dec.stderr,'probe':p,'sampled_frames':frames,'actual_listening':False,'continuous_playback':False};(out/'technical_check.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'sha256':d['sha256'],'bytes':d['bytes'],'duration':p['format']['duration'],'frames':video['nb_frames'],'actual_samples':len(frames)},indent=2))
