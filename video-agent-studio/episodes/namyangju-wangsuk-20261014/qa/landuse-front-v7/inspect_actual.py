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
frames=[0,110,111,668,669,1499,1500,1650,2008,2009,2400,3000,4543,4544,4560,4800,7791,7792,8400,8803,8804,8840,9000,9305,9306,9891,9892,10200,10500,10670,10850,11150,12200,12500,13080,13086]
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
