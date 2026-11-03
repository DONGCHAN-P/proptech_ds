from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v2';O.mkdir(exist_ok=True)
p=json.loads((EP/'outputs/production-v1/rendered_project_r3.json').read_text(encoding='utf8'))
for x in p['visual_intervals']:
 if x['kind']!='body':continue
 q=x['props'];sc=x['scene_id'];n=int(x['unit_id'].split('_')[-1]) if x['unit_id'].split('_')[-1].isdigit() else 999;q['reviewKind']=None
 if sc=='M000' and n in [4,5]:q.update(reviewKind='series',phase='previous')
 elif sc=='M001':q.update(reviewKind='overview')
 elif sc=='M002':q.update(reviewKind='jobsExternal' if n<=11 else 'jobsInternal')
 elif sc=='M003':q.update(reviewKind='rail',phase='operating' if n<=5 else 'planned' if n<=12 else 'calendar' if n<=16 else 'operating')
 elif sc=='M004':q.update(reviewKind='price',phase='51' if n in [6,7] else '59' if n==8 else 'extension' if n in [9,10] else 'summary',priceStage='basic' if n in [6,8] else 'total')
 elif sc=='M005':q.update(reviewKind='life')
 elif sc=='M006':q.update(reviewKind='supply',phase='scale' if n<=3 or 10<=n<=12 or n==17 else 'restrictions' if 13<=n<=16 else 'dates')
 elif sc=='M007':
  stage=1 if n==7 else 2 if n==8 else 3 if n in [9,10] else 4 if n==11 else 5
  focus={7:'하남자이',8:'꿈동산신안',9:'대명강변타운',11:'미사레스티아',12:'감일한라비발디'}.get(n,'')
  q.update(reviewKind='compare',stage=stage,focus=focus)
 elif sc=='M008':
  if q['active'] in ['C2','B2']:q.update(reviewKind='candidate')
  else:
   a='북부' if 12<=n<=16 else '남부' if 17<=n<=19 else '중앙'
   rows=[dict(label='중앙 · C2 / B2',detail='장래 중심성 · 실제 분양가·역 동선 확인'),dict(label='북부 · A2',detail='초기 생활권 · 공개된 진입조건'),dict(label='남부 · 자족과 녹지',detail='기업 입주 · 일상 이동 실현 여부')]
   q.update(reviewKind='decision',active='A2' if 14<=n<=16 else a,rows=rows)
 elif sc in ['M009','ending']:q.update(reviewKind='series',phase='cta' if n>=9 else 'previous')
 if q['reviewKind'] is None:del q['reviewKind']
 else:q['reviewUnit']=n
rows=[]
for x in p['visual_intervals']:
 if x.get('unit_id')=='M009_009':
  for i in range(45):rows.append(dict(x,start_frame=x['start_frame']+i,end_frame=x['start_frame']+i+1,duration_frames=1,props=dict(x['props'],motionFrame=i)))
  rows.append(dict(x,start_frame=x['start_frame']+45,duration_frames=x['duration_frames']-45))
 else:rows.append(x)
p['visual_intervals']=rows
assert p['duration_frames']==29808
(O/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'duration_frames':p['duration_frames'],'changed_intervals':sum(bool(x.get('props',{}).get('reviewKind')) for x in p['visual_intervals'])}))

