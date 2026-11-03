import json,subprocess,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
Q=Path(__file__).resolve().parent/sys.argv[2]; Q.mkdir(exist_ok=True); E=Q.parents[1]
F=Path(sys.argv[1]);B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
sha=hashlib.sha256(F.read_bytes()).hexdigest()
def run(args):
 r=subprocess.run(args,capture_output=True);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout
probe=json.loads(run([str(B/'ffprobe.exe'),'-v','error','-show_format','-show_streams','-of','json',str(F)]))
modes={'front':[0,210,917,2048,4949,4950,4951,8189,8190,8191,11069,11070,11071,11370,15270,15749], 'part1':[0,150,534,570,640,692,800,942,970,1050,1150,1264,1450,2150,2700,2770,3239], 'part2':[0,450,595,800,1012,1040,1120,1514,1600,2100,2205,2488,2500,2593,2879], 'part3':[0,30,220,300,602,640,720,933,1000,1219,1240,1324,1600,2415,2500,2730,2885,3100,3463,3600,4056,4200,4300,4679]};frames=modes[sys.argv[2]]
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

