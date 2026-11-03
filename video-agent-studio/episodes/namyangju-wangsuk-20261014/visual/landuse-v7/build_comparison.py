from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
P=Path(__file__).parent;E=P.parents[1]
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',28)
for prefix,source in [('w2',P/'w2_internal_reference.png'),('w1_north',E/'research/landuse-v7/source_assets/w1_north_detail_reference.png')]:
 own=P/f'{prefix}_board.png'
 if not source.exists() or not own.exists():continue
 canvas=Image.new('RGB',(1500,1300),'white');d=ImageDraw.Draw(canvas)
 for x,label,path in [(0,'공식 원본 대조용 (최종 삽입 아님)',source),(750,'직접 정리한 주요 용도·배치 도해',own)]:
  d.text((x+20,20),label,font=font,fill='#203345');im=Image.open(path).convert('RGB');im.thumbnail((730,1200));canvas.paste(im,(x+(750-im.width)//2,80))
 canvas.save(P/f'{prefix}_source_comparison.png')
