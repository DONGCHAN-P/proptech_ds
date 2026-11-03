from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import json,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2]
OUT=EP/'outputs/jun-quality-v2/thumbnail';OUT.mkdir(parents=True,exist_ok=True)
fonts=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/visual/map-preview-v1'
font=lambda s:ImageFont.truetype(str(fonts/'Pretendard-Bold.ttf'),s)
im=Image.new('RGB',(1920,1080),'#f6f4ef');d=ImageDraw.Draw(im)
d.rounded_rectangle((45,45,1875,1035),45,fill='#f6f4ef',outline='#173348',width=4)
d.rounded_rectangle((104,95,680,185),45,fill='#173348')
d.text((145,112),'현금 1억부터 5억까지',font=font(48),fill='white')
d.text((100,245),'내 돈으로',font=font(120),fill='#173348')
d.text((100,405),'얼마짜리 집?',font=font(136),fill='#286cda')
d.text((110,615),'현금 + 대출 − 남겨둘 돈',font=font(52),fill='#607680')
house=Image.open(EP/'visual/jun-user-script-v1/outputs/S02_house_cutout_AI.png').convert('RGBA')
house.thumbnail((740,650),Image.Resampling.LANCZOS)
shadow=Image.new('RGBA',im.size,(0,0,0,0));sd=ImageDraw.Draw(shadow)
sd.ellipse((1155,770,1775,850),fill=(23,51,72,32));shadow=shadow.filter(ImageFilter.GaussianBlur(28))
im=Image.alpha_composite(im.convert('RGBA'),shadow);im.alpha_composite(house,(1070,200))
d=ImageDraw.Draw(im)
d.rounded_rectangle((1150,795,1740,930),32,fill='#173348')
d.text((1230,815),'내 집 예산 = ?',font=font(67),fill='white')
d.rounded_rectangle((105,825,905,945),30,fill='#e4ebf5')
d.text((145,845),'집값보다 월 부담까지',font=font(58),fill='#173348')
im=im.convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
im.save(OUT/'thumbnail.png',optimize=True)
im.resize((320,180),Image.Resampling.LANCZOS).save(OUT/'mobile_preview.jpg',quality=93)
meta={'title':'현금 1억부터 5억까지, 얼마짜리 집을 살 수 있을까?｜대출·세금·월 부담 계산',
 'concept':'내 현금과 매물 가격을 연결하는 질문. 썸네일은 실제 사례와 계산 순서를 약속한다.',
 'size':[1280,720],'thumbnail_sha256':hashlib.sha256((OUT/'thumbnail.png').read_bytes()).hexdigest(),
 'background':'native typography and approved house cutout b77e9bc6…','new_paid_generation':False}
(OUT/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False))
