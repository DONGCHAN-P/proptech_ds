import subprocess,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[2];Q=Path(__file__).parent;O=P/'outputs/shorts-release-v1'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');ff=str(B/'ffmpeg.exe');fp=str(B/'ffprobe.exe')
manifest=json.loads((O/'manifest.json').read_text(encoding='utf8'));report=[]
for m in manifest:
 v=O/(m['id']+'.mp4');out=Q/m['id'];out.mkdir(exist_ok=True)
 sha=hashlib.sha256(v.read_bytes()).hexdigest();assert sha==m['sha256']
 probe=json.loads(subprocess.run([fp,'-v','error','-show_format','-show_streams','-of','json',str(v)],stdout=subprocess.PIPE,check=True).stdout)
 decode=subprocess.run([ff,'-v','error','-i',str(v),'-f','null','NUL'],stderr=subprocess.PIPE)
 assert decode.returncode==0,decode.stderr
 frames=sorted(set([0,1,m['duration_frames']//3,m['duration_frames']//2,m['duration_frames']-2,m['duration_frames']-1]+([1149,1150,1151] if m['id']=='01_rail' else [])))
 for f in frames:
  subprocess.run([ff,'-v','error','-ss',str(f/30),'-i',str(v),'-frames:v','1',str(out/('f'+str(f)+'.png'))],check=True)
 im=Image.new('RGB',(1080,960*((len(frames)+2)//3)),'white');d=ImageDraw.Draw(im)
 for i,f in enumerate(frames):
  shot=Image.open(out/('f'+str(f)+'.png'));shot.thumbnail((360,930));x=i%3*360;y=i//3*960;im.paste(shot,(x,y+25));d.text((x+10,y+5),'f'+str(f),fill='black')
 im.save(out/'contact.png')
 report.append({'id':m['id'],'sha256':sha,'probe':probe,'whole_decode_pass':True,'sample_frames':frames,'actual_listening':False,'continuous_playback':False})
(Q/'technical.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps([{'id':r['id'],'sha256':r['sha256'],'frames_checked':r['sample_frames']} for r in report]))
