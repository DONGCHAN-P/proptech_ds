import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
Q=Path(__file__).parent
F=Path(sys.argv[1]);BASE=Path(sys.argv[2])
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def run(args):
 r=subprocess.run(args,capture_output=True);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout
frames=[0,1920,1927,2100,2107,2280,2560,5100,5483,5484,5491,5499,5506,5514,5521,5538,5641,5642,5891,5892,5899,5910,5946,6100,6213,6214,7100,7474,7481,7504,7598,7605,7630,7720,8640,9000,10500,10507,10610,10617,10678,10685,10690,10708,10732,11370,15270,15749]
def extract(file,tag,fr):
 D=Q/tag;D.mkdir(exist_ok=True);sel='+'.join('eq(n,%d)'%f for f in fr)
 run([str(B/'ffmpeg.exe'),'-v','error','-i',str(file),'-vf',"select='"+sel+"'",'-vsync','0','-y',str(D/'seq%03d.png')])
 for i,f in enumerate(fr,1):(D/('seq%03d.png'%i)).rename(D/('f%05d.png'%f))
 return D
D=extract(F,'actual',frames)
compare=[8640,9000,10500,10610,11370,15270]
OLD=extract(BASE,'v10_baseline',compare)
diff=[]
for f in compare:
 a=np.asarray(Image.open(D/('f%05d.png'%f)).convert('RGB')).astype(np.int16)
 b=np.asarray(Image.open(OLD/('f%05d.png'%f)).convert('RGB')).astype(np.int16)
 delta=np.abs(a-b);diff.append({'frame':f,'whole_mean_abs_delta':float(delta.mean()),'caption_mean_abs_delta':float(delta[922:1052].mean()),'map_mean_abs_delta':float(delta[190:840,80:1840].mean())})
for start in range(0,len(frames),8):
 board=Image.new('RGB',(1280,4*382),'#ddd');dr=ImageDraw.Draw(board)
 for i,f in enumerate(frames[start:start+8]):
  im=Image.open(D/('f%05d.png'%f));im.thumbnail((640,360));x=i%2*640;y=i//2*382;board.paste(im,(x,y));dr.text((x+5,y+361),'%d / %.3fs'%(f,f/30),fill='black')
 board.save(Q/('board_%02d.jpg'%(start//8+1)))
raw=run([str(B/'ffmpeg.exe'),'-v','error','-i',str(F),'-vf','crop=1600:2:150:930,format=gray','-f','rawvideo','-'])
means=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3200).mean(axis=1)
probe=json.loads(run([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(F)]))
r={'sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'bytes':F.stat().st_size,'probe':probe,'sample_frames':frames,'v10_comparison':diff,'white_roi_frames':len(means),'white_roi_failed':np.flatnonzero(means<250).tolist(),'actual_listening':False,'continuous_playback':False}
(Q/'actual_check.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps({'sha256':r['sha256'],'samples':len(frames),'whitefail':len(r['white_roi_failed']),'comparison':diff}))
