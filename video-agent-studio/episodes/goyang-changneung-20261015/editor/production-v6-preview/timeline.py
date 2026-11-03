from pathlib import Path
import json,re,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v6-preview'
units=json.loads((EP/'narration/preview-v6/segments.json').read_text(encoding='utf-8'))
intro_at=round(units[0]['end_s']*30);intro_duration=150
def frame(t):return round(t*30)+(intro_duration if t>=units[0]['end_s']-.00001 else 0)
def setting(u):
 s=u['scene_id'];n=int(u['file'].split('_')[1].split('.')[0]);t=u['text'];p={'board':'plan','focus':'all'}
 if s=='M000':p={'board':'legacy','cue':'M000_C2'} if n==1 else {'board':'series'} if n==2 else {'board':'plan','focus':'all'}
 if s=='M001':p={'board':'legacy','cue':'M001_C1'} if n==1 else {'board':'legacy','cue':'M000_C2'} if n==2 else {'board':'plan','focus':'all'}
 if s=='M002':
  p={'board':'legacy','cue':'M002_C1' if n<=2 else 'M002_C3'} if n<=5 else {'board':'commute','focus':'all'}
  if n in [9,12,13,14]:p['focus']='상암 MBC'
  if n==10:p['focus']='강남역'
 if s=='M003':p={'board':'legacy','cue':'M003_C6' if n<=3 else 'M003_C2' if n==4 else 'M003_C5' if n<=6 else 'M003_C15' if n>=13 else 'M003_C10'}
 if s=='M003' and n<=3:p={'board':'transit','focus':'원흥' if n==1 else '새절'}
 if s=='M003' and 7<=n<=12:p={'board':'calendar','variant':'rail'}
 if s=='M004':p={'board':'price','focus':'S4' if 6<=n<=8 else 'all'} if n<=8 else {'board':'alternatives','focus':'all'}
 if s=='M005':
  p={'board':'calendar','variant':'school'} if n<=3 or n==17 else {'board':'legacy','cue':'M005_C4' if n<=5 else 'M005_C6' if n==6 else 'M005_C8' if n<=9 else 'M005_C10' if n<=12 else 'M005_C14' if n==14 else 'M005_C13'}
 if s=='M006':p={'board':'supply'} if n<=8 else {'board':'restrictions'}
 if s=='M007':p={'board':'alternatives','focus':'all'} if n<=4 or n>=12 else {'board':'pair','pair':0 if n<=6 else 1 if n<=9 else 2}
 if s=='M008':p={'board':'family'}
 if s=='M009':p={'board':'decision','focus':'S4' if n<=4 else 'S5' if n<=6 else 'S1' if n<=8 else 'all'} if n<=11 else {'board':'next'} if n==12 else {'board':'legacy','cue':'M009_C23'}
 return p
def chunks(t):
 # Split only at word boundaries, preserving numeric and named-entity tokens.
 # Keep multi-token currency, block+quantity, dates and sizes intact.
 protected=re.sub(r'(?:약\s*)?\d[\d,.]*(?:억\s*\d[\d,.]*만)?\s*원(?:입니다)?|S[145]\s+\d[\d,]*세대',lambda m:m.group().replace(' ','\u00a0'),t)
 ws=protected.split(' ');out=[];cur=''
 for w in ws:
  if len(cur)+len(w)+1>48 and cur:out.append(cur);cur=w
  else:cur=(cur+' '+w).strip()
 if cur:out.append(cur)
 return [x.replace('\u00a0',' ') for x in out]
overrides={
 'M002_009.wav':['세 위치의 결과를 묶으면 광화문역은 약 65분에서 70분,','상암 MBC는 약 45분에서 65분입니다.'],
 'M002_010.wav':['여의도역은 약 60분에서 80분,','마곡 LG사이언스파크는 약 70분에서 80분,','강남역은 약 85분에서 95분입니다.'],
 'M002_014.wav':['상암을 오가는 가구와','강남을 오가는 가구의 판단이 달라져야 하는 이유입니다.'],
 'M004_004.wav':['S5는 약 7억 7,700만 원,','S1은 약 7억 9,000만 원,','S4는 약 8억 7,300만 원입니다.'],
 'M006_003.wav':['오늘 비교한 세 후보만 놓으면','2028년 1월 S5 759세대,','2029년 5월 S1 494세대,','2030년 3월 S4 1,024세대가 입주 예정입니다.'],
 'M007_005.wav':['삼송2차아이파크는 9억 2,000만 원,','삼송원흥역센트럴푸르지오는 8억 5,000만 원입니다.'],
 'M007_007.wav':['도래울센트럴더포레는 7억 4,500만 원,','동산동의 기존 창릉호반써밋은 약 8억 3,800만 원입니다.'],
 'M007_010.wav':['지축역센트럴푸르지오는 약 11억 2,800만 원,','지축역중흥 S-클래스 북한산파크뷰는 8억 4,500만 원입니다.']}
