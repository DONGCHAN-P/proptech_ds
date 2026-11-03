from pathlib import Path
import re,json,hashlib
EP=Path(__file__).resolve().parents[1];data=json.loads((EP/'writer/scenes_v1.json').read_text(encoding='utf8'));out=EP/'narration';units=[]
spoken={'GTX-D':'지티엑스 디','GTX':'지티엑스','A2':'에이 투','A-2':'에이 투','A3':'에이 쓰리','A-3':'에이 쓰리','LH':'엘에이치','DMC':'디엠씨','㎡':'제곱미터','5호선':'오호선','3호선':'삼호선','9호선':'구호선'}
for s in data:
 for n,u in enumerate(s['units'],1):
  t=u['text'];say=t
  for a,b in sorted(spoken.items(),key=lambda x:-len(x[0])):say=say.replace(a,b)
  units.append(dict(scene_id=s['scene_id'],title=s['title'],unit_id=f"{s['scene_id']}_{n:03}",file=f"{s['scene_id']}_{n:03}.wav",text=t,spoken_text=say,visual=u.get('visual',s.get('visual',{})),claim_ids=u.get('claim_ids',[])))
(out/'units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
(out/'input_manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256((EP/'writer/scenes_v1.json').read_bytes()).hexdigest(),engine='Windows SAPI COM Heami',rate=2,cost=0,network=False,semantic_unit_count=len(units),narration_characters=sum(len(u['text'])for u in units)),indent=2),encoding='utf8')
print('prepared',len(units),'units',sum(len(u['text'])for u in units),'characters')
