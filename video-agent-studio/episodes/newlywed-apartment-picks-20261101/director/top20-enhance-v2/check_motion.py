"""Nine decoded frames across one 0.6-second comparison reveal, not playback."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
H=E/'editor/top20-enhance-v2';rec=json.loads((H/'render_receipt_main_v1.json').read_text(encoding='utf-8'));video=Path(rec['output'])
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
out=D/'evidence/motion';out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',21)
sheet=Image.new('RGB',(1530,3*175),(246,244,239));draw=ImageDraw.Draw(sheet)
times=[241.8+i*.1 for i in range(9)]
for i,t in enumerate(times):
 p=out/f'{t:.3f}.jpg';cp=subprocess.run([str(FF),'-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2','-y',str(p)],capture_output=True)
 assert cp.returncode==0 and p.exists()
 im=Image.open(p).crop((830,270,1850,540)).resize((510,135));x=(i%3)*510;y=(i//3)*175
 draw.text((x+10,y+4),f'{t:.3f}s',font=font,fill=(23,51,72));sheet.paste(im,(x,y+35))
sheet.save(out/'count_reveal_strip.jpg',quality=93)
(out/'manifest.json').write_text(json.dumps({'video_sha256':rec['output_sha256'],'times_s':times,'scene_id':'S013','source_anchor_local_s':1.75,'nominal_motion_duration_s':.6,'scope':'nine decoded frames; not continuous playback or hearing'},ensure_ascii=False,indent=2),encoding='utf-8')
print(str(out/'count_reveal_strip.jpg'))
