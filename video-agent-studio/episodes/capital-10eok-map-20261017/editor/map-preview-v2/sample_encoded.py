from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw
E=Path('video-agent-studio/episodes/capital-10eok-map-20261017');O=E/'outputs/map-preview-v2';F=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe');v=O/'style_preview_6s.mp4';frames=[]
for label,t in [('start',0),('middle',2.5),('last',4.5),('cut_before',1.966667),('cut_after',2.0)]:
 out=O/f'encoded_{label}.png';subprocess.run([str(F),'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out)],check=True);frames.append({'time':t,'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
contact=Image.new('RGB',(1080,760),'#f6f4ef')
for i,name in enumerate(['encoded_start.png','encoded_middle.png','encoded_last.png']):
 im=Image.open(O/name);im=im.crop((136,428,836,1180)).resize((350,376),Image.Resampling.LANCZOS);contact.paste(im,(i*360,30))
contact.save(O/'encoded_contact_sheet.png');(O/'encoded_frame_samples.json').write_text(json.dumps({'video':v.name,'samples':frames,'continuous_playback':False,'audio_absent':True},indent=2),encoding='utf8')
