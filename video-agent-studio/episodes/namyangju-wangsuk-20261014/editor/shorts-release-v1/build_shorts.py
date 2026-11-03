import json, hashlib, subprocess, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
OUT=EP/'outputs/shorts-release-v1'; OUT.mkdir(exist_ok=True)
SRC=EP/'outputs/readability-cta-v15/namyangju_readability_cta_full_v15.mp4'
FF=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
CAP=json.loads((EP/'outputs/readability-cta-v15/timed_captions_v15.json').read_text(encoding='utf-8'))
NAVY='#102c45'; BLUE='#1768dc'; BG='#f4f3ed'; MUTED='#536878'
def font(n,bold=False): return ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if bold else '')+'.ttf',n)
def text(im,xy,s,size=36,fill=NAVY,bold=False): ImageDraw.Draw(im).text(xy,s,font=font(size,bold),fill=fill)
def box(im,rect,fill='white',outline=None): ImageDraw.Draw(im).rounded_rectangle(rect,24,fill=fill,outline=outline,width=2)
def base(k,title,sub):
 im=Image.new('RGB',(1080,1920),BG);text(im,(64,64),'데이터로 보는 부동산  /  왕숙',30,BLUE,True)
 for j,line in enumerate(title):text(im,(62,130+j*77),line,66,NAVY,True)
 text(im,(64,300),sub,29,MUTED)
 box(im,(48,1460,1032,1758),'white')
 text(im,(64,1875),'전체 분석과 출처는 본편에서 확인하세요',25,MUTED)
 return im
def paste_crop(im,src,rect,target):
 pic=Image.open(src).convert('RGB')
 if Path(src).name=='a3_source.png': ImageDraw.Draw(pic).rectangle((450,690,1015,750),fill=pic.getpixel((800,680)))
 if Path(src).name=='rail_operating.png': ImageDraw.Draw(pic).rectangle((110,673,721,729),fill=pic.getpixel((725,650)))
 pic=pic.crop(rect);pic=pic.resize(target[2:],Image.Resampling.LANCZOS);im.paste(pic,target[:2])
def rows(im,y,items):
 for j,(a,b) in enumerate(items):
  yy=y+j*84;box(im,(58,yy,1022,yy+73),'white');text(im,(80,yy+15),a,32,BLUE,True);text(im,(485,yy+15),b,32,NAVY,True)

# 지도판은 의미 있는 범위를 함께 표시하며 9:16 중앙 크롭을 사용하지 않는다.
rail=base('rail',['입주는 2028년,','GTX는 2031년?'],'왕숙의 집 달력과 교통 달력을 나란히')
paste_crop(rail,WORK/'rail_source.png',(650,190,1460,750),(48,360,984,680))
rows(rail,1060,[('2028.12 예정','왕숙1 A24·B17 입주'),('2029.02 / 2030.05','왕숙2 A1 / A3 입주'),('2031 목표','왕숙역 GTX-B 개통')])
text(rail,(64,1330),'9호선 연장·일패역 개통 미정',33,BLUE,True)
text(rail,(64,1380),'계획 구간 표시 · 역 중심·출입구 미확정',26,MUTED)
text(rail,(64,1810),'© OpenStreetMap 기여자 · 정부 발표/공고 기준 목표·예정',22,MUTED)
rail.save(OUT/'rail_plate.png')
rail2=rail.copy();paste_crop(rail2,WORK/'rail_operating.png',(650,190,1460,750),(48,360,984,680));rail2.save(OUT/'rail_operating_plate.png')

price=base('price',['왕숙이 주변 모든 집보다','쌀까?'],'실거래 중위값과 공고 기본가격은 서로 다른 조건')
plate=EP/'outputs/locator-timeline-v14/price_plate.png'
paste_crop(price,plate,(75,235,925,785),(52,360,976,510))
paste_crop(price,plate,(995,235,1845,785),(52,892,976,510))
text(price,(64,1415),'B17: 2025.11 공고 기본형 · 확장·옵션·세금 별도',24,NAVY,True)
text(price,(64,1773),'실거래 2026.7~9 · 83≤전용<85㎡ · 5층+ · 취소제외',26,MUTED)
text(price,(64,1810),'자이더스타 11.85억 n22 / B17 기본가 6.4411억',26,MUTED)
text(price,(64,1845),'출처: 국토교통부 실거래·LH 공고 / © OpenStreetMap 기여자',18,MUTED)
price.save(OUT/'price_plate.png')

choice=base('choice',['왕숙2, A3와 A1','어느 쪽부터 볼까?'],'입지 후보와 예산·입주 경쟁, 우선순위가 다릅니다')
paste_crop(choice,WORK/'a3_source.png',(830,190,1770,750),(48,360,984,650))
rows(choice,1030,[('A3 · 84A1 / 84.75㎡','7.3245억 · 2030.05'),('A1 · 84A / 84.67㎡','6.9363억 · 2029.02')])
text(choice,(64,1214),'공고 기본형 · 2026.04 · 확장·옵션·세금 별도',28,MUTED)
text(choice,(64,1260),'학교 개교 2029.03 목표 / 상가·역 개통 미정',28,BLUE,True)
text(choice,(64,1310),'접수 종료 · 현재 자유매매 물건 아님',29,NAVY,True)
text(choice,(64,1354),'공고 거주의무 A1 5년 · A3 3년 / 전매 각 3년',27,MUTED)
text(choice,(64,1396),'기산일·실제 양도조건 별도 확인 · 미래 시세 순위 아님',24,MUTED)
text(choice,(64,1810),'LH 공고·팸플릿 동일 원도 좌표 기반 자체 도해 · 시설은 계획',22,MUTED)
choice.save(OUT/'choice_plate.png')