intervals=[];sentence_rows=[]
for i,u in enumerate(units):
 start=0 if i==0 else frame(u['start_s']);end=intro_at if i==0 else frame(u['end_s']);p=setting(u);cs=overrides.get(u['file'],chunks(u['text']));total=sum(len(c) for c in cs);pos=start
 for j,c in enumerate(cs):
  pp=dict({'board':'plan','focus':'all'} if u['file']=='M000_002.wav' and j>0 else p)
  if pp['board']=='commute' and u['file'] in ['M002_009.wav','M002_010.wav']:
   pp['focus']=next((x for x in ['광화문역','상암 MBC','여의도역','LG사이언스파크','강남역'] if x in c),'all')
  if u['file']=='M004_004.wav':pp['focus']=next(x for x in ['S5','S1','S4'] if x in c)
  if u['file']=='M002_014.wav':pp['focus']='강남역' if c.startswith('강남') else '상암 MBC'
  en=end if j==len(cs)-1 else start+round((end-start)*sum(len(x) for x in cs[:j+1])/total)
  base={k:v for k,v in pp.items() if k!='focus' or pp['board']=='transit'}
  intervals.append({'scene_id':u['scene_id'],'unit':u['file'],'start_frame':pos,'end_frame':en,'duration_frames':en-pos,'props':{**pp,'caption':c},'caption_timing_basis':'measured sentence boundaries; proportional internal word-group estimate','board_key':json.dumps(base,sort_keys=True)})
  pos=en
 sentence_rows.append({'scene_id':u['scene_id'],'unit':u['file'],'start_frame':start,'end_frame':end,'props':p})
speech_end=frame(units[-1]['end_s']);hold=90;outro=300
intervals.append({'scene_id':'CTA_HOLD','unit':'hold','start_frame':speech_end,'end_frame':speech_end+hold,'duration_frames':hold,'props':{'board':'legacy','cue':'M009_C23','caption':'','hideCaption':True},'board_key':'hold'})
scenes=[]
for s in dict.fromkeys(u['scene_id'] for u in units):
 rows=[x for x in sentence_rows if x['scene_id']==s];scenes.append({'scene_id':s,'start_frame':rows[0]['start_frame'],'end_frame':rows[-1]['end_frame'],'timing_basis':'measured free TTS PCM sentence boundaries; internal captions estimated','audio_revision':'audio-v6-preview-heami-rateminus1'})
project={'revision':'production-v6-preview','fps':30,'width':1920,'height':1080,'duration_frames':speech_end+hold+outro,'intro_at':intro_at,'intro_frames':150,'outro_start':speech_end+hold,'outro_frames':300,'speech_end_frame':speech_end,'intervals':intervals,'sentences':sentence_rows,'scenes':scenes,'inputs':{'script':'outputs/script-review-v6/script_v6.md','script_sha256':hashlib.sha256((EP/'outputs/script-review-v6/script_v6.md').read_bytes()).hexdigest(),'audio':'outputs/production-v6-preview/audio/narration_v6_preview.wav'},'actual_listening':False,'continuous_playback':False}
(O/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8');(E/'scene_proposal.json').write_text(json.dumps({'revision':'timing-proposal-v6-preview','duration_frames':project['duration_frames'],'scenes':scenes,'intro_insert_after_first_question_frame':intro_at,'speech_end_frame':speech_end,'outro_start_frame':speech_end+hold,'caption_basis':'sentence PCM measured; internal phrase timing provisional'},ensure_ascii=False,indent=2),encoding='utf-8')
(O/'captions.json').write_text(json.dumps([{'text':x['props']['caption'],'startMs':x['start_frame']/30*1000,'endMs':x['end_frame']/30*1000,'timestampMs':None,'confidence':None} for x in intervals if x['props']['caption']],ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Timeline: {project['duration_frames']/30:.3f}s; {len(intervals)} caption intervals; intro at {intro_at/30:.3f}s")
