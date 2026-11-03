import pathlib,json,shutil
from PIL import Image,ImageDraw,ImageFont
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
pub=ROOT/'video/public/data-insight-v2';src=ROOT/'video/src/data-insight-v2';pub.mkdir(exist_ok=True);src.mkdir(exist_ok=True)
d=json.loads((EP/'scenes_v2.json').read_text(encoding='utf8'))
manifest=json.loads((EP/'inputs/manifest.json').read_text(encoding='utf8'))
ids={x for s in d['scenes'] for x in s['asset_ids']}
d['assets']={}
for a in manifest:
 if a['id'] in ids:
  p=pathlib.Path(a['path']);shutil.copy2(p,pub/p.name);d['assets'][a['id']]=p.name
for n in ['monitor','laptop','phone']:shutil.copy2(EP/'visual-v2'/f'{n}_reference.jpg',pub/f'{n}_reference.jpg')
for n in ['monitor','laptop','phone']:
 if (EP/'visual-v2'/f'{n}.mp4').exists():shutil.copy2(EP/'visual-v2'/f'{n}.mp4',pub/f'{n}.mp4')
for name in ['bold.woff2','regular.woff2','bgm.wav']:shutil.copy2(ROOT/'video/public/data-insight-v1'/name,pub/name)
im=Image.open(EP/'inputs/A05.gif');d['gif_durations']=[]
for i in range(im.n_frames):
 im.seek(i);im.convert('RGB').save(pub/f'A05_{i}.png');d['gif_durations'].append(im.info.get('duration',100))
# Preliminary keyframe measurements at 1280x720, converted into composition pixels.
q={'monitor':[[459,187],[1112,167],[1110,535],[457,505]],'laptop':[[666,285],[1100,293],[1077,556],[629,523]],'phone':[[836,153],[999,168],[915,601],[732,574]]}
d['tracks']={name:[{'time':0,'quad':[[x*1.5,y*1.5] for x,y in points]}] for name,points in q.items()}
d['track_status']='keyframe_only_preliminary; actual source frames must be measured before final render'
(src/'data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
text=['# v2 렌더 전 한글·고정문구 목록','', '출처: script_v2.md / scenes_v2.json. 모든 원본 UI 글자는 입력 픽셀을 유지한다.']
for s in d['scenes']:text.extend(['',f"## {s['scene_id']}",s['title'],s['caption']])
text+=['','공통: DATA INSIGHT / AI 재현 · 화면 합성','S3c: 입력·요건서 정리 과정 · 빠르게 재생','S4: 매시 10분 · 야간·주말 이상 알림 / 제공 화면 기반 모바일 재구성','S3d 기기 안: 원본 자료의 대시보드 예시','S5: Weekly 7회 / 2~3시간 → 5분 / 수치: 사용자 제공 구성안','모바일 채널표시: # yogi_signal_room / # yogi_promo_room','기기 안 원본 UI 외의 별도 캡처 카드는 표시하지 않는다.']
(EP/'editor-v2/on_screen_text_v2.md').write_text('\n'.join(text)+'\n',encoding='utf8')
with (EP/'editor-v2/on_screen_text_v2.md').open('a',encoding='utf8') as f:f.write('\n'+(EP/'editor-v2/mobile_text_inventory.md').read_text(encoding='utf8'))
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',25)
def mobile(id,channel,crops):
 original=Image.open(pub/d['assets'][id]).convert('RGB');screen=Image.new('RGB',(430,932),'white');draw=ImageDraw.Draw(screen)
 draw.rectangle((0,0,430,132),fill='#491349');draw.text((22,77),'# '+channel,font=font,fill='white')
 y=152
 for crop in crops:
  part=original.crop(crop);height=round(part.height*390/part.width);part=part.resize((390,height),Image.Resampling.LANCZOS);screen.paste(part,(20,y));y+=height+22
 draw.line((0,878,430,878),fill='#dedbe2',width=2)
 for x in [55,160,270,375]:draw.ellipse((x-8,902,x+8,918),fill='#6e6173')
 screen.save(pub/f'{id}_mobile.png')
mobile('A01','yogi_signal_room',[(1100,340,2410,1210),(1100,1290,2410,2130)])
mobile('A07','yogi_promo_room',[(520,170,1520,310),(550,320,860,550),(875,320,1180,550)])
Image.open(pub/d['assets']['A10']).crop((674,166,826,267)).save(pub/'A10_dashboard_crop.png')
def mobile_alert(phase):
 canvas=Image.new('RGB',(430,932),'white');draw=ImageDraw.Draw(canvas)
 regular=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22);bold=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',24);headline=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',27);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
 draw.rectangle((0,0,430,128),fill='#491349');draw.text((20,76),'# yogi_signal_room',font=bold,fill='white')
 draw.text((20,151),'Daily Briefing',font=bold,fill='#242126');draw.rounded_rectangle((212,156,255,181),radius=3,fill='#ededed');draw.text((218,159),'APP',font=small,fill='#555')
 if phase=='spike':
  title='10시 급증 ▲ · 7,710건';metrics='평소 ▲78% · 전주 ▲90%';cumulative='누적 1.4만건 ▲39% · z +3.8';lines=['동반 쿠폰: 포장 선착순','파바픽업 7,000원 할인','+4,008','전국적, 특히 영남권(+98%)','수도권(+87%)'];box=(1150,710,2355,1205)
 else:
  title='14시 급감 ▼ · 3,882건';metrics='평소 ▼20% · 전주 ▼12%';cumulative='누적 3.9만건 ▲8% · z -2.0';lines=['동반 쿠폰: Panama - vms 쿠폰','+943','전국적, 특히 수도권(-22%)','영남권(-20%)'];box=(1150,1625,2355,2110)
 draw.text((20,205),title,font=headline,fill='#242126');draw.text((20,254),metrics,font=regular,fill='#d72465');draw.text((20,292),cumulative,font=regular,fill='#242126')
 draw.line((20,335,410,335),fill='#dedbe2',width=2)
 for i,line in enumerate(lines):draw.text((20,360+i*34),line,font=regular,fill='#343038')
 graph=Image.open(pub/'A01.png').crop(box);gh=round(graph.height*390/graph.width);canvas.paste(graph.resize((390,gh),Image.Resampling.LANCZOS),(20,555))
 draw.rounded_rectangle((16,823,414,883),radius=12,outline='#beb8c4',width=2,fill='#fafafa');draw.text((30,845),'Message #yogi_signal_room',font=small,fill='#8b818d');draw.line((174,912,256,912),fill='#302a34',width=4)
 canvas.save(pub/f'A01_mobile_{phase}.png')
mobile_alert('spike');mobile_alert('drop')
print('v2 UI assets, keyframe references, font/BGM and prewritten text inventory ready.')
