"""Assemble unchanged, scaled static review screenshots; no generated place imagery."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
S=E/'editor/top20-explain-v3/evidence/대표PNG'; O=R/'영상/신혼부부_지역별아파트/수정안_v3'
def main():
    items=[('O002_intro','자료·기준 시점'),('S006_feature','연수구 · 지역 설명'),
           ('S019_feature','강서구 · 랜드마크'),('S005_price','기흥구 · 긴 단지명'),
           ('S017_price','강남구 · 큰 금액'),('S022_price','옛 서구 · 구역과 단지 위치')]
    sheet=Image.new('RGB',(1920,1758),'#ffffff');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22); records=[]
    for i,(name,label)in enumerate(items):
        path=S/(name+'.png'); pic=Image.open(path).convert('RGB'); assert pic.size==(1920,1080)
        x=(i%2)*960;y=(i//2)*586;sheet.paste(pic.resize((960,540),Image.Resampling.LANCZOS),(x,y))
        draw.text((x+20,y+549),label,font=font,fill='#173348')
        records.append({'source':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'operation':'uniform downscale only; no crop or retouch'})
    O.mkdir(parents=True,exist_ok=True);dest=O/'대표화면.jpg';sheet.save(dest,quality=95,subsampling=0)
    (D/'review_contactsheet_sources.json').write_text(json.dumps({'scope':'static representative screenshots; provisional timing; no audio/MP4',
          'source_scene_json_sha256':'8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e',
          'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':[1920,1758],'sources':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_frames':len(items),'output':dest.relative_to(R).as_posix(),'size':sheet.size},ensure_ascii=False))
if __name__=='__main__':main()
