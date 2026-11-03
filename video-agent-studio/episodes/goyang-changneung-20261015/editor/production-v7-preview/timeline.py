from pathlib import Path
import json,re,math,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v7-preview';O.mkdir(exist_ok=True)
units=json.loads((EP/'narration/preview-v7/segments.json').read_text(encoding='utf-8-sig'))
chap={'M002':'01 · 일자리','M003':'02 · 교통','M004':'03 · 가격','M007':'04 · 주변 가격 비교','M006':'05 · 공급','M005':'06 · 생활시설'}
def b(mode,active='all',**kw):return dict(mode=mode,active=active,**kw)
def note(title,*lines):return b('note',title=title,lines=list(lines))
def visual(s,n):
 if s=='M000':
  if n in [3,4]:return b('previous')
  if n>=5:return b('plan')
  return note('창릉이 완성되면, 먼저 선택받을 집은?', '가격 수준을 이끌 후보','초기 부담과 도시 완성 효과를 함께 비교')
 if s=='M001':
  if n<=4:return b('transit','원흥')
  if n==6:return b('plan','S5')
  if n==7:return b('plan','S1')
  return b('plan')
 if s=='M002':
  if n<=6:return b('jobs')
  if n<=8:return note('숫자보다 먼저, 조회 조건','블록 대표 좌표 → 표기 목적지','평일 08:00 · 접근·대기·환승 포함 / 현재 교통')
  return b('commute', '광화문역' if n==9 else '상암 MBC' if n in [10,12,13,14,15] else 'LG사이언스파크' if n==11 else '강남역' if n in [16,17] else 'all')
 if s=='M003':
  if n<=3:return b('transit','새절' if n==3 else '원흥')
  if n in [4,5,6,7]:return b('rail', 'GTX' if n==4 else 'S5' if n==5 else 'waiting' if n==6 else 'sameyear')
  if n<=10:return b('plan')
  return note('철도 효과를 가격과 함께 읽기','앞으로 편리해질 여지가 얼마나 남았나','그 기대를 지금 가격에 얼마나 지불하나')
 if s=='M004':
  if n in [2,3]:return b('price_basic' if n==2 else 'price_balcony')
  if n<=7:return b('price')
  if n in [8,9]:return b('price','S4',phase='delta')
  return note('가격 수준과 상승 여력은 다른 질문','미래 가격이 높을 후보 ≠ 가장 높은 수익률','실제 진입가격과 주변 대안을 함께 비교')
 if s=='M007':
  names={5:'지축역센트럴푸르지오',6:'삼송2차아이파크',9:'삼송원흥역센트럴푸르지오',10:'지축역중흥S-클래스북한산파크뷰',11:'지축역중흥S-클래스북한산파크뷰',12:'지축역중흥S-클래스북한산파크뷰',13:'창릉호반써밋',14:'창릉호반써밋',15:'도래울센트럴더포레'}
  if n in names:return b('resale_map',names[n])
  if n in [7,8]:return b('resale_map','삼송2차아이파크')
  return b('resale')
 if s=='M006':
  if n>=17:return b('restrictions',stage=0 if n<18 else 1 if n<20 else 2)
  return b('supply',stage=0 if n<=6 else 1 if n<=10 else 2)
 if s=='M005':
  if n in [4,5,6]:return b('life','IKEA' if n==4 else '롯데아울렛' if n==5 else 'S4')
  if n in [7,8,9,10,11]:return b('school','S5' if n==7 else 'S4' if n==8 else 'S1')
  return note('생활시설은 정착 수요를 보조하는 조건','상권·학교·공원은 실제 이용 시점으로 확인','기존 생활권 수요 · 진입가격 · 직장 접근과 함께')
 if s=='M009':
  if n==6:return b('price','S4',phase='delta')
  if n==7:return note('S4 · 가격 수준 후보의 조건','현재 통근이 모든 업무지에서 최단인 것은 아닙니다','높은 진입가격을 정당화할 수요가 붙는지 확인')
  if n<=9:return b('decision','S4')
  if n<=13:return b('decision','S5')
  if n<=17:return b('decision','S1')
  if n<=21:return b('decision')
  if n==22:return b('previous')
  return note('다음 편 · 하남 교산','데이터로 보는 부동산','구독하고 함께 도시의 변화를 살펴보세요' if n==24 else '시청해 주셔서 감사합니다' if n==25 else '다음 도시에서도 같은 기준으로 비교합니다')
 raise ValueError(s)
def chunks(t):
 parts=re.split(r'(?<=[.!?])\s+|(?<=[,，])\s+',t)
 out=[]
 for x in parts:
  if not x:continue
  if len(x)<=68:out.append(x);continue
  # retain complete number/currency/date phrase; prefer predicate boundaries.
  bits=re.split(r'(?<=고)\s+|(?<=데)\s+|(?<=면)\s+|(?<=서)\s+',x)
  if len(bits)==1:bits=[x]
  cur=''
  for q in bits:
   if cur and len(cur)+len(q)>68:out.append(cur);cur=q
   else:cur=(cur+' '+q).strip()
  if cur:out.append(cur)
 return out
