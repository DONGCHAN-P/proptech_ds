from pathlib import Path
import json
r=Path('video/public/pilot-v8')
script=json.loads((r/'script.json').read_text(encoding='utf8'))
fix={'gwanggyo-growth':('십팔억 육천칠백오십만','십팔억 칠천만'),'distribution':('천팔백이십구','천팔백이십팔'),'unjeong':('칠억 이천오백만','칠억 이천팔백만'),'gimpo':('사억 구천팔백만','사억 구천칠백만'),'recovery':('이십이 점 일','이십이 점 이')}
for s in script['segments']:
 if s['id'] in fix:
  a,b=fix[s['id']];s['text']=s['text'].replace(a,b)
  if (r/(s['id']+'.mp3')).exists():(r/(s['id']+'.mp3')).rename(r/(s['id']+'-previous.mp3'))
(r/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2),encoding='utf8')
base=json.loads(Path('video/public/pilot-v5/plan.json').read_text(encoding='utf8'));s=base['segments'][3];s['text']=s['text'].replace('이천칠백칠십구','이천칠백팔십칠');s['file']='volume-refresh.mp3';s['folder']='pilot-v8'
(r/'base-extra.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf8')
for old,new in [('ContinuationV6','ContinuationV8'),('MediaV7','MediaV8')]:
 p=Path('video/src/'+old+'.tsx').read_text(encoding='utf-8-sig').replace("../public/pilot-v5/leaders.json","../public/pilot-v8/representatives.json").replace("../public/pilot-v2/metrics.json","../public/pilot-v8/regional.json").replace("'./ContinuationV6'","'./ContinuationV8'")
 Path('video/src/'+new+'.tsx').write_text(p,encoding='utf8')
p=Path('analysis/build_v8.py').read_text(encoding='utf8')
p=p.replace('p=re.sub(','''p=p.replace("./ContinuationV6","./ContinuationV8").replace("./MediaV7","./MediaV8").replace("pilot-v5/plan.json","pilot-v8/base-extra.json").replace("pilot-v5/leaders.json","pilot-v8/representatives.json").replace("pilot-v2/metrics.json","pilot-v8/regional.json").replace('2,779','2,787')
p=re.sub(''',1).replace("Path('video/public/pilot-v5/plan.json')","Path('video/public/pilot-v8/base-extra.json')").replace('range(2779)','range(2787)')
Path('analysis/build_v8.py').write_text(p,encoding='utf8')
p=Path('video/src/ExpandedV8.tsx').read_text(encoding='utf8').replace('pilot-v2/metrics.json','pilot-v8/regional.json').replace('2,779','2,787').replace('r.count/2779','r.count/2787').replace('18.675','18.70').replace('국평36건','국평37건').replace('1,829','1,828').replace('122.1','122.2').replace('75.1','75.0')
Path('video/src/ExpandedV8.tsx').write_text(p,encoding='utf8')
