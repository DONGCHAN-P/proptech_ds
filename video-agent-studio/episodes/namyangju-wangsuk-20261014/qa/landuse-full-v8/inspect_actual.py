import json,subprocess,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
Q=Path(__file__).resolve().parent; E=Q.parents[1]
F=Path(sys.argv[1]);B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
sha=hashlib.sha256(F.read_bytes()).hexdigest()
def run(args):
 r=subprocess.run(args,capture_output=True);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout
probe=json.loads(run([str(B/'ffprobe.exe'),'-v','error','-show_format','-show_streams','-of','json',str(F)]))
frames=[0, 45, 90, 210, 425, 500, 690, 850, 916, 917, 1066, 1067, 1737, 1897, 1898, 1918, 2048, 2248, 2406, 2407, 2497, 2498, 2499, 2543, 2548, 2587, 2588, 2589, 2633, 2648, 2678, 3674, 4941, 4942, 4958, 5198, 6566, 7348, 8189, 8190, 8198, 8798, 9240, 9398, 10289, 10290, 10598, 11548, 11887, 13484, 13485, 13619, 14248, 14621, 15757, 15758, 17041, 17203, 17764, 18647, 18648, 20142, 21635, 21636, 21798, 22148, 23752, 24898, 25867, 25868, 26144, 26398, 26419, 26420, 26450, 26570, 26719]
D=Q/'actual';D.mkdir(exist_ok=True)
sel='+'.join('eq(n,%d)'%f for f in frames)
run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-vf',"select='"+sel+"'",'-vsync','0','-y',str(D/'seq_%03d.png')])
for i,f in enumerate(frames,1):(D/('seq_%03d.png'%i)).rename(D/('frame_%05d.png'%f))
# A white top strip inside the fixed caption panel, away from text/rounded corners.
raw=run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-vf','crop=1600:2:150:930,format=gray','-f','rawvideo','-'])
a=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3200)
means=a.mean(axis=1); bad=np.flatnonzero(means<250).tolist()
for start in range(0,len(frames),8):
 board=Image.new('RGB',(1280,4*202),'#ddd');dr=ImageDraw.Draw(board)
 for j,f in enumerate(frames[start:start+8]):
  im=Image.open(D/('frame_%05d.png'%f));im.thumbnail((640,180));x=(j%2)*640;y=(j//2)*202;board.paste(im,(x,y));dr.text((x+5,y+181),str(f)+' / '+str(round(f/30,3))+'s',fill='black')
 board.save(Q/('board_%02d.jpg'%(start//8+1)))
r={'sha256':sha,'bytes':F.stat().st_size,'probe':probe,'frames':frames,'white_caption_roi':{'xywh':[150,930,1600,2],'decoded_frames':len(a),'min_frame_mean':float(means.min()),'threshold':250,'failed_frames':bad},'actual_listening':False,'continuous_playback':False}
(Q/'actual_check.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps({'sha256':sha,'sample_frames':len(frames),'ROI_frames':len(a),'ROI_failed':len(bad)}))
