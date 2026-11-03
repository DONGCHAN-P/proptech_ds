from pathlib import Path
import json
p=Path('video/public/pilot-v10/plan.json');plan=json.loads(p.read_text(encoding='utf8'))
removals={'gwanggyo-growth':' 오른쪽 라벨은 마지막 거래 분기와 거래 건수입니다.','unjeong':' 가격과 함께 표본 수를 보면 선을 읽는 근거가 더 분명해집니다.','gimpo':' 이 단지도 한 번도 오르지 않은 곳은 아닙니다.','okjeong':' 가격 옆의 기간과 표본을 함께 읽겠습니다.'}
for s in plan['segments']:
 if s['id'] in removals:s['text']=s['text'].replace(removals[s['id']],'')
q=p.parent/'gwanggyo-growth.mp3'
if q.exists():q.rename(p.parent/'gwanggyo-growth-first.mp3')
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
