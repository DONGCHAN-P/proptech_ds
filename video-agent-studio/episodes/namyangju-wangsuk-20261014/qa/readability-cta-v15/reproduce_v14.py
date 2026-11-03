from pathlib import Path
import subprocess,json
P=Path(__file__).resolve().parents[2];Q=Path(__file__).parent
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
frames=[2640,4950,5639,5640,5641,6150,24030]
for n in frames:
 subprocess.run([ff,'-v','error','-ss',str(n/30),'-i',str(P/'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4'),'-frames:v','1',str(Q/('v14_'+str(n)+'.png'))],check=True)
(Q/'reproduction.json').write_text(json.dumps({'base_sha256':'ba5bcfdc625f3c15b3f13548f43696e6f7d8b0579c8f8374d46df7d2083966f1','actual_frames':frames,'actual_listening':False,'continuous_playback':False}),encoding='utf8')
