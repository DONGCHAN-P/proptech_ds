import json, hashlib, subprocess, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
EP=Path(__file__).resolve().parents[2]
ROOT=EP.parents[2]
OUT=EP/'outputs/shorts-safe-v2'; OUT.mkdir(exist_ok=True)
OLD=EP/'outputs/shorts-release-v1'
FF=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
PROFILE=ROOT/'config/vertical_video_safe_area.json'
CONFIG=json.loads(PROFILE.read_text(encoding='utf-8'))
PROFILE_NAME=sys.argv[sys.argv.index('--profile')+1] if '--profile' in sys.argv else CONFIG['default_profile']
P=CONFIG['profiles'][PROFILE_NAME]
if '--output-tag' in sys.argv:
 tag=sys.argv[sys.argv.index('--output-tag')+1]
 assert tag.replace('-','').replace('_','').isalnum()
 OUT=EP/'outputs/shorts-safe-v2'/tag;OUT.mkdir(exist_ok=True)
R=P['critical_rect'];SAFE=(R['left'],R['top'],R['right'],R['bottom'])
BOUNDS=[]
def font(n,b=True): return ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if b else '')+'.ttf',n)
def label(im,xy,s,n=28,color='#102c45',kind='text'):
 d=ImageDraw.Draw(im); b=d.textbbox(xy,s,font=font(n)); assert b[0]>=SAFE[0] and b[1]>=SAFE[1] and b[2]<=SAFE[2] and b[3]<=SAFE[3],(s,b)
 d.text(xy,s,font=font(n),fill=color); BOUNDS.append(dict(kind=kind,text=s,font_px=n,bbox=b))
def wrap(s,n=44,width=628):
 lines=[];cur=''
 for w in s.replace('·','· ').split():
  if font(n).getlength((cur+' '+w).strip())>width and cur:lines.append(cur);cur=w
  else:cur=(cur+' '+w).strip()
 if cur:lines.append(cur)
 assert all(font(n).getlength(x)<=width for x in lines)
 return lines
def card(im,lines,y,n=38):
 for i,s in enumerate(lines):label(im,(168,y+i*(n+8)),s,n,kind='key_value')
def map_image(im,name,rect):
 pic=Image.open(OLD/name)
 pic=pic.crop(rect); pic.thumbnail((656,204),Image.Resampling.LANCZOS)
 x=158+(656-pic.width)//2;y=580+(204-pic.height)//2
 im.paste(pic,(x,y)); BOUNDS.append(dict(kind='map_source_bbox',source=name,source_crop=rect,bbox=[x,y,x+pic.width,y+pic.height],embedded_labels='bounded by complete map raster; key target repeated as separate text'))
def draw(ident,frame,caption=''):
 first_bound=len(BOUNDS)
 im=Image.new('RGB',(1080,1920),'#f4f3ed');d=ImageDraw.Draw(im)
 # Brand row disabled by conservative tablet-cover profile.
 titles={'01_rail':['입주는 2028년,','GTX는 2031년?'],'02_price':['왕숙이 주변 모든 집보다','쌀까?'],'03_choice':['왕숙2, A3와 A1','어느 쪽부터 볼까?']}
 for j,s in enumerate(titles[ident]):label(im,(168,448+j*54),s,44,kind='title')
 if ident=='01_rail':
  operating=frame>=1150
  map_image(im,'rail_operating_plate.png' if operating else 'rail_plate.png',(48,360,1032,1040))
  if operating: vals=['기존역: 별내 · 별내별가람','오남 · 진접 / 운영 철도']; n=36
  elif frame<523: vals=['왕숙역 GTX-B · 2031 목표','9호선·일패역 개통 미정']; n=36
  elif frame<653: vals=['왕숙1 A24·B17','2028.12 입주예정']; n=38
  elif frame<738: vals=['왕숙2 A1 · 2029.02','입주예정']; n=38
  elif frame<835: vals=['왕숙2 A3 · 2030.05','입주예정']; n=38
  else: vals=['입주 2028~2030 예정','GTX-B 2031 목표']; n=38
  card(im,vals,790,n)
  cond=['계획 구간·역 중심·출입구 미확정','입주 예정 / 개통 목표·미정 구분','정부 발표·공고 / © OpenStreetMap 기여자']
 elif ident=='02_price':
  if frame<67: who='다산롯데캐슬'; value='10.95억 · 중위값 · n=11';rect=(52,360,1028,870)
  elif frame<437: who='별내자이더스타';value='11.85억 · 중위값 · n=22';rect=(52,892,1028,1402)
  elif frame<826: who='별내푸르지오';value='6.775억 · 중위값 · n=16';rect=(52,892,1028,1402)
  else: who='왕숙1 B17 · 공고 기본형';value='6.4411억 · 2025.11 공고';rect=(52,892,1028,1402)
  if frame<826:map_image(im,'price_plate.png',rect)
  else:
   card(im,['별내푸르지오 · 실거래 중위값','6.775억 · n=16','왕숙1 B17 · 공고 기본형','6.4411억'],580,36)
  card(im,[who,value],790,38)
  cond=['실거래 2026.7~9 · 83≤전용<85㎡ · 5층+','취소제외 / B17 확장·옵션·세금·입주대기 별도','국토교통부 실거래·LH / © OpenStreetMap 기여자']
 else:
  a1=756<=frame
  if a1:
   card(im,['왕숙2 A1 · 동측 학교군','2029.03 개교 목표'],590,36)
   label(im,(168,700),'학교 배정·기존 역 연결 별도 확인',28,kind='map_key_label')
  else:map_image(im,'choice_plate.png',(48,360,1032,1010))
  card(im,['A1 · 84A / 84.67㎡' if a1 else 'A3 · 84A1 / 84.75㎡','6.9363억 · 2029.02 입주예정' if a1 else '7.3245억 · 2030.05 입주예정'],790,38)
  if frame<756:cond=['2026.04 공고 기본형 · 확장·옵션·세금 별도','거주의무 A1 5년·A3 3년 / 전매 각 3년','기산일·실제 양도조건 별도 확인 / LH 공고·팸플릿']
  else:cond=['2026.04 공고 기본형 · 확장·옵션·세금 별도','학교 2029.03 목표·상가/역 미정·접수 종료','자유매매 물건·미래 시세 순위 아님','LH 공고·팸플릿 / 자체 도해 · 시설은 계획']
 d.rounded_rectangle((156,894,816,1034),18,fill='white')
 lines=wrap(caption);assert len(lines)<=3,(ident,lines)
 y=886+(132-len(lines)*44)//2
 for j,s in enumerate(lines):label(im,(168,y+j*44),s,44,kind='caption')
 for j,s in enumerate(cond):label(im,(168,1044+j*(27 if len(cond)==4 else 34)),s,24,kind='condition_source')
 for b in BOUNDS[first_bound:]:b.update(short_id=ident,frame=frame,scene_id={'01_rail':'M003','02_price':'M007','03_choice':'M008'}[ident])
 return im
