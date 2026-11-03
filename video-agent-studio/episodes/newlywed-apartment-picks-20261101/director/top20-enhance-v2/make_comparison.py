"""Compare decoded old/new MP4 pixels at three unchanged regional timestamps."""
from pathlib import Path
import json,subprocess,sys
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
sys.path.insert(0,str(R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/image-deps'))
from PIL import Image,ImageDraw,ImageFont
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
old=R/json.loads((D/'previous_state.json').read_text(encoding='utf-8'))['video']
rec=json.loads((E/'editor/top20-enhance-v2/render_receipt_main_v1.json').read_text(encoding='utf-8'));new=Path(rec['output'])
out=E/'outputs/top20-enhance-v2';evi=D/'evidence/comparison';evi.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',27)
sheet=Image.new('RGB',(1920,3*592),(246,244,239));draw=ImageDraw.Draw(sheet)
for i,(t,label)in enumerate([(85,'사진 중심 · 인천 연수구'),(252,'옆 순위 비교 · 인천 미추홀구'),(416,'상위권 · 인천 옛 서구')]):
 for col,source,name in [(0,old,'기존'),(1,new,'수정')]:
  p=evi/f'{i}-{name}.jpg';cp=subprocess.run([str(FF),'-v','error','-ss',str(t),'-i',str(source),'-frames:v','1','-q:v','2','-y',str(p)],capture_output=True)
  assert cp.returncode==0 and p.exists()
  im=Image.open(p).convert('RGB').resize((960,540))
  draw.text((col*960+20,i*592+10),f'{name} | {label} | {t}초',font=font,fill=(23,51,72))
  sheet.paste(im,(col*960,i*592+48))
p=out/'비주얼_전후비교.jpg';sheet.save(p,quality=92);print(str(p))