SPECS=[dict(id='01_rail',start=6324,end=8190,plate='rail_plate.png',title='입주는 2028년, GTX는 2031년? 왕숙 교통 시차',description='입주예정과 교통 개통목표를 함께 봅니다. 왕숙역 GTX-B 2031은 정부 발표 목표이며, 9호선 연장·일패역 개통은 미정입니다. 기존 철도까지의 실제 연결도 확인하세요.'),dict(id='02_price',start=16343,end=17885,plate='price_plate.png',title='왕숙이 주변 모든 집보다 쌀까? 84㎡ 실거래 비교',description='2026년 7~9월, 전용83㎡ 이상85㎡ 미만·5층 이상·취소표시제외 실거래 중위값. 다산롯데캐슬10.95억(n11), 별내푸르지오6.775억(n16), 별내자이더스타11.85억(n22). B17 공고기본형6.4411억과 상품·시점이 다르며 확장/옵션/세금·입주대기 별도입니다.'),dict(id='03_choice',start=24487,end=25935,plate='choice_plate.png',title='왕숙2 A3와 A1, 입지와 예산·입주 비교',description='2026년4월 공고 기본형 기준: A3 84A1·84.75㎡7.3245억, A1 84A·84.67㎡6.9363억. 확장·옵션·세금 별도. 입주/학교는 예정·목표이며 현재 모집·자유매매 안내가 아닙니다. 거주의무 A1 5년/A3 3년, 전매제한 각3년; 기산일·실양도조건 별도 확인. 미래 시세 순위가 아닙니다.')]

def stamp(sec,ass=False):
 if ass:
  t=round(sec*100);return f'{t//360000}:{t//6000%60:02}:{t//100%60:02}.{t%100:02}'
 t=round(sec*1000);return f'{t//3600000:02}:{t//60000%60:02}:{t//1000%60:02},{t%1000:03}'
def wrap(s):
 words=s.split();lines=[];line=''
 for w in words:
  candidate=(line+' '+w).strip()
  if font(52,True).getlength(candidate)>870 and line:lines.append(line);line=w
  else:line=candidate
 if line:lines.append(line)
 return lines
def prepare(s):
 cues=[c for c in CAP if c['from_frame']>=s['start'] and c['to_frame']<=s['end']]
 ass='[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Malgun Gothic,52,&H00452C10,&H00452C10,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,95,95,0,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
 sr=[];rel=[]
 for i,c in enumerate(cues):
  a=(c['from_frame']-s['start'])/30;b=(c['to_frame']-s['start'])/30;lines=wrap(' '.join(c['lines']))
  if c['from_frame']==17169: lines=['왕숙1 B17은 기본가격','약 6억 4천만 원이니']
  assert len(lines)<=4,(s['id'],lines)
  ass+=f'Dialogue: 0,{stamp(a,True)},{stamp(b,True)},Default,,0,0,0,,{{\\pos(540,1608)}}'+r'\N'.join(lines)+'\n'
  sr.append(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n'+ '\n'.join(lines)+'\n')
  rel.append(dict(from_frame=c['from_frame']-s['start'],to_frame=c['to_frame']-s['start'],lines=lines,source=c))
 (OUT/f"{s['id']}.ass").write_text(ass,encoding='utf-8-sig');(OUT/f"{s['id']}.srt").write_text('\n'.join(sr),encoding='utf-8-sig');(OUT/f"{s['id']}_captions.json").write_text(json.dumps(rel,ensure_ascii=False,indent=2),encoding='utf-8')
 return len(cues)

if __name__=='__main__':
 import sys
 existing=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if (OUT/'manifest.json').exists() else []
 for s in SPECS:
  if len(sys.argv)>1 and s['id']!=sys.argv[1]:
   old=next((x for x in existing if x['id']==s['id']),None)
   if old:s.update(old)
   continue
  s['cue_count']=prepare(s);s['duration_frames']=s['end']-s['start'];s['source_sha256']=hashlib.sha256(SRC.read_bytes()).hexdigest()
  cmd=[str(FF/'ffmpeg.exe'),'-y','-v','warning','-loop','1','-framerate','30','-i',str(OUT/s['plate']),'-ss',f"{s['start']/30:.9f}",'-i',str(SRC)]
  if s['id']=='01_rail':
   cmd+=['-loop','1','-framerate','30','-i',str(OUT/'rail_operating_plate.png')]
   filt="[0:v][2:v]overlay=0:0:enable='gte(t,39.8)'[plate];[plate]"
  else:filt='[0:v]'
  # Run in OUT: relative ASS path avoids Windows drive-colon escaping.
  filt+=f"ass={s['id']}.ass,format=yuv420p[v]"
  cmd+=['-filter_complex',filt,'-map','[v]','-map','1:a:0','-frames:v',str(s['duration_frames']),'-t',f"{s['duration_frames']/30:.9f}",'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(OUT/f"{s['id']}.mp4")]
  print('RENDER',s['id'],flush=True);subprocess.run(cmd,cwd=OUT,check=True)
  p=OUT/f"{s['id']}.mp4";s['file']=str(p);s['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  (OUT/'manifest.json').write_text(json.dumps(SPECS,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'manifest.json').write_text(json.dumps(SPECS,ensure_ascii=False,indent=2),encoding='utf-8')
 print('DONE',flush=True)
