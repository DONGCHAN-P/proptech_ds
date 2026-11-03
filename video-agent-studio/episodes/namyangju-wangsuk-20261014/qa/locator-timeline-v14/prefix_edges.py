from pathlib import Path
import json,subprocess,sys
from PIL import Image,ImageDraw
Q=Path(__file__).parent/sys.argv[2]
F=Path(sys.argv[1]);d=json.loads((Q/'motion_audit.json').read_text())
cuts=sorted(set(d['cut_candidate_frames']+[0,44,45,916,917,1066,1067,2407,4942,8190,15758,18648,21635]))
fr=sorted(set(n+k for n in cuts for k in [-1,0,1] if 0<=n+k<d['decoded_frames']))
D=Q/'edges';D.mkdir(exist_ok=True)
B='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
for off in range(0,len(fr),40):
 batch=fr[off:off+40];sel='+'.join('eq(n,%d)'%n for n in batch)
 r=subprocess.run([B,'-v','error','-i',str(F),'-vf',"select='"+sel+"',scale=960:540",'-vsync','0','-y',str(D/'seq%03d.png')],capture_output=True)
 assert r.returncode==0,r.stderr
 for i,n in enumerate(batch,1):(D/('seq%03d.png'%i)).rename(D/('f%05d.png'%n))
for start in range(0,len(cuts),5):
 board=Image.new('RGB',(1440,5*294),'#ddd');dr=ImageDraw.Draw(board)
 for row,n in enumerate(cuts[start:start+5]):
  for col,k in enumerate([-1,0,1]):
   if n+k not in fr:continue
   im=Image.open(D/('f%05d.png'%(n+k)));im.thumbnail((480,270));x=col*480;y=row*294;board.paste(im,(x,y));dr.text((x+5,y+271),'frame%d %.4fs'%(n+k,(n+k)/30),fill='black')
 board.save(Q/('edges_%02d.jpg'%(start//5+1)))
(Q/'edges_manifest.json').write_text(json.dumps({'cut_edges':cuts,'sample_frames':fr,'sample_frame_count':len(fr),'boards':(len(cuts)+4)//5},indent=2))
print(json.dumps({'cuts':len(cuts),'frames':len(fr),'boards':(len(cuts)+4)//5}))
