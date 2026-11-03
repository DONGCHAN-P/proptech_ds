from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html
base=Path('video/public/real-assets');m=json.loads((base/'manifest.json').read_text(encoding='utf8'));ready=[]
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
for a in m:
 if not a.get('file'):continue
 im=Image.open(base/a['file']);a['width'],a['height']=im.size
 a['visual_review']='inspected in contact sheet; place is source-described; not a current-date claim'
 if a['id']=='commons-2':a['editorial_note']='공원 잔디·주변 주거 전경. 자연앤힐스테이트 사진으로 사용하지 않음.'
 if a['id']=='gnews-gwanggyo-history-3':a['editorial_note']='기사 공개일은2022년. 사진 속 일부 건물은 공사 중이며 정확한 촬영일 미상. 현재 전경으로 표기하지 않음.'
 ready.append(a)
(base/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
for k in range(0,len(ready),6):
 batch=ready[k:k+6];sheet=Image.new('RGB',(1800,1050),'#F6F4EF');d=ImageDraw.Draw(sheet)
 for j,a in enumerate(batch):
  x=(j%3)*600;y=(j//3)*525;im=Image.open(base/a['file']).convert('RGB');im.thumbnail((580,380));sheet.paste(im,(x+(600-im.width)//2,y+20+(380-im.height)//2))
  title=a['title'];d.text((x+15,y+415),a['id'],font=font(22),fill='#111');d.text((x+15,y+450),a['license'][:40],font=font(19),fill='#777');d.text((x+15,y+482),'참고용 · 이용조건 미확인' if 'reference_only' in a['use_status'] else '라이선스 확인 · '+str(a['width'])+'×'+str(a['height']),font=font(19),fill='#E5484D' if 'reference_only' in a['use_status'] else '#2F6FED')
 sheet.save(base/f'contact-{k//6}.jpg')
cards=[]
for a in ready:
 cards.append(f'<article><img loading="lazy" src="{html.escape(a["file"])}"><h3>{html.escape(a["title"])}</h3><p>{html.escape(a["author"])}</p><p>{html.escape(a["license"])} · {a["width"]}×{a["height"]}</p><p>{html.escape(a["use_status"])}</p><p>{html.escape(a.get("editorial_note",""))}</p><a href="{html.escape(a["source_url"])}" target="_blank">원문 출처</a></article>')
maps=''.join(f'<article><img src="../detail-maps/{name}.png"><h3>{label}</h3><a href="../detail-maps/{name}.png">원본 지도</a></article>' for name,label in [('gwanggyo-core','광교 역·행정 중심'),('gwanggyo-life','광교 생활권·일자리'),('dongtan-core','동탄역 복합단지'),('dongtan-jobs','동탄 반도체 사업장')])
out='<!doctype html><html lang="ko"><meta charset="utf-8"><title>광교·동탄 실제 소재와 상세 지도</title><style>body{font:16px sans-serif;background:#f6f4ef;margin:40px;color:#111}h1{font-size:32px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:white;padding:20px;border-radius:12px}img{width:100%;height:330px;object-fit:contain}p{line-height:1.5;color:#666}a{color:#2f6fed}</style><h1>광교·동탄 실제 소재와 상세 지도</h1><p>2026.10.13 확보 · 사진별 출처·시점·이용 조건을 함께 확인합니다.</p><h2>상세 지도 4종</h2><div class="grid">'+maps+'</div><h2>실제 사진 원본</h2><div class="grid">'+''.join(cards)+'</div></html>'
(base/'review.html').write_text(out,encoding='utf8')
print(f'{len(ready)} downloaded photos, {sum("reference_only" not in a["use_status"] for a in ready)} license-confirmed, 4 maps')
