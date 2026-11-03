from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
E=Path('video-agent-studio/episodes/capital-10eok-map-20261017');O=E/'outputs/map-preview-v3';fo=ImageFont.truetype(str(E/'visual/map-preview-v1/Pretendard-Bold.ttf'),18)
for year in [2006,2025,2026]:
 im=Image.open(O/f'year_{year}.png');im.resize((375,667),Image.Resampling.LANCZOS).save(O/f'phone375_{year}.png')
a=Image.open(E/'outputs/map-preview-v2/year_2026.png').resize((375,667),Image.Resampling.LANCZOS);b=Image.open(O/'phone375_2026.png');canvas=Image.new('RGB',(766,710),'#111827');d=ImageDraw.Draw(canvas);d.text((10,10),'v2: 375px',font=fo,fill='white');d.text((394,10),'v3: 375px',font=fo,fill='white');canvas.paste(a,(0,38));canvas.paste(b,(391,38));canvas.save(O/'phone375_v2_vs_v3.png')
