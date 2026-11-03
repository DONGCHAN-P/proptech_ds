from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
EP=Path('video-agent-studio/episodes/goyang-changneung-20261015');O=EP/'outputs/visual-review-v8';E=EP/'editor/revision-v8';files=['06_chapter_jobs.png','04_chapter_transport.png','07_chapter_price.png','08_chapter_comparison.png','09_chapter_supply.png','05_chapter_school_life.png'];im=Image.new('RGB',(1920,780),'#ddd');d=ImageDraw.Draw(im)
for i,n in enumerate(files):x=i%3*640;y=i//3*390;im.paste(Image.open(O/n).resize((640,360)),(x,y));d.text((x+6,y+366),n,fill='black')
im.save(O/'chapters_6_contactsheet.jpg',quality=94)
files=['01_method_map_clock.png','02_price_evidence.png','03_life_real_parcels.png'];im=Image.new('RGB',(1920,1200),'#ddd');d=ImageDraw.Draw(im)
for i,n in enumerate(files):x=i%2*960;y=i//2*600;im.paste(Image.open(O/n).resize((960,540)),(x,y));d.text((x+8,y+550),n,fill='black')
im.save(O/'replacement_3_contactsheet.jpg',quality=94)
mobile=O/'mobile512';mobile.mkdir(exist_ok=True);allfiles=[x['name']+'.png'for x in json.loads((O/'render_receipt.json').read_text())['receipts']]
for n in allfiles:Image.open(O/n).resize((512,288)).save(mobile/n)
im=Image.new('RGB',(1536,948),'#ddd');d=ImageDraw.Draw(im)
for i,n in enumerate(allfiles):x=i%3*512;y=i//3*316;im.paste(Image.open(mobile/n),(x,y));d.text((x+6,y+290),n,fill='black')
im.save(O/'mobile_9_contactsheet.jpg',quality=95)
# Assert reuse identity without new research calls.
W=json.loads(Path('video/src/changneung-v6/data.json').read_text());V=json.loads(Path('video/src/changneung-v7/data.json').read_text());assert W['commute']==[[66,68,67],[46,62,56],[63,78,72],[72,80,68],[87,94,94]];assert[(x['median_eok'],x['n'])for x in V['resale']]==[(11.275,6),(9.2,11),(8.5,3),(8.45,17),(8.375,20),(7.45,11)]
facts={'approved_facts_reused':True,'new_research':False,'commute_actual_example':'S4 강남 08:06~09:34,08:00기준6분대기+88분경로=94분; research/commute-v6/report.md','source_prices':'specific 84㎡/5층 이상 basic+balcony, dated 2025/2026 notices; not current available acquisition prices','new_future_price_or_return':False,'chapter_background_type':'root supplied six GPT generic AI concept backgrounds, not actual Changneung/site/official plan','chapter_numbers':['01 일자리','02 교통','03 가격','04 주변 가격 비교','05 공급','06 생활시설'],'no_full_render_or_voice':True}
(O/'data_checks.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8');print('9 actual PNGs / mobile / facts checks pass')
