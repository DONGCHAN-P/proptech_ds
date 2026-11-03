from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
E=Path('video-agent-studio/episodes/namyangju-wangsuk-20261014');Q=E/'qa/stable-maps-v11/front_actual';F=E/'outputs/stable-maps-v11/stable-maps_v11_front.mp4';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
intervals=[(57,60),(63,66),(75,79),(163,167),(178,182),(272,275),(342,345)]
for a,b in intervals:
 D=Q/('repro_%d_%d'%(a,b));D.mkdir(exist_ok=True)
 r=subprocess.run([str(B),'-v','error','-ss',str(a),'-i',str(F),'-t',str(b-a),'-vf','fps=4,scale=480:270','-y',str(D/'%03d.png')],capture_output=True);assert r.returncode==0,r.stderr
 files=sorted(D.glob('*.png'))
 board=Image.new('RGB',(1920,((len(files)+3)//4)*294),'#ddd');dr=ImageDraw.Draw(board)
 for i,p in enumerate(files):
  x=i%4*480;y=i//4*294;board.paste(Image.open(p),(x,y));dr.text((x+6,y+271),'%.2fs'%(a+i*.25),fill='black')
 board.save(D/'contact.jpg')
print('six dense sequences extracted')
