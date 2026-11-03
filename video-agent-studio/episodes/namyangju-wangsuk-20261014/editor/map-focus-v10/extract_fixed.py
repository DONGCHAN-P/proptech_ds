from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[2];o=r/'outputs/map-focus-v10';ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
for kind,frames in [('3',[267,268,300,339,340]),('front',[4949,4950,4951,8189,8190,8191,11069,11070,11071,11337,11338,11370,11409,11410,15749])]:
 expr='+'.join(f'eq(n\\,{n})' for n in frames)
 subprocess.run([ff,'-v','error','-i',str(o/f'map-focus_v10_{kind}.mp4'),'-vf','select='+expr,'-fps_mode','vfr','-y',str(o/f'boundary_{kind}_%03d.png')],check=True)
 for i,n in enumerate(frames):(o/f'boundary_{kind}_{i+1:03}.png').replace(o/f'fixed_{kind}_{n}.png')
print('actual fix and join boundaries ready')
