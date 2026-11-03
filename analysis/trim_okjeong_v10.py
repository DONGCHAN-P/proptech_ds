from pathlib import Path
import json
p=Path('video/public/pilot-v10/plan.json');d=json.loads(p.read_text(encoding='utf8'))
for s in d['segments']:
 if s['id']=='okjeong':s['text']=s['text'].replace(' 없는 가격을 선으로 채우면 실제보다 연속적인 흐름처럼 보일 수 있습니다.',' 없는 가격은 만들어 채우지 않습니다.')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');(p.parent/'okjeong.mp3').rename(p.parent/'okjeong-first.mp3')
