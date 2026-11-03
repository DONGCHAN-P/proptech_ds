"""Prepare local revised metadata, preserving the existing complete source credits."""
from pathlib import Path
import json,re
D=Path(__file__).resolve().parent;E=D.parents[1];O=E/'outputs/top20-enhance-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
t=read(D/'locked_timing.json');old=read(E/'outputs/top20-production-v1/metadata/main.json')
byid={s['scene_id']:s for s in t['scenes']}
chosen=[('O001','신혼부부는 어디에 살까'),('O002','집계 기준'),('S003','20위부터 16위'),('I001','같은 규모, 다른 변화'),('S008','15위부터 11위'),('I002','전체와 초혼·재혼 구성'),('S013','10위부터 6위'),('I003','서울·경기·인천 분포'),('S018','5위부터 1위'),('N001','초혼 기준으로 다시 읽는 TOP20'),('N002','같은 지역, 달라지는 비교 목록'),('C001','우리 부부의 지역 비교')]
chapters=[]
for sid,name in chosen:
 sec=int(byid[sid]['start_s']);chapters.append(f'{sec//60:02d}:{sec%60:02d} {name}')
desc=re.sub(r'(?m)^\d{2}:\d{2} .+\n?','',old['description']);desc=re.sub(r'\n{3,}','\n\n',desc)
_,rest=desc.split('\n\n',1)
intro='수도권 53개 구의 신혼부부 TOP20. 규모·전년 변화·부부 구성과 초혼 기준에서 바뀌는 지역을 비교합니다.'
desc=intro+'\n\n'+'\n'.join(chapters)+'\n\n'+rest
assert len(desc.encode('utf-8'))<=5000
old.update(description=desc,description_utf8_bytes=len(desc.encode('utf-8')),revision='top20-enhance-v2',privacy='private_candidate_not_uploaded',upload_performed_this_revision=False,voice='free Edge InJoon; existing audio reused; only57.345seconds new narration',duration_s=t['duration_s'],chapters=[{'scene_id':sid,'title':name,'start_s':byid[sid]['start_s']}for sid,name in chosen])
O.mkdir(parents=True,exist_ok=True)
(O/'metadata.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'설명란.txt').write_text(old['title']+'\n\n'+desc,encoding='utf-8')
print(json.dumps({'chapters':len(chapters),'duration_s':t['duration_s'],'description_utf8_bytes':old['description_utf8_bytes'],'uploaded':False},ensure_ascii=False))
