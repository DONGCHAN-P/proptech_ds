from pathlib import Path
import json
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5';p=json.loads((O/'timing_locked.json').read_text(encoding='utf8'));state='functions'
ai_source='하남시 2025.12.17 참여 계획 · 청정하남 2026.10.01 사업기간 · 하남시의회 2026.07.16 지정 추진\n공식 발표 사실 자체 재구성 · 발표 사진·조감도·기관 로고 미사용 · 실제 입주/고용 완료 아님'
for x in p['visual_intervals']:
 if x['kind']!='body':continue
 q=x['props'];sc=x['scene_id'];text=q.get('phrase_text','');parent=q.get('parent_unit_id','');n=int(parent.split('_')[-1]) if parent else 999
 q['motionFrame']=44
 if sc=='M000':
  if n in [4,5]:q.update(reviewKind='series',phase='previous')
  elif n in [2,3,7,8]:q.update(reviewKind='v4_regions',focus='all')
 elif sc=='M001':
  q.update(reviewKind='overview',highlight='jobs' if '자족' in text else 'park' if '공원' in text else 'home' if '주택' in text else '')
  if n>=10:q.update(reviewKind='v4_regions',focus='all')
 elif sc=='M002':
  q.update(reviewKind='jobsExternal' if n<=11 else 'jobsInternal',focus={5:'잠실역',6:'강남역',7:'판교역'}.get(n,'all'))
  if n==14:
   if '구체적으로' in text:state='functions'
   if '하남시는 2025' in text or any(a in text for a in ['KT클라우드','KT자산운용','포스텍','카네기멜론','싱가포르']):state='participants'
   if '구상에는' in text:state='functions'
   if '사업기간' in text or '2030년까지' in text:state='period'
   if '자족7' in text:state='industry'
   q.update(reviewKind='v4_ai',stage=state,source=ai_source)
 elif sc=='M003':
  q.update(reviewKind='rail',phase='operating' if n<=5 or n>=17 else 'planned')
  if 13<=n<=16:q.update(reviewKind='v4_calendar')
 elif sc=='M004':
  q.update(reviewKind='price',phase='51' if n in [6,7] else '59' if n==8 else 'extension' if n in [9,10] else 'summary',priceStage='basic' if n in [6,8] or '기본 공급금액' in text else 'total')
  if n==7 and '확장비' in text:q.update(phase='extension51')
  if 13<=n<=15:q.update(reviewKind='v4_area')
 elif sc=='M005':
  q.update(reviewKind='life',lifeFocus='school' if any(a in text for a in ['학교','초등','중학','자녀']) else 'park' if '공원' in text else '')
  if n in [8,9]:q.update(reviewKind='v4_commerce')
  if n in [10,11,12]:q.update(reviewKind='v4_outside',active='camp' if n==10 else 'starfield',source='하남시 청정하남 2026.10.01 · 캠프콜번 2027년 SPC 설립 향후 계획 · 개점일 아님\n스타필드 하남 공식 주소: 미사대로750 · 현재 운영시설 · 지구 밖 시설/교산 도보권 보장 아님 · 도로 © OpenStreetMap contributors/ODbL(2026.10.20)' )
 elif sc=='M006':q.update(reviewKind='supply',phase='scale' if n<=3 or 10<=n<=12 or n==17 else 'restrictions' if 13<=n<=16 else 'dates')
 elif sc=='M007':
  stage=1 if n==7 else 2 if n==8 else 3 if n in [9,10] else 4 if n==11 else 5
  q.update(reviewKind='compare',stage=stage,focus={7:'하남자이',8:'꿈동산신안',9:'대명강변타운',11:'미사레스티아',12:'감일한라비발디'}.get(n,''))
  if n>=16:q.update(reviewKind='v4_area')
 elif sc=='M008':
  if q['active'] in ['C2','B2']:q.update(reviewKind='candidate')
  else:q.update(reviewKind='decision',active='A2' if 14<=n<=16 else '북부' if 12<=n<=13 else '남부' if 17<=n<=19 else '중앙',rows=[dict(label='중앙 · C2 / B2',detail='장래 중심성 · 실제 분양가·역 동선 확인'),dict(label='북부 · A2',detail='초기 생활권 · 공개된 진입조건'),dict(label='남부 · 기업 용지와 녹지',detail='기업 입주 · 일상 이동 실현 여부')])
 elif sc in ['M009','ending']:
  q.update(reviewKind='series',phase='cta' if n>=9 else 'previous')
  if n==1:q.update(reviewKind='candidate',active='C2')
  if n==2:q.update(reviewKind='decision',active='중앙',rows=[dict(label='교통·생활시설',detail='이곳에 살 수요를 만드는 조건'),dict(label='진입가격',detail='실제로 감당할 수 있는 가격')])
  if n==3:
   q.update(reviewKind='price',phase='summary')
   if '기존 단지' in text or '실거래 중위값' in text:
    reference=next(u for u in p['audio_units'] if u['scene_id']=='M007')
    q.update(reviewKind='compare',stage=5,focus='',items=reference['visual']['items'],source='국토교통부 실거래2026.7~9 · 전용83㎡이상85㎡미만 · 5층 이상 · 해제제외 · 중개/직거래 포함 · 중위값/거래건수')
  if n==4:q.update(reviewKind='v4_calendar')
  if n==5:q.update(reviewKind='v4_area')
 # 시각자료 전환은 구절 경계만 사용한다. 화면은 고정하고 대상 강조만 변화한다.
 q['visual_key']=q.get('reviewKind',q['mode'])+'_'+str(q.get('stage',q.get('phase',q.get('active','all'))))+'_'+q.get('focus','')+'_'+q.get('lifeFocus',q.get('highlight',''))
for x in p['visual_intervals']:
 q=x.get('props',{})
 if q.get('reviewKind')=='v4_ai' and q.get('stage')=='participants':q.update(motionFrame=89,motionEnd=89)
rows=[];seen=set()
for x in p['visual_intervals']:
 q=x.get('props',{});parent=q.get('parent_unit_id','');n=int(parent.split('_')[-1]) if parent else 0
 animate=x['kind']=='body' and ((x['scene_id']=='M002' and (n in [5,6,7] or q.get('reviewKind')=='v4_ai')) or (x['scene_id']=='M003' and (n==6 or q.get('reviewKind')=='v4_calendar')) or q.get('reviewKind')=='v4_area' or (q.get('reviewKind')=='price' and q.get('phase','').startswith('extension')) or (x['scene_id']=='M009' and n==9))
 key=(x['scene_id'],q.get('visual_key'))
 if animate and key not in seen and x['duration_frames']>50:
  seen.add(key)
  length=90 if q.get('stage')=='participants' else 45
  length=min(length,x['duration_frames']-1)
  for i in range(length):rows.append(dict(x,start_frame=x['start_frame']+i,end_frame=x['start_frame']+i+1,duration_frames=1,props=dict(q,motionFrame=i)))
  rows.append(dict(x,start_frame=x['start_frame']+length,duration_frames=x['duration_frames']-length,props=dict(q,motionFrame=q.get('motionEnd',44))))
 else:rows.append(x)
p['visual_intervals']=rows
assert sum(x['duration_frames'] for x in rows)==p['duration_frames']
(O/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(intervals=len(rows),motion_sequences=len(seen),duration_s=p['duration_frames']/30)))
