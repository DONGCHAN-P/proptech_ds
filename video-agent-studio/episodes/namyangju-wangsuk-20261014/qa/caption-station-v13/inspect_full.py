from pathlib import Path
import subprocess,json,numpy as np
from PIL import Image,ImageDraw
Q=Path(__file__).parent/'full_actual'
E=Q.parents[2]
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
F=E/'outputs/caption-station-v13/caption-station_v13_full.mp4'
fr=[15749,15750,15751,15757,15758,15759,26419,26420,26421,26570,26719]
D=Q/'frames';D.mkdir(exist_ok=True)
sel='+'.join('eq(n,%d)'%i for i in fr)
subprocess.run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-vf',"select='"+sel+"'",'-vsync','0','-y',str(D/'seq%03d.png')],check=True,capture_output=True)
board=Image.new('RGB',(1440,4*294),'#ddd');dr=ImageDraw.Draw(board)
for i,f in enumerate(fr,1):
    (D/('seq%03d.png'%i)).rename(D/('f%05d.png'%f))
    im=Image.open(D/('f%05d.png'%f));im.thumbnail((480,270))
    x=(i-1)%3*480;y=(i-1)//3*294
    board.paste(im,(x,y));dr.text((x+4,y+271),str(f),fill='black')
board.save(Q/'joints.jpg')
raw=subprocess.check_output([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-vf','crop=1600:2:150:930,format=gray','-f','rawvideo','-'])
v=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3200).mean(1)
bad=np.flatnonzero(v<250)
unexpected=[int(i) for i in bad if not(i<45 or 917<=i<1067 or i>=26420)]
r={'frames':len(v),'expected_no_box_ranges':[[0,45],[917,1067],[26420,26720]],'unexpected_missing_white':unexpected,'outro_white_frames':int((v[26420:]>250).sum()),'actual_frames':fr}
(Q/'caption_roi.json').write_text(json.dumps(r,indent=2));print(r)
