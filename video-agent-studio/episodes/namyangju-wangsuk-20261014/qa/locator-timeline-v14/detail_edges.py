import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[2];q=Path(__file__).parent/'detail_actual'
m=json.loads((q/'motion_audit.json').read_text())
edges=sorted(set(m['motion_candidate_frames'])-set(m['cut_candidate_frames']))
frames=sorted(set(f for e in edges for f in [e-1,e]))
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
expr='+'.join('eq(n\\,%d)'%f for f in frames)
subprocess.run([ff,'-v','error','-i',str(p/'outputs/locator-timeline-v14/landuse_locator_timeline_v14.mp4'),'-vf','select='+expr+',scale=640:360','-fps_mode','vfr',str(q/'edge_%03d.png')],check=True)
fs=sorted(q.glob('edge_*.png'))
for i in range(0,len(fs),12):
 im=Image.new('RGB',(1280,2310),'white');d=ImageDraw.Draw(im)
 for j,f in enumerate(fs[i:i+12]):
  x=j%2*640;y=j//2*385
  im.paste(Image.open(f),(x,y+25));d.text((x+10,y+6),'global '+str(frames[i+j]+8190),fill='black')
 im.save(q/('extra_board_%d.png'%(i//12)))
print(json.dumps({'frames':frames,'count':len(fs)}))