def main():
 preview='--preview' in sys.argv
 if not preview: assert PROFILE.exists(),'Required common safe profile missing'
 specs=json.loads((OLD/'manifest.json').read_text(encoding='utf-8'))
 manifest=[]
 for s in specs:
  ident=s['id']; cues=json.loads((OLD/f'{ident}_captions.json').read_text(encoding='utf-8'))
  if '--changed' in sys.argv and ident=='02_price':
   if not preview:manifest.append(next(x for x in json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if x['id']==ident))
   BOUNDS.extend(x for x in json.loads((OUT/'layout_bounds.json').read_text(encoding='utf-8'))['elements'] if x['short_id']==ident)
   continue
  folder=OUT/ident;folder.mkdir(exist_ok=True)
  events={0:s['duration_frames']}
  for c in cues:events[c['from_frame']]=c['to_frame'];events[c['to_frame']]=s['duration_frames']
  points=sorted(set([0,s['duration_frames']]+[p for c in cues for p in [c['from_frame'],c['to_frame']]]))
  concat=[]
  for i,(a,b) in enumerate(zip(points,points[1:])):
   cue=next((c for c in cues if c['from_frame']<=a<c['to_frame']),None)
   caption=' '.join(cue['lines']) if cue else ''
   im=draw(ident,a,caption);p=folder/f'plate_{i:03}.png';im.save(p)
   concat += [f"file '{p.as_posix()}'",f'duration {(b-a)/30:.12f}']
  concat += [concat[-2]]
  (folder/'frames.txt').write_text('\n'.join(concat),encoding='utf-8')
  draw(ident,0,' '.join(cues[0]['lines'])).save(OUT/f'{ident}_representative.png')
  longest=max(cues,key=lambda c:len(' '.join(c['lines'])))
  draw(ident,longest['from_frame'],' '.join(longest['lines'])).save(OUT/f'{ident}_longest.png')
  shutil.copyfile(OLD/f'{ident}.srt',OUT/f'{ident}.srt')
  shutil.copyfile(OLD/f'{ident}_captions.json',OUT/f'{ident}_captions.json')
  if not preview:
   target=OUT/f'{ident}_safe_v2.mp4'
   cmd=[str(FF/'ffmpeg.exe'),'-y','-v','warning','-f','concat','-safe','0','-i',str(folder/'frames.txt'),'-i',str(OLD/f'{ident}.mp4'),'-map','0:v:0','-map','1:a:0','-vf','fps=30,format=yuv420p','-frames:v',str(s['duration_frames']),'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','copy','-movflags','+faststart',str(target)]
   (folder/'render_command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2),encoding='utf-8')
   subprocess.run(cmd,check=True)
   probe=subprocess.check_output([str(FF/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(target)])
   (OUT/f'{ident}_probe.json').write_bytes(probe)
   with (OUT/f'{ident}_decode.log').open('w') as log:subprocess.run([str(FF/'ffmpeg.exe'),'-v','error','-i',str(target),'-f','null','-'],stderr=log,check=True)
   for name,t in [('actual_representative',0),('actual_longest',longest['from_frame']/30)]:
    subprocess.run([str(FF/'ffmpeg.exe'),'-y','-v','error','-ss',str(t),'-i',str(target),'-frames:v','1',str(OUT/f'{ident}_{name}.png')],check=True)
   manifest.append(dict(id=ident,file=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),source_frame_range=[s['start'],s['end']],frames=s['duration_frames'],profile=str(PROFILE),profile_sha256=hashlib.sha256(PROFILE.read_bytes()).hexdigest(),audio='AAC packets stream-copied from v1; no paid generation',srt_sha256=hashlib.sha256((OUT/f'{ident}.srt').read_bytes()).hexdigest(),source_srt_sha256=hashlib.sha256((OLD/f'{ident}.srt').read_bytes()).hexdigest()))
  print(ident,'preview' if preview else 'rendered',flush=True)
 (OUT/'layout_bounds.json').write_text(json.dumps(dict(safe_rect=SAFE,method='Pillow actual font textbbox; map complete raster bounds',pass_all=True,elements=BOUNDS),ensure_ascii=False,indent=2),encoding='utf-8')
 if not preview:(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()