intervals=[];audio=[];captionrows=[];scenes=[];cursor=0;lastscene=None;intro_at=None
for u in units:
 s=u['scene_id'];n=int(u['unit_id'].split('_')[1])
 if s!=lastscene:
  if s in chap:
   intervals.append(dict(start_frame=cursor,end_frame=cursor+90,duration_frames=90,props=b('chapter',chapter=chap[s]),kind='chapter',unit_id=s+'_chapter'));cursor+=90
  scenes.append(dict(scene_id=s,start_frame=cursor,chapter=chap.get(s)))
  lastscene=s
 if s=='M000' and n==5:
  intro_at=cursor;intervals.append(dict(start_frame=cursor,end_frame=cursor+150,duration_frames=150,kind='intro',props={},unit_id='brand_intro'));cursor+=150
 dur=round(u['duration_s']*30);start=cursor;end=start+dur
 audio.append(dict(unit_id=u['unit_id'],audio_path=u['audio_path'],start_frame=start,end_frame=end,original_start_s=u['start_s'],original_end_s=u['end_s']))
 cs=chunks(u['text']);
 if s=='M001' and n==5:cs=[u['text']]
 if s=='M003' and n==2:cs=u['text'].replace('길과 ','길과|').split('|')
 weights=[len(re.sub(r'\s','',x)) for x in cs];total=sum(weights);cut=start
 for j,(t,w) in enumerate(zip(cs,weights)):
  ce=end if j==len(cs)-1 else start+round(dur*sum(weights[:j+1])/total)
  props=visual(s,n)
  if s=='M001' and n==6:props=b('plan','S4' if 'S4' in t else 'S5')
  if s=='M006' and n in [3,6]:
   props=b('supply',stage=0,active='S6' if n==6 else next((z for z in ['S5','S1','S4'] if z in t),'all'))
  # Phrase-level focus changes on a fixed base; internal boundaries are text-weight estimates.
  if s=='M002':
   for key,target in [('광화문','광화문역'),('상암','상암 MBC'),('MBC','상암 MBC'),('여의도','여의도역'),('LG','LG사이언스파크'),('강남','강남역')]:
    if key in t and n>=9:props=b('commute',target)
  if s=='M003' and n==2:props=b('transit','새절' if '새절' in t else '원흥')
  if s=='M003' and n==4:props=b('rail','EP' if '고양은평' in t else 'GTX')
  if s=='M003' and n==5:
   for x in ['S5','S1','S4']:
    if x in t:props=b('rail',x)
  if s=='M004' and n==5:
   for x in ['S5','S1','S4']:
    if x in t:props=b('price',x)
  if s=='M004' and n==9:props=note('같은 조건의 공고가 사례 차이','S4 · S1 대비 약 8,300만원 추가','타입·공고일 차이를 포함한 사례 비교 · 미래 차익 아님')
  if s=='M006' and n==18:props=b('restrictions',stage=1 if '거주의무' in t else 0)
  props['caption']=t
  intervals.append(dict(start_frame=cut,end_frame=ce,duration_frames=ce-cut,props=props,kind='body',unit_id=u['unit_id'],scene_id=s,estimated_internal_boundary=len(cs)>1));captionrows.append(dict(start_frame=cut,end_frame=ce,text=t,unit_id=u['unit_id']));cut=ce
 cursor=end
# exact final audible signal +3s, rounded to frame, preserving the entire PCM tail.
last=units[-1];last_audio=audio[-1];signal=last_audio['start_frame']/30+(1011.533514739-last['start_s']);outro=round((signal+3)*30)
assert outro>=cursor
intervals.append(dict(start_frame=cursor,end_frame=outro,duration_frames=outro-cursor,kind='body',unit_id='last_hold',props={**visual('M009',25),'hideCaption':True,'caption':''}));intervals.append(dict(start_frame=outro,end_frame=outro+300,duration_frames=300,kind='outro',unit_id='brand_outro',props={}))
p=dict(revision='production-v7-preview',script_sha256='ceb9a4e443dc2d7b36cdf84f5c515fa726d501a85e04d82ca81a4439c894bbbc',approval_decision='2f76a375b4a4',fps=30,duration_frames=outro+300,intro_at=intro_at,outro_start=outro,signal_end_s=signal,signal_threshold_dbfs=-60,audio_units=audio,visual_intervals=intervals,captions=captionrows,scenes=scenes,internal_caption_alignment='Text-weight estimates inside individually measured PCM units; no forced alignment',audio_revision='audio-v7-preview-heami-rate0',paid_generation=False)
(O/'project_v7.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
def ts(f):
 ms=round(f/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(O/'captions_v7.srt').write_text('\n\n'.join(f'{i+1}\n{ts(x["start_frame"])} --> {ts(x["end_frame"])}\n{x["text"]}' for i,x in enumerate(captionrows))+'\n',encoding='utf-8')
(E/'scene_proposal.json').write_text(json.dumps({'scenes':scenes,'duration_frames':p['duration_frames'],'outro_start':outro,'speech_signal_end_s':signal,'note':'new measured unit timeline with 150f brand after M000_004 and six 90f silent independent analysis cards; shared state not modified'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(frames=p['duration_frames'],seconds=p['duration_frames']/30,intervals=len(intervals),captions=len(captionrows),outro=outro)))
