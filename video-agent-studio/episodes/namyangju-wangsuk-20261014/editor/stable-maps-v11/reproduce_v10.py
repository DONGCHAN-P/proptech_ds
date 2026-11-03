from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw,ImageChops,ImageStat
EP=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
V=EP/'outputs/map-focus-v10/map-focus_v10_front.mp4'
FF='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
records=[]
for name,start,duration in [('around_64',62.75,3.5),('around_165',164,4),('around_180',179,5)]:
 dst=OWN/name;dst.mkdir(exist_ok=True)
 subprocess.run([FF,'-v','error','-ss',str(start),'-i',str(V),'-t',str(duration),'-vf','fps=4,scale=960:540','-y',str(dst/'dense_%03d.png')],check=True)
 frames=sorted(dst.glob('dense_*.png'));board=Image.new('RGB',(1920,290*((len(frames)+3)//4)),(240,240,240));means=[];prev=None
 for i,p in enumerate(frames):
  im=Image.open(p).convert('RGB');roi=im.crop((40,95,920,420))
  if prev is not None:means.append(sum(ImageStat.Stat(ImageChops.difference(roi,prev)).mean)/3)
  prev=roi;thumb=im.resize((480,270));x=(i%4)*480;y=(i//4)*290;board.paste(thumb,(x,y));ImageDraw.Draw(board).text((x+8,y+272),f'{start+i/4:.2f}s',fill=(0,0,0))
 board.save(OWN/f'{name}_contact.png');records.append({'source':str(V),'range_s':[start,start+duration],'fps_sampled':4,'frames':len(frames),'map_roi_difference_means':means,'contact':str(OWN/f'{name}_contact.png')})
(OWN/'dense_reproduction.json').write_text(json.dumps({'method':'actual MP4 sampled at4fps; map ROI excludes subtitle area; not continuous playback','intervals':records},indent=2),encoding='utf-8')
print('dense reproduction ready')
