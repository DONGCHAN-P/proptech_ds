from pathlib import Path
import json
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-preview');p=q/'findings.json';f=json.loads(p.read_text(encoding='utf-8'))
for x in f:
 if x['issue_id']=='QAV6-003':x['issue_id']='QAV6-004'
f.append({'issue_id':'QAV6-003','scene_id':'M002','timecode':'units 009,010','severity':'required','문제':'한 문장 내 여러 업무지 발화에 강조가 MBC/강남으로 고정됨','evidence':'root source/timeline review; rendered-frame verification pending','수정안':'목적지 절마다 caption/focus를 일치시키고 지도판과 표 모션은 유지','owner':'editor_v6','status':'open','checked_revision':'production-v6-preview initial timeline'})
p.write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf-8')
