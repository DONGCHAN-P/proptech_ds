"""Native portrait projects from director's exact sentence-ID selection.
No new speech. Sentence cuts remain provisional until actual timing arrives.
Run after build.py. Optional --clips JSON replaces source_start_s/end_s by ID.
"""
from pathlib import Path
import argparse,html,json,re,shutil,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from caption_tools import make_cues
H=Path(__file__).resolve().parent;E=H.parents[1];R=E.parents[2];M=H/'main'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,s):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def save(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def e(s):return html.escape(str(s))
def text(s,x,y,w,sz=36,c='#173348',wt=400,id=''):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="t" style="left:{x}px;top:{y}px;width:{w}px;font-size:{sz}px;color:{c};font-weight:{wt}">{e(s)}</div>'
def rect(x,y,w,h,c,rad=12,id=''):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="r" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{c};border-radius:{rad}px"></div>'
def image(src,x,y,w,h):return f'<img src="assets/{src}" alt="" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:contain">'
def split(t):
 tokens=re.findall(r'(?:\d+만\s+[\d,]+쌍|(?:여섯|열세|열아홉|스무|열|다섯|두|한|세|네)\s+(?:곳|쌍|개|사람|지역|가지|구|해)[가-힣]*|\S+)',t);out=[];cur=''
 for w in tokens:
  if cur and len(cur)+1+len(w)>22:out.append(cur);cur=w
  else:cur=(cur+' '+w).strip()
 if cur:out.append(cur)
 return out
ap=argparse.ArgumentParser();ap.add_argument('--clips');a=ap.parse_args()
timeline=read(H/'timeline_resolved.json');story=read(E/'director/top20-production-v1/shorts_story_plan.json')
mapping={}
for s in timeline['scenes']:
 for st in s['sentence_times']:mapping[st['sentence_id']]={**st,'scene_id':s['scene_id'],'global_start':s['start_s']+st['start_s'],'global_end':s['start_s']+st['end_s']}
exact=read(a.clips) if a.clips else {};byitem={v['id']:v for v in exact.get('items',[])}
facts={r['region_id']:r for r in read(E/'research/top20-8min-v2/combined_facts.json')['regions']}
word_groups={}
wp=Path(timeline.get('words_file') or E/'narration/top20-production-v1/production-v2/words_v2.json')
if timeline['timing_locked'] and wp.exists():
 for w in read(wp)['words']:word_groups.setdefault(w['sentence_id'],[]).append(w)
photo={r['region_id']:r for r in read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']}
CSS='''@font-face{font-family:Pretendard;src:url(assets/Pretendard-Regular.woff2);font-weight:400}@font-face{font-family:Pretendard;src:url(assets/Pretendard-Bold.woff2);font-weight:700}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef;font-family:Pretendard,sans-serif}#portrait{position:relative;width:100%;height:100%;overflow:hidden}.t{position:absolute;line-height:1.22;word-break:keep-all;letter-spacing:-.02em;font-variant-numeric:tabular-nums}.r{position:absolute;display:block;transform-origin:left center}.section{position:absolute;inset:0}.cue{position:absolute;left:140px;top:1100px;width:700px;height:150px;background:#fff;border-radius:13px;display:flex;align-items:center;justify-content:center;text-align:center;padding:10px 18px;font-size:54px;line-height:1.2;word-break:keep-all;color:#173348;letter-spacing:-.018em}'''
def comparison(title,rows,maxn,gap=None):
 body=rect(125,490,730,570,'#fffef9')+text(title,145,510,680,39,wt=700)
 for i,(lab,val,col) in enumerate(rows):
  y=600+i*167;body+=text(lab,145,y,270,36,wt=700)+text(f'{val:,}쌍',500,y,320,43,col,700)
  body+=rect(145,y+67,670,36,'#dfe4e5',4)+rect(145,y+67,670*val/maxn,36,col,4)
 if gap:body+=text(gap,145,945,680,48,'#286cda',700)
 body+=text(f'동일 척도 0–{maxn:,}쌍',145,1020,680,26,'#536873')
 return body
receipts=[]
for item in story['items']:
 kind=item['id'];D=H/'shorts'/kind;A=D/'assets';A.mkdir(parents=True,exist_ok=True)
 for p in (M/'assets').glob('*'):
  if p.suffix in ['.woff2','.js'] or p.name in ['top20_overview.svg','R10.jpg','R11.jpg','R01.jpg','R06.jpg','R01_locator.svg','R06_locator.svg']:shutil.copy2(p,A/p.name)
 audio=timeline.get('audio_file')
 if audio:shutil.copy2(audio,A/('narration'+Path(audio).suffix));audio='assets/narration'+Path(audio).suffix
 exactitem=byitem.get(kind,{});cuts={}
 for clip in exactitem.get('clips',[]):
  ids=clip.get('sentence_ids') or [clip['sentence_id']]
  for j,sid in enumerate(ids):
   # Parent owns source cuts and full WAV. These subdivisions only switch visuals.
   cuts[sid]={**clip,'source_start_s':clip['source_start_s'] if j==0 else mapping[sid]['global_start'],'source_end_s':clip['source_end_s'] if j+1==len(ids) else mapping[ids[j+1]]['global_start']}
 full_short_audio=exactitem.get('audio_file')
 if full_short_audio:
  assert hashlib.sha256(Path(full_short_audio).read_bytes()).hexdigest()==exactitem['audio_sha256']
  shutil.copy2(full_short_audio,A/'narration.wav');audio='assets/narration.wav'
 pos=0;placements=[];sections=[];audios=[];captions=[];finalextra=3
 for i,sid in enumerate(item['sentence_ids']):
  st=mapping[sid];cut=cuts.get(sid,{});b=cut.get('source_start_s',st['global_start']);en=cut.get('source_end_s',st['global_end']);dur=en-b;assert dur>0
  placements.append({'sentence_id':sid,'source_start_s':b,'source_end_s':en,'start_s':pos,'end_s':pos+dur,'text':st['text']})
  last=i==len(item['sentence_ids'])-1
  if last:finalextra=exactitem.get('duration_s',pos+dur+3)-(pos+dur) if full_short_audio else exactitem.get('additional_final_hold_s',3)
  viewdur=dur+(finalextra if last else 0)
  title='신혼부부가 사는 곳' if kind=='promo' else '많이 사는 곳, 늘어난 곳'
  body=text(title,140,275,700,58,wt=700)
  # Every visual is native 1080x1920; all meaning-bearing text stays x140..840.
  if sid.startswith('S013'):
   body+=image('R10.jpg',0,440,1080,650)+comparison('노원구와 미추홀구', [('미추홀구',8483,'#286cda'),('노원구',8473,'#a47d32')],10000,'차이는 10쌍')
  elif sid.startswith('S022'):
   if sid.endswith('05'):body+=image('R01.jpg',0,440,1080,650)+comparison('2024 옛 서구',[('2023',15941,'#a47d32'),('2024',15737,'#286cda')],16000,'204쌍 · 1.3% 감소')
   else:
    body+=image('R01_locator.svg',0,440,1080,650)+rect(125,820,730,245,'#fffef9')+text('2024 옛 인천 서구',145,842,680,40,wt=700)+text('15,737쌍',145,902,680,87,'#286cda',700)
    body+=text('현재 서해구+검단구 범위',145,1017,680,29)
  elif sid.startswith('S017'):
   if sid.endswith('03'):body+=image('R06.jpg',0,440,1080,650)+comparison('서울 강남구',[('2023',8523,'#a47d32'),('2024',9321,'#286cda')],16000,'798쌍 · 9.4% 증가')
   else:body+=image('R06.jpg',0,440,1080,650)+rect(125,820,730,245,'#fffef9')+text('6위 서울 강남구',145,848,680,42,wt=700)+text('9,321쌍',145,919,680,88,'#286cda',700)
  elif sid=='C001-02':
   body+=image('top20_overview.svg',0,440,1080,650)+rect(125,490,730,570,'#fffef9')
   body+=text('1년 동안의 변화',145,520,680,40,wt=700)+text('강남구',145,630,300,42,wt=700)+text('+9.4%',145,698,680,94,'#286cda',700)+text('옛 서구',145,850,300,42,wt=700)+text('−1.3%',145,918,680,94,'#88631b',700)
  else:
   body+=image('top20_overview.svg',0,440,1080,650)
   if sid=='C001-03':body+=rect(125,825,730,240,'#fffef9')+text('규모와 변화',145,855,680,55,'#286cda',700)+text('두 축으로 함께 비교',145,940,680,46,wt=700)
   elif last:body+=rect(125,825,730,240,'#fffef9')+text(item['end_card'],145,855,680,53,'#286cda',700)+text('구독 · 좋아요',145,995,680,38,wt=700)
   else:body+=rect(125,825,730,240,'#fffef9')+text('수도권 53개 구',145,855,680,57,'#286cda',700)+text('20위부터 1위까지',145,955,680,45,wt=700)
  # Record real photo credits with the relevant place. Full individual terms stay in credits.json.
  yrs='2023·2024' if kind=='analysis' else '2024'
  body+=text(f'통계청 {yrs} 신혼부부통계',140,1260,700,26)+text('수도권 53개 구 · 전체 · 단위: 쌍',140,1292,700,26)
  credit='통계청 신혼부부통계 | 지도: SGIS · CC BY 4.0'
  rid=('R10' if sid.startswith('S013') else 'R01' if sid.startswith('S022') else 'R06' if sid.startswith('S017') else None)
  if rid:
   p=photo[rid]
   credit={'R01':'사진: 인천시설공단 · 공공누리1','R06':'사진: 서울시·서울연구원 / CC BY4.0','R10':'사진: Narburu7 · CC BY4.0'}[rid]
   isphoto=rid!='R01' or sid=='S022-05'
   if isphoto:
    yr=p['photo_capture_year'] or '연도 미상';body+=rect(125,1057,730,36,'#fffef9',4)+text(f'실제 장소 자료사진 · 촬영 {yr}',145,1060,680,26)
   else:credit='지도: SGIS · vuski/admdongkor · CC BY4.0'
  body+=text(credit,140,1325,700,26,c='#536873')
  compid=f'{kind}-S{i:02d}'
  subbody=body.replace('src="assets/','src="../assets/')
  sub=f'<template><style>#{compid}{{position:absolute;inset:0;width:100%;height:100%}}</style><div id="{compid}" data-composition-id="{compid}" data-width="1080" data-height="1920" data-duration="{viewdur:.6f}">{subbody}</div><script>window.__timelines["{compid}"]=gsap.timeline({{paused:true}});</script></template>'
  write(D/f'scenes/{compid}.html',sub)
  sections.append(f'<div id="{compid}" class="clip section" data-composition-id="{compid}" data-composition-src="scenes/{compid}.html" data-start="{pos:.6f}" data-duration="{viewdur:.6f}" data-track-index="1" data-width="1080" data-height="1920"></div>')
  if audio and not full_short_audio:audios.append(f'<audio id="speech-{i}" class="clip" src="{audio}" data-start="{pos:.6f}" data-duration="{dur:.6f}" data-media-start="{b:.6f}" data-track-index="3"></audio>')
  scene=next(s for s in timeline['scenes'] if s['scene_id']==st['scene_id'])
  for cue in make_cues(st,word_groups.get(sid,[]),st.get('reading_text'),22):
   cb=pos+scene['start_s']+cue['start_s']-b;ce=pos+scene['start_s']+cue['end_s']-b
   captions.append({**cue,'start_s':max(pos,cb),'end_s':min(pos+dur,ce)})
  pos+=dur
 total=pos+finalextra
 if full_short_audio:audios=[f'<audio id="main-narration" class="clip" src="assets/narration.wav" data-start="0" data-duration="{total:.6f}" data-track-index="3"></audio>']
 from caption_backgrounds import markup
 cues=markup([[0,max(c['end_s'] for c in captions)]],kind,True)+''.join(f'<div id="caption-{i}" class="clip cue" data-start="{c["start_s"]:.6f}" data-duration="{c["end_s"]-c["start_s"]:.6f}" data-track-kind="captions" data-track-index="4">{e(c["text"])}</div>' for i,c in enumerate(captions))
 capid=kind+'-CAPTIONS';write(D/f'scenes/{capid}.html',f'<template><style>#{capid}{{position:absolute;inset:0;width:100%;height:100%}}</style><div id="{capid}" data-composition-id="{capid}" data-width="1080" data-height="1920" data-duration="{total:.6f}">{cues}</div><script>window.__timelines["{capid}"]=gsap.timeline({{paused:true}});</script></template>')
 caphost=f'<div id="{capid}" class="clip" data-composition-id="{capid}" data-composition-src="scenes/{capid}.html" data-start="0" data-duration="{total:.6f}" data-track-index="4" data-track-kind="captions" data-width="1080" data-height="1920"></div>'
 write(D/'index.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body><div id="portrait" data-composition-id="portrait" data-width="1080" data-height="1920" data-duration="{total:.6f}">{"".join(sections)}{"".join(audios)}{caphost}</div><script>window.__timelines["portrait"]=gsap.timeline({{paused:true}});</script></body></html>')
 save(D/'hyperframes.json',{'name':'top20-'+kind,'authoringSkill':'general-video','paths':{'assets':'assets','blocks':'compositions','components':'compositions/components'}})
 save(D/'clip_contract.json',{'id':kind,'profile':story['profile'],'timing_locked':bool(timeline['timing_locked'] and exact.get('timing_locked')),'status':'actual_sentence_cuts' if cuts else 'provisional_sentence_estimates','sentence_ids':item['sentence_ids'],'placements':placements,'last_complete_sentence_end_s':total-3,'final_hold_s':3,'included_silent_tail_s':3-finalextra,'duration_s':total,'caption_timing_basis':'provider word boundaries with display/reading mapping' if word_groups else 'provisional display cues','new_tts':False,'actual_listening':False,'source_story_sha256':hashlib.sha256((E/'director/top20-production-v1/shorts_story_plan.json').read_bytes()).hexdigest()})
 save(D/'caption_mapping.json',{'cues':captions})
 receipts.append({'id':kind,'project':str(D),'duration_s':total,'sentence_count':len(placements),'timing_locked':bool(timeline['timing_locked'] and exact.get('timing_locked'))})
save(H/'shorts_build_receipt.json',receipts)
print(json.dumps(receipts,ensure_ascii=False))
