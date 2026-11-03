from pathlib import Path
import subprocess,json
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/readability-cta-v15';F='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
for s in [88,165,188,801]:
 subprocess.run([F,'-v','error','-y','-ss',str(s),'-i',str(EP/'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4'),'-frames:v','1',str(O/f'baseline_{s}s.png')],check=True)
print('baseline frames extracted')
